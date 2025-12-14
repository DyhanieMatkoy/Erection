"""Conflict Resolution Service

This module provides conflict resolution strategies for handling
simultaneous modifications to the same data across different nodes.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    SyncNode, SyncChange, ObjectVersionHistory, SyncOperation,
    Base
)
from .sync_manager import SyncManager

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy:
    """Base class for conflict resolution strategies"""
    
    def resolve(self, local_data: Dict[str, Any], remote_data: Dict[str, Any],
               local_updated: datetime, remote_updated: datetime,
               source_node_id: str) -> Dict[str, Any]:
        """Resolve conflict between local and remote data
        
        Args:
            local_data: Local entity data
            remote_data: Remote entity data
            local_updated: Local update timestamp
            remote_updated: Remote update timestamp
            source_node_id: Source node ID
            
        Returns:
            Resolved entity data
        """
        raise NotImplementedError


class ServerWinsStrategy(ConflictResolutionStrategy):
    """Server wins conflict resolution strategy"""
    
    def resolve(self, local_data: Dict[str, Any], remote_data: Dict[str, Any],
               local_updated: datetime, remote_updated: datetime,
               source_node_id: str) -> Dict[str, Any]:
        """Server always wins - keep local data"""
        logger.info(f"Server wins conflict: keeping local data updated at {local_updated}")
        return local_data


class TimestampWinsStrategy(ConflictResolutionStrategy):
    """Timestamp-based conflict resolution strategy"""
    
    def resolve(self, local_data: Dict[str, Any], remote_data: Dict[str, Any],
               local_updated: datetime, remote_updated: datetime,
               source_node_id: str) -> Dict[str, Any]:
        """Most recent timestamp wins"""
        if remote_updated > local_updated:
            logger.info(f"Remote wins conflict: remote data updated at {remote_updated} vs local {local_updated}")
            return remote_data
        else:
            logger.info(f"Local wins conflict: local data updated at {local_updated} vs remote {remote_updated}")
            return local_data


class ManualResolutionStrategy(ConflictResolutionStrategy):
    """Manual conflict resolution strategy"""
    
    def resolve(self, local_data: Dict[str, Any], remote_data: Dict[str, Any],
               local_updated: datetime, remote_updated: datetime,
               source_node_id: str) -> Dict[str, Any]:
        """Store both versions for manual resolution"""
        # This strategy would require UI intervention
        # For now, we'll store the conflict and return local data
        logger.warning(f"Manual resolution required for conflict between local ({local_updated}) and remote ({remote_updated})")
        return local_data


class ConflictResolver:
    """Conflict resolution service"""
    
    def __init__(self, sync_manager: SyncManager):
        """Initialize conflict resolver
        
        Args:
            sync_manager: Sync manager instance
        """
        self.sync_manager = sync_manager
        self.strategies = {
            'server_wins': ServerWinsStrategy(),
            'timestamp_wins': TimestampWinsStrategy(),
            'manual': ManualResolutionStrategy()
        }
        self.default_strategy = 'server_wins'
    
    def detect_conflict(self, entity_type: str, entity_uuid: str,
                      remote_data: Dict[str, Any], remote_updated: datetime,
                      source_node_id: str) -> bool:
        """Detect if there's a conflict for an entity
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            remote_data: Remote entity data
            remote_updated: Remote update timestamp
            source_node_id: Source node ID
            
        Returns:
            True if conflict detected
        """
        # Get local entity
        local_data = self.sync_manager.serialize_entity(entity_type, entity_uuid)
        if not local_data:
            # No local entity, no conflict
            return False
        
        local_updated = datetime.fromisoformat(
            local_data.get('updated_at', '').replace('Z', '+00:00')
        )
        
        # Check if both entities were modified after last sync
        # This is a simplified conflict detection
        # In practice, you'd track last sync time per entity
        return True
    
    def resolve_conflict(self, entity_type: str, entity_uuid: str,
                      remote_data: Dict[str, Any], remote_updated: datetime,
                      source_node_id: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """Resolve a conflict for an entity
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            remote_data: Remote entity data
            remote_updated: Remote update timestamp
            source_node_id: Source node ID
            strategy: Resolution strategy to use
            
        Returns:
            Resolved entity data
        """
        if not strategy:
            strategy = self.default_strategy
        
        if strategy not in self.strategies:
            logger.error(f"Unknown conflict resolution strategy: {strategy}")
            strategy = self.default_strategy
        
        # Get local entity
        local_data = self.sync_manager.serialize_entity(entity_type, entity_uuid)
        if not local_data:
            # No local entity, accept remote
            return remote_data
        
        local_updated = datetime.fromisoformat(
            local_data.get('updated_at', '').replace('Z', '+00:00')
        )
        
        # Store conflict version if versioning is enabled
        self._store_conflict_version(entity_type, entity_uuid, local_data, remote_data,
                                  source_node_id)
        
        # Apply resolution strategy
        resolver = self.strategies[strategy]
        resolved_data = resolver.resolve(local_data, remote_data, local_updated,
                                    remote_updated, source_node_id)
        
        # Log resolution
        self._log_resolution(entity_type, entity_uuid, strategy, local_updated,
                          remote_updated, source_node_id)
        
        return resolved_data
    
    def _store_conflict_version(self, entity_type: str, entity_uuid: str,
                              local_data: Dict[str, Any], remote_data: Dict[str, Any],
                              source_node_id: str) -> None:
        """Store conflicting version in history
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            local_data: Local entity data
            remote_data: Remote entity data
            source_node_id: Source node ID
        """
        with self.sync_manager.get_session() as session:
            # Store remote version (local version is already in database)
            version = ObjectVersionHistory(
                id=UUID(),
                entity_uuid=entity_uuid,
                entity_type=entity_type,
                source_node_id=source_node_id,
                serialized_data=remote_data,
                conflict_resolution="AUTO_RESOLVED"
            )
            session.add(version)
            session.commit()
    
    def _log_resolution(self, entity_type: str, entity_uuid: str, strategy: str,
                      local_updated: datetime, remote_updated: datetime,
                      source_node_id: str) -> None:
        """Log conflict resolution decision
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            strategy: Resolution strategy used
            local_updated: Local update timestamp
            remote_updated: Remote update timestamp
            source_node_id: Source node ID
        """
        logger.info(f"Conflict resolved for {entity_type} {entity_uuid}:")
        logger.info(f"  Strategy: {strategy}")
        logger.info(f"  Local updated: {local_updated}")
        logger.info(f"  Remote updated: {remote_updated}")
        logger.info(f"  Source node: {source_node_id}")
    
    def get_conflict_history(self, entity_type: Optional[str] = None,
                           entity_uuid: Optional[str] = None,
                           limit: int = 100) -> List[ObjectVersionHistory]:
        """Get conflict history
        
        Args:
            entity_type: Filter by entity type
            entity_uuid: Filter by entity UUID
            limit: Maximum number of records to return
            
        Returns:
            List of conflict history records
        """
        with self.sync_manager.get_session() as session:
            query = session.query(ObjectVersionHistory)
            
            if entity_type:
                query = query.filter(ObjectVersionHistory.entity_type == entity_type)
            
            if entity_uuid:
                query = query.filter(ObjectVersionHistory.entity_uuid == entity_uuid)
            
            return query.order_by(ObjectVersionHistory.arrival_time.desc()).limit(limit).all()
    
    def get_unresolved_conflicts(self) -> List[ObjectVersionHistory]:
        """Get unresolved conflicts
        
        Returns:
            List of unresolved conflict records
        """
        with self.sync_manager.get_session() as session:
            return session.query(ObjectVersionHistory).filter(
                ObjectVersionHistory.conflict_resolution == "PENDING"
            ).order_by(ObjectVersionHistory.arrival_time.desc()).all()
    
    def manually_resolve_conflict(self, version_id: str, resolution_data: Dict[str, Any],
                                resolver_name: str) -> bool:
        """Manually resolve a conflict
        
        Args:
            version_id: ID of conflict version to resolve
            resolution_data: Resolved entity data
            resolver_name: Name of person resolving
            
        Returns:
            True if resolved successfully
        """
        try:
            with self.sync_manager.get_session() as session:
                # Get conflict version
                version = session.query(ObjectVersionHistory).filter(
                    ObjectVersionHistory.id == version_id
                ).first()
                
                if not version:
                    logger.error(f"Conflict version not found: {version_id}")
                    return False
                
                # Apply resolved data
                entity_type = version.entity_type
                entity_uuid = version.entity_uuid
                
                success = self.sync_manager.apply_change(
                    entity_type, entity_uuid, SyncOperation.UPDATE, resolution_data
                )
                
                if success:
                    # Mark conflict as resolved
                    version.conflict_resolution = f"MANUAL_RESOLVED_BY_{resolver_name}"
                    version.resolved_at = datetime.now(timezone.utc)
                    version.serialized_data = resolution_data  # Store resolved version
                    session.commit()
                    
                    logger.info(f"Manually resolved conflict {version_id} by {resolver_name}")
                    return True
                
                return False
        
        except Exception as e:
            logger.error(f"Error manually resolving conflict {version_id}: {e}")
            return False
    
    def set_default_strategy(self, strategy: str) -> bool:
        """Set default conflict resolution strategy
        
        Args:
            strategy: Strategy name
            
        Returns:
            True if strategy was set
        """
        if strategy in self.strategies:
            self.default_strategy = strategy
            logger.info(f"Set default conflict resolution strategy to: {strategy}")
            return True
        else:
            logger.error(f"Unknown conflict resolution strategy: {strategy}")
            return False
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available conflict resolution strategies
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())
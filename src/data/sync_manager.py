"""Synchronization Manager

This module provides the core synchronization functionality for the construction
time management system, including change tracking, conflict resolution,
and data serialization.
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Type
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import and_, or_, desc
from sqlalchemy.event import listen
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import insert as standard_insert

from .models import (
    SyncNode, SyncChange, ObjectVersionHistory, SyncOperation,
    Base, User, Person, Organization, Counterparty, Object, Work,
    Estimate, EstimateLine, DailyReport, DailyReportLine, Timesheet, TimesheetLine,
    Material, CostItem, Unit, WorkSpecification
)
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SyncManager:
    """Core synchronization manager for handling data changes and sync operations"""
    
    # Mapping of entity names to SQLAlchemy model classes
    ENTITY_MODEL_MAP: Dict[str, Type[Base]] = {
        'User': User,
        'Person': Person,
        'Organization': Organization,
        'Counterparty': Counterparty,
        'Object': Object,
        'Work': Work,
        'Estimate': Estimate,
        'EstimateLine': EstimateLine,
        'DailyReport': DailyReport,
        'DailyReportLine': DailyReportLine,
        'Timesheet': Timesheet,
        'TimesheetLine': TimesheetLine,
        'Material': Material,
        'CostItem': CostItem,
        'Unit': Unit,
        'WorkSpecification': WorkSpecification,
    }
    
    # List of synchronizable entity names
    SYNCHRONIZABLE_ENTITIES = list(ENTITY_MODEL_MAP.keys())
    
    def __init__(self, db_manager: DatabaseManager, node_id: Optional[str] = None):
        """Initialize sync manager
        
        Args:
            db_manager: Database manager instance
            node_id: UUID of this sync node (None for server)
        """
        self.db_manager = db_manager
        self.node_id = node_id
        self._session_factory = None
        self._setup_session_factory()
        
    def _setup_session_factory(self):
        """Setup SQLAlchemy session factory"""
        try:
            engine = self.db_manager.get_engine()
            self._session_factory = sessionmaker(bind=engine)
        except Exception:
            # Fallback for legacy database manager
            self._session_factory = None
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self._session_factory:
            self._setup_session_factory()
        return self._session_factory()
    
    def register_node(self, code: str, name: str) -> str:
        """Register a new sync node
        
        Args:
            code: Unique node code
            name: Human-readable node name
            
        Returns:
            UUID of the registered node
        """
        with self.get_session() as session:
            # Check if node already exists
            existing = session.query(SyncNode).filter(SyncNode.code == code).first()
            if existing:
                return str(existing.id)
            
            # Create new node
            node = SyncNode(
                id=uuid.uuid4(),
                code=code,
                name=name
            )
            session.add(node)
            session.commit()
            
            logger.info(f"Registered sync node: {code} ({name})")
            return str(node.id)
    
    def get_node_by_code(self, code: str) -> Optional[SyncNode]:
        """Get sync node by code"""
        with self.get_session() as session:
            return session.query(SyncNode).filter(SyncNode.code == code).first()
    
    def get_node_by_id(self, node_id: str) -> Optional[SyncNode]:
        """Get sync node by ID"""
        with self.get_session() as session:
            return session.query(SyncNode).filter(SyncNode.id == node_id).first()
    
    def register_change(self, entity_type: str, entity_uuid: str, 
                     operation: SyncOperation, target_node_id: Optional[str] = None) -> None:
        """Register a change for synchronization
        
        Args:
            entity_type: Type of entity that changed
            entity_uuid: UUID of the entity
            operation: Type of operation (INSERT/UPDATE/DELETE)
            target_node_id: Target node for this change (None for broadcast)
        """
        if entity_type not in self.SYNCHRONIZABLE_ENTITIES:
            logger.warning(f"Skipping sync registration for non-synchronizable entity: {entity_type}")
            return
        
        with self.get_session() as session:
            # Get next change ID
            max_id = session.query(SyncChange).order_by(desc(SyncChange.id)).first()
            next_id = (max_id.id + 1) if max_id else 1
            
            # Create change record
            change = SyncChange(
                id=next_id,
                node_id=target_node_id or self.node_id,
                entity_type=entity_type,
                entity_uuid=entity_uuid,
                operation=operation
            )
            session.add(change)
            session.commit()
            
            logger.debug(f"Registered change: {entity_type} {entity_uuid} {operation.value}")
    
    def get_pending_changes(self, target_node_id: str, limit: int = 1000) -> List[SyncChange]:
        """Get pending changes for a target node
        
        Args:
            target_node_id: UUID of target node
            limit: Maximum number of changes to return
            
        Returns:
            List of pending changes
        """
        with self.get_session() as session:
            return session.query(SyncChange).filter(
                and_(
                    SyncChange.node_id == target_node_id,
                    SyncChange.packet_no.is_(None)
                )
            ).order_by(SyncChange.created_at).limit(limit).all()
    
    def mark_changes_sent(self, change_ids: List[int], packet_no: int) -> None:
        """Mark changes as sent in a packet
        
        Args:
            change_ids: List of change IDs to mark
            packet_no: Packet number
        """
        with self.get_session() as session:
            session.query(SyncChange).filter(
                SyncChange.id.in_(change_ids)
            ).update({
                SyncChange.packet_no: packet_no
            }, synchronize_session=False)
            session.commit()
    
    def acknowledge_packet(self, source_node_id: str, packet_no: int) -> None:
        """Acknowledge receipt of a packet
        
        Args:
            source_node_id: UUID of source node
            packet_no: Packet number to acknowledge
        """
        with self.get_session() as session:
            # Update node's received packet number
            node = session.query(SyncNode).filter(SyncNode.id == source_node_id).first()
            if node:
                node.received_packet_no = packet_no
                node.last_sync_in = datetime.now(timezone.utc)
                session.commit()
            
            # Delete acknowledged changes
            session.query(SyncChange).filter(
                and_(
                    SyncChange.node_id == source_node_id,
                    SyncChange.packet_no <= packet_no
                )
            ).delete(synchronize_session=False)
            session.commit()
    
    def serialize_entity(self, entity_type: str, entity_uuid: str) -> Optional[Dict[str, Any]]:
        """Serialize an entity to JSON format
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            
        Returns:
            Serialized entity data or None if not found
        """
        if entity_type not in self.ENTITY_MODEL_MAP:
            logger.error(f"Unknown entity type: {entity_type}")
            return None
        
        model_class = self.ENTITY_MODEL_MAP[entity_type]
        
        with self.get_session() as session:
            entity = session.query(model_class).filter(
                model_class.uuid == entity_uuid,
                model_class.is_deleted == False
            ).first()
            
            if not entity:
                return None
            
            # Convert entity to dictionary
            data = {}
            for column in entity.__table__.columns:
                value = getattr(entity, column.name)
                
                # Handle UUID objects
                if hasattr(value, 'hex'):
                    value = str(value)
                # Handle datetime objects
                elif isinstance(value, datetime):
                    value = value.isoformat()
                # Handle decimal objects
                elif hasattr(value, 'float'):
                    value = float(value)
                
                data[column.name] = value
            
            return data
    
    def deserialize_entity(self, entity_type: str, data: Dict[str, Any]) -> Base:
        """Deserialize entity from JSON data
        
        Args:
            entity_type: Type of entity
            data: Serialized entity data
            
        Returns:
            Entity instance
        """
        if entity_type not in self.ENTITY_MODEL_MAP:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        model_class = self.ENTITY_MODEL_MAP[entity_type]
        
        # Create entity instance
        entity = model_class()
        
        for column_name, value in data.items():
            if hasattr(entity, column_name):
                # Handle UUID fields
                if column_name == 'uuid' and isinstance(value, str):
                    value = uuid.UUID(value)
                # Handle datetime fields
                elif column_name.endswith('_at') and isinstance(value, str):
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                
                setattr(entity, column_name, value)
        
        return entity
    
    def apply_change(self, entity_type: str, entity_uuid: str, 
                   operation: SyncOperation, data: Optional[Dict[str, Any]] = None,
                   source_node_id: Optional[str] = None) -> bool:
        """Apply a change to the local database
        
        Args:
            entity_type: Type of entity
            entity_uuid: UUID of entity
            operation: Operation to apply
            data: Entity data (for INSERT/UPDATE)
            source_node_id: Source node ID
            
        Returns:
            True if change was applied successfully
        """
        if entity_type not in self.ENTITY_MODEL_MAP:
            logger.error(f"Unknown entity type: {entity_type}")
            return False
        
        model_class = self.ENTITY_MODEL_MAP[entity_type]
        
        try:
            with self.get_session() as session:
                if operation == SyncOperation.DELETE:
                    # Soft delete
                    entity = session.query(model_class).filter(
                        model_class.uuid == entity_uuid
                    ).first()
                    if entity:
                        entity.is_deleted = True
                        entity.updated_at = datetime.now(timezone.utc)
                        session.commit()
                        logger.debug(f"Soft deleted {entity_type} {entity_uuid}")
                        return True
                
                elif operation in [SyncOperation.INSERT, SyncOperation.UPDATE]:
                    if not data:
                        logger.error(f"No data provided for {operation.value} operation")
                        return False
                    
                    # Check for existing entity
                    existing = session.query(model_class).filter(
                        model_class.uuid == entity_uuid
                    ).first()
                    
                    if operation == SyncOperation.INSERT and existing:
                        # Conflict - store version history
                        self._store_conflict_version(session, entity_type, entity_uuid, 
                                                 data, source_node_id)
                        return False
                    
                    if operation == SyncOperation.UPDATE and not existing:
                        # Entity doesn't exist, treat as insert
                        operation = SyncOperation.INSERT
                    
                    if operation == SyncOperation.INSERT:
                        # Create new entity
                        entity = self.deserialize_entity(entity_type, data)
                        entity.uuid = entity_uuid
                        entity.updated_at = datetime.now(timezone.utc)
                        session.add(entity)
                        session.commit()
                        logger.debug(f"Inserted {entity_type} {entity_uuid}")
                        return True
                    
                    else:  # UPDATE
                        # Update existing entity
                        for column_name, value in data.items():
                            if hasattr(existing, column_name) and column_name not in ['id', 'uuid']:
                                # Handle UUID fields
                                if column_name == 'uuid' and isinstance(value, str):
                                    value = uuid.UUID(value)
                                # Handle datetime fields
                                elif column_name.endswith('_at') and isinstance(value, str):
                                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                
                                setattr(existing, column_name, value)
                        
                        existing.updated_at = datetime.now(timezone.utc)
                        session.commit()
                        logger.debug(f"Updated {entity_type} {entity_uuid}")
                        return True
        
        except Exception as e:
            logger.error(f"Error applying change to {entity_type} {entity_uuid}: {e}")
            return False
        
        return False
    
    def _store_conflict_version(self, session: Session, entity_type: str, 
                              entity_uuid: str, data: Dict[str, Any],
                              source_node_id: Optional[str]) -> None:
        """Store conflicting version in history
        
        Args:
            session: Database session
            entity_type: Type of entity
            entity_uuid: UUID of entity
            data: Conflicting entity data
            source_node_id: Source node ID
        """
        version = ObjectVersionHistory(
            id=uuid.uuid4(),
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            source_node_id=source_node_id,
            serialized_data=data,
            conflict_resolution="PENDING"
        )
        session.add(version)
        session.commit()
        logger.info(f"Stored conflict version for {entity_type} {entity_uuid}")
    
    def get_sync_packet(self, target_node_id: str, packet_no: int) -> Dict[str, Any]:
        """Create a synchronization packet
        
        Args:
            target_node_id: UUID of target node
            packet_no: Packet number
            
        Returns:
            Sync packet data
        """
        # Get pending changes
        changes = self.get_pending_changes(target_node_id)
        
        # Serialize entities
        entities = []
        for change in changes:
            entity_data = self.serialize_entity(change.entity_type, change.entity_uuid)
            if entity_data:
                entities.append({
                    'type': change.entity_type,
                    'uuid': str(change.entity_uuid),
                    'operation': change.operation.value,
                    'data': entity_data
                })
        
        # Get source node info
        source_node = self.get_node_by_id(self.node_id) if self.node_id else None
        
        return {
            'header': {
                'sender_node_id': self.node_id or 'SERVER',
                'recipient_node_id': target_node_id,
                'packet_no': packet_no,
                'ack_packet_no': 0,  # TODO: Get from target node
                'schema_version': '1.0.0',
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            'body': {
                'entities': entities
            }
        }
    
    def process_sync_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming synchronization packet
        
        Args:
            packet_data: Packet data
            
        Returns:
            Processing result
        """
        header = packet_data.get('header', {})
        body = packet_data.get('body', {})
        
        source_node_id = header.get('sender_node_id')
        packet_no = header.get('packet_no')
        ack_packet_no = header.get('ack_packet_no', 0)
        
        if not source_node_id or packet_no is None:
            return {'success': False, 'error': 'Invalid packet header'}
        
        try:
            # Process acknowledgments
            if ack_packet_no > 0:
                self.acknowledge_packet(source_node_id, ack_packet_no)
            
            # Process entities
            entities = body.get('entities', [])
            processed_count = 0
            error_count = 0
            
            for entity_data in entities:
                entity_type = entity_data.get('type')
                entity_uuid = entity_data.get('uuid')
                operation = SyncOperation(entity_data.get('operation'))
                data = entity_data.get('data')
                
                if self.apply_change(entity_type, entity_uuid, operation, data, source_node_id):
                    processed_count += 1
                else:
                    error_count += 1
            
            # Update source node info
            source_node = self.get_node_by_id(source_node_id)
            if source_node:
                with self.get_session() as session:
                    source_node.last_sync_in = datetime.now(timezone.utc)
                    session.commit()
            
            return {
                'success': True,
                'processed_count': processed_count,
                'error_count': error_count
            }
        
        except Exception as e:
            logger.error(f"Error processing sync packet: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for change tracking"""
        for model_class in self.ENTITY_MODEL_MAP.values():
            listen(model_class, 'after_insert', self._after_insert)
            listen(model_class, 'after_update', self._after_update)
            listen(model_class, 'after_delete', self._after_delete)
    
    def _after_insert(self, mapper, connection, target):
        """Handle after insert events"""
        if hasattr(target, 'uuid'):
            self.register_change(
                target.__class__.__name__,
                str(target.uuid),
                SyncOperation.INSERT
            )
    
    def _after_update(self, mapper, connection, target):
        """Handle after update events"""
        if hasattr(target, 'uuid'):
            self.register_change(
                target.__class__.__name__,
                str(target.uuid),
                SyncOperation.UPDATE
            )
    
    def _after_delete(self, mapper, connection, target):
        """Handle after delete events"""
        if hasattr(target, 'uuid'):
            self.register_change(
                target.__class__.__name__,
                str(target.uuid),
                SyncOperation.DELETE
            )


# Global sync manager instance
_sync_manager: Optional[SyncManager] = None


def get_sync_manager(db_manager: DatabaseManager, node_id: Optional[str] = None) -> SyncManager:
    """Get or create global sync manager instance"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager(db_manager, node_id)
        _sync_manager.setup_event_listeners()
    return _sync_manager
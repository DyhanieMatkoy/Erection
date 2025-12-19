"""
UUID Synchronization Service

This service handles UUID-based synchronization for works and related entities,
including conflict resolution and UUID-based foreign key relationships.
"""

import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from enum import Enum

from ..data.database_manager import DatabaseManager
from ..data.models.sqlalchemy_models import Work, Base


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving UUID conflicts during synchronization"""
    LATEST_WINS = "latest_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE_CHANGES = "merge_changes"
    SKIP_CONFLICT = "skip_conflict"


class SyncDirection(Enum):
    """Direction of synchronization"""
    PUSH = "push"  # Local to remote
    PULL = "pull"  # Remote to local
    BIDIRECTIONAL = "bidirectional"


class UUIDSynchronizationService:
    """Service for UUID-based synchronization of works and related data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def find_work_by_uuid(self, session: Session, work_uuid: str) -> Optional[Work]:
        """Find a work record by its UUID"""
        if not work_uuid:
            return None
        
        try:
            return session.query(Work).filter(Work.uuid == work_uuid).first()
        except Exception as e:
            self.logger.error(f"Error finding work by UUID {work_uuid}: {e}")
            return None
    
    def find_works_by_uuids(self, session: Session, work_uuids: List[str]) -> Dict[str, Work]:
        """Find multiple work records by their UUIDs"""
        if not work_uuids:
            return {}
        
        try:
            works = session.query(Work).filter(Work.uuid.in_(work_uuids)).all()
            return {work.uuid: work for work in works}
        except Exception as e:
            self.logger.error(f"Error finding works by UUIDs: {e}")
            return {}
    
    def create_uuid_lookup_index(self, session: Session) -> bool:
        """Create optimized indexes for UUID-based lookups"""
        try:
            # Create UUID index on works table if it doesn't exist
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_works_uuid_lookup 
                ON works(uuid) 
                WHERE uuid IS NOT NULL AND uuid != ''
            """))
            
            # Create indexes on foreign key UUID columns
            fk_tables = [
                ('estimate_lines', 'work_uuid'),
                ('daily_report_lines', 'work_uuid'),
                ('work_execution_register', 'work_uuid'),
                ('cost_item_materials', 'work_uuid'),
                ('work_specifications', 'work_uuid')
            ]
            
            for table_name, uuid_column in fk_tables:
                try:
                    session.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_{uuid_column}_lookup 
                        ON {table_name}({uuid_column}) 
                        WHERE {uuid_column} IS NOT NULL AND {uuid_column} != ''
                    """))
                except Exception as e:
                    # Table or column might not exist, that's OK
                    self.logger.warning(f"Could not create index on {table_name}.{uuid_column}: {e}")
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating UUID lookup indexes: {e}")
            return False
    
    def detect_uuid_conflicts(self, session: Session, external_works: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between local and external work records"""
        conflicts = []
        
        # Get UUIDs from external works
        external_uuids = [work.get('uuid') for work in external_works if work.get('uuid')]
        
        if not external_uuids:
            return conflicts
        
        # Find existing local works with same UUIDs
        local_works = self.find_works_by_uuids(session, external_uuids)
        
        for external_work in external_works:
            external_uuid = external_work.get('uuid')
            if not external_uuid:
                continue
            
            local_work = local_works.get(external_uuid)
            if local_work:
                # Compare timestamps to detect conflicts
                external_updated = external_work.get('updated_at')
                local_updated = local_work.updated_at
                
                if external_updated and local_updated:
                    # Parse external timestamp if it's a string
                    if isinstance(external_updated, str):
                        try:
                            external_updated = datetime.fromisoformat(external_updated.replace('Z', '+00:00'))
                        except ValueError:
                            external_updated = None
                    
                    if external_updated and external_updated != local_updated:
                        conflicts.append({
                            'uuid': external_uuid,
                            'local_work': {
                                'id': local_work.id,
                                'name': local_work.name,
                                'updated_at': local_updated.isoformat() if local_updated else None
                            },
                            'external_work': external_work,
                            'conflict_type': 'timestamp_mismatch'
                        })
        
        return conflicts
    
    def resolve_uuid_conflict(self, session: Session, conflict: Dict[str, Any], 
                             strategy: ConflictResolutionStrategy) -> Dict[str, Any]:
        """Resolve a UUID conflict using the specified strategy"""
        result = {
            'uuid': conflict['uuid'],
            'resolution': strategy.value,
            'success': False,
            'action_taken': None,
            'error': None
        }
        
        try:
            local_work_data = conflict['local_work']
            external_work_data = conflict['external_work']
            
            local_work = self.find_work_by_uuid(session, conflict['uuid'])
            if not local_work:
                result['error'] = "Local work not found"
                return result
            
            if strategy == ConflictResolutionStrategy.LATEST_WINS:
                # Compare timestamps and keep the latest
                local_updated = local_work.updated_at
                external_updated = external_work_data.get('updated_at')
                
                if isinstance(external_updated, str):
                    try:
                        external_updated = datetime.fromisoformat(external_updated.replace('Z', '+00:00'))
                    except ValueError:
                        external_updated = None
                
                if external_updated and (not local_updated or external_updated > local_updated):
                    # External is newer, update local
                    self._update_work_from_external(local_work, external_work_data)
                    result['action_taken'] = 'updated_from_external'
                else:
                    # Local is newer or equal, keep local
                    result['action_taken'] = 'kept_local'
                
                result['success'] = True
            
            elif strategy == ConflictResolutionStrategy.MANUAL_REVIEW:
                # Mark for manual review
                result['action_taken'] = 'marked_for_manual_review'
                result['success'] = True
                # In a real implementation, this would add to a review queue
            
            elif strategy == ConflictResolutionStrategy.MERGE_CHANGES:
                # Attempt to merge non-conflicting changes
                merged = self._merge_work_changes(local_work, external_work_data)
                if merged:
                    result['action_taken'] = 'merged_changes'
                    result['success'] = True
                else:
                    result['action_taken'] = 'merge_failed'
                    result['error'] = 'Could not automatically merge changes'
            
            elif strategy == ConflictResolutionStrategy.SKIP_CONFLICT:
                # Skip this conflict
                result['action_taken'] = 'skipped'
                result['success'] = True
        
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error resolving UUID conflict for {conflict['uuid']}: {e}")
        
        return result
    
    def _update_work_from_external(self, local_work: Work, external_data: Dict[str, Any]):
        """Update local work record with external data"""
        # Update basic fields
        if 'name' in external_data:
            local_work.name = external_data['name']
        if 'code' in external_data:
            local_work.code = external_data['code']
        if 'price' in external_data:
            local_work.price = external_data['price']
        if 'labor_rate' in external_data:
            local_work.labor_rate = external_data['labor_rate']
        if 'unit_id' in external_data:
            local_work.unit_id = external_data['unit_id']
        if 'parent_id' in external_data:
            local_work.parent_id = external_data['parent_id']
        if 'is_group' in external_data:
            local_work.is_group = external_data['is_group']
        
        # Update timestamps
        if 'updated_at' in external_data:
            updated_at = external_data['updated_at']
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except ValueError:
                    updated_at = datetime.now()
            local_work.updated_at = updated_at
    
    def _merge_work_changes(self, local_work: Work, external_data: Dict[str, Any]) -> bool:
        """Attempt to merge changes between local and external work data"""
        try:
            # Simple merge strategy: update non-conflicting fields
            # In a real implementation, this would be more sophisticated
            
            # Only update fields that are different and not null in external
            if external_data.get('name') and external_data['name'] != local_work.name:
                local_work.name = external_data['name']
            
            if external_data.get('code') and external_data['code'] != local_work.code:
                local_work.code = external_data['code']
            
            # For numeric fields, take the non-zero value if one is zero
            if 'price' in external_data:
                ext_price = external_data['price'] or 0
                if ext_price > 0 and local_work.price == 0:
                    local_work.price = ext_price
            
            if 'labor_rate' in external_data:
                ext_labor = external_data['labor_rate'] or 0
                if ext_labor > 0 and local_work.labor_rate == 0:
                    local_work.labor_rate = ext_labor
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging work changes: {e}")
            return False
    
    def synchronize_works_by_uuid(self, session: Session, external_works: List[Dict[str, Any]], 
                                 direction: SyncDirection = SyncDirection.PULL,
                                 conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_WINS) -> Dict[str, Any]:
        """Synchronize works using UUID-based matching"""
        
        sync_results = {
            'start_time': datetime.now(),
            'end_time': None,
            'direction': direction.value,
            'conflict_strategy': conflict_strategy.value,
            'total_external_works': len(external_works),
            'works_created': 0,
            'works_updated': 0,
            'works_skipped': 0,
            'conflicts_detected': 0,
            'conflicts_resolved': 0,
            'errors': []
        }
        
        try:
            # Detect conflicts
            conflicts = self.detect_uuid_conflicts(session, external_works)
            sync_results['conflicts_detected'] = len(conflicts)
            
            # Process external works
            for external_work in external_works:
                external_uuid = external_work.get('uuid')
                if not external_uuid:
                    sync_results['works_skipped'] += 1
                    continue
                
                try:
                    local_work = self.find_work_by_uuid(session, external_uuid)
                    
                    if local_work:
                        # Check if this work has a conflict
                        conflict = next((c for c in conflicts if c['uuid'] == external_uuid), None)
                        
                        if conflict:
                            # Resolve conflict
                            resolution = self.resolve_uuid_conflict(session, conflict, conflict_strategy)
                            if resolution['success']:
                                sync_results['conflicts_resolved'] += 1
                                if resolution['action_taken'] in ['updated_from_external', 'merged_changes']:
                                    sync_results['works_updated'] += 1
                            else:
                                sync_results['errors'].append(f"Failed to resolve conflict for UUID {external_uuid}: {resolution.get('error')}")
                        else:
                            # No conflict, update if needed
                            self._update_work_from_external(local_work, external_work)
                            sync_results['works_updated'] += 1
                    
                    else:
                        # Create new work
                        new_work = self._create_work_from_external(external_work)
                        if new_work:
                            session.add(new_work)
                            sync_results['works_created'] += 1
                        else:
                            sync_results['works_skipped'] += 1
                
                except Exception as e:
                    error_msg = f"Error processing work UUID {external_uuid}: {str(e)}"
                    sync_results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            # Commit changes
            session.commit()
            
        except Exception as e:
            session.rollback()
            error_msg = f"Critical error during UUID synchronization: {str(e)}"
            sync_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        finally:
            sync_results['end_time'] = datetime.now()
        
        return sync_results
    
    def _create_work_from_external(self, external_data: Dict[str, Any]) -> Optional[Work]:
        """Create a new work record from external data"""
        try:
            work = Work(
                uuid=external_data.get('uuid', str(uuid.uuid4())),
                name=external_data.get('name', ''),
                code=external_data.get('code'),
                price=external_data.get('price', 0.0),
                labor_rate=external_data.get('labor_rate', 0.0),
                unit_id=external_data.get('unit_id'),
                parent_id=external_data.get('parent_id'),
                is_group=external_data.get('is_group', False),
                marked_for_deletion=external_data.get('marked_for_deletion', False)
            )
            
            # Set timestamps
            if 'updated_at' in external_data:
                updated_at = external_data['updated_at']
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    except ValueError:
                        updated_at = datetime.now()
                work.updated_at = updated_at
            
            return work
            
        except Exception as e:
            self.logger.error(f"Error creating work from external data: {e}")
            return None
    
    def export_works_for_sync(self, session: Session, modified_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export works data for synchronization to external systems"""
        try:
            query = session.query(Work).filter(Work.is_deleted == False)
            
            if modified_since:
                query = query.filter(Work.updated_at > modified_since)
            
            works = query.all()
            
            exported_works = []
            for work in works:
                work_data = {
                    'uuid': work.uuid,
                    'name': work.name,
                    'code': work.code,
                    'price': work.price,
                    'labor_rate': work.labor_rate,
                    'unit_id': work.unit_id,
                    'parent_id': work.parent_id,
                    'is_group': work.is_group,
                    'marked_for_deletion': work.marked_for_deletion,
                    'updated_at': work.updated_at.isoformat() if work.updated_at else None,
                    'created_at': work.created_at.isoformat() if work.created_at else None
                }
                exported_works.append(work_data)
            
            return exported_works
            
        except Exception as e:
            self.logger.error(f"Error exporting works for sync: {e}")
            return []
    
    def validate_uuid_relationships(self, session: Session) -> Dict[str, Any]:
        """Validate UUID-based foreign key relationships"""
        validation_results = {
            'valid_relationships': 0,
            'invalid_relationships': [],
            'orphaned_references': [],
            'validation_passed': False
        }
        
        try:
            # Check works self-references (parent_id)
            orphaned_parents = session.execute(text("""
                SELECT id, uuid, parent_id 
                FROM works 
                WHERE parent_id IS NOT NULL 
                AND parent_id NOT IN (SELECT id FROM works WHERE id IS NOT NULL)
            """)).fetchall()
            
            for orphan in orphaned_parents:
                validation_results['orphaned_references'].append({
                    'table': 'works',
                    'record_id': orphan.id,
                    'record_uuid': orphan.uuid,
                    'invalid_reference': orphan.parent_id,
                    'reference_type': 'parent_id'
                })
            
            # Check UUID-based foreign key tables
            fk_tables = [
                ('estimate_lines', 'work_uuid'),
                ('daily_report_lines', 'work_uuid'),
                ('work_execution_register', 'work_uuid'),
                ('cost_item_materials', 'work_uuid'),
                ('work_specifications', 'work_uuid')
            ]
            
            for table_name, uuid_column in fk_tables:
                try:
                    # Check for orphaned UUID references
                    orphaned_sql = f"""
                    SELECT id, {uuid_column} 
                    FROM {table_name} 
                    WHERE {uuid_column} IS NOT NULL 
                    AND {uuid_column} != ''
                    AND {uuid_column} NOT IN (
                        SELECT uuid FROM works 
                        WHERE uuid IS NOT NULL AND uuid != ''
                    )
                    """
                    
                    orphaned_refs = session.execute(text(orphaned_sql)).fetchall()
                    
                    for orphan in orphaned_refs:
                        validation_results['orphaned_references'].append({
                            'table': table_name,
                            'record_id': orphan.id,
                            'invalid_reference': getattr(orphan, uuid_column),
                            'reference_type': uuid_column
                        })
                
                except Exception as e:
                    # Table might not exist or have UUID column yet
                    self.logger.warning(f"Could not validate {table_name}.{uuid_column}: {e}")
            
            # Count valid relationships
            total_works = session.query(Work).count()
            validation_results['valid_relationships'] = total_works - len(validation_results['orphaned_references'])
            
            # Determine if validation passed
            validation_results['validation_passed'] = len(validation_results['orphaned_references']) == 0
            
        except Exception as e:
            self.logger.error(f"Error validating UUID relationships: {e}")
        
        return validation_results
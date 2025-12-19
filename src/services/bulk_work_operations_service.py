"""
Bulk Work Operations Service

This service provides bulk operations specifically for work records,
including bulk unit assignments, validation, and integrity checks.
Implements requirements 5.3, 5.4 for bulk operations and data integrity.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import logging
from datetime import datetime

from ..data.models.sqlalchemy_models import Work, Unit, WorkUnitMigration
from ..data.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class BulkWorkOperationsService:
    """Service for bulk operations on work records"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def bulk_update_unit_assignments(
        self, 
        work_unit_mappings: List[Dict[str, Any]], 
        validate_integrity: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk update work unit assignments
        
        Args:
            work_unit_mappings: List of dicts with 'work_id' and 'unit_id' keys
            validate_integrity: Whether to validate referential integrity
            batch_size: Number of records to process in each batch
            
        Returns:
            Dict with operation results
            
        Validates: Requirements 5.3, 5.4 - Bulk operations with integrity checks
        """
        results = {
            'success_count': 0,
            'failure_count': 0,
            'errors': [],
            'processed_batches': 0,
            'total_records': len(work_unit_mappings)
        }
        
        if not work_unit_mappings:
            return results
        
        try:
            with self.db_manager.get_session() as session:
                # Process in batches for better performance
                for i in range(0, len(work_unit_mappings), batch_size):
                    batch = work_unit_mappings[i:i + batch_size]
                    batch_results = self._process_unit_assignment_batch(
                        session, batch, validate_integrity
                    )
                    
                    results['success_count'] += batch_results['success_count']
                    results['failure_count'] += batch_results['failure_count']
                    results['errors'].extend(batch_results['errors'])
                    results['processed_batches'] += 1
                    
                    # Commit each batch to avoid long-running transactions
                    session.commit()
                    
                logger.info(f"Bulk unit assignment completed: {results['success_count']} successful, {results['failure_count']} failed")
                
        except Exception as e:
            logger.error(f"Bulk unit assignment failed: {str(e)}")
            results['errors'].append(f"Critical error: {str(e)}")
            
        return results
    
    def _process_unit_assignment_batch(
        self, 
        session: Session, 
        batch: List[Dict[str, Any]], 
        validate_integrity: bool
    ) -> Dict[str, Any]:
        """Process a single batch of unit assignments"""
        batch_results = {
            'success_count': 0,
            'failure_count': 0,
            'errors': []
        }
        
        for mapping in batch:
            try:
                work_id = mapping.get('work_id')
                unit_id = mapping.get('unit_id')
                
                if not work_id:
                    batch_results['errors'].append("Missing work_id in mapping")
                    batch_results['failure_count'] += 1
                    continue
                
                # Validate integrity if requested
                if validate_integrity:
                    validation_error = self._validate_unit_assignment(session, work_id, unit_id)
                    if validation_error:
                        batch_results['errors'].append(f"Work {work_id}: {validation_error}")
                        batch_results['failure_count'] += 1
                        continue
                
                # Update the work record
                work = session.query(Work).filter(Work.id == work_id).first()
                if not work:
                    batch_results['errors'].append(f"Work {work_id} not found")
                    batch_results['failure_count'] += 1
                    continue
                
                work.unit_id = unit_id
                work.modified_at = datetime.now()
                
                batch_results['success_count'] += 1
                
            except Exception as e:
                batch_results['errors'].append(f"Work {mapping.get('work_id', 'unknown')}: {str(e)}")
                batch_results['failure_count'] += 1
        
        return batch_results
    
    def _validate_unit_assignment(self, session: Session, work_id: int, unit_id: Optional[int]) -> Optional[str]:
        """Validate a single unit assignment"""
        # Check if work exists and is not deleted
        work = session.query(Work).filter(
            and_(Work.id == work_id, Work.marked_for_deletion == False)
        ).first()
        
        if not work:
            return "Work not found or marked for deletion"
        
        # If unit_id is provided, validate it exists
        if unit_id is not None:
            unit = session.query(Unit).filter(
                and_(Unit.id == unit_id, Unit.marked_for_deletion == False)
            ).first()
            
            if not unit:
                return f"Unit {unit_id} not found or marked for deletion"
        
        return None
    
    def bulk_validate_referential_integrity(
        self, 
        work_ids: List[int], 
        check_units: bool = True,
        check_hierarchy: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk validate referential integrity for work records
        
        Args:
            work_ids: List of work IDs to validate
            check_units: Whether to validate unit references
            check_hierarchy: Whether to validate hierarchy relationships
            batch_size: Number of records to process in each batch
            
        Returns:
            Dict with validation results
            
        Validates: Requirements 5.1, 5.2 - Data integrity validation
        """
        results = {
            'valid_count': 0,
            'invalid_count': 0,
            'validation_errors': [],
            'processed_batches': 0,
            'total_records': len(work_ids)
        }
        
        if not work_ids:
            return results
        
        try:
            with self.db_manager.get_session() as session:
                # Process in batches
                for i in range(0, len(work_ids), batch_size):
                    batch = work_ids[i:i + batch_size]
                    batch_results = self._validate_integrity_batch(
                        session, batch, check_units, check_hierarchy
                    )
                    
                    results['valid_count'] += batch_results['valid_count']
                    results['invalid_count'] += batch_results['invalid_count']
                    results['validation_errors'].extend(batch_results['validation_errors'])
                    results['processed_batches'] += 1
                
                logger.info(f"Bulk validation completed: {results['valid_count']} valid, {results['invalid_count']} invalid")
                
        except Exception as e:
            logger.error(f"Bulk validation failed: {str(e)}")
            results['validation_errors'].append(f"Critical error: {str(e)}")
            
        return results
    
    def _validate_integrity_batch(
        self, 
        session: Session, 
        work_ids: List[int], 
        check_units: bool, 
        check_hierarchy: bool
    ) -> Dict[str, Any]:
        """Validate integrity for a batch of work records"""
        batch_results = {
            'valid_count': 0,
            'invalid_count': 0,
            'validation_errors': []
        }
        
        # Get all works in batch
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        work_dict = {work.id: work for work in works}
        
        for work_id in work_ids:
            work = work_dict.get(work_id)
            if not work:
                batch_results['validation_errors'].append(f"Work {work_id}: Not found")
                batch_results['invalid_count'] += 1
                continue
            
            is_valid = True
            
            # Validate unit reference
            if check_units and work.unit_id is not None:
                unit = session.query(Unit).filter(
                    and_(Unit.id == work.unit_id, Unit.marked_for_deletion == False)
                ).first()
                
                if not unit:
                    batch_results['validation_errors'].append(
                        f"Work {work_id}: Invalid unit_id {work.unit_id}"
                    )
                    is_valid = False
            
            # Validate hierarchy
            if check_hierarchy and work.parent_id is not None:
                # Check parent exists
                parent = session.query(Work).filter(
                    and_(Work.id == work.parent_id, Work.marked_for_deletion == False)
                ).first()
                
                if not parent:
                    batch_results['validation_errors'].append(
                        f"Work {work_id}: Invalid parent_id {work.parent_id}"
                    )
                    is_valid = False
                else:
                    # Check for circular references
                    if self._has_circular_reference(session, work_id, work.parent_id):
                        batch_results['validation_errors'].append(
                            f"Work {work_id}: Circular reference detected"
                        )
                        is_valid = False
            
            if is_valid:
                batch_results['valid_count'] += 1
            else:
                batch_results['invalid_count'] += 1
        
        return batch_results
    
    def _has_circular_reference(self, session: Session, work_id: int, parent_id: int) -> bool:
        """Check if setting parent_id would create a circular reference"""
        visited = set()
        current_id = parent_id
        
        while current_id is not None and current_id not in visited:
            if current_id == work_id:
                return True
            
            visited.add(current_id)
            
            # Get parent of current work
            parent_work = session.query(Work).filter(Work.id == current_id).first()
            if parent_work:
                current_id = parent_work.parent_id
            else:
                break
        
        return False
    
    def bulk_migrate_legacy_units(
        self, 
        work_ids: List[int], 
        auto_apply_threshold: float = 0.8,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk migrate legacy unit strings to unit_id references
        
        Args:
            work_ids: List of work IDs to migrate
            auto_apply_threshold: Confidence threshold for automatic application
            batch_size: Number of records to process in each batch
            
        Returns:
            Dict with migration results
            
        Validates: Requirements 1.3, 1.5 - Legacy unit migration
        """
        results = {
            'migrated_count': 0,
            'pending_count': 0,
            'error_count': 0,
            'errors': [],
            'processed_batches': 0,
            'total_records': len(work_ids)
        }
        
        if not work_ids:
            return results
        
        try:
            # Import migration service
            from .unit_matching_service import UnitMatchingService
            
            matching_service = UnitMatchingService(self.db_manager)
            
            with self.db_manager.get_session() as session:
                # Process in batches
                for i in range(0, len(work_ids), batch_size):
                    batch = work_ids[i:i + batch_size]
                    batch_results = self._migrate_legacy_units_batch(
                        session, batch, matching_service, auto_apply_threshold
                    )
                    
                    results['migrated_count'] += batch_results['migrated_count']
                    results['pending_count'] += batch_results['pending_count']
                    results['error_count'] += batch_results['error_count']
                    results['errors'].extend(batch_results['errors'])
                    results['processed_batches'] += 1
                    
                    # Commit each batch
                    session.commit()
                
                logger.info(f"Bulk legacy migration completed: {results['migrated_count']} migrated, {results['pending_count']} pending")
                
        except Exception as e:
            logger.error(f"Bulk legacy migration failed: {str(e)}")
            results['errors'].append(f"Critical error: {str(e)}")
            
        return results
    
    def _migrate_legacy_units_batch(
        self, 
        session: Session, 
        work_ids: List[int], 
        matching_service, 
        auto_apply_threshold: float
    ) -> Dict[str, Any]:
        """Migrate legacy units for a batch of work records"""
        batch_results = {
            'migrated_count': 0,
            'pending_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        # Get works that need migration (have legacy unit but no unit_id)
        works = session.query(Work).filter(
            and_(
                Work.id.in_(work_ids),
                Work.unit_id.is_(None),
                Work.unit.isnot(None),
                Work.unit != '',
                Work.marked_for_deletion == False
            )
        ).all()
        
        for work in works:
            try:
                # Try to match legacy unit to unit_id
                match_result = matching_service.find_unit_match(work.unit)
                
                if match_result and match_result['confidence'] >= auto_apply_threshold:
                    # Auto-apply high-confidence matches
                    work.unit_id = match_result['unit_id']
                    work.modified_at = datetime.now()
                    
                    # Update migration tracking
                    migration_entry = session.query(WorkUnitMigration).filter(
                        WorkUnitMigration.work_id == work.id
                    ).first()
                    
                    if migration_entry:
                        migration_entry.migration_status = 'completed'
                        migration_entry.matched_unit_id = match_result['unit_id']
                        migration_entry.confidence_score = match_result['confidence']
                        migration_entry.updated_at = datetime.now()
                    
                    batch_results['migrated_count'] += 1
                else:
                    # Mark for manual review
                    migration_entry = session.query(WorkUnitMigration).filter(
                        WorkUnitMigration.work_id == work.id
                    ).first()
                    
                    if not migration_entry:
                        migration_entry = WorkUnitMigration(
                            work_id=work.id,
                            legacy_unit=work.unit,
                            migration_status='manual',
                            manual_review_reason='Low confidence match or no match found'
                        )
                        session.add(migration_entry)
                    else:
                        migration_entry.migration_status = 'manual'
                        migration_entry.manual_review_reason = 'Low confidence match or no match found'
                        migration_entry.updated_at = datetime.now()
                    
                    if match_result:
                        migration_entry.matched_unit_id = match_result['unit_id']
                        migration_entry.confidence_score = match_result['confidence']
                    
                    batch_results['pending_count'] += 1
                
            except Exception as e:
                batch_results['errors'].append(f"Work {work.id}: {str(e)}")
                batch_results['error_count'] += 1
        
        return batch_results
    
    def get_bulk_operation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about bulk operations and data integrity
        
        Returns:
            Dict with various statistics
        """
        stats = {
            'total_works': 0,
            'works_with_unit_id': 0,
            'works_with_legacy_unit': 0,
            'works_needing_migration': 0,
            'migration_status_breakdown': {},
            'integrity_issues': {
                'invalid_unit_references': 0,
                'invalid_parent_references': 0,
                'circular_references': 0
            }
        }
        
        try:
            with self.db_manager.get_session() as session:
                # Basic counts
                stats['total_works'] = session.query(Work).filter(
                    Work.marked_for_deletion == False
                ).count()
                
                stats['works_with_unit_id'] = session.query(Work).filter(
                    and_(Work.unit_id.isnot(None), Work.marked_for_deletion == False)
                ).count()
                
                stats['works_with_legacy_unit'] = session.query(Work).filter(
                    and_(
                        Work.unit.isnot(None), 
                        Work.unit != '', 
                        Work.marked_for_deletion == False
                    )
                ).count()
                
                stats['works_needing_migration'] = session.query(Work).filter(
                    and_(
                        Work.unit_id.is_(None),
                        Work.unit.isnot(None),
                        Work.unit != '',
                        Work.marked_for_deletion == False
                    )
                ).count()
                
                # Migration status breakdown
                migration_status_query = session.query(
                    WorkUnitMigration.migration_status,
                    session.query(WorkUnitMigration).filter(
                        WorkUnitMigration.migration_status == WorkUnitMigration.migration_status
                    ).count().label('count')
                ).group_by(WorkUnitMigration.migration_status).all()
                
                for status, count in migration_status_query:
                    stats['migration_status_breakdown'][status] = count
                
                # Integrity issues (simplified checks)
                # Invalid unit references
                invalid_unit_refs = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM works w
                    LEFT JOIN units u ON w.unit_id = u.id
                    WHERE w.unit_id IS NOT NULL 
                    AND (u.id IS NULL OR u.marked_for_deletion = 1)
                    AND w.marked_for_deletion = 0
                """)).fetchone()
                
                stats['integrity_issues']['invalid_unit_references'] = invalid_unit_refs[0] if invalid_unit_refs else 0
                
                # Invalid parent references
                invalid_parent_refs = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM works w
                    LEFT JOIN works p ON w.parent_id = p.id
                    WHERE w.parent_id IS NOT NULL 
                    AND (p.id IS NULL OR p.marked_for_deletion = 1)
                    AND w.marked_for_deletion = 0
                """)).fetchone()
                
                stats['integrity_issues']['invalid_parent_references'] = invalid_parent_refs[0] if invalid_parent_refs else 0
                
        except Exception as e:
            logger.error(f"Failed to get bulk operation statistics: {str(e)}")
            stats['error'] = str(e)
        
        return stats
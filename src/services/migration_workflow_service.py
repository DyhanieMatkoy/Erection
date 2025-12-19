"""Migration workflow service for work unit migration

This service orchestrates the complete unit migration process,
including batch processing, progress tracking, and status reporting.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..data.models.sqlalchemy_models import Work, Unit, WorkUnitMigration
from ..data.database_manager import DatabaseManager
from .unit_matching_service import UnitMatchingService
from .work_unit_migration_service import WorkUnitMigrationService


class MigrationWorkflowService:
    """Service for orchestrating unit migration workflow"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.unit_matching_service = UnitMatchingService(db_manager)
        self.migration_service = WorkUnitMigrationService(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def analyze_migration_scope(self) -> Dict[str, Any]:
        """Analyze the scope of migration work needed"""
        with self.db_manager.get_session() as session:
            # Migration is complete - legacy unit column has been removed
            # All works should now use unit_id foreign key relationships
            legacy_works = []
            unique_units = set()
            work_count_by_unit = {}
            
            # Get existing migration entries
            existing_entries = session.query(WorkUnitMigration).count()
            
            return {
                'total_works_needing_migration': len(legacy_works),
                'unique_legacy_units': len(unique_units),
                'legacy_unit_strings': list(unique_units),
                'work_count_by_unit': work_count_by_unit,
                'existing_migration_entries': existing_entries,
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def create_migration_plan(self, batch_size: int = 100) -> Dict[str, Any]:
        """Create a migration plan with batch processing"""
        analysis = self.analyze_migration_scope()
        
        # Get matching statistics for all unique units
        legacy_units = analysis['legacy_unit_strings']
        match_stats = self.unit_matching_service.get_match_statistics(legacy_units)
        
        # Calculate estimated processing time (rough estimate)
        total_works = analysis['total_works_needing_migration']
        estimated_batches = (total_works + batch_size - 1) // batch_size
        estimated_minutes = estimated_batches * 2  # Rough estimate: 2 minutes per batch
        
        return {
            'analysis': analysis,
            'match_statistics': match_stats,
            'batch_size': batch_size,
            'estimated_batches': estimated_batches,
            'estimated_processing_time_minutes': estimated_minutes,
            'plan_created_at': datetime.now().isoformat()
        }
    
    def execute_migration_batch(self, batch_size: int = 100, 
                               start_offset: int = 0) -> Dict[str, Any]:
        """Execute a single batch of migration"""
        batch_start_time = datetime.now()
        
        with self.db_manager.get_session() as session:
            # Get works for this batch
            # Migration is complete - no works need migration
            works_query = session.query(Work).filter(False)  # Empty query.offset(start_offset).limit(batch_size)
            
            works = works_query.all()
            
            if not works:
                return {
                    'batch_number': (start_offset // batch_size) + 1,
                    'works_processed': 0,
                    'results': [],
                    'processing_time_seconds': 0,
                    'message': 'No more works to process'
                }
            
            batch_results = []
            
            for work in works:
                try:
                    # Check if migration entry already exists
                    existing_entry = session.query(WorkUnitMigration).filter(
                        WorkUnitMigration.work_id == work.id
                    ).first()
                    
                    if existing_entry:
                        batch_results.append({
                            'work_id': work.id,
                            'legacy_unit': work.unit,
                            'status': 'skipped',
                            'reason': 'migration_entry_exists'
                        })
                        continue
                    
                    # Find best match for the unit
                    matched_unit, confidence, match_type = self.unit_matching_service.find_best_match(work.unit)
                    
                    # Determine migration status based on confidence and match type
                    if match_type == 'exact' or (match_type.startswith('fuzzy') and confidence >= 0.9):
                        migration_status = 'matched'
                    elif match_type == 'no_match' or confidence < 0.5:
                        migration_status = 'manual'
                        manual_review_reason = f'Low confidence match: {confidence:.2f}'
                    else:
                        migration_status = 'pending'
                        manual_review_reason = f'Medium confidence: {confidence:.2f}, type: {match_type}'
                    
                    # Create migration entry
                    migration_entry = WorkUnitMigration(
                        work_id=work.id,
                        legacy_unit=work.unit,
                        matched_unit_id=matched_unit.id if matched_unit else None,
                        migration_status=migration_status,
                        confidence_score=confidence,
                        manual_review_reason=manual_review_reason if migration_status != 'matched' else None
                    )
                    
                    session.add(migration_entry)
                    
                    batch_results.append({
                        'work_id': work.id,
                        'legacy_unit': work.unit,
                        'matched_unit_id': matched_unit.id if matched_unit else None,
                        'matched_unit_name': matched_unit.name if matched_unit else None,
                        'confidence_score': confidence,
                        'match_type': match_type,
                        'migration_status': migration_status,
                        'status': 'processed'
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error processing work {work.id}: {str(e)}")
                    batch_results.append({
                        'work_id': work.id,
                        'legacy_unit': work.unit,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Commit the batch
            session.commit()
            
            batch_end_time = datetime.now()
            processing_time = (batch_end_time - batch_start_time).total_seconds()
            
            return {
                'batch_number': (start_offset // batch_size) + 1,
                'works_processed': len(works),
                'results': batch_results,
                'processing_time_seconds': processing_time,
                'batch_completed_at': batch_end_time.isoformat()
            }
    
    def execute_full_migration(self, batch_size: int = 100) -> Dict[str, Any]:
        """Execute complete migration process in batches"""
        migration_start_time = datetime.now()
        
        # Create migration plan
        plan = self.create_migration_plan(batch_size)
        
        all_results = []
        batch_number = 0
        total_processed = 0
        
        self.logger.info(f"Starting full migration with {plan['estimated_batches']} estimated batches")
        
        while True:
            batch_result = self.execute_migration_batch(
                batch_size=batch_size,
                start_offset=batch_number * batch_size
            )
            
            if batch_result['works_processed'] == 0:
                break
            
            all_results.append(batch_result)
            total_processed += batch_result['works_processed']
            batch_number += 1
            
            self.logger.info(f"Completed batch {batch_number}, processed {total_processed} works")
        
        migration_end_time = datetime.now()
        total_time = (migration_end_time - migration_start_time).total_seconds()
        
        # Get final statistics
        final_stats = self.migration_service.get_migration_statistics()
        
        return {
            'migration_plan': plan,
            'batches_executed': batch_number,
            'total_works_processed': total_processed,
            'batch_results': all_results,
            'final_statistics': final_stats,
            'total_processing_time_seconds': total_time,
            'migration_completed_at': migration_end_time.isoformat()
        }
    
    def apply_migration_results(self, auto_apply_threshold: float = 0.9) -> Dict[str, Any]:
        """Apply migration results to work records"""
        application_start_time = datetime.now()
        
        with self.db_manager.get_session() as session:
            # Get all completed migrations above threshold
            high_confidence_migrations = session.query(WorkUnitMigration).filter(
                and_(
                    WorkUnitMigration.migration_status == 'matched',
                    WorkUnitMigration.confidence_score >= auto_apply_threshold,
                    WorkUnitMigration.matched_unit_id.isnot(None)
                )
            ).all()
            
            applied_count = 0
            errors = []
            
            for migration in high_confidence_migrations:
                try:
                    # Update the work record
                    work = session.query(Work).filter(Work.id == migration.work_id).first()
                    if work:
                        work.unit_id = migration.matched_unit_id
                        migration.migration_status = 'completed'
                        applied_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error applying migration for work {migration.work_id}: {str(e)}")
                    errors.append({
                        'work_id': migration.work_id,
                        'error': str(e)
                    })
            
            session.commit()
            
            application_end_time = datetime.now()
            processing_time = (application_end_time - application_start_time).total_seconds()
            
            return {
                'applied_count': applied_count,
                'errors': errors,
                'auto_apply_threshold': auto_apply_threshold,
                'processing_time_seconds': processing_time,
                'application_completed_at': application_end_time.isoformat()
            }
    
    def get_migration_progress(self) -> Dict[str, Any]:
        """Get current migration progress"""
        stats = self.migration_service.get_migration_statistics()
        
        # Calculate progress percentages
        total_entries = stats['total_entries']
        if total_entries > 0:
            status_percentages = {}
            for status, count in stats['status_counts'].items():
                status_percentages[status] = round((count / total_entries) * 100, 2)
        else:
            status_percentages = {}
        
        return {
            'statistics': stats,
            'status_percentages': status_percentages,
            'progress_timestamp': datetime.now().isoformat()
        }
    
    def get_manual_review_items(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get items requiring manual review"""
        manual_migrations = self.migration_service.get_manual_review_migrations()
        
        if limit:
            manual_migrations = manual_migrations[:limit]
        
        items = []
        with self.db_manager.get_session() as session:
            for migration in manual_migrations:
                work = session.query(Work).filter(Work.id == migration.work_id).first()
                
                # Get potential matches for review
                potential_matches = self.unit_matching_service.similarity_match(
                    migration.legacy_unit, max_results=3
                )
                
                items.append({
                    'work_id': migration.work_id,
                    'work_name': work.name if work else 'Unknown',
                    'legacy_unit': migration.legacy_unit,
                    'confidence_score': migration.confidence_score,
                    'manual_review_reason': migration.manual_review_reason,
                    'potential_matches': [
                        {
                            'unit_id': unit.id,
                            'unit_name': unit.name,
                            'similarity': similarity
                        }
                        for unit, similarity in potential_matches
                    ]
                })
        
        return items
    
    def resolve_manual_review(self, work_id: int, selected_unit_id: Optional[int] = None) -> bool:
        """Resolve a manual review item"""
        try:
            migration = self.migration_service.get_migration_entry(work_id)
            if not migration:
                return False
            
            if selected_unit_id:
                # Apply the selected unit
                with self.db_manager.get_session() as session:
                    work = session.query(Work).filter(Work.id == work_id).first()
                    if work:
                        work.unit_id = selected_unit_id
                        migration.matched_unit_id = selected_unit_id
                        migration.migration_status = 'completed'
                        migration.confidence_score = 1.0  # Manual selection = 100% confidence
                        session.commit()
                        return True
            else:
                # Mark as no match needed
                migration.migration_status = 'no_match_needed'
                migration.manual_review_reason = 'Manual review: no unit assignment needed'
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving manual review for work {work_id}: {str(e)}")
            return False
    
    def reset_migration(self) -> Dict[str, Any]:
        """Reset migration state (for testing/restart)"""
        reset_start_time = datetime.now()
        
        # Clear all migration entries
        cleared_count = self.migration_service.clear_all_migrations()
        
        # Reset unit_id on works that were migrated
        with self.db_manager.get_session() as session:
            works_reset = session.query(Work).filter(
                and_(
                    Work.unit_id.isnot(None),
                    Work.unit.isnot(None),
                    Work.unit != ''
                )
            ).update({Work.unit_id: None})
            session.commit()
        
        reset_end_time = datetime.now()
        processing_time = (reset_end_time - reset_start_time).total_seconds()
        
        return {
            'migration_entries_cleared': cleared_count,
            'works_reset': works_reset,
            'processing_time_seconds': processing_time,
            'reset_completed_at': reset_end_time.isoformat()
        }
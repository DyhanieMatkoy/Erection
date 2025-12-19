"""Work unit migration service

This service provides CRUD operations and utilities for managing
work unit migration tracking.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..data.models.sqlalchemy_models import WorkUnitMigration, Work, Unit
from ..data.database_manager import DatabaseManager


class WorkUnitMigrationService:
    """Service for managing work unit migration tracking"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_migration_entry(self, work_id: int, legacy_unit: str, 
                             matched_unit_id: Optional[int] = None,
                             migration_status: str = 'pending',
                             confidence_score: float = 0.0,
                             manual_review_reason: Optional[str] = None) -> WorkUnitMigration:
        """Create a new migration tracking entry"""
        with self.db_manager.get_session() as session:
            migration_entry = WorkUnitMigration(
                work_id=work_id,
                legacy_unit=legacy_unit,
                matched_unit_id=matched_unit_id,
                migration_status=migration_status,
                confidence_score=confidence_score,
                manual_review_reason=manual_review_reason
            )
            session.add(migration_entry)
            session.commit()
            session.refresh(migration_entry)
            return migration_entry
    
    def get_migration_entry(self, work_id: int) -> Optional[WorkUnitMigration]:
        """Get migration entry by work_id"""
        with self.db_manager.get_session() as session:
            return session.query(WorkUnitMigration).filter(
                WorkUnitMigration.work_id == work_id
            ).first()
    
    def update_migration_entry(self, work_id: int, **kwargs) -> Optional[WorkUnitMigration]:
        """Update migration entry"""
        with self.db_manager.get_session() as session:
            migration_entry = session.query(WorkUnitMigration).filter(
                WorkUnitMigration.work_id == work_id
            ).first()
            
            if migration_entry:
                for key, value in kwargs.items():
                    if hasattr(migration_entry, key):
                        setattr(migration_entry, key, value)
                session.commit()
                session.refresh(migration_entry)
            
            return migration_entry
    
    def delete_migration_entry(self, work_id: int) -> bool:
        """Delete migration entry"""
        with self.db_manager.get_session() as session:
            migration_entry = session.query(WorkUnitMigration).filter(
                WorkUnitMigration.work_id == work_id
            ).first()
            
            if migration_entry:
                session.delete(migration_entry)
                session.commit()
                return True
            return False
    
    def get_migrations_by_status(self, status: str) -> List[WorkUnitMigration]:
        """Get all migration entries by status"""
        with self.db_manager.get_session() as session:
            return session.query(WorkUnitMigration).filter(
                WorkUnitMigration.migration_status == status
            ).all()
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """Get migration statistics"""
        with self.db_manager.get_session() as session:
            # Count by status
            status_counts = session.query(
                WorkUnitMigration.migration_status,
                func.count(WorkUnitMigration.work_id)
            ).group_by(WorkUnitMigration.migration_status).all()
            
            # Total works with legacy units
            total_legacy_works = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    or_(Work.unit_id.is_(None), Work.unit_id == 0)
                )
            ).count()
            
            # Total migration entries
            total_entries = session.query(WorkUnitMigration).count()
            
            # Average confidence score
            avg_confidence = session.query(
                func.avg(WorkUnitMigration.confidence_score)
            ).scalar() or 0.0
            
            return {
                'status_counts': dict(status_counts),
                'total_legacy_works': total_legacy_works,
                'total_entries': total_entries,
                'average_confidence': round(avg_confidence, 2),
                'completion_percentage': round((total_entries / max(total_legacy_works, 1)) * 100, 2)
            }
    
    def get_pending_migrations(self, limit: Optional[int] = None) -> List[WorkUnitMigration]:
        """Get pending migration entries"""
        with self.db_manager.get_session() as session:
            query = session.query(WorkUnitMigration).filter(
                WorkUnitMigration.migration_status == 'pending'
            ).order_by(WorkUnitMigration.created_at)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_manual_review_migrations(self) -> List[WorkUnitMigration]:
        """Get migrations requiring manual review"""
        with self.db_manager.get_session() as session:
            return session.query(WorkUnitMigration).filter(
                WorkUnitMigration.migration_status == 'manual'
            ).order_by(WorkUnitMigration.created_at).all()
    
    def bulk_create_migration_entries(self, entries: List[Dict[str, Any]]) -> int:
        """Bulk create migration entries"""
        with self.db_manager.get_session() as session:
            migration_entries = [
                WorkUnitMigration(**entry) for entry in entries
            ]
            session.add_all(migration_entries)
            session.commit()
            return len(migration_entries)
    
    def clear_all_migrations(self) -> int:
        """Clear all migration entries (for testing/reset)"""
        with self.db_manager.get_session() as session:
            count = session.query(WorkUnitMigration).count()
            session.query(WorkUnitMigration).delete()
            session.commit()
            return count
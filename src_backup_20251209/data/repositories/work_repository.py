"""
Repository for Work operations
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.data.models.sqlalchemy_models import Work
from src.data.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class WorkRepository:
    """Repository for Work CRUD operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def find_all(self) -> List[Dict]:
        """Find all works"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Work.id,
                    Work.parent_id,
                    Work.name,
                    Work.code,
                    Work.unit,
                    Work.price,
                    Work.labor_rate,
                    Work.is_group,
                    Work.marked_for_deletion
                )\
                    .filter(Work.marked_for_deletion == False)\
                    .order_by(Work.code, Work.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'parent_id': row.parent_id,
                        'name': row.name,
                        'code': row.code,
                        'unit': row.unit,
                        'price': row.price,
                        'labor_rate': row.labor_rate,
                        'is_group': row.is_group,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find all works: {e}")
            return []
    
    def find_by_id(self, work_id: int) -> Optional[Dict]:
        """Find work by ID"""
        try:
            with self.db_manager.session_scope() as session:
                result = session.query(
                    Work.id,
                    Work.parent_id,
                    Work.name,
                    Work.code,
                    Work.unit,
                    Work.price,
                    Work.labor_rate,
                    Work.is_group,
                    Work.marked_for_deletion
                )\
                    .filter(Work.id == work_id)\
                    .filter(Work.marked_for_deletion == False)\
                    .first()
                
                if result:
                    return {
                        'id': result.id,
                        'parent_id': result.parent_id,
                        'name': result.name,
                        'code': result.code,
                        'unit': result.unit,
                        'price': result.price,
                        'labor_rate': result.labor_rate,
                        'is_group': result.is_group,
                        'marked_for_deletion': result.marked_for_deletion
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to find work by ID {work_id}: {e}")
            return None
    
    def find_groups(self) -> List[Dict]:
        """Find all group works"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Work.id,
                    Work.parent_id,
                    Work.name,
                    Work.code,
                    Work.unit,
                    Work.price,
                    Work.labor_rate,
                    Work.is_group,
                    Work.marked_for_deletion
                )\
                    .filter(Work.is_group == True)\
                    .filter(Work.marked_for_deletion == False)\
                    .order_by(Work.code, Work.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'parent_id': row.parent_id,
                        'name': row.name,
                        'code': row.code,
                        'unit': row.unit,
                        'price': row.price,
                        'labor_rate': row.labor_rate,
                        'is_group': row.is_group,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find work groups: {e}")
            return []
    
    def find_children(self, parent_id: int) -> List[Dict]:
        """Find all child works for a given parent"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Work.id,
                    Work.parent_id,
                    Work.name,
                    Work.code,
                    Work.unit,
                    Work.price,
                    Work.labor_rate,
                    Work.is_group,
                    Work.marked_for_deletion
                )\
                    .filter(Work.parent_id == parent_id)\
                    .filter(Work.marked_for_deletion == False)\
                    .order_by(Work.code, Work.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'parent_id': row.parent_id,
                        'name': row.name,
                        'code': row.code,
                        'unit': row.unit,
                        'price': row.price,
                        'labor_rate': row.labor_rate,
                        'is_group': row.is_group,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find children for parent {parent_id}: {e}")
            return []
    
    
    
    def search_by_name(self, search_term: str) -> List[Dict]:
        """Search works by name"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Work.id,
                    Work.parent_id,
                    Work.name,
                    Work.code,
                    Work.unit,
                    Work.price,
                    Work.labor_rate,
                    Work.is_group,
                    Work.marked_for_deletion
                )\
                    .filter(Work.name.ilike(f'%{search_term}%'))\
                    .filter(Work.marked_for_deletion == False)\
                    .order_by(Work.code, Work.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'parent_id': row.parent_id,
                        'name': row.name,
                        'code': row.code,
                        'unit': row.unit,
                        'price': row.price,
                        'labor_rate': row.labor_rate,
                        'is_group': row.is_group,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to search works by name '{search_term}': {e}")
            return []
    
    def save(self, work: Work) -> Optional[int]:
        """Save work to database"""
        try:
            with self.db_manager.session_scope() as session:
                session.add(work)
                session.flush()
                return work.id
        except Exception as e:
            logger.error(f"Failed to save work: {e}")
            return None
    
    def update(self, work: Work) -> bool:
        """Update existing work"""
        try:
            with self.db_manager.session_scope() as session:
                session.merge(work)
                return True
        except Exception as e:
            logger.error(f"Failed to update work: {e}")
            return False
    
    def delete(self, work_id: int) -> bool:
        """Mark work as deleted (soft delete)"""
        try:
            with self.db_manager.session_scope() as session:
                work = session.query(Work).filter(Work.id == work_id).first()
                if work:
                    work.marked_for_deletion = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete work with ID {work_id}: {e}")
            return False
"""Unit repository for database operations"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ...data.models.sqlalchemy_models import Unit
from ...data.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class UnitRepository:
    """Repository for Unit entities"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create(self, unit_data: Dict) -> Optional[int]:
        """Create a new unit"""
        try:
            with self.db_manager.session_scope() as session:
                unit = Unit(
                    name=unit_data['name'],
                    description=unit_data.get('description', '')
                )
                session.add(unit)
                session.flush()
                return unit.id
        except Exception as e:
            logger.error(f"Failed to create unit: {e}")
            return None
    
    def find_by_id(self, unit_id: int) -> Optional[Dict]:
        """Find unit by ID"""
        try:
            with self.db_manager.session_scope() as session:
                unit = session.query(Unit).filter(Unit.id == unit_id).first()
                if unit:
                    return {
                        'id': unit.id,
                        'name': unit.name,
                        'description': unit.description,
                        'marked_for_deletion': unit.marked_for_deletion
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to find unit by ID: {e}")
            return None
    
    def find_all(self) -> List[Dict]:
        """Find all units"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Unit.id,
                    Unit.name,
                    Unit.description,
                    Unit.marked_for_deletion
                )\
                    .filter(Unit.marked_for_deletion == False)\
                    .order_by(Unit.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'name': row.name,
                        'description': row.description,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to find all units: {e}")
            return []
    
    def update(self, unit_id: int, unit_data: Dict) -> bool:
        """Update unit"""
        try:
            with self.db_manager.session_scope() as session:
                unit = session.query(Unit).filter(Unit.id == unit_id).first()
                if unit:
                    unit.name = unit_data.get('name', unit.name)
                    unit.description = unit_data.get('description', unit.description)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update unit: {e}")
            return False
    
    def delete(self, unit_id: int) -> bool:
        """Mark unit as deleted"""
        try:
            with self.db_manager.session_scope() as session:
                unit = session.query(Unit).filter(Unit.id == unit_id).first()
                if unit:
                    unit.marked_for_deletion = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete unit: {e}")
            return False
    
    def search_by_name(self, name: str) -> List[Dict]:
        """Search units by name"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    Unit.id,
                    Unit.name,
                    Unit.description,
                    Unit.marked_for_deletion
                )\
                    .filter(Unit.name.ilike(f'%{name}%'))\
                    .filter(Unit.marked_for_deletion == False)\
                    .order_by(Unit.name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'name': row.name,
                        'description': row.description,
                        'marked_for_deletion': row.marked_for_deletion
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to search units by name: {e}")
            return []
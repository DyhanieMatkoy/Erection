"""
Repository for Work Specification operations
"""
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy import func
from src.data.models.sqlalchemy_models import WorkSpecification
from src.data.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class WorkSpecificationRepository:
    """Repository for Work Specification CRUD operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_by_work_id(self, work_id: int) -> List[Dict]:
        """Get all specifications for a work"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(WorkSpecification)\
                    .filter(WorkSpecification.work_id == work_id)\
                    .filter(WorkSpecification.marked_for_deletion == False)\
                    .order_by(WorkSpecification.component_type, WorkSpecification.component_name)
                
                results = []
                for row in query.all():
                    results.append({
                        'id': row.id,
                        'work_id': row.work_id,
                        'component_type': row.component_type,
                        'component_name': row.component_name,
                        'unit_id': row.unit_id,
                        'unit_name': row.unit_ref.name if row.unit_ref else None,
                        'consumption_rate': row.consumption_rate,
                        'unit_price': row.unit_price,
                        'total_cost': row.total_cost,
                        'material_id': row.material_id,
                        'created_at': row.created_at,
                        'modified_at': row.modified_at
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to get specifications for work {work_id}: {e}")
            return []
            
    def create(self, data: Dict) -> Optional[int]:
        """Create a new specification entry"""
        try:
            with self.db_manager.session_scope() as session:
                spec = WorkSpecification(
                    work_id=data['work_id'],
                    component_type=data['component_type'],
                    component_name=data['component_name'],
                    unit_id=data.get('unit_id'),
                    consumption_rate=data['consumption_rate'],
                    unit_price=data['unit_price']
                )
                session.add(spec)
                session.flush() # To get ID
                return spec.id
        except Exception as e:
            logger.error(f"Failed to create specification: {e}")
            return None
            
    def update(self, spec_id: int, data: Dict) -> bool:
        """Update a specification entry"""
        try:
            with self.db_manager.session_scope() as session:
                spec = session.query(WorkSpecification).filter(WorkSpecification.id == spec_id).first()
                if not spec:
                    return False
                
                if 'component_type' in data:
                    spec.component_type = data['component_type']
                if 'component_name' in data:
                    spec.component_name = data['component_name']
                if 'unit_id' in data:
                    spec.unit_id = data['unit_id']
                if 'consumption_rate' in data:
                    spec.consumption_rate = data['consumption_rate']
                if 'unit_price' in data:
                    spec.unit_price = data['unit_price']
                
                spec.modified_at = func.now()
                return True
        except Exception as e:
            logger.error(f"Failed to update specification {spec_id}: {e}")
            return False
            
    def delete(self, spec_id: int) -> bool:
        """Delete a specification entry"""
        try:
            with self.db_manager.session_scope() as session:
                spec = session.query(WorkSpecification).filter(WorkSpecification.id == spec_id).first()
                if not spec:
                    return False
                
                # Hard delete or soft delete?
                # The model has marked_for_deletion, but usually for child items we might just delete them
                # Requirements say: "WHEN a user selects a specification entry and clicks delete THEN the system SHALL remove the entry from the specification table"
                # But we have marked_for_deletion column.
                # Let's use soft delete for safety, or hard delete if that's the pattern.
                # Other repos use marked_for_deletion.
                spec.marked_for_deletion = True
                return True
        except Exception as e:
            logger.error(f"Failed to delete specification {spec_id}: {e}")
            return False

    def copy_from_work(self, target_work_id: int, source_work_id: int) -> bool:
        """Copy all specifications from source work to target work"""
        try:
            with self.db_manager.session_scope() as session:
                # Get source specs
                source_specs = session.query(WorkSpecification)\
                    .filter(WorkSpecification.work_id == source_work_id)\
                    .filter(WorkSpecification.marked_for_deletion == False)\
                    .all()
                
                for source in source_specs:
                    new_spec = WorkSpecification(
                        work_id=target_work_id,
                        component_type=source.component_type,
                        component_name=source.component_name,
                        unit_id=source.unit_id,
                        consumption_rate=source.consumption_rate,
                        unit_price=source.unit_price
                    )
                    session.add(new_spec)
                return True
        except Exception as e:
            logger.error(f"Failed to copy specifications from {source_work_id} to {target_work_id}: {e}")
            return False

    def get_totals_by_type(self, work_id: int) -> Dict[str, Decimal]:
        """Get total cost grouped by component type"""
        try:
            with self.db_manager.session_scope() as session:
                # This relies on total_cost being computed in DB or we compute it here
                # total_cost is computed column in DB
                
                query = session.query(
                    WorkSpecification.component_type,
                    func.sum(WorkSpecification.total_cost).label('total')
                )\
                    .filter(WorkSpecification.work_id == work_id)\
                    .filter(WorkSpecification.marked_for_deletion == False)\
                    .group_by(WorkSpecification.component_type)
                
                results = {
                    'Material': Decimal(0),
                    'Labor': Decimal(0),
                    'Equipment': Decimal(0),
                    'Other': Decimal(0)
                }
                
                for row in query.all():
                    if row.component_type in results:
                        results[row.component_type] = row.total or Decimal(0)
                    else:
                        results[row.component_type] = row.total or Decimal(0)
                        
                return results
        except Exception as e:
            logger.error(f"Failed to get totals for work {work_id}: {e}")
            return {}

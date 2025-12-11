"""Estimate repository"""
from typing import List, Optional
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.estimate import Estimate, EstimateLine
from ..models.sqlalchemy_models import Estimate as EstimateModel, EstimateLine as EstimateLineModel

logger = logging.getLogger(__name__)


class EstimateRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, estimate_id: int) -> Optional[Estimate]:
        """Find estimate by ID using SQLAlchemy session"""
        try:
            with self.db_manager.session_scope() as session:
                # Query with eager loading of lines
                estimate_model = session.query(EstimateModel)\
                    .options(joinedload(EstimateModel.lines))\
                    .filter(EstimateModel.id == estimate_id)\
                    .first()
                
                if not estimate_model:
                    return None
                
                # Convert SQLAlchemy model to dataclass
                return self._model_to_dataclass(estimate_model)
                
        except Exception as e:
            logger.error(f"Failed to find estimate by ID {estimate_id}: {e}")
            return None
    
    def save(self, estimate: Estimate) -> bool:
        """Save estimate using SQLAlchemy session with transaction handling"""
        try:
            with self.db_manager.session_scope() as session:
                if estimate.id == 0:
                    # Create new estimate
                    estimate_model = EstimateModel(
                        number=estimate.number,
                        date=estimate.date,
                        customer_id=estimate.customer_id if estimate.customer_id else None,
                        object_id=estimate.object_id if estimate.object_id else None,
                        contractor_id=estimate.contractor_id if estimate.contractor_id else None,
                        responsible_id=estimate.responsible_id if estimate.responsible_id else None,
                        total_sum=estimate.total_sum,
                        total_labor=estimate.total_labor
                    )
                    session.add(estimate_model)
                    session.flush()  # Get the ID without committing
                    estimate.id = estimate_model.id
                    
                    # Add lines
                    for i, line in enumerate(estimate.lines):
                        line_model = EstimateLineModel(
                            estimate_id=estimate.id,
                            line_number=i + 1,
                            work_id=line.work_id if line.work_id else None,
                            quantity=line.quantity,
                            unit=line.unit,
                            price=line.price,
                            labor_rate=line.labor_rate,
                            sum=line.sum,
                            planned_labor=line.planned_labor,
                            is_group=line.is_group,
                            group_name=line.group_name,
                            parent_group_id=line.parent_group_id if line.parent_group_id else None,
                            is_collapsed=line.is_collapsed
                        )
                        session.add(line_model)
                else:
                    # Update existing estimate
                    estimate_model = session.query(EstimateModel)\
                        .filter(EstimateModel.id == estimate.id)\
                        .first()
                    
                    if not estimate_model:
                        logger.error(f"Estimate with ID {estimate.id} not found")
                        return False
                    
                    # Update fields
                    estimate_model.number = estimate.number
                    estimate_model.date = estimate.date
                    estimate_model.customer_id = estimate.customer_id if estimate.customer_id else None
                    estimate_model.object_id = estimate.object_id if estimate.object_id else None
                    estimate_model.contractor_id = estimate.contractor_id if estimate.contractor_id else None
                    estimate_model.responsible_id = estimate.responsible_id if estimate.responsible_id else None
                    estimate_model.total_sum = estimate.total_sum
                    estimate_model.total_labor = estimate.total_labor
                    
                    # Delete existing lines (cascade will handle this)
                    session.query(EstimateLineModel)\
                        .filter(EstimateLineModel.estimate_id == estimate.id)\
                        .delete()
                    
                    # Add new lines
                    for i, line in enumerate(estimate.lines):
                        line_model = EstimateLineModel(
                            estimate_id=estimate.id,
                            line_number=i + 1,
                            work_id=line.work_id if line.work_id else None,
                            quantity=line.quantity,
                            unit=line.unit,
                            price=line.price,
                            labor_rate=line.labor_rate,
                            sum=line.sum,
                            planned_labor=line.planned_labor,
                            is_group=line.is_group,
                            group_name=line.group_name,
                            parent_group_id=line.parent_group_id if line.parent_group_id else None,
                            is_collapsed=line.is_collapsed
                        )
                        session.add(line_model)
                
                # Transaction will be committed by session_scope
                return True
                
        except Exception as e:
            logger.error(f"Failed to save estimate: {e}")
            return False
    
    def find_by_responsible(self, person_id: int) -> List[Estimate]:
        """Find estimates by responsible person using SQLAlchemy query API"""
        try:
            with self.db_manager.session_scope() as session:
                # Query estimates by responsible person, ordered by date descending
                estimate_models = session.query(EstimateModel)\
                    .filter(EstimateModel.responsible_id == person_id)\
                    .order_by(EstimateModel.date.desc())\
                    .all()
                
                # Convert to dataclasses (without loading lines for list view)
                estimates = []
                for model in estimate_models:
                    estimate = Estimate(
                        id=model.id,
                        number=model.number,
                        date=model.date,
                        customer_id=model.customer_id or 0,
                        object_id=model.object_id or 0,
                        contractor_id=model.contractor_id or 0,
                        responsible_id=model.responsible_id or 0,
                        total_sum=model.total_sum,
                        total_labor=model.total_labor
                    )
                    estimates.append(estimate)
                
                return estimates
                
        except Exception as e:
            logger.error(f"Failed to find estimates by responsible {person_id}: {e}")
            return []
    
    def _model_to_dataclass(self, estimate_model: EstimateModel) -> Estimate:
        """Convert SQLAlchemy model to dataclass
        
        Args:
            estimate_model: SQLAlchemy Estimate model instance
            
        Returns:
            Estimate dataclass instance
        """
        # Convert estimate
        estimate = Estimate(
            id=estimate_model.id,
            number=estimate_model.number,
            date=estimate_model.date,
            customer_id=estimate_model.customer_id or 0,
            object_id=estimate_model.object_id or 0,
            contractor_id=estimate_model.contractor_id or 0,
            responsible_id=estimate_model.responsible_id or 0,
            total_sum=estimate_model.total_sum,
            total_labor=estimate_model.total_labor
        )
        
        # Convert lines
        lines = []
        for line_model in estimate_model.lines:
            line = EstimateLine(
                id=line_model.id,
                estimate_id=line_model.estimate_id,
                line_number=line_model.line_number,
                work_id=line_model.work_id or 0,
                quantity=line_model.quantity,
                unit=line_model.unit or "",
                price=line_model.price,
                labor_rate=line_model.labor_rate,
                sum=line_model.sum,
                planned_labor=line_model.planned_labor,
                is_group=line_model.is_group,
                group_name=line_model.group_name or "",
                parent_group_id=line_model.parent_group_id or 0,
                is_collapsed=line_model.is_collapsed
            )
            lines.append(line)
        
        estimate.lines = lines
        return estimate

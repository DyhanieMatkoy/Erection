"""Work execution register repository"""
from typing import List, Dict, Optional
import logging
from sqlalchemy import func
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import (
    WorkExecutionRegister as WorkExecutionRegisterModel,
    Object as ObjectModel,
    Estimate as EstimateModel,
    Work as WorkModel,
    DailyReportLine as DailyReportLineModel,
    DailyReportExecutor as DailyReportExecutorModel
)

logger = logging.getLogger(__name__)


class WorkExecutionRegisterRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def get_movements(self, recorder_type: str, recorder_id: int) -> List[Dict]:
        """Get movements for a document using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                movements = session.query(WorkExecutionRegisterModel)\
                    .filter(WorkExecutionRegisterModel.recorder_type == recorder_type)\
                    .filter(WorkExecutionRegisterModel.recorder_id == recorder_id)\
                    .order_by(WorkExecutionRegisterModel.line_number)\
                    .all()
                
                return [self._model_to_dict(m) for m in movements]
                
        except Exception as e:
            logger.error(f"Failed to get movements for {recorder_type} {recorder_id}: {e}")
            return []
    
    def delete_movements(self, recorder_type: str, recorder_id: int):
        """Delete all movements for a document using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                session.query(WorkExecutionRegisterModel)\
                    .filter(WorkExecutionRegisterModel.recorder_type == recorder_type)\
                    .filter(WorkExecutionRegisterModel.recorder_id == recorder_id)\
                    .delete()
                # Transaction will be committed by session_scope
                
        except Exception as e:
            logger.error(f"Failed to delete movements for {recorder_type} {recorder_id}: {e}")
            raise
    
    def create_movement(self, movement: Dict):
        """Create a single movement using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                # Convert period string to date object if needed
                period_value = movement['period']
                if isinstance(period_value, str):
                    from datetime import date
                    period_value = date.fromisoformat(period_value)
                
                movement_model = WorkExecutionRegisterModel(
                    recorder_type=movement['recorder_type'],
                    recorder_id=movement['recorder_id'],
                    line_number=movement['line_number'],
                    period=period_value,
                    object_id=movement['object_id'],
                    estimate_id=movement['estimate_id'],
                    work_id=movement['work_id'],
                    quantity_income=movement.get('quantity_income', 0),
                    quantity_expense=movement.get('quantity_expense', 0),
                    sum_income=movement.get('sum_income', 0),
                    sum_expense=movement.get('sum_expense', 0)
                )
                session.add(movement_model)
                # Transaction will be committed by session_scope
                
        except Exception as e:
            logger.error(f"Failed to create movement: {e}")
            raise
    
    def get_balance(self, filters: Optional[Dict] = None, grouping: Optional[List[str]] = None) -> List[Dict]:
        """
        Get balance with grouping using SQLAlchemy
        
        Args:
            filters: Dict with keys: period_end, object_id, estimate_id, work_id
            grouping: List of fields to group by: 'object', 'estimate', 'work', 'period'
        """
        try:
            if grouping is None:
                grouping = ['estimate', 'work']
            
            with self.db_manager.session_scope() as session:
                # Build SELECT clause
                select_fields = []
                group_by_fields = []
                
                if 'object' in grouping:
                    select_fields.append(ObjectModel.name.label('object_name'))
                    select_fields.append(WorkExecutionRegisterModel.object_id)
                    group_by_fields.append(WorkExecutionRegisterModel.object_id)
                
                if 'estimate' in grouping:
                    select_fields.append(EstimateModel.number.label('estimate_number'))
                    select_fields.append(WorkExecutionRegisterModel.estimate_id)
                    group_by_fields.append(WorkExecutionRegisterModel.estimate_id)
                
                if 'work' in grouping:
                    select_fields.append(WorkModel.name.label('work_name'))
                    select_fields.append(WorkExecutionRegisterModel.work_id)
                    group_by_fields.append(WorkExecutionRegisterModel.work_id)
                
                if 'period' in grouping:
                    select_fields.append(WorkExecutionRegisterModel.period)
                    group_by_fields.append(WorkExecutionRegisterModel.period)
                
                # Add aggregates
                select_fields.extend([
                    func.sum(WorkExecutionRegisterModel.quantity_income).label('quantity_income'),
                    func.sum(WorkExecutionRegisterModel.quantity_expense).label('quantity_expense'),
                    (func.sum(WorkExecutionRegisterModel.quantity_income) - 
                     func.sum(WorkExecutionRegisterModel.quantity_expense)).label('quantity_balance'),
                    func.sum(WorkExecutionRegisterModel.sum_income).label('sum_income'),
                    func.sum(WorkExecutionRegisterModel.sum_expense).label('sum_expense'),
                    (func.sum(WorkExecutionRegisterModel.sum_income) - 
                     func.sum(WorkExecutionRegisterModel.sum_expense)).label('sum_balance')
                ])
                
                # Build query
                query = session.query(*select_fields)\
                    .outerjoin(ObjectModel, WorkExecutionRegisterModel.object_id == ObjectModel.id)\
                    .outerjoin(EstimateModel, WorkExecutionRegisterModel.estimate_id == EstimateModel.id)\
                    .outerjoin(WorkModel, WorkExecutionRegisterModel.work_id == WorkModel.id)
                
                # Apply filters
                if filters:
                    if 'period_end' in filters:
                        query = query.filter(WorkExecutionRegisterModel.period <= filters['period_end'])
                    
                    if 'object_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.object_id == filters['object_id'])
                    
                    if 'estimate_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.estimate_id == filters['estimate_id'])
                    
                    if 'work_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.work_id == filters['work_id'])
                
                # Apply grouping
                if group_by_fields:
                    query = query.group_by(*group_by_fields)
                    query = query.order_by(*group_by_fields)
                
                # Execute and convert to dicts
                results = []
                for row in query.all():
                    result = {}
                    idx = 0
                    
                    if 'object' in grouping:
                        result['object_name'] = row[idx]
                        result['object_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'estimate' in grouping:
                        result['estimate_number'] = row[idx]
                        result['estimate_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'work' in grouping:
                        result['work_name'] = row[idx]
                        result['work_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'period' in grouping:
                        result['period'] = row[idx]
                        idx += 1
                    
                    # Add aggregates
                    result['quantity_income'] = row[idx] or 0
                    result['quantity_expense'] = row[idx + 1] or 0
                    result['quantity_balance'] = row[idx + 2] or 0
                    result['sum_income'] = row[idx + 3] or 0
                    result['sum_expense'] = row[idx + 4] or 0
                    result['sum_balance'] = row[idx + 5] or 0
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return []
    
    def get_turnovers(self, period_start: str, period_end: str, 
                     filters: Optional[Dict] = None, 
                     grouping: Optional[List[str]] = None) -> List[Dict]:
        """
        Get turnovers for period with grouping using SQLAlchemy
        
        Args:
            period_start: Start date
            period_end: End date
            filters: Dict with keys: object_id, estimate_id, work_id, executor_id
            grouping: List of fields to group by: 'object', 'estimate', 'work', 'period'
        """
        try:
            if grouping is None:
                grouping = ['estimate', 'work']
            
            with self.db_manager.session_scope() as session:
                # Build SELECT clause
                select_fields = []
                group_by_fields = []
                
                if 'object' in grouping:
                    select_fields.append(ObjectModel.name.label('object_name'))
                    select_fields.append(WorkExecutionRegisterModel.object_id)
                    group_by_fields.append(WorkExecutionRegisterModel.object_id)
                
                if 'estimate' in grouping:
                    select_fields.append(EstimateModel.number.label('estimate_number'))
                    select_fields.append(WorkExecutionRegisterModel.estimate_id)
                    group_by_fields.append(WorkExecutionRegisterModel.estimate_id)
                
                if 'work' in grouping:
                    select_fields.append(WorkModel.name.label('work_name'))
                    select_fields.append(WorkExecutionRegisterModel.work_id)
                    group_by_fields.append(WorkExecutionRegisterModel.work_id)
                
                if 'period' in grouping:
                    select_fields.append(WorkExecutionRegisterModel.period)
                    group_by_fields.append(WorkExecutionRegisterModel.period)
                
                # Add aggregates
                select_fields.extend([
                    func.sum(WorkExecutionRegisterModel.quantity_income).label('quantity_income'),
                    func.sum(WorkExecutionRegisterModel.quantity_expense).label('quantity_expense'),
                    func.sum(WorkExecutionRegisterModel.sum_income).label('sum_income'),
                    func.sum(WorkExecutionRegisterModel.sum_expense).label('sum_expense')
                ])
                
                # Build query
                query = session.query(*select_fields)\
                    .outerjoin(ObjectModel, WorkExecutionRegisterModel.object_id == ObjectModel.id)\
                    .outerjoin(EstimateModel, WorkExecutionRegisterModel.estimate_id == EstimateModel.id)\
                    .outerjoin(WorkModel, WorkExecutionRegisterModel.work_id == WorkModel.id)
                
                # Check if we need to filter by executor
                needs_executor_join = filters and 'executor_id' in filters
                if needs_executor_join:
                    # Join with daily reports and executors
                    query = query.outerjoin(
                        DailyReportLineModel,
                        (WorkExecutionRegisterModel.recorder_type == 'DailyReport') &
                        (WorkExecutionRegisterModel.recorder_id == DailyReportLineModel.report_id) &
                        (WorkExecutionRegisterModel.line_number == DailyReportLineModel.line_number)
                    ).outerjoin(
                        DailyReportExecutorModel,
                        DailyReportLineModel.id == DailyReportExecutorModel.report_line_id
                    )
                    query = query.filter(DailyReportExecutorModel.executor_id == filters['executor_id'])
                
                # Apply period filters
                query = query.filter(WorkExecutionRegisterModel.period >= period_start)
                query = query.filter(WorkExecutionRegisterModel.period <= period_end)
                
                # Apply other filters
                if filters:
                    if 'object_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.object_id == filters['object_id'])
                    
                    if 'estimate_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.estimate_id == filters['estimate_id'])
                    
                    if 'work_id' in filters:
                        query = query.filter(WorkExecutionRegisterModel.work_id == filters['work_id'])
                
                # Apply grouping
                if group_by_fields:
                    query = query.group_by(*group_by_fields)
                    query = query.order_by(*group_by_fields)
                
                # Execute and convert to dicts
                results = []
                for row in query.all():
                    result = {}
                    idx = 0
                    
                    if 'object' in grouping:
                        result['object_name'] = row[idx]
                        result['object_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'estimate' in grouping:
                        result['estimate_number'] = row[idx]
                        result['estimate_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'work' in grouping:
                        result['work_name'] = row[idx]
                        result['work_id'] = row[idx + 1]
                        idx += 2
                    
                    if 'period' in grouping:
                        result['period'] = row[idx]
                        idx += 1
                    
                    # Add aggregates
                    result['quantity_income'] = row[idx] or 0
                    result['quantity_expense'] = row[idx + 1] or 0
                    result['sum_income'] = row[idx + 2] or 0
                    result['sum_expense'] = row[idx + 3] or 0
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get turnovers: {e}")
            return []

    def _model_to_dict(self, model: WorkExecutionRegisterModel) -> Dict:
        """Convert SQLAlchemy model to dict"""
        return {
            'id': model.id,
            'recorder_type': model.recorder_type,
            'recorder_id': model.recorder_id,
            'line_number': model.line_number,
            'period': model.period,
            'object_id': model.object_id,
            'estimate_id': model.estimate_id,
            'work_id': model.work_id,
            'quantity_income': model.quantity_income,
            'quantity_expense': model.quantity_expense,
            'sum_income': model.sum_income,
            'sum_expense': model.sum_expense,
            'created_at': model.created_at
        }

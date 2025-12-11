"""Payroll register repository"""
from typing import List, Dict, Optional
from datetime import date
import logging
from sqlalchemy.exc import IntegrityError
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import PayrollRegister as PayrollRegisterModel

logger = logging.getLogger(__name__)


class PayrollRegisterRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def write_records(self, records: List[Dict]) -> bool:
        """Write records to register with uniqueness check using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                for record in records:
                    record_model = PayrollRegisterModel(
                        recorder_type=record['recorder_type'],
                        recorder_id=record['recorder_id'],
                        line_number=record['line_number'],
                        period=record['period'],
                        object_id=record.get('object_id'),
                        estimate_id=record.get('estimate_id'),
                        employee_id=record['employee_id'],
                        work_date=record['work_date'],
                        hours_worked=record.get('hours_worked', 0),
                        amount=record.get('amount', 0)
                    )
                    session.add(record_model)
                
                # Transaction will be committed by session_scope
                return True
                
        except IntegrityError as e:
            logger.error(f"Integrity error writing payroll records: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to write payroll records: {e}")
            raise
    
    def delete_by_recorder(self, recorder_type: str, recorder_id: int) -> bool:
        """Delete all records by recorder using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                session.query(PayrollRegisterModel)\
                    .filter(PayrollRegisterModel.recorder_type == recorder_type)\
                    .filter(PayrollRegisterModel.recorder_id == recorder_id)\
                    .delete()
                # Transaction will be committed by session_scope
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete payroll records for {recorder_type} {recorder_id}: {e}")
            return False
    
    def check_duplicates(self, records: List[Dict]) -> List[Dict]:
        """Check for duplicate records using SQLAlchemy"""
        try:
            duplicates = []
            
            with self.db_manager.session_scope() as session:
                for record in records:
                    existing = session.query(PayrollRegisterModel)\
                        .filter(PayrollRegisterModel.object_id == record.get('object_id'))\
                        .filter(PayrollRegisterModel.estimate_id == record.get('estimate_id'))\
                        .filter(PayrollRegisterModel.employee_id == record['employee_id'])\
                        .filter(PayrollRegisterModel.work_date == record['work_date'])\
                        .first()
                    
                    if existing:
                        duplicates.append({
                            'record': record,
                            'existing': self._model_to_dict(existing)
                        })
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to check duplicates: {e}")
            return []
    
    def get_by_dimensions(
        self, 
        object_id: int, 
        estimate_id: int, 
        employee_id: int, 
        work_date: date
    ) -> Optional[Dict]:
        """Get record by unique key using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                record = session.query(PayrollRegisterModel)\
                    .filter(PayrollRegisterModel.object_id == object_id)\
                    .filter(PayrollRegisterModel.estimate_id == estimate_id)\
                    .filter(PayrollRegisterModel.employee_id == employee_id)\
                    .filter(PayrollRegisterModel.work_date == work_date)\
                    .first()
                
                return self._model_to_dict(record) if record else None
                
        except Exception as e:
            logger.error(f"Failed to get payroll record by dimensions: {e}")
            return None
    
    def get_by_recorder(self, recorder_type: str, recorder_id: int) -> List[Dict]:
        """Get all records by recorder using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                records = session.query(PayrollRegisterModel)\
                    .filter(PayrollRegisterModel.recorder_type == recorder_type)\
                    .filter(PayrollRegisterModel.recorder_id == recorder_id)\
                    .order_by(PayrollRegisterModel.line_number)\
                    .all()
                
                return [self._model_to_dict(r) for r in records]
                
        except Exception as e:
            logger.error(f"Failed to get payroll records for {recorder_type} {recorder_id}: {e}")
            return []

    def _model_to_dict(self, model: PayrollRegisterModel) -> Dict:
        """Convert SQLAlchemy model to dict"""
        return {
            'id': model.id,
            'recorder_type': model.recorder_type,
            'recorder_id': model.recorder_id,
            'line_number': model.line_number,
            'period': model.period,
            'object_id': model.object_id,
            'estimate_id': model.estimate_id,
            'employee_id': model.employee_id,
            'work_date': model.work_date,
            'hours_worked': model.hours_worked,
            'amount': model.amount,
            'created_at': model.created_at
        }

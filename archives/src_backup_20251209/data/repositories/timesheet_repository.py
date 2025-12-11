"""Timesheet repository"""
from typing import List, Dict, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import joinedload
from ..database_manager import DatabaseManager
from ..models.sqlalchemy_models import (
    Timesheet as TimesheetModel,
    TimesheetLine as TimesheetLineModel,
    Object as ObjectModel,
    Estimate as EstimateModel,
    Person as PersonModel
)

logger = logging.getLogger(__name__)


class TimesheetRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_all(self, foreman_id: Optional[int] = None) -> List[Dict]:
        """Get all timesheets, optionally filtered by foreman using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(
                    TimesheetModel,
                    ObjectModel.name.label('object_name'),
                    EstimateModel.number.label('estimate_number'),
                    PersonModel.full_name.label('foreman_name')
                ).outerjoin(
                    ObjectModel, TimesheetModel.object_id == ObjectModel.id
                ).outerjoin(
                    EstimateModel, TimesheetModel.estimate_id == EstimateModel.id
                ).outerjoin(
                    PersonModel, TimesheetModel.foreman_id == PersonModel.id
                ).filter(
                    TimesheetModel.marked_for_deletion == False
                )
                
                if foreman_id is not None:
                    query = query.filter(TimesheetModel.foreman_id == foreman_id)
                
                query = query.order_by(
                    TimesheetModel.date.desc(),
                    TimesheetModel.number.desc()
                )
                
                results = []
                for timesheet, object_name, estimate_number, foreman_name in query.all():
                    result = {
                        'id': timesheet.id,
                        'number': timesheet.number,
                        'date': timesheet.date,
                        'object_id': timesheet.object_id,
                        'estimate_id': timesheet.estimate_id,
                        'foreman_id': timesheet.foreman_id,
                        'month_year': timesheet.month_year,
                        'is_posted': timesheet.is_posted,
                        'posted_at': timesheet.posted_at,
                        'marked_for_deletion': timesheet.marked_for_deletion,
                        'created_at': timesheet.created_at,
                        'modified_at': timesheet.modified_at,
                        'object_name': object_name,
                        'estimate_number': estimate_number,
                        'foreman_name': foreman_name
                    }
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to find all timesheets: {e}")
            return []
    
    def find_by_id(self, timesheet_id: int) -> Optional[Dict]:
        """Get timesheet by ID with lines using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                # Query with eager loading of lines
                result = session.query(
                    TimesheetModel,
                    ObjectModel.name.label('object_name'),
                    EstimateModel.number.label('estimate_number'),
                    PersonModel.full_name.label('foreman_name')
                ).options(
                    joinedload(TimesheetModel.lines).joinedload(TimesheetLineModel.employee)
                ).outerjoin(
                    ObjectModel, TimesheetModel.object_id == ObjectModel.id
                ).outerjoin(
                    EstimateModel, TimesheetModel.estimate_id == EstimateModel.id
                ).outerjoin(
                    PersonModel, TimesheetModel.foreman_id == PersonModel.id
                ).filter(
                    TimesheetModel.id == timesheet_id
                ).first()
                
                if not result:
                    return None
                
                timesheet_model, object_name, estimate_number, foreman_name = result
                
                # Convert to dict
                timesheet = {
                    'id': timesheet_model.id,
                    'number': timesheet_model.number,
                    'date': timesheet_model.date,
                    'object_id': timesheet_model.object_id,
                    'estimate_id': timesheet_model.estimate_id,
                    'foreman_id': timesheet_model.foreman_id,
                    'month_year': timesheet_model.month_year,
                    'is_posted': timesheet_model.is_posted,
                    'posted_at': timesheet_model.posted_at,
                    'marked_for_deletion': timesheet_model.marked_for_deletion,
                    'created_at': timesheet_model.created_at,
                    'modified_at': timesheet_model.modified_at,
                    'object_name': object_name,
                    'estimate_number': estimate_number,
                    'foreman_name': foreman_name
                }
                
                # Convert lines
                lines = []
                for line_model in sorted(timesheet_model.lines, key=lambda x: x.line_number):
                    # Convert day columns to days dict
                    days = {}
                    for day in range(1, 32):
                        day_value = getattr(line_model, f'day_{day:02d}')
                        if day_value > 0:
                            days[day] = day_value
                    
                    line = {
                        'id': line_model.id,
                        'timesheet_id': line_model.timesheet_id,
                        'line_number': line_model.line_number,
                        'employee_id': line_model.employee_id,
                        'hourly_rate': line_model.hourly_rate,
                        'total_hours': line_model.total_hours,
                        'total_amount': line_model.total_amount,
                        'employee_name': line_model.employee.full_name if line_model.employee else None,
                        'days': days
                    }
                    
                    # Also include individual day columns for compatibility
                    for day in range(1, 32):
                        day_col = f'day_{day:02d}'
                        line[day_col] = getattr(line_model, day_col)
                    
                    lines.append(line)
                
                timesheet['lines'] = lines
                return timesheet
                
        except Exception as e:
            logger.error(f"Failed to find timesheet by ID {timesheet_id}: {e}")
            return None
    
    def create(self, timesheet_data: Dict, foreman_id: int) -> Dict:
        """Create new timesheet using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                # Convert date string to date object if needed
                date_value = timesheet_data['date']
                if isinstance(date_value, str):
                    from datetime import date
                    date_value = date.fromisoformat(date_value)
                
                # Create timesheet
                timesheet_model = TimesheetModel(
                    number=timesheet_data['number'],
                    date=date_value,
                    object_id=timesheet_data.get('object_id'),
                    estimate_id=timesheet_data.get('estimate_id'),
                    foreman_id=foreman_id,
                    month_year=timesheet_data['month_year']
                )
                session.add(timesheet_model)
                session.flush()  # Get the ID without committing
                
                timesheet_id = timesheet_model.id
                
                # Create lines
                if 'lines' in timesheet_data:
                    for line in timesheet_data['lines']:
                        self._create_line_model(session, timesheet_id, line)
                
                # Transaction will be committed by session_scope
            
            return self.find_by_id(timesheet_id)
            
        except Exception as e:
            logger.error(f"Failed to create timesheet: {e}")
            return None
    
    def update(self, timesheet_id: int, timesheet_data: Dict) -> Dict:
        """Update existing timesheet using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                # Get existing timesheet
                timesheet_model = session.query(TimesheetModel)\
                    .filter(TimesheetModel.id == timesheet_id)\
                    .first()
                
                if not timesheet_model:
                    logger.error(f"Timesheet with ID {timesheet_id} not found")
                    return None
                
                # Convert date string to date object if needed
                date_value = timesheet_data['date']
                if isinstance(date_value, str):
                    from datetime import date
                    date_value = date.fromisoformat(date_value)
                
                # Update fields
                timesheet_model.number = timesheet_data['number']
                timesheet_model.date = date_value
                timesheet_model.object_id = timesheet_data.get('object_id')
                timesheet_model.estimate_id = timesheet_data.get('estimate_id')
                timesheet_model.month_year = timesheet_data['month_year']
                
                # Delete old lines (cascade will handle this)
                session.query(TimesheetLineModel)\
                    .filter(TimesheetLineModel.timesheet_id == timesheet_id)\
                    .delete()
                
                # Create new lines
                if 'lines' in timesheet_data:
                    for line in timesheet_data['lines']:
                        self._create_line_model(session, timesheet_id, line)
                
                # Transaction will be committed by session_scope
            
            return self.find_by_id(timesheet_id)
            
        except Exception as e:
            logger.error(f"Failed to update timesheet: {e}")
            return None
    
    def delete(self, timesheet_id: int) -> bool:
        """Delete timesheet (soft delete) using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                timesheet_model = session.query(TimesheetModel)\
                    .filter(TimesheetModel.id == timesheet_id)\
                    .first()
                
                if timesheet_model:
                    timesheet_model.marked_for_deletion = True
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete timesheet {timesheet_id}: {e}")
            return False
    
    def mark_posted(self, timesheet_id: int) -> bool:
        """Mark timesheet as posted using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                timesheet_model = session.query(TimesheetModel)\
                    .filter(TimesheetModel.id == timesheet_id)\
                    .first()
                
                if timesheet_model:
                    timesheet_model.is_posted = True
                    timesheet_model.posted_at = datetime.now()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to mark timesheet {timesheet_id} as posted: {e}")
            return False
    
    def unmark_posted(self, timesheet_id: int) -> bool:
        """Unmark timesheet as posted using SQLAlchemy"""
        try:
            with self.db_manager.session_scope() as session:
                timesheet_model = session.query(TimesheetModel)\
                    .filter(TimesheetModel.id == timesheet_id)\
                    .first()
                
                if timesheet_model:
                    timesheet_model.is_posted = False
                    timesheet_model.posted_at = None
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to unmark timesheet {timesheet_id} as posted: {e}")
            return False
    
    def _create_line_model(self, session, timesheet_id: int, line: Dict):
        """Create timesheet line model"""
        # Prepare day columns
        day_values = {}
        for day in range(1, 32):
            day_col = f'day_{day:02d}'
            day_values[day_col] = line.get('days', {}).get(day, 0)
        
        # Calculate totals
        total_hours = sum(line.get('days', {}).values())
        total_amount = total_hours * line.get('hourly_rate', 0)
        
        # Create line model
        line_model = TimesheetLineModel(
            timesheet_id=timesheet_id,
            line_number=line['line_number'],
            employee_id=line['employee_id'],
            hourly_rate=line.get('hourly_rate', 0),
            day_01=day_values['day_01'],
            day_02=day_values['day_02'],
            day_03=day_values['day_03'],
            day_04=day_values['day_04'],
            day_05=day_values['day_05'],
            day_06=day_values['day_06'],
            day_07=day_values['day_07'],
            day_08=day_values['day_08'],
            day_09=day_values['day_09'],
            day_10=day_values['day_10'],
            day_11=day_values['day_11'],
            day_12=day_values['day_12'],
            day_13=day_values['day_13'],
            day_14=day_values['day_14'],
            day_15=day_values['day_15'],
            day_16=day_values['day_16'],
            day_17=day_values['day_17'],
            day_18=day_values['day_18'],
            day_19=day_values['day_19'],
            day_20=day_values['day_20'],
            day_21=day_values['day_21'],
            day_22=day_values['day_22'],
            day_23=day_values['day_23'],
            day_24=day_values['day_24'],
            day_25=day_values['day_25'],
            day_26=day_values['day_26'],
            day_27=day_values['day_27'],
            day_28=day_values['day_28'],
            day_29=day_values['day_29'],
            day_30=day_values['day_30'],
            day_31=day_values['day_31'],
            total_hours=total_hours,
            total_amount=total_amount
        )
        session.add(line_model)

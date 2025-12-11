"""Timesheet posting service"""
from typing import Tuple, List, Dict
from datetime import date, datetime
from ..data.repositories.timesheet_repository import TimesheetRepository
from ..data.repositories.payroll_register_repository import PayrollRegisterRepository


class TimesheetPostingService:
    def __init__(self):
        self.timesheet_repo = TimesheetRepository()
        self.payroll_repo = PayrollRegisterRepository()
    
    def post_timesheet(self, timesheet_id: int) -> Tuple[bool, str]:
        """Post timesheet and create payroll records"""
        timesheet = self.timesheet_repo.find_by_id(timesheet_id)
        
        if not timesheet:
            return False, "Timesheet not found"
        
        if timesheet['is_posted']:
            return False, "Timesheet is already posted"
        
        # Validate timesheet has data
        if not timesheet.get('lines'):
            return False, "Cannot post: timesheet has no lines"
        
        # Check if any line has working hours
        has_hours = False
        for line in timesheet['lines']:
            if line.get('total_hours', 0) > 0:
                has_hours = True
                break
        
        if not has_hours:
            return False, "Cannot post: timesheet has no working hours"
        
        # Create payroll records
        records = self._create_payroll_records(timesheet)
        
        if not records:
            return False, "Cannot post: no records to create"
        
        # Check for duplicates
        duplicates = self.payroll_repo.check_duplicates(records)
        if duplicates:
            # Format error message
            dup_messages = []
            for dup in duplicates[:3]:  # Show first 3 duplicates
                rec = dup['record']
                dup_messages.append(
                    f"Employee ID {rec['employee_id']} on {rec['work_date']}"
                )
            
            message = "Cannot post: duplicate records found:\n" + "\n".join(dup_messages)
            if len(duplicates) > 3:
                message += f"\n... and {len(duplicates) - 3} more"
            
            return False, message
        
        # Write records
        try:
            self.payroll_repo.write_records(records)
            self.timesheet_repo.mark_posted(timesheet_id)
            return True, "Timesheet posted successfully"
        except Exception as e:
            return False, f"Error posting timesheet: {str(e)}"
    
    def unpost_timesheet(self, timesheet_id: int) -> Tuple[bool, str]:
        """Unpost timesheet and delete payroll records"""
        timesheet = self.timesheet_repo.find_by_id(timesheet_id)
        
        if not timesheet:
            return False, "Timesheet not found"
        
        if not timesheet['is_posted']:
            return False, "Timesheet is not posted"
        
        try:
            self.payroll_repo.delete_by_recorder('timesheet', timesheet_id)
            self.timesheet_repo.unmark_posted(timesheet_id)
            return True, "Timesheet unposted successfully"
        except Exception as e:
            return False, f"Error unposting timesheet: {str(e)}"
    
    def _create_payroll_records(self, timesheet: Dict) -> List[Dict]:
        """Create payroll records from timesheet lines"""
        records = []
        
        # Parse month_year
        try:
            year, month = map(int, timesheet['month_year'].split('-'))
        except (ValueError, AttributeError):
            return records
        
        for line in timesheet['lines']:
            days = line.get('days', {})
            
            for day, hours in days.items():
                if hours > 0:
                    try:
                        work_date = date(year, month, day)
                    except ValueError:
                        # Invalid date (e.g., Feb 30)
                        continue
                    
                    amount = hours * line.get('hourly_rate', 0)
                    
                    record = {
                        'recorder_type': 'timesheet',
                        'recorder_id': timesheet['id'],
                        'line_number': line['line_number'],
                        'period': work_date,
                        'object_id': timesheet.get('object_id'),
                        'estimate_id': timesheet.get('estimate_id'),
                        'employee_id': line['employee_id'],
                        'work_date': work_date,
                        'hours_worked': hours,
                        'amount': amount
                    }
                    records.append(record)
        
        return records

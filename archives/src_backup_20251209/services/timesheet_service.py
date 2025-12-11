"""Timesheet service"""
from typing import List, Dict, Optional
from ..data.repositories.timesheet_repository import TimesheetRepository
from ..data.repositories.reference_repository import ReferenceRepository


class TimesheetService:
    def __init__(self):
        self.timesheet_repo = TimesheetRepository()
        self.person_repo = ReferenceRepository()
    
    def get_timesheets(self, user_id: int, role: str) -> List[Dict]:
        """Get timesheets based on user role"""
        if role == 'admin':
            return self.timesheet_repo.find_all()
        else:
            # Get foreman's person_id
            person = self.person_repo.find_person_by_user_id(user_id)
            if person:
                return self.timesheet_repo.find_all(foreman_id=person['id'])
            return []
    
    def get_by_id(self, timesheet_id: int) -> Optional[Dict]:
        """Get timesheet by ID"""
        return self.timesheet_repo.find_by_id(timesheet_id)
    
    def create_timesheet(self, timesheet_data: Dict, user_id: int) -> Dict:
        """Create new timesheet"""
        person = self.person_repo.find_person_by_user_id(user_id)
        if not person:
            raise ValueError("User has no associated person record")
        
        # Recalculate totals
        self._recalculate_totals(timesheet_data)
        
        return self.timesheet_repo.create(timesheet_data, person['id'])
    
    def update_timesheet(self, timesheet_id: int, timesheet_data: Dict) -> Dict:
        """Update timesheet"""
        # Recalculate totals
        self._recalculate_totals(timesheet_data)
        
        return self.timesheet_repo.update(timesheet_id, timesheet_data)
    
    def delete_timesheet(self, timesheet_id: int) -> bool:
        """Delete timesheet"""
        return self.timesheet_repo.delete(timesheet_id)
    
    def _recalculate_totals(self, timesheet_data: Dict):
        """Recalculate total hours and amount for each line"""
        if 'lines' not in timesheet_data:
            return
        
        for line in timesheet_data['lines']:
            days = line.get('days', {})
            total_hours = sum(days.values())
            hourly_rate = line.get('hourly_rate', 0)
            total_amount = total_hours * hourly_rate
            
            line['total_hours'] = total_hours
            line['total_amount'] = total_amount

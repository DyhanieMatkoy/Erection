"""Auto-fill service for timesheets from daily reports"""
from typing import List, Dict
from datetime import date, timedelta
from sqlalchemy import func
from ..data.database_manager import DatabaseManager
from ..data.models.sqlalchemy_models import DailyReport, DailyReportLine, Person, DailyReportExecutor

class AutoFillService:
    def __init__(self, session=None):
        self.session = session or DatabaseManager().get_session()
        self._owns_session = session is None
    
    def __del__(self):
        if self._owns_session:
            self.session.close()

    def fill_from_daily_reports(
        self,
        object_id: int,
        estimate_id: int,
        month_year: str
    ) -> List[Dict]:
        """
        Fill timesheet lines from daily reports
        
        Args:
            object_id: Object ID
            estimate_id: Estimate ID
            month_year: Month in format "YYYY-MM"
            
        Returns:
            List of timesheet line dictionaries
        """
        # Parse month_year
        try:
            year, month = map(int, month_year.split('-'))
        except (ValueError, AttributeError):
            return []
        
        # Calculate period
        start_date = date(year, month, 1)
        
        # Calculate last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get daily reports for period
        reports = (
            self.session.query(DailyReport)
            .filter(
                DailyReport.estimate_id == estimate_id,
                DailyReport.date >= start_date,
                DailyReport.date <= end_date,
                DailyReport.marked_for_deletion == False
            )
            .order_by(DailyReport.date)
            .all()
        )
        
        if not reports:
            return []
        
        # Aggregate hours by employee and day
        employee_hours = {}  # {employee_id: {day: hours}}
        employee_rates = {}  # {employee_id: hourly_rate}
        
        for report in reports:
            report_day = report.date.day
            
            # Get report lines with executors
            # We filter in python loop or can query lines directly if needed.
            # Querying lines directly is more efficient if reports are many.
            # But iterating report.lines is easier if lazy loading is efficient or eager loaded.
            # Let's query lines directly for all fetched reports to avoid N+1 if not eager loaded.
            
            # Actually, let's just iterate report.lines as the number of reports per month isn't huge (30 max)
            for line in report.lines:
                if line.is_group or line.actual_labor <= 0:
                    continue
                
                # Get executors
                executors = line.executors # This is a list of DailyReportExecutor objects
                
                if executors:
                    # Distribute hours
                    hours_per_executor = line.actual_labor / len(executors)
                    
                    for executor_assoc in executors:
                        executor_id = executor_assoc.executor_id
                        
                        if executor_id not in employee_hours:
                            employee_hours[executor_id] = {}
                        
                        if report_day not in employee_hours[executor_id]:
                            employee_hours[executor_id][report_day] = 0
                        
                        employee_hours[executor_id][report_day] += hours_per_executor

        # Get hourly rates for employees
        if employee_hours:
            employee_ids = list(employee_hours.keys())
            persons = self.session.query(Person).filter(Person.id.in_(employee_ids)).all()
            for person in persons:
                employee_rates[person.id] = person.hourly_rate or 0.0
        
        # Create timesheet lines
        lines = []
        for line_number, (employee_id, days) in enumerate(employee_hours.items(), 1):
            hourly_rate = employee_rates.get(employee_id, 0)
            
            line = {
                'line_number': line_number,
                'employee_id': employee_id,
                'hourly_rate': hourly_rate,
                'days': days
            }
            lines.append(line)
        
        return lines

"""Auto-fill service for timesheets from daily reports"""
from typing import List, Dict
from datetime import date, timedelta
from ..data.database_manager import DatabaseManager


class AutoFillService:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
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
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT dr.id, dr.date
            FROM daily_reports dr
            WHERE dr.estimate_id = ?
              AND dr.date >= ?
              AND dr.date <= ?
              AND dr.marked_for_deletion = 0
            ORDER BY dr.date
        """, (estimate_id, start_date.isoformat(), end_date.isoformat()))
        
        report_rows = cursor.fetchall()
        
        if not report_rows:
            return []
        
        # Aggregate hours by employee and day
        employee_hours = {}  # {employee_id: {day: hours}}
        employee_rates = {}  # {employee_id: hourly_rate}
        
        for report_row in report_rows:
            report_id = report_row['id']
            report_date = date.fromisoformat(report_row['date'])
            day = report_date.day
            
            # Get report lines with executors
            cursor.execute("""
                SELECT drl.id, drl.actual_labor
                FROM daily_report_lines drl
                WHERE drl.daily_report_id = ?
                  AND drl.is_group = 0
                  AND drl.actual_labor > 0
            """, (report_id,))
            
            line_rows = cursor.fetchall()
            
            for line_row in line_rows:
                line_id = line_row['id']
                actual_labor = line_row['actual_labor']
                
                # Get executors for this line
                cursor.execute("""
                    SELECT executor_id
                    FROM daily_report_executors
                    WHERE report_line_id = ?
                """, (line_id,))
                
                executor_rows = cursor.fetchall()
                executor_ids = [row['executor_id'] for row in executor_rows]
                
                if executor_ids:
                    # Distribute hours among executors
                    hours_per_executor = actual_labor / len(executor_ids)
                    
                    for executor_id in executor_ids:
                        if executor_id not in employee_hours:
                            employee_hours[executor_id] = {}
                        
                        if day not in employee_hours[executor_id]:
                            employee_hours[executor_id][day] = 0
                        
                        employee_hours[executor_id][day] += hours_per_executor
        
        # Get hourly rates for employees
        if employee_hours:
            employee_ids = list(employee_hours.keys())
            placeholders = ','.join('?' * len(employee_ids))
            
            # Note: Assuming hourly_rate field exists in persons table
            # If not, we'll use 0 as default
            cursor.execute(f"""
                SELECT id, full_name
                FROM persons
                WHERE id IN ({placeholders})
            """, employee_ids)
            
            for row in cursor.fetchall():
                employee_rates[row['id']] = 0  # Default rate, can be updated later
        
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

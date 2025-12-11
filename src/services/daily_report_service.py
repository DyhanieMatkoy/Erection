"""Daily report service"""
from typing import Optional, List
from ..data.models.daily_report import DailyReport
from ..data.database_manager import DatabaseManager
from .daily_report_print_form import DailyReportPrintForm


class DailyReportService:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.print_form = DailyReportPrintForm()
    
    def create(self) -> DailyReport:
        """Create new daily report"""
        return DailyReport()
    
    def load(self, report_id: int) -> Optional[DailyReport]:
        """Load daily report"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, date, estimate_id, foreman_id
            FROM daily_reports
            WHERE id = ?
        """, (report_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        report = DailyReport()
        report.id = row['id']
        report.date = row['date']
        report.estimate_id = row['estimate_id']
        report.foreman_id = row['foreman_id']
        
        # Load lines
        cursor.execute("""
            SELECT id, line_number, work_id, planned_labor, actual_labor, deviation_percent,
                   is_group, group_name, parent_group_id, is_collapsed
            FROM daily_report_lines
            WHERE daily_report_id = ?
            ORDER BY line_number
        """, (report_id,))
        
        from ..data.models.daily_report import DailyReportLine
        for line_row in cursor.fetchall():
            line = DailyReportLine()
            line.id = line_row['id']
            line.daily_report_id = report_id
            line.line_number = line_row['line_number']
            line.work_id = line_row['work_id']
            
            # Convert to float, handling non-numeric values
            try:
                line.planned_labor = float(line_row['planned_labor']) if line_row['planned_labor'] else 0.0
            except (ValueError, TypeError):
                line.planned_labor = 0.0
            
            try:
                line.actual_labor = float(line_row['actual_labor']) if line_row['actual_labor'] else 0.0
            except (ValueError, TypeError):
                line.actual_labor = 0.0
            
            try:
                line.deviation_percent = float(line_row['deviation_percent']) if line_row['deviation_percent'] else 0.0
            except (ValueError, TypeError):
                line.deviation_percent = 0.0
            
            line.is_group = bool(line_row.get('is_group', 0))
            line.group_name = line_row.get('group_name', '')
            line.parent_group_id = line_row.get('parent_group_id', 0) or 0
            line.is_collapsed = bool(line_row.get('is_collapsed', 0))
            
            # Load executors
            cursor.execute("""
                SELECT executor_id
                FROM daily_report_executors
                WHERE report_line_id = ?
            """, (line.id,))
            line.executor_ids = [row['executor_id'] for row in cursor.fetchall()]
            
            report.lines.append(line)
        
        return report
    
    def save(self, report: DailyReport) -> bool:
        """Save daily report"""
        try:
            cursor = self.db.cursor()
            
            if report.id == 0:
                # Insert new
                cursor.execute("""
                    INSERT INTO daily_reports (date, estimate_id, foreman_id)
                    VALUES (?, ?, ?)
                """, (report.date, report.estimate_id, report.foreman_id))
                
                report.id = cursor.lastrowid
            else:
                # Update existing
                cursor.execute("""
                    UPDATE daily_reports 
                    SET date = ?, estimate_id = ?, foreman_id = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (report.date, report.estimate_id, report.foreman_id, report.id))
                
                # Delete old lines and executors
                cursor.execute("DELETE FROM daily_report_executors WHERE report_line_id IN (SELECT id FROM daily_report_lines WHERE daily_report_id = ?)", (report.id,))
                cursor.execute("DELETE FROM daily_report_lines WHERE daily_report_id = ?", (report.id,))
            
            # Insert lines
            for line in report.lines:
                cursor.execute("""
                    INSERT INTO daily_report_lines (daily_report_id, line_number, work_id, planned_labor, 
                                                   actual_labor, deviation_percent, is_group, group_name,
                                                   parent_group_id, is_collapsed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (report.id, line.line_number, line.work_id, line.planned_labor,
                      line.actual_labor, line.deviation_percent, 1 if line.is_group else 0,
                      line.group_name, line.parent_group_id or None, 1 if line.is_collapsed else 0))
                
                line_id = cursor.lastrowid
                
                # Insert executors
                for executor_id in line.executor_ids:
                    cursor.execute("""
                        INSERT INTO daily_report_executors (report_line_id, executor_id)
                        VALUES (?, ?)
                    """, (line_id, executor_id))
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving daily report: {e}")
            return False
    
    def get_unfinished_estimates(self) -> List[tuple]:
        """Get list of unfinished estimates"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT e.id, e.number, e.date, c.name as customer_name, o.name as object_name
            FROM estimates e
            LEFT JOIN counterparties c ON e.customer_id = c.id
            LEFT JOIN objects o ON e.object_id = o.id
            ORDER BY e.date DESC, e.number
        """)
        
        return cursor.fetchall()
    
    def get_estimate_works(self, estimate_id: int) -> List[tuple]:
        """Get works from estimate with planned labor"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT el.work_id, w.name as work_name, el.planned_labor
            FROM estimate_lines el
            JOIN works w ON el.work_id = w.id
            WHERE el.estimate_id = ? AND el.is_group = 0
            ORDER BY el.line_number
        """, (estimate_id,))
        
        return cursor.fetchall()
    
    def fill_from_estimate(self, report: DailyReport, selected_line_ids: List[int]) -> bool:
        """
        Fill daily report from selected estimate lines
        
        Args:
            report: Daily report to fill
            selected_line_ids: List of estimate line IDs to copy
            
        Returns:
            True if successful
        """
        try:
            cursor = self.db.cursor()
            
            # Load selected estimate lines
            if not selected_line_ids:
                return False
            
            placeholders = ','.join('?' * len(selected_line_ids))
            cursor.execute(f"""
                SELECT el.id, el.work_id, el.planned_labor, el.is_group, el.group_name,
                       el.parent_group_id, w.name as work_name
                FROM estimate_lines el
                LEFT JOIN works w ON el.work_id = w.id
                WHERE el.id IN ({placeholders})
                ORDER BY el.line_number
            """, selected_line_ids)
            
            from ..data.models.daily_report import DailyReportLine
            
            # Clear existing lines
            report.lines = []
            
            # Add lines from estimate
            line_number = 1
            for row in cursor.fetchall():
                line = DailyReportLine()
                line.line_number = line_number
                line.work_id = row['work_id']
                
                # Convert planned_labor to float, handling non-numeric values
                try:
                    line.planned_labor = float(row['planned_labor']) if row['planned_labor'] else 0.0
                except (ValueError, TypeError):
                    line.planned_labor = 0.0
                
                line.actual_labor = 0.0
                line.deviation_percent = 0.0
                line.is_group = bool(row['is_group'])
                line.group_name = row['group_name'] or ""
                line.parent_group_id = row['parent_group_id'] or 0
                
                report.lines.append(line)
                line_number += 1
            
            return True
            
        except Exception as e:
            print(f"Error filling from estimate: {e}")
            return False
    
    def generate_print_form(self, report_id: int) -> Optional[bytes]:
        """
        Generate print form for daily report
        
        Args:
            report_id: ID of the daily report
            
        Returns:
            PDF content as bytes or None if report not found
        """
        return self.print_form.generate(report_id)

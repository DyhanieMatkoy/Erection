"""Document posting service"""
from datetime import datetime
from typing import Optional
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository


class DocumentPostingService:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.register_repo = WorkExecutionRegisterRepository()
    
    def post_estimate(self, estimate_id: int) -> tuple[bool, Optional[str]]:
        """
        Post estimate document
        
        Returns:
            (success, error_message)
        """
        cursor = self.db.cursor()
        
        # Load estimate
        cursor.execute("""
            SELECT e.*, e.date, e.object_id
            FROM estimates e
            WHERE e.id = ?
        """, (estimate_id,))
        
        estimate = cursor.fetchone()
        if not estimate:
            return False, "Смета не найдена"
        
        if estimate['is_posted']:
            return False, "Смета уже проведена"
        
        # Validate
        if not estimate['number']:
            return False, "Не заполнен номер сметы"
        
        if not estimate['customer_id']:
            return False, "Не заполнен заказчик"
        
        if not estimate['object_id']:
            return False, "Не заполнен объект"
        
        # Load lines
        cursor.execute("""
            SELECT * FROM estimate_lines
            WHERE estimate_id = ?
            ORDER BY line_number
        """, (estimate_id,))
        
        lines = cursor.fetchall()
        if not lines:
            return False, "Смета не содержит строк"
        
        try:
            # Delete old movements (if any)
            self.register_repo.delete_movements('estimate', estimate_id)
            
            # Create movements
            for line in lines:
                movement = {
                    'recorder_type': 'estimate',
                    'recorder_id': estimate_id,
                    'line_number': line['line_number'],
                    'period': estimate['date'],
                    'object_id': estimate['object_id'],
                    'estimate_id': estimate_id,
                    'work_id': line['work_id'],
                    'quantity_income': line['quantity'],
                    'quantity_expense': 0,
                    'sum_income': line['sum'],
                    'sum_expense': 0
                }
                self.register_repo.create_movement(movement)
            
            # Mark as posted
            cursor.execute("""
                UPDATE estimates
                SET is_posted = 1, posted_at = ?
                WHERE id = ?
            """, (datetime.now(), estimate_id))
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Ошибка при проведении: {str(e)}"
    
    def unpost_estimate(self, estimate_id: int) -> tuple[bool, Optional[str]]:
        """
        Unpost estimate document
        
        Returns:
            (success, error_message)
        """
        cursor = self.db.cursor()
        
        # Check if posted
        cursor.execute("SELECT is_posted FROM estimates WHERE id = ?", (estimate_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Смета не найдена"
        
        if not row['is_posted']:
            return False, "Смета не проведена"
        
        try:
            # Delete movements
            self.register_repo.delete_movements('estimate', estimate_id)
            
            # Mark as not posted
            cursor.execute("""
                UPDATE estimates
                SET is_posted = 0, posted_at = NULL
                WHERE id = ?
            """, (estimate_id,))
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Ошибка при отмене проведения: {str(e)}"
    
    def post_daily_report(self, report_id: int) -> tuple[bool, Optional[str]]:
        """
        Post daily report document
        
        Returns:
            (success, error_message)
        """
        cursor = self.db.cursor()
        
        # Load report
        cursor.execute("""
            SELECT dr.*, e.object_id, e.number as estimate_number
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            WHERE dr.id = ?
        """, (report_id,))
        
        report = cursor.fetchone()
        if not report:
            return False, "Отчет не найден"
        
        if report['is_posted']:
            return False, "Отчет уже проведен"
        
        # Validate
        if not report['estimate_id']:
            return False, "Не выбрана смета"
        
        if not report['foreman_id']:
            return False, "Не выбран бригадир"
        
        if not report['object_id']:
            return False, "У сметы не заполнен объект"
        
        # Load lines
        cursor.execute("""
            SELECT drl.*, w.price
            FROM daily_report_lines drl
            LEFT JOIN works w ON drl.work_id = w.id
            WHERE drl.report_id = ?
            ORDER BY drl.line_number
        """, (report_id,))
        
        lines = cursor.fetchall()
        if not lines:
            return False, "Отчет не содержит строк"
        
        try:
            # Delete old movements (if any)
            self.register_repo.delete_movements('daily_report', report_id)
            
            # Create movements
            for line in lines:
                # Calculate sum based on actual labor and work price
                sum_value = line['actual_labor'] * (line['price'] or 0)
                
                movement = {
                    'recorder_type': 'daily_report',
                    'recorder_id': report_id,
                    'line_number': line['line_number'],
                    'period': report['date'],
                    'object_id': report['object_id'],
                    'estimate_id': report['estimate_id'],
                    'work_id': line['work_id'],
                    'quantity_income': 0,
                    'quantity_expense': line['actual_labor'],
                    'sum_income': 0,
                    'sum_expense': sum_value
                }
                self.register_repo.create_movement(movement)
            
            # Mark as posted
            cursor.execute("""
                UPDATE daily_reports
                SET is_posted = 1, posted_at = ?
                WHERE id = ?
            """, (datetime.now(), report_id))
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Ошибка при проведении: {str(e)}"
    
    def unpost_daily_report(self, report_id: int) -> tuple[bool, Optional[str]]:
        """
        Unpost daily report document
        
        Returns:
            (success, error_message)
        """
        cursor = self.db.cursor()
        
        # Check if posted
        cursor.execute("SELECT is_posted FROM daily_reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Отчет не найден"
        
        if not row['is_posted']:
            return False, "Отчет не проведен"
        
        try:
            # Delete movements
            self.register_repo.delete_movements('daily_report', report_id)
            
            # Mark as not posted
            cursor.execute("""
                UPDATE daily_reports
                SET is_posted = 0, posted_at = NULL
                WHERE id = ?
            """, (report_id,))
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Ошибка при отмене проведения: {str(e)}"

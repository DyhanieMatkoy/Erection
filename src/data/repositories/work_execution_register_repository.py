"""Work execution register repository"""
from typing import List, Dict, Optional
from ..database_manager import DatabaseManager


class WorkExecutionRegisterRepository:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
    def get_movements(self, recorder_type: str, recorder_id: int) -> List[Dict]:
        """Get movements for a document"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT *
            FROM work_execution_register
            WHERE recorder_type = ? AND recorder_id = ?
            ORDER BY line_number
        """, (recorder_type, recorder_id))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_movements(self, recorder_type: str, recorder_id: int):
        """Delete all movements for a document"""
        cursor = self.db.cursor()
        cursor.execute("""
            DELETE FROM work_execution_register
            WHERE recorder_type = ? AND recorder_id = ?
        """, (recorder_type, recorder_id))
        self.db.commit()
    
    def create_movement(self, movement: Dict):
        """Create a single movement"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO work_execution_register (
                recorder_type, recorder_id, line_number, period,
                object_id, estimate_id, work_id,
                quantity_income, quantity_expense,
                sum_income, sum_expense
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movement['recorder_type'],
            movement['recorder_id'],
            movement['line_number'],
            movement['period'],
            movement['object_id'],
            movement['estimate_id'],
            movement['work_id'],
            movement.get('quantity_income', 0),
            movement.get('quantity_expense', 0),
            movement.get('sum_income', 0),
            movement.get('sum_expense', 0)
        ))
        self.db.commit()
    
    def get_balance(self, filters: Optional[Dict] = None, grouping: Optional[List[str]] = None) -> List[Dict]:
        """
        Get balance with grouping
        
        Args:
            filters: Dict with keys: period_end, object_id, estimate_id, work_id
            grouping: List of fields to group by: 'object', 'estimate', 'work', 'period'
        """
        if grouping is None:
            grouping = ['estimate', 'work']
        
        # Build SELECT clause
        select_fields = []
        group_fields = []
        
        if 'object' in grouping:
            select_fields.append('o.name as object_name')
            select_fields.append('r.object_id')
            group_fields.append('r.object_id')
        
        if 'estimate' in grouping:
            select_fields.append('e.number as estimate_number')
            select_fields.append('r.estimate_id')
            group_fields.append('r.estimate_id')
        
        if 'work' in grouping:
            select_fields.append('w.name as work_name')
            select_fields.append('r.work_id')
            group_fields.append('r.work_id')
        
        if 'period' in grouping:
            select_fields.append('r.period')
            group_fields.append('r.period')
        
        select_clause = ', '.join(select_fields) if select_fields else '1'
        group_clause = ', '.join(group_fields) if group_fields else ''
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if filters:
            if 'period_end' in filters:
                where_clauses.append('r.period <= ?')
                params.append(filters['period_end'])
            
            if 'object_id' in filters:
                where_clauses.append('r.object_id = ?')
                params.append(filters['object_id'])
            
            if 'estimate_id' in filters:
                where_clauses.append('r.estimate_id = ?')
                params.append(filters['estimate_id'])
            
            if 'work_id' in filters:
                where_clauses.append('r.work_id = ?')
                params.append(filters['work_id'])
        
        where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        # Build query
        query = f"""
            SELECT 
                {select_clause},
                SUM(r.quantity_income) as quantity_income,
                SUM(r.quantity_expense) as quantity_expense,
                SUM(r.quantity_income - r.quantity_expense) as quantity_balance,
                SUM(r.sum_income) as sum_income,
                SUM(r.sum_expense) as sum_expense,
                SUM(r.sum_income - r.sum_expense) as sum_balance
            FROM work_execution_register r
            LEFT JOIN objects o ON r.object_id = o.id
            LEFT JOIN estimates e ON r.estimate_id = e.id
            LEFT JOIN works w ON r.work_id = w.id
            WHERE {where_clause}
        """
        
        if group_clause:
            query += f" GROUP BY {group_clause}"
        
        query += " ORDER BY " + (group_clause if group_clause else '1')
        
        cursor = self.db.cursor()
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_turnovers(self, period_start: str, period_end: str, 
                     filters: Optional[Dict] = None, 
                     grouping: Optional[List[str]] = None) -> List[Dict]:
        """
        Get turnovers for period with grouping
        
        Args:
            period_start: Start date
            period_end: End date
            filters: Dict with keys: object_id, estimate_id, work_id
            grouping: List of fields to group by: 'object', 'estimate', 'work', 'period'
        """
        if grouping is None:
            grouping = ['estimate', 'work']
        
        # Build SELECT clause
        select_fields = []
        group_fields = []
        
        if 'object' in grouping:
            select_fields.append('o.name as object_name')
            select_fields.append('r.object_id')
            group_fields.append('r.object_id')
        
        if 'estimate' in grouping:
            select_fields.append('e.number as estimate_number')
            select_fields.append('r.estimate_id')
            group_fields.append('r.estimate_id')
        
        if 'work' in grouping:
            select_fields.append('w.name as work_name')
            select_fields.append('r.work_id')
            group_fields.append('r.work_id')
        
        if 'period' in grouping:
            select_fields.append('r.period')
            group_fields.append('r.period')
        
        select_clause = ', '.join(select_fields) if select_fields else '1'
        group_clause = ', '.join(group_fields) if group_fields else ''
        
        # Build WHERE clause
        where_clauses = ['r.period >= ?', 'r.period <= ?']
        params = [period_start, period_end]
        
        if filters:
            if 'object_id' in filters:
                where_clauses.append('r.object_id = ?')
                params.append(filters['object_id'])
            
            if 'estimate_id' in filters:
                where_clauses.append('r.estimate_id = ?')
                params.append(filters['estimate_id'])
            
            if 'work_id' in filters:
                where_clauses.append('r.work_id = ?')
                params.append(filters['work_id'])
        
        where_clause = ' AND '.join(where_clauses)
        
        # Build query
        query = f"""
            SELECT 
                {select_clause},
                SUM(r.quantity_income) as quantity_income,
                SUM(r.quantity_expense) as quantity_expense,
                SUM(r.sum_income) as sum_income,
                SUM(r.sum_expense) as sum_expense
            FROM work_execution_register r
            LEFT JOIN objects o ON r.object_id = o.id
            LEFT JOIN estimates e ON r.estimate_id = e.id
            LEFT JOIN works w ON r.work_id = w.id
            WHERE {where_clause}
        """
        
        if group_clause:
            query += f" GROUP BY {group_clause}"
        
        query += " ORDER BY " + (group_clause if group_clause else '1')
        
        cursor = self.db.cursor()
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]

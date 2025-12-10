"""Estimate repository"""
from typing import List, Optional
from ..database_manager import DatabaseManager
from ..models.estimate import Estimate, EstimateLine


class EstimateRepository:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
    def find_by_id(self, estimate_id: int) -> Optional[Estimate]:
        """Find estimate by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM estimates WHERE id = ?", (estimate_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        estimate = Estimate(
            id=row['id'],
            number=row['number'],
            date=row['date'],
            customer_id=row['customer_id'],
            object_id=row['object_id'],
            contractor_id=row['contractor_id'],
            responsible_id=row['responsible_id'],
            total_sum=row['total_sum'],
            total_labor=row['total_labor']
        )
        
        estimate.lines = self._load_lines(estimate_id)
        return estimate
    
    def save(self, estimate: Estimate) -> bool:
        """Save estimate"""
        try:
            cursor = self.db.cursor()
            
            if estimate.id == 0:
                cursor.execute("""
                    INSERT INTO estimates (number, date, customer_id, object_id, 
                                         contractor_id, responsible_id, total_sum, total_labor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (estimate.number, estimate.date, estimate.customer_id, estimate.object_id,
                      estimate.contractor_id, estimate.responsible_id, estimate.total_sum, estimate.total_labor))
                estimate.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE estimates 
                    SET number=?, date=?, customer_id=?, object_id=?, contractor_id=?, 
                        responsible_id=?, total_sum=?, total_labor=?, modified_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (estimate.number, estimate.date, estimate.customer_id, estimate.object_id,
                      estimate.contractor_id, estimate.responsible_id, estimate.total_sum, 
                      estimate.total_labor, estimate.id))
            
            self._save_lines(estimate)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Failed to save estimate: {e}")
            return False
    
    def find_by_responsible(self, person_id: int) -> List[Estimate]:
        """Find estimates by responsible person"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM estimates 
            WHERE responsible_id = ? 
            ORDER BY date DESC
        """, (person_id,))
        
        estimates = []
        for row in cursor.fetchall():
            estimate = Estimate(
                id=row['id'],
                number=row['number'],
                date=row['date'],
                customer_id=row['customer_id'],
                object_id=row['object_id'],
                contractor_id=row['contractor_id'],
                responsible_id=row['responsible_id'],
                total_sum=row['total_sum'],
                total_labor=row['total_labor']
            )
            estimates.append(estimate)
        
        return estimates
    
    def _load_lines(self, estimate_id: int) -> List[EstimateLine]:
        """Load estimate lines"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM estimate_lines 
            WHERE estimate_id = ? 
            ORDER BY line_number
        """, (estimate_id,))
        
        lines = []
        for row in cursor.fetchall():
            line = EstimateLine(
                id=row['id'],
                estimate_id=estimate_id,
                line_number=row['line_number'],
                work_id=row['work_id'],
                quantity=row['quantity'],
                unit=row['unit'],
                price=row['price'],
                labor_rate=row['labor_rate'],
                sum=row['sum'],
                planned_labor=row['planned_labor'],
                is_group=bool(row.get('is_group', 0)),
                group_name=row.get('group_name', ''),
                parent_group_id=row.get('parent_group_id', 0) or 0,
                is_collapsed=bool(row.get('is_collapsed', 0))
            )
            lines.append(line)
        
        return lines
    
    def _save_lines(self, estimate: Estimate):
        """Save estimate lines"""
        cursor = self.db.cursor()
        
        # Delete existing lines
        cursor.execute("DELETE FROM estimate_lines WHERE estimate_id = ?", (estimate.id,))
        
        # Insert new lines
        for i, line in enumerate(estimate.lines):
            cursor.execute("""
                INSERT INTO estimate_lines 
                (estimate_id, line_number, work_id, quantity, unit, price, labor_rate, sum, planned_labor,
                 is_group, group_name, parent_group_id, is_collapsed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (estimate.id, i + 1, line.work_id, line.quantity, line.unit, 
                  line.price, line.labor_rate, line.sum, line.planned_labor,
                  1 if line.is_group else 0, line.group_name, line.parent_group_id or None, 
                  1 if line.is_collapsed else 0))

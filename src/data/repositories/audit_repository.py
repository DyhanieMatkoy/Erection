from typing import List, Optional, Tuple
from datetime import datetime
from ..database_manager import DatabaseManager
from ..models.audit import AuditLog

class AuditRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, log: AuditLog) -> AuditLog:
        query = """
            INSERT INTO audit_logs (
                user_id, username, action, resource_type, resource_id, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            log.user_id,
            log.username,
            log.action,
            log.resource_type,
            log.resource_id,
            log.details,
            log.created_at
        )
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        log.id = cursor.lastrowid
        conn.commit()
        return log

    def get_logs(self, 
                 limit: int = 100, 
                 offset: int = 0, 
                 resource_type: Optional[str] = None,
                 resource_id: Optional[int] = None) -> Tuple[List[AuditLog], int]:
        
        where_clauses = []
        params = []
        
        if resource_type:
            where_clauses.append("resource_type = ?")
            params.append(resource_type)
            
        if resource_id:
            where_clauses.append("resource_id = ?")
            params.append(resource_id)
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get count
        count_query = f"SELECT COUNT(*) FROM audit_logs {where_sql}"
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get data
        query = f"""
            SELECT id, user_id, username, action, resource_type, resource_id, details, created_at
            FROM audit_logs
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        
        logs = []
        for row in cursor.fetchall():
            logs.append(AuditLog(
                id=row[0],
                user_id=row[1],
                username=row[2],
                action=row[3],
                resource_type=row[4],
                resource_id=row[5],
                details=row[6],
                created_at=datetime.fromisoformat(str(row[7])) if row[7] else datetime.now()
            ))
            
        return logs, total

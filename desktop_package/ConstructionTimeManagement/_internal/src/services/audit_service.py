from typing import Optional, List, Tuple
from ..data.models.audit import AuditLog
from ..data.repositories.audit_repository import AuditRepository

class AuditService:
    def __init__(self):
        self.repository = AuditRepository()

    def log(self, 
            user_id: int, 
            username: str, 
            action: str, 
            resource_type: str, 
            resource_id: int, 
            details: str = ""):
        """Create an audit log entry"""
        try:
            log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
            self.repository.create(log)
        except Exception as e:
            # Audit logging should not break the application flow, but should be logged to system logs
            import logging
            logging.error(f"Failed to create audit log: {e}")

    def get_logs(self, limit: int = 100, offset: int = 0, resource_type: str = None, resource_id: int = None) -> Tuple[List[AuditLog], int]:
        return self.repository.get_logs(limit, offset, resource_type, resource_id)

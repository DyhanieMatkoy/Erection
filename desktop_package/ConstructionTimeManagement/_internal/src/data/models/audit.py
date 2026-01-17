from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AuditLog:
    id: Optional[int] = None
    user_id: int = 0
    username: str = "" # Denormalized for easier display
    action: str = "" # create, update, delete, link, unlink
    resource_type: str = "" # estimate, daily_report, etc.
    resource_id: int = 0
    details: str = "" # JSON or text description
    created_at: datetime = datetime.now()

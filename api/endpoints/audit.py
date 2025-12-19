from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from api.dependencies.auth import get_current_user
from api.models.auth import UserInfo
from src.services.audit_service import AuditService
from pydantic import BaseModel
from datetime import datetime
import math

router = APIRouter(prefix="/audit", tags=["Audit"])

class AuditLogSchema(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: int
    details: str
    created_at: datetime

class AuditLogListResponse(BaseModel):
    data: List[AuditLogSchema]
    pagination: Dict[str, Any]

@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role != 'admin':
        raise HTTPException(403, "Only admins can view audit logs")
        
    service = AuditService()
    logs, total = service.get_logs(
        limit=page_size, 
        offset=(page-1)*page_size,
        resource_type=resource_type,
        resource_id=resource_id
    )
    
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    
    return {
        "data": [
            AuditLogSchema(
                id=log.id,
                user_id=log.user_id,
                username=log.username,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                created_at=log.created_at
            ) for log in logs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages
        }
    }

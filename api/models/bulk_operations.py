from pydantic import BaseModel
from typing import List, Optional, Any

class BulkOperationRequest(BaseModel):
    """Base request for bulk operations"""
    ids: List[int]
    operation_type: str
    parameters: Optional[dict] = None

class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete (just IDs)"""
    ids: List[int]

class BulkOperationResult(BaseModel):
    """Result of bulk operation"""
    success: bool
    message: str
    processed: int
    errors: List[str] = []
    data: Optional[Any] = None

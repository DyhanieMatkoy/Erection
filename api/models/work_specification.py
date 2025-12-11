from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class WorkSpecificationBase(BaseModel):
    work_id: int
    component_type: str
    component_name: str
    unit_id: Optional[int] = None
    consumption_rate: float = Field(ge=0)  # Changed from gt=0 to ge=0
    unit_price: float = Field(ge=0)

class WorkSpecificationCreate(WorkSpecificationBase):
    pass

class WorkSpecificationUpdate(BaseModel):
    component_type: Optional[str] = None
    component_name: Optional[str] = None
    unit_id: Optional[int] = None
    consumption_rate: Optional[float] = Field(None, ge=0)  # Changed from gt=0 to ge=0
    unit_price: Optional[float] = Field(None, ge=0)

class WorkSpecification(WorkSpecificationBase):
    id: int
    total_cost: float
    unit_name: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkSpecificationSummary(BaseModel):
    work_id: int
    work_name: str
    work_code: Optional[str] = None
    specifications: List[WorkSpecification] = []
    totals_by_type: Dict[str, float] = {}
    total_cost: float = 0.0

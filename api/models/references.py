"""
Reference data models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Base models
class ReferenceBase(BaseModel):
    """Base model for reference data"""
    name: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[int] = None
    is_deleted: bool = False
    uuid: Optional[str] = None


class ReferenceCreate(ReferenceBase):
    """Model for creating reference data"""
    pass


class ReferenceUpdate(ReferenceBase):
    """Model for updating reference data"""
    pass


class Reference(ReferenceBase):
    """Model for reference data with ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Counterparty models
class CounterpartyBase(ReferenceBase):
    """Base model for counterparty"""
    inn: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    is_group: bool = False


class CounterpartyCreate(CounterpartyBase):
    """Model for creating counterparty"""
    pass


class CounterpartyUpdate(CounterpartyBase):
    """Model for updating counterparty"""
    pass


class Counterparty(Reference):
    """Model for counterparty with ID"""
    pass


# Object models
class ObjectBase(BaseModel):
    """Base model for object"""
    name: str = Field(..., min_length=1, max_length=500)
    address: Optional[str] = None
    owner_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_deleted: bool = False


class ObjectCreate(ObjectBase):
    """Model for creating object"""
    pass


class ObjectUpdate(ObjectBase):
    """Model for updating object"""
    pass


class Object(ObjectBase):
    """Model for object with ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Work models
class WorkBase(ReferenceBase):
    """Base model for work"""
    unit: Optional[str] = None  # Deprecated, for backward compatibility
    unit_id: Optional[int] = None
    price: Optional[float] = 0.0
    labor_rate: Optional[float] = 0.0
    is_group: bool = False


class WorkCreate(WorkBase):
    """Model for creating work"""
    pass


class WorkUpdate(WorkBase):
    """Model for updating work"""
    pass


class Work(WorkBase):
    """Model for work with ID and enhanced unit information"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Enhanced unit information
    unit_display: Optional[str] = None
    unit_name: Optional[str] = None
    unit_description: Optional[str] = None
    
    # Hierarchy information
    hierarchy_path: Optional[List[str]] = None
    level: Optional[int] = None
    children_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class WorkListResponse(BaseModel):
    """Enhanced response model for work list"""
    success: bool = True
    data: List[Work]
    pagination: "PaginationInfo"
    hierarchy_mode: Optional[str] = None
    parent_id: Optional[int] = None


# Person models
class PersonBase(BaseModel):
    """Base model for person"""
    full_name: str = Field(..., min_length=1, max_length=500)
    position: Optional[str] = None
    parent_id: Optional[int] = None
    is_deleted: bool = False


class PersonCreate(PersonBase):
    """Model for creating person"""
    pass


class PersonUpdate(PersonBase):
    """Model for updating person"""
    pass


class Person(PersonBase):
    """Model for person with ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Organization models
class OrganizationBase(ReferenceBase):
    """Base model for organization"""
    pass


class OrganizationCreate(OrganizationBase):
    """Model for creating organization"""
    pass


class OrganizationUpdate(OrganizationBase):
    """Model for updating organization"""
    pass


class Organization(Reference):
    """Model for organization with ID"""
    pass


# Unit models
class UnitBase(BaseModel):
    """Base model for unit"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    marked_for_deletion: bool = False


class UnitCreate(UnitBase):
    """Model for creating unit"""
    pass


class UnitUpdate(UnitBase):
    """Model for updating unit"""
    pass


class Unit(UnitBase):
    """Model for unit with ID"""
    id: int
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Pagination models
class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ReferenceListResponse(BaseModel):
    """Response model for reference list"""
    success: bool = True
    data: List[Reference]
    pagination: PaginationInfo

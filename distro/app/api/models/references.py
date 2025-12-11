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
    pass


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
    unit: Optional[str] = None


class WorkCreate(WorkBase):
    """Model for creating work"""
    pass


class WorkUpdate(WorkBase):
    """Model for updating work"""
    pass


class Work(WorkBase):
    """Model for work with ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


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

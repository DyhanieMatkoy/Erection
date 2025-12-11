"""
Reference data endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from api.models.references import (
    Counterparty, CounterpartyCreate, CounterpartyUpdate,
    Object, ObjectCreate, ObjectUpdate,
    Work, WorkCreate, WorkUpdate,
    Person, PersonCreate, PersonUpdate,
    Organization, OrganizationCreate, OrganizationUpdate,
    PaginationInfo
)
from api.models.auth import UserInfo
from api.dependencies.auth import get_current_user
from src.data.database_manager import DatabaseManager
from api.config import settings
import math


router = APIRouter(prefix="/references", tags=["References"])


def get_db():
    """Dependency to get database connection"""
    db_manager = DatabaseManager()
    if not db_manager._connection:
        db_manager.initialize(settings.DATABASE_PATH)
    return db_manager.get_connection()


def create_pagination_info(page: int, page_size: int, total_items: int) -> PaginationInfo:
    """Create pagination info"""
    total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
    return PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages
    )


# Counterparties endpoints
@router.get("/counterparties")
async def list_counterparties(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get list of counterparties"""
    offset = (page - 1) * page_size
    
    items = repo.get_counterparties(
        search=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = repo.count_counterparties(search=search)
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/counterparties", status_code=status.HTTP_201_CREATED)
async def create_counterparty(
    data: CounterpartyCreate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Create new counterparty"""
    item_id = repo.create_counterparty(
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_counterparty_by_id(item_id)
    return {"success": True, "data": item}


@router.get("/counterparties/{item_id}")
async def get_counterparty(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get counterparty by ID"""
    item = repo.get_counterparty_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Counterparty not found")
    return {"success": True, "data": item}


@router.put("/counterparties/{item_id}")
async def update_counterparty(
    item_id: int,
    data: CounterpartyUpdate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Update counterparty"""
    repo.update_counterparty(
        item_id=item_id,
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_counterparty_by_id(item_id)
    return {"success": True, "data": item}


@router.delete("/counterparties/{item_id}")
async def delete_counterparty(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Mark counterparty as deleted"""
    repo.delete_counterparty(item_id)
    return {"success": True, "message": "Counterparty marked as deleted"}


# Objects endpoints
@router.get("/objects")
async def list_objects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get list of objects"""
    offset = (page - 1) * page_size
    
    items = repo.get_objects(
        search=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = repo.count_objects(search=search)
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/objects", status_code=status.HTTP_201_CREATED)
async def create_object(
    data: ObjectCreate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Create new object"""
    item_id = repo.create_object(
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_object_by_id(item_id)
    return {"success": True, "data": item}


@router.get("/objects/{item_id}")
async def get_object(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get object by ID"""
    item = repo.get_object_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Object not found")
    return {"success": True, "data": item}


@router.put("/objects/{item_id}")
async def update_object(
    item_id: int,
    data: ObjectUpdate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Update object"""
    repo.update_object(
        item_id=item_id,
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_object_by_id(item_id)
    return {"success": True, "data": item}


@router.delete("/objects/{item_id}")
async def delete_object(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Mark object as deleted"""
    repo.delete_object(item_id)
    return {"success": True, "message": "Object marked as deleted"}


# Works endpoints
@router.get("/works")
async def list_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get list of works"""
    offset = (page - 1) * page_size
    
    items = repo.get_works(
        search=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = repo.count_works(search=search)
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/works", status_code=status.HTTP_201_CREATED)
async def create_work(
    data: WorkCreate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Create new work"""
    item_id = repo.create_work(
        name=data.name,
        unit=data.unit,
        parent_id=data.parent_id
    )
    item = repo.get_work_by_id(item_id)
    return {"success": True, "data": item}


@router.get("/works/{item_id}")
async def get_work(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get work by ID"""
    item = repo.get_work_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work not found")
    return {"success": True, "data": item}


@router.put("/works/{item_id}")
async def update_work(
    item_id: int,
    data: WorkUpdate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Update work"""
    repo.update_work(
        item_id=item_id,
        name=data.name,
        unit=data.unit,
        parent_id=data.parent_id
    )
    item = repo.get_work_by_id(item_id)
    return {"success": True, "data": item}


@router.delete("/works/{item_id}")
async def delete_work(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Mark work as deleted"""
    repo.delete_work(item_id)
    return {"success": True, "message": "Work marked as deleted"}


# Persons endpoints
@router.get("/persons")
async def list_persons(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get list of persons"""
    offset = (page - 1) * page_size
    
    items = repo.get_persons(
        search=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = repo.count_persons(search=search)
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/persons", status_code=status.HTTP_201_CREATED)
async def create_person(
    data: PersonCreate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Create new person"""
    item_id = repo.create_person(
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_person_by_id(item_id)
    return {"success": True, "data": item}


@router.get("/persons/{item_id}")
async def get_person(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get person by ID"""
    item = repo.get_person_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"success": True, "data": item}


@router.put("/persons/{item_id}")
async def update_person(
    item_id: int,
    data: PersonUpdate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Update person"""
    repo.update_person(
        item_id=item_id,
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_person_by_id(item_id)
    return {"success": True, "data": item}


@router.delete("/persons/{item_id}")
async def delete_person(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Mark person as deleted"""
    repo.delete_person(item_id)
    return {"success": True, "message": "Person marked as deleted"}


# Organizations endpoints
@router.get("/organizations")
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get list of organizations"""
    offset = (page - 1) * page_size
    
    items = repo.get_organizations(
        search=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = repo.count_organizations(search=search)
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Create new organization"""
    item_id = repo.create_organization(
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_organization_by_id(item_id)
    return {"success": True, "data": item}


@router.get("/organizations/{item_id}")
async def get_organization(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Get organization by ID"""
    item = repo.get_organization_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"success": True, "data": item}


@router.put("/organizations/{item_id}")
async def update_organization(
    item_id: int,
    data: OrganizationUpdate,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Update organization"""
    repo.update_organization(
        item_id=item_id,
        name=data.name,
        parent_id=data.parent_id
    )
    item = repo.get_organization_by_id(item_id)
    return {"success": True, "data": item}


@router.delete("/organizations/{item_id}")
async def delete_organization(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    repo: ReferenceRepository = Depends(get_reference_repo)
):
    """Mark organization as deleted"""
    repo.delete_organization(item_id)
    return {"success": True, "message": "Organization marked as deleted"}

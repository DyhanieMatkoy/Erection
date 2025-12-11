"""
Reference data endpoints - rewritten to use direct DB access
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
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
from api.dependencies.database import get_db_connection
from api.config import settings
from api.validation.work_validation_direct import (
    validate_work_name_direct,
    validate_group_work_constraints_direct,
    validate_parent_circular_reference_direct
)
import math


router = APIRouter(prefix="/references", tags=["References"])


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
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of counterparties"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    where_clause = "marked_for_deletion = 0"
    params = []
    
    if search:
        where_clause += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM counterparties WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, name, parent_id, marked_for_deletion
        FROM counterparties
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/counterparties", status_code=status.HTTP_201_CREATED)
async def create_counterparty(
    data: CounterpartyCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new counterparty"""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO counterparties (name, parent_id) VALUES (?, ?)",
        (data.name, data.parent_id)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM counterparties WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/counterparties/{item_id}")
async def get_counterparty(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get counterparty by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM counterparties WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Counterparty not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/counterparties/{item_id}")
async def update_counterparty(
    item_id: int,
    data: CounterpartyUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update counterparty"""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE counterparties SET name = ?, parent_id = ? WHERE id = ?",
        (data.name, data.parent_id, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM counterparties WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/counterparties/{item_id}")
async def delete_counterparty(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark counterparty as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE counterparties SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Counterparty marked as deleted"}


# Objects endpoints
@router.get("/objects")
async def list_objects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of objects"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    where_clause = "marked_for_deletion = 0"
    params = []
    
    if search:
        where_clause += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM objects WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, name, address, owner_id, parent_id, marked_for_deletion
        FROM objects
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/objects", status_code=status.HTTP_201_CREATED)
async def create_object(
    data: ObjectCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new object"""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO objects (name, address, owner_id, parent_id) VALUES (?, ?, ?, ?)",
        (data.name, data.address, data.owner_id, data.parent_id)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM objects WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/objects/{item_id}")
async def get_object(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get object by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM objects WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Object not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/objects/{item_id}")
async def update_object(
    item_id: int,
    data: ObjectUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update object"""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE objects SET name = ?, address = ?, owner_id = ?, parent_id = ? WHERE id = ?",
        (data.name, data.address, data.owner_id, data.parent_id, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM objects WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/objects/{item_id}")
async def delete_object(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark object as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE objects SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Object marked as deleted"}


# Works endpoints
@router.get("/works")
async def list_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of works"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    where_clause = "marked_for_deletion = 0"
    params = []
    
    if search:
        where_clause += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM works WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, name, code, unit, price, labor_rate, is_group, parent_id, marked_for_deletion
        FROM works
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/works", status_code=status.HTTP_201_CREATED)
async def create_work(
    data: WorkCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new work
    
    Validation:
    - Work name must not be empty or whitespace-only (Req 1.2, 11.1)
    - Group works cannot have price or labor_rate (Req 1.3, 11.2)
    - Parent must not create circular reference (Req 1.4, 15.3)
    """
    # Validate work name
    validate_work_name_direct(data.name)
    
    # Validate group work constraints
    validate_group_work_constraints_direct(data.is_group, data.price, data.labor_rate)
    
    # Validate parent circular reference (work_id is None for new works)
    validate_parent_circular_reference_direct(db, None, data.parent_id)
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO works (name, unit, price, labor_rate, is_group, parent_id) VALUES (?, ?, ?, ?, ?, ?)",
        (data.name, data.unit, data.price or 0.0, data.labor_rate or 0.0, data.is_group, data.parent_id)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM works WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/works/{item_id}")
async def get_work(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get work by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM works WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Work not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/works/{item_id}")
async def update_work(
    item_id: int,
    data: WorkUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update work
    
    Validation:
    - Work name must not be empty or whitespace-only (Req 1.2, 11.1)
    - Group works cannot have price or labor_rate (Req 1.3, 11.2)
    - Parent must not create circular reference (Req 1.4, 15.3)
    """
    # Validate work name
    validate_work_name_direct(data.name)
    
    # Validate group work constraints
    validate_group_work_constraints_direct(data.is_group, data.price, data.labor_rate)
    
    # Validate parent circular reference
    validate_parent_circular_reference_direct(db, item_id, data.parent_id)
    
    cursor = db.cursor()
    cursor.execute(
        "UPDATE works SET name = ?, unit = ?, price = ?, labor_rate = ?, is_group = ?, parent_id = ? WHERE id = ?",
        (data.name, data.unit, data.price or 0.0, data.labor_rate or 0.0, data.is_group, data.parent_id, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM works WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/works/{item_id}")
async def delete_work(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark work as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE works SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Work marked as deleted"}


# Persons endpoints
@router.get("/persons")
async def list_persons(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("full_name", regex="^(full_name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of persons"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    where_clause = "marked_for_deletion = 0"
    params = []
    
    if search:
        where_clause += " AND full_name LIKE ?"
        params.append(f"%{search}%")
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM persons WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, full_name, position, parent_id, marked_for_deletion
        FROM persons
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/persons", status_code=status.HTTP_201_CREATED)
async def create_person(
    data: PersonCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new person"""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO persons (full_name, position, parent_id) VALUES (?, ?, ?)",
        (data.full_name, data.position, data.parent_id)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM persons WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/persons/{item_id}")
async def get_person(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get person by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM persons WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/persons/{item_id}")
async def update_person(
    item_id: int,
    data: PersonUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update person"""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE persons SET full_name = ?, position = ?, parent_id = ? WHERE id = ?",
        (data.full_name, data.position, data.parent_id, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM persons WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/persons/{item_id}")
async def delete_person(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark person as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE persons SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Person marked as deleted"}


# Organizations endpoints
@router.get("/organizations")
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of organizations"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    where_clause = "marked_for_deletion = 0"
    params = []
    
    if search:
        where_clause += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM organizations WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, name, parent_id, marked_for_deletion
        FROM organizations
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total)
    }


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new organization"""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO organizations (name, parent_id) VALUES (?, ?)",
        (data.name, data.parent_id)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM organizations WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/organizations/{item_id}")
async def get_organization(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get organization by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM organizations WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/organizations/{item_id}")
async def update_organization(
    item_id: int,
    data: OrganizationUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update organization"""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE organizations SET name = ?, parent_id = ? WHERE id = ?",
        (data.name, data.parent_id, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM organizations WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/organizations/{item_id}")
async def delete_organization(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark organization as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE organizations SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Organization marked as deleted"}


# ============================================================================
# Bulk Operations
# ============================================================================

from pydantic import BaseModel
from typing import List

class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete"""
    ids: List[int]

class BulkOperationResult(BaseModel):
    """Result of bulk operation"""
    success: bool
    message: str
    processed: int
    errors: List[str] = []


@router.post("/counterparties/bulk-delete")
async def bulk_delete_counterparties(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete counterparties"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for item_id in request.ids:
        try:
            cursor.execute("UPDATE counterparties SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
            processed += 1
        except Exception as e:
            errors.append(f"ID {item_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Processed {processed} of {len(request.ids)} items",
        processed=processed,
        errors=errors
    )


@router.post("/objects/bulk-delete")
async def bulk_delete_objects(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete objects"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for item_id in request.ids:
        try:
            cursor.execute("UPDATE objects SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
            processed += 1
        except Exception as e:
            errors.append(f"ID {item_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Processed {processed} of {len(request.ids)} items",
        processed=processed,
        errors=errors
    )


@router.post("/works/bulk-delete")
async def bulk_delete_works(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete works"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for item_id in request.ids:
        try:
            cursor.execute("UPDATE works SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
            processed += 1
        except Exception as e:
            errors.append(f"ID {item_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Processed {processed} of {len(request.ids)} items",
        processed=processed,
        errors=errors
    )


@router.post("/persons/bulk-delete")
async def bulk_delete_persons(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete persons"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for item_id in request.ids:
        try:
            cursor.execute("UPDATE persons SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
            processed += 1
        except Exception as e:
            errors.append(f"ID {item_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Processed {processed} of {len(request.ids)} items",
        processed=processed,
        errors=errors
    )


@router.post("/organizations/bulk-delete")
async def bulk_delete_organizations(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete organizations"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for item_id in request.ids:
        try:
            cursor.execute("UPDATE organizations SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
            processed += 1
        except Exception as e:
            errors.append(f"ID {item_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Processed {processed} of {len(request.ids)} items",
        processed=processed,
        errors=errors
    )


# ============================================================================
# User-Person Linking (Admin only)
# ============================================================================

class LinkUserPersonRequest(BaseModel):
    """Request to link user to person"""
    user_id: int
    person_id: Optional[int] = None  # None to unlink


@router.post("/persons/link-user")
async def link_user_to_person(
    request: LinkUserPersonRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Link a user to a person record (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    
    # Verify user exists
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (request.user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # If person_id provided, verify it exists
    if request.person_id:
        cursor.execute("SELECT id, full_name FROM persons WHERE id = ?", (request.person_id,))
        person = cursor.fetchone()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
        
        # Check if person is already linked to another user
        cursor.execute("SELECT id FROM persons WHERE user_id = ? AND id != ?", (request.user_id, request.person_id))
        if cursor.fetchone():
            # Unlink the old person
            cursor.execute("UPDATE persons SET user_id = NULL WHERE user_id = ?", (request.user_id,))
        
        # Link the new person
        cursor.execute("UPDATE persons SET user_id = ? WHERE id = ?", (request.user_id, request.person_id))
        db.commit()
        
        return {
            "success": True,
            "message": f"User '{user['username']}' linked to person '{person['full_name']}'"
        }
    else:
        # Unlink user from any person
        cursor.execute("UPDATE persons SET user_id = NULL WHERE user_id = ?", (request.user_id,))
        db.commit()
        
        return {
            "success": True,
            "message": f"User '{user['username']}' unlinked from person"
        }


@router.get("/persons/available-for-user/{user_id}")
async def get_persons_available_for_user(
    user_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get persons that can be linked to a user (not already linked to another user)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, full_name, position, user_id
        FROM persons
        WHERE marked_for_deletion = 0
        AND (user_id IS NULL OR user_id = ?)
        ORDER BY full_name
    """, (user_id,))
    
    persons = [dict(row) for row in cursor.fetchall()]
    
    return {"success": True, "data": persons}


# ============================================================================
# CSV Import for Works
# ============================================================================

from fastapi import UploadFile, File
from pydantic import BaseModel
import csv
import io


class ImportWorksResult(BaseModel):
    """Result of works import"""
    success: bool
    message: str
    added: int
    skipped: int
    errors: list[str]


def parse_price(price_str: str) -> float:
    """Parse price from string"""
    try:
        clean_price = ''.join(c for c in price_str if c.isdigit() or c in '.,')
        if not clean_price:
            return 0.0
        clean_price = clean_price.replace(',', '.')
        return float(clean_price)
    except (ValueError, AttributeError):
        return 0.0


def parse_unit(unit_str: str) -> str:
    """Parse unit from string"""
    if not unit_str:
        return ""
    
    # Если есть "руб./", берем то, что после слэша
    if 'руб./' in unit_str:
        unit = unit_str.split('руб./')[1].strip()
    elif 'руб/' in unit_str:
        unit = unit_str.split('руб/')[1].strip()
    else:
        # Убираем "руб." если это просто "руб."
        unit = unit_str.replace('руб.', '').strip()
    
    # Удаляем все пробелы и лишние слэши
    unit = unit.replace(' ', '').lstrip('/')
    
    if not unit or unit.lower() == 'бесплатно':
        return ""
    
    return unit


@router.post("/works/import-csv")
async def import_works_from_csv(
    file: UploadFile = File(...),
    parent_id: Optional[int] = Query(None, description="Parent work ID to import under"),
    skip_existing: bool = Query(True, description="Skip existing works"),
    delete_mode: bool = Query(False, description="Mark works for deletion instead of importing"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Import works from CSV file or mark for deletion"""
    
    # Check file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    added = 0
    skipped = 0
    errors = []
    work_groups = {}  # Cache for work groups
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=';')
        cursor = db.cursor()
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                work_type = (row.get('Тип работ') or '').strip()
                work_name = (row.get('Наименование работы') or '').strip()
                price_str = (row.get('Цена') or '0').strip()
                unit_str = (row.get('Единица измерения') or '').strip()
                
                if not work_name:
                    errors.append(f"Строка {row_num}: Пустое наименование работы")
                    continue
                
                # DELETE MODE: Mark works for deletion by name
                if delete_mode:
                    cursor.execute(
                        "UPDATE works SET marked_for_deletion = 1 WHERE name = ? AND marked_for_deletion = 0",
                        (work_name,)
                    )
                    if cursor.rowcount > 0:
                        db.commit()
                        added += cursor.rowcount
                    else:
                        skipped += 1
                    continue
                
                # IMPORT MODE: Add or update works
                # Determine parent_id
                work_parent_id = parent_id
                
                # If work_type is specified, create/get subgroup
                if work_type:
                    # Create cache key based on parent_id and work_type
                    cache_key = f"{parent_id}:{work_type}"
                    
                    if cache_key in work_groups:
                        work_parent_id = work_groups[cache_key]
                    else:
                        # Check if subgroup exists
                        cursor.execute(
                            "SELECT id FROM works WHERE name = ? AND parent_id IS ?",
                            (work_type, parent_id)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            work_parent_id = result['id']
                        else:
                            # Create new subgroup
                            cursor.execute(
                                """INSERT INTO works (name, unit, price, labor_rate, parent_id, marked_for_deletion)
                                   VALUES (?, '', 0, 0, ?, 0)""",
                                (work_type, parent_id)
                            )
                            work_parent_id = cursor.lastrowid
                            db.commit()
                        
                        work_groups[cache_key] = work_parent_id
                
                # Check if work exists
                if skip_existing:
                    cursor.execute(
                        "SELECT id FROM works WHERE name = ? AND parent_id IS ?",
                        (work_name, work_parent_id)
                    )
                    if cursor.fetchone():
                        skipped += 1
                        continue
                
                # Parse data
                price = parse_price(price_str)
                unit = parse_unit(unit_str)
                
                # Add work
                cursor.execute(
                    """INSERT INTO works (name, unit, price, labor_rate, parent_id, marked_for_deletion)
                       VALUES (?, ?, ?, 0, ?, 0)""",
                    (work_name, unit, price, work_parent_id)
                )
                db.commit()
                added += 1
            
            except Exception as e:
                errors.append(f"Строка {row_num}: {str(e)}")
                continue
    
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please use UTF-8 encoding"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import error: {str(e)}"
        )
    
    message = f"Marked for deletion: {added}" if delete_mode else f"Import completed: {added} added, {skipped} skipped"
    
    return ImportWorksResult(
        success=True,
        message=message,
        added=added,
        skipped=skipped,
        errors=errors
    )


# ============================================================================
# Bulk Move Works to Group
# ============================================================================

class MoveWorksRequest(BaseModel):
    """Request to move works to a new parent group"""
    work_ids: list[int]
    new_parent_id: Optional[int] = None


@router.post("/works/bulk-move")
async def bulk_move_works(
    request: MoveWorksRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Move multiple works to a new parent group"""
    
    cursor = db.cursor()
    processed = 0
    errors = []
    
    for work_id in request.work_ids:
        try:
            cursor.execute(
                "UPDATE works SET parent_id = ? WHERE id = ?",
                (request.new_parent_id, work_id)
            )
            processed += 1
        except Exception as e:
            errors.append(f"ID {work_id}: {str(e)}")
    
    db.commit()
    
    return BulkOperationResult(
        success=True,
        message=f"Moved {processed} of {len(request.work_ids)} works",
        processed=processed,
        errors=errors
    )


# ============================================================================
# Permanent Delete Marked Items
# ============================================================================

@router.delete("/counterparties/permanent-delete-marked")
async def permanent_delete_marked_counterparties(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Permanently delete all marked counterparties"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM counterparties WHERE marked_for_deletion = 1")
    count = cursor.fetchone()['count']
    
    if count == 0:
        return BulkOperationResult(
            success=True,
            message="No marked items to delete",
            processed=0,
            errors=[]
        )
    
    try:
        cursor.execute("DELETE FROM counterparties WHERE marked_for_deletion = 1")
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {count} marked counterparties",
            processed=count,
            errors=[]
        )
    except Exception as e:
        return BulkOperationResult(
            success=False,
            message="Error deleting marked counterparties",
            processed=0,
            errors=[str(e)]
        )


@router.delete("/objects/permanent-delete-marked")
async def permanent_delete_marked_objects(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Permanently delete all marked objects"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM objects WHERE marked_for_deletion = 1")
    count = cursor.fetchone()['count']
    
    if count == 0:
        return BulkOperationResult(
            success=True,
            message="No marked items to delete",
            processed=0,
            errors=[]
        )
    
    try:
        cursor.execute("DELETE FROM objects WHERE marked_for_deletion = 1")
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {count} marked objects",
            processed=count,
            errors=[]
        )
    except Exception as e:
        return BulkOperationResult(
            success=False,
            message="Error deleting marked objects",
            processed=0,
            errors=[str(e)]
        )


@router.delete("/works/permanent-delete-marked")
async def permanent_delete_marked_works(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Permanently delete all marked works"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM works WHERE marked_for_deletion = 1")
    count = cursor.fetchone()['count']
    
    if count == 0:
        return BulkOperationResult(
            success=True,
            message="No marked items to delete",
            processed=0,
            errors=[]
        )
    
    try:
        cursor.execute("DELETE FROM works WHERE marked_for_deletion = 1")
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {count} marked works",
            processed=count,
            errors=[]
        )
    except Exception as e:
        return BulkOperationResult(
            success=False,
            message="Error deleting marked works",
            processed=0,
            errors=[str(e)]
        )


@router.delete("/persons/permanent-delete-marked")
async def permanent_delete_marked_persons(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Permanently delete all marked persons"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM persons WHERE marked_for_deletion = 1")
    count = cursor.fetchone()['count']
    
    if count == 0:
        return BulkOperationResult(
            success=True,
            message="No marked items to delete",
            processed=0,
            errors=[]
        )
    
    try:
        cursor.execute("DELETE FROM persons WHERE marked_for_deletion = 1")
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {count} marked persons",
            processed=count,
            errors=[]
        )
    except Exception as e:
        return BulkOperationResult(
            success=False,
            message="Error deleting marked persons",
            processed=0,
            errors=[str(e)]
        )


@router.delete("/organizations/permanent-delete-marked")
async def permanent_delete_marked_organizations(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Permanently delete all marked organizations"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM organizations WHERE marked_for_deletion = 1")
    count = cursor.fetchone()['count']
    
    if count == 0:
        return BulkOperationResult(
            success=True,
            message="No marked items to delete",
            processed=0,
            errors=[]
        )
    
    try:
        cursor.execute("DELETE FROM organizations WHERE marked_for_deletion = 1")
        db.commit()
        
        return BulkOperationResult(
            success=True,
            message=f"Permanently deleted {count} marked organizations",
            processed=count,
            errors=[]
        )
    except Exception as e:
        return BulkOperationResult(
            success=False,
            message="Error deleting marked organizations",
            processed=0,
            errors=[str(e)]
        )

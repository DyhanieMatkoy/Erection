"""
Reference data endpoints - rewritten to use direct DB access
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional
import uuid
from api.models.auth import UserInfo
from api.models.references import (
    Counterparty, CounterpartyCreate, CounterpartyUpdate,
    Object, ObjectCreate, ObjectUpdate,
    Work, WorkCreate, WorkUpdate,
    Person, PersonCreate, PersonUpdate,
    Organization, OrganizationCreate, OrganizationUpdate,
    Unit, UnitCreate, UnitUpdate,
    PaginationInfo, ReferenceListResponse
)
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


def _get_work_hierarchy_path(cursor, work_id: int) -> list[str]:
    """Get hierarchy path for a work item"""
    path = []
    current_id = work_id
    
    # Prevent infinite loops
    visited = set()
    
    while current_id is not None and current_id not in visited:
        visited.add(current_id)
        cursor.execute("SELECT name, parent_id FROM works WHERE id = ?", (current_id,))
        row = cursor.fetchone()
        
        if row:
            path.insert(0, row['name'])
            current_id = row['parent_id']
        else:
            break
    
    return path


# Counterparties endpoints
@router.get("/counterparties")
async def list_counterparties(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    is_deleted: Optional[bool] = Query(None, alias="isDeleted"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of counterparties"""
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    params = []
    where_clauses = []
    
    # Handle deleted status
    if is_deleted is not None:
        where_clauses.append("marked_for_deletion = ?")
        params.append(1 if is_deleted else 0)
    else:
        # Default: show only active
        where_clauses.append("marked_for_deletion = 0")
    
    if search:
        where_clauses.append("name LIKE ?")
        params.append(f"%{search}%")
        
    where_clause = " AND ".join(where_clauses)
    
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
    
    # Generate UUID if not provided
    item_uuid = data.uuid or str(uuid.uuid4())
    
    cursor.execute(
        """
        INSERT INTO counterparties (
            name, parent_id, inn, contact_person, phone, is_group, uuid, marked_for_deletion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            data.name, 
            data.parent_id, 
            data.inn, 
            data.contact_person, 
            data.phone, 
            data.is_group,
            item_uuid
        )
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
    
    # Generate UUID if not provided
    item_uuid = data.uuid or str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO objects (name, address, owner_id, parent_id, uuid, marked_for_deletion) VALUES (?, ?, ?, ?, ?, 0)",
        (data.name, data.address, data.owner_id, data.parent_id, item_uuid)
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
    
    # Check if exists and check UUID
    cursor.execute("SELECT uuid FROM objects WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
         raise HTTPException(status_code=404, detail="Object not found")
         
    if not row['uuid']:
        new_uuid = str(uuid.uuid4())
        cursor.execute("UPDATE objects SET uuid = ? WHERE id = ?", (new_uuid, item_id))

    cursor.execute(
        "UPDATE objects SET name = ?, address = ?, owner_id = ?, parent_id = ?, modified_at = CURRENT_TIMESTAMP WHERE id = ?",
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
    page_size: int = Query(50, ge=1, le=10000),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    is_deleted: Optional[bool] = Query(None, alias="isDeleted"),
    include_unit_info: bool = Query(True),
    hierarchy_mode: str = Query("flat", regex="^(flat|tree|breadcrumb)$"),
    parent_id: Optional[int] = Query(None),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Enhanced works listing with proper unit joins and hierarchy options
    
    Args:
        hierarchy_mode: Display mode - 'flat' (all works), 'tree' (hierarchical), 'breadcrumb' (with path)
        parent_id: Filter by parent ID (None for root level in tree mode)
        include_unit_info: Include unit information from units table
    """
    offset = (page - 1) * page_size
    cursor = db.cursor()
    
    # Build query
    params = []
    where_clauses = []
    
    # Handle deleted status
    if is_deleted is not None:
        where_clauses.append("w.marked_for_deletion = ?")
        params.append(1 if is_deleted else 0)
    else:
        # Default: show only active
        where_clauses.append("w.marked_for_deletion = 0")
    
    # Handle hierarchy filtering
    if hierarchy_mode == "tree":
        if parent_id is not None:
            where_clauses.append("w.parent_id = ?")
            params.append(parent_id)
        else:
            where_clauses.append("w.parent_id IS NULL")
    
    if search:
        where_clauses.append("w.name LIKE ?")
        params.append(f"%{search}%")
        
    where_clause = " AND ".join(where_clauses)
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM works w WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Build select fields based on options
    select_fields = [
        "w.id", "w.name", "w.code", "w.price", "w.labor_rate", 
        "w.is_group", "w.parent_id", "w.marked_for_deletion", "w.uuid"
    ]
    
    if include_unit_info:
        select_fields.extend([
            "w.unit_id", 
            "COALESCE(u.name, w.unit) as unit_display",
            "u.name as unit_name",
            "u.description as unit_description"
        ])
    else:
        select_fields.append("w.unit as unit_display")
    
    # Add hierarchy path for breadcrumb mode
    if hierarchy_mode == "breadcrumb":
        # We'll build the hierarchy path in a separate query for each item
        pass
    
    # Get items
    join_clause = "LEFT JOIN units u ON w.unit_id = u.id" if include_unit_info else ""
    query = f"""
        SELECT {', '.join(select_fields)}
        FROM works w
        {join_clause}
        WHERE {where_clause}
        ORDER BY w.{sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    
    items = [dict(row) for row in cursor.fetchall()]
    
    # Add hierarchy information for breadcrumb mode
    if hierarchy_mode == "breadcrumb":
        for item in items:
            item['hierarchy_path'] = _get_work_hierarchy_path(cursor, item['id'])
            item['level'] = len(item['hierarchy_path']) - 1
    
    # Add children count for tree mode
    if hierarchy_mode == "tree":
        for item in items:
            cursor.execute(
                "SELECT COUNT(*) as count FROM works WHERE parent_id = ? AND marked_for_deletion = 0",
                (item['id'],)
            )
            item['children_count'] = cursor.fetchone()['count']
    
    return {
        "success": True,
        "data": items,
        "pagination": create_pagination_info(page, page_size, total),
        "hierarchy_mode": hierarchy_mode,
        "parent_id": parent_id
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
    - Unit_id must reference valid unit if provided (Req 1.2, 4.3)
    """
    # Validate work name
    validate_work_name_direct(data.name)
    
    # Validate group work constraints
    validate_group_work_constraints_direct(data.is_group, data.price, data.labor_rate)
    
    # Validate parent circular reference (work_id is None for new works)
    validate_parent_circular_reference_direct(db, None, data.parent_id)
    
    cursor = db.cursor()
    
    # Validate unit_id if provided
    if data.unit_id is not None:
        cursor.execute("SELECT id FROM units WHERE id = ? AND marked_for_deletion = 0", (data.unit_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Invalid unit_id: unit not found or deleted")
    
    # Generate UUID if not provided
    item_uuid = data.uuid or str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO works (name, unit, unit_id, price, labor_rate, is_group, parent_id, uuid, marked_for_deletion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (data.name, data.unit, data.unit_id, data.price or 0.0, data.labor_rate or 0.0, data.is_group, data.parent_id, item_uuid)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    
    # Return work with proper unit information
    cursor.execute("""
        SELECT w.*, 
               COALESCE(u.name, w.unit) as unit_display,
               u.name as unit_name,
               u.description as unit_description
        FROM works w
        LEFT JOIN units u ON w.unit_id = u.id
        WHERE w.id = ?
    """, (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/works/{item_id}")
async def get_work(
    item_id: int,
    include_unit_info: bool = Query(True),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get work by ID with enhanced unit information"""
    cursor = db.cursor()
    
    if include_unit_info:
        cursor.execute("""
            SELECT w.*, 
                   COALESCE(u.name, w.unit) as unit_display,
                   u.name as unit_name,
                   u.description as unit_description
            FROM works w
            LEFT JOIN units u ON w.unit_id = u.id
            WHERE w.id = ? AND w.marked_for_deletion = 0
        """, (item_id,))
    else:
        cursor.execute("""
            SELECT w.*, w.unit as unit_display
            FROM works w
            WHERE w.id = ? AND w.marked_for_deletion = 0
        """, (item_id,))
    
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Work not found")
    
    work_data = dict(row)
    
    # Add hierarchy information
    work_data['hierarchy_path'] = _get_work_hierarchy_path(cursor, item_id)
    work_data['level'] = len(work_data['hierarchy_path']) - 1
    
    # Add children count
    cursor.execute(
        "SELECT COUNT(*) as count FROM works WHERE parent_id = ? AND marked_for_deletion = 0",
        (item_id,)
    )
    work_data['children_count'] = cursor.fetchone()['count']
    
    return {"success": True, "data": work_data}


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
    - Unit_id must reference valid unit if provided (Req 1.2, 4.3)
    """
    # Validate work name
    validate_work_name_direct(data.name)
    
    # Validate group work constraints
    validate_group_work_constraints_direct(data.is_group, data.price, data.labor_rate)
    
    # Validate parent circular reference
    validate_parent_circular_reference_direct(db, item_id, data.parent_id)
    
    cursor = db.cursor()
    
    # Check if exists and check UUID
    cursor.execute("SELECT uuid FROM works WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
         raise HTTPException(status_code=404, detail="Work not found")
         
    if not row['uuid']:
        new_uuid = str(uuid.uuid4())
        cursor.execute("UPDATE works SET uuid = ? WHERE id = ?", (new_uuid, item_id))
    
    # Validate unit_id if provided
    if data.unit_id is not None:
        cursor.execute("SELECT id FROM units WHERE id = ? AND marked_for_deletion = 0", (data.unit_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Invalid unit_id: unit not found or deleted")
        
    cursor.execute(
        "UPDATE works SET name = ?, unit = ?, unit_id = ?, price = ?, labor_rate = ?, is_group = ?, parent_id = ?, modified_at = CURRENT_TIMESTAMP WHERE id = ?",
        (data.name, data.unit, data.unit_id, data.price or 0.0, data.labor_rate or 0.0, data.is_group, data.parent_id, item_id)
    )
    db.commit()
    
    # Return work with proper unit information
    cursor.execute("""
        SELECT w.*, 
               COALESCE(u.name, w.unit) as unit_display,
               u.name as unit_name,
               u.description as unit_description
        FROM works w
        LEFT JOIN units u ON w.unit_id = u.id
        WHERE w.id = ?
    """, (item_id,))
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


# ============================================================================
# Work Unit Migration Control Endpoints
# ============================================================================

from pydantic import BaseModel
from typing import Dict, Any


class MigrationStatusResponse(BaseModel):
    """Migration status response"""
    success: bool
    data: Dict[str, Any]


class StartMigrationRequest(BaseModel):
    """Request to start migration"""
    auto_apply_threshold: float = 0.8
    batch_size: int = 100


class ManualReviewRequest(BaseModel):
    """Request for manual review override"""
    work_id: int
    unit_id: Optional[int] = None
    action: str  # 'approve', 'reject', 'assign'


@router.get("/works/migration-status")
async def get_migration_status(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get status of unit migration process
    
    Note: Migration is complete - legacy unit column has been removed.
    All works now use unit_id foreign key relationships.
    """
    cursor = db.cursor()
    
    # Get migration statistics
    cursor.execute("""
        SELECT 
            migration_status,
            COUNT(*) as count
        FROM work_unit_migration 
        GROUP BY migration_status
    """)
    status_counts = {row['migration_status']: row['count'] for row in cursor.fetchall()}
    
    # Get total works with legacy units
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM works 
        WHERE unit IS NOT NULL 
        AND unit != '' 
        AND unit_id IS NULL 
        AND marked_for_deletion = 0
    """)
    total_legacy_works = cursor.fetchone()['count']
    
    # Get total migration entries
    cursor.execute("SELECT COUNT(*) as count FROM work_unit_migration")
    total_entries = cursor.fetchone()['count']
    
    # Calculate completion percentage
    completed = status_counts.get('completed', 0)
    completion_percentage = (completed / total_legacy_works * 100) if total_legacy_works > 0 else 0
    
    return MigrationStatusResponse(
        success=True,
        data={
            'total_works': total_legacy_works,
            'migrated_count': completed,
            'pending_count': status_counts.get('pending', 0),
            'manual_review_count': status_counts.get('manual', 0),
            'matched_count': status_counts.get('matched', 0),
            'completion_percentage': round(completion_percentage, 2),
            'total_entries': total_entries,
            'status_breakdown': status_counts
        }
    )


@router.post("/works/migrate-units")
async def start_unit_migration(
    request: StartMigrationRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Start or continue unit migration process"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    try:
        # Import migration service
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from src.services.migration_workflow_service import MigrationWorkflowService
        from src.data.database_manager import DatabaseManager
        
        # Initialize services
        db_manager = DatabaseManager()
        migration_service = MigrationWorkflowService(db_manager)
        
        # Start migration
        result = migration_service.start_migration_process(
            auto_apply_threshold=request.auto_apply_threshold,
            batch_size=request.batch_size
        )
        
        return {
            "success": True,
            "message": "Migration process started",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/works/migration-pending")
async def get_pending_migrations(
    limit: int = Query(50, ge=1, le=1000),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get works requiring manual review"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            m.work_id,
            m.legacy_unit,
            m.matched_unit_id,
            m.confidence_score,
            m.manual_review_reason,
            m.migration_status,
            w.name as work_name,
            u.name as matched_unit_name
        FROM work_unit_migration m
        JOIN works w ON m.work_id = w.id
        LEFT JOIN units u ON m.matched_unit_id = u.id
        WHERE m.migration_status IN ('pending', 'manual')
        ORDER BY m.confidence_score DESC, m.created_at
        LIMIT ?
    """, (limit,))
    
    items = [dict(row) for row in cursor.fetchall()]
    
    return {
        "success": True,
        "data": items
    }


@router.post("/works/migration-review")
async def manual_migration_review(
    request: ManualReviewRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Handle manual review of migration entries"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    cursor = db.cursor()
    
    # Get migration entry
    cursor.execute("""
        SELECT * FROM work_unit_migration WHERE work_id = ?
    """, (request.work_id,))
    migration_entry = cursor.fetchone()
    
    if not migration_entry:
        raise HTTPException(status_code=404, detail="Migration entry not found")
    
    try:
        if request.action == 'approve':
            # Approve the suggested match
            if migration_entry['matched_unit_id']:
                cursor.execute("""
                    UPDATE works SET unit_id = ? WHERE id = ?
                """, (migration_entry['matched_unit_id'], request.work_id))
                
                cursor.execute("""
                    UPDATE work_unit_migration 
                    SET migration_status = 'completed' 
                    WHERE work_id = ?
                """, (request.work_id,))
            else:
                raise HTTPException(status_code=400, detail="No unit match to approve")
                
        elif request.action == 'assign':
            # Manually assign a unit
            if not request.unit_id:
                raise HTTPException(status_code=400, detail="unit_id required for assign action")
            
            # Verify unit exists
            cursor.execute("SELECT id FROM units WHERE id = ? AND marked_for_deletion = 0", (request.unit_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Unit not found")
            
            cursor.execute("""
                UPDATE works SET unit_id = ? WHERE id = ?
            """, (request.unit_id, request.work_id))
            
            cursor.execute("""
                UPDATE work_unit_migration 
                SET migration_status = 'completed', matched_unit_id = ? 
                WHERE work_id = ?
            """, (request.unit_id, request.work_id))
            
        elif request.action == 'reject':
            # Reject the migration - keep legacy unit
            cursor.execute("""
                UPDATE work_unit_migration 
                SET migration_status = 'rejected' 
                WHERE work_id = ?
            """, (request.work_id,))
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Migration {request.action} completed for work {request.work_id}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review action failed: {str(e)}"
        )


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
    
    # Generate UUID if not provided
    item_uuid = data.uuid or str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO persons (full_name, position, parent_id, uuid, marked_for_deletion) VALUES (?, ?, ?, ?, 0)",
        (data.full_name, data.position, data.parent_id, item_uuid)
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
    
    # Check if exists and check UUID
    cursor.execute("SELECT uuid FROM persons WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
         raise HTTPException(status_code=404, detail="Person not found")
         
    if not row['uuid']:
        new_uuid = str(uuid.uuid4())
        cursor.execute("UPDATE persons SET uuid = ? WHERE id = ?", (new_uuid, item_id))
        
    cursor.execute(
        "UPDATE persons SET full_name = ?, position = ?, parent_id = ?, modified_at = CURRENT_TIMESTAMP WHERE id = ?",
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


# Units endpoints
@router.get("/units")
async def list_units(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    is_deleted: Optional[bool] = Query(None, alias="isDeleted"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of units"""
    offset = (page - 1) * page_size
    
    # Build WHERE clause
    params = []
    where_clauses = []
    
    # Handle deleted status
    if is_deleted is not None:
        where_clauses.append("marked_for_deletion = ?")
        params.append(1 if is_deleted else 0)
    else:
        # Default: show only active
        where_clauses.append("marked_for_deletion = 0")
    
    if search:
        where_clauses.append("name LIKE ?")
        params.append(f"%{search}%")
        
    where_clause = " AND ".join(where_clauses)
    
    # Get total count
    cursor = db.cursor()
    cursor.execute(f"SELECT COUNT(*) as count FROM units WHERE {where_clause}", params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT id, name, description, marked_for_deletion, created_at, modified_at
        FROM units
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


@router.post("/units", status_code=status.HTTP_201_CREATED)
async def create_unit(
    data: UnitCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new unit"""
    cursor = db.cursor()
    
    # Generate UUID if not provided
    item_uuid = data.uuid or str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO units (name, description, marked_for_deletion, uuid) VALUES (?, ?, ?, ?)",
        (data.name, data.description, data.marked_for_deletion, item_uuid)
    )
    db.commit()
    
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM units WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.get("/units/{item_id}")
async def get_unit(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get unit by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM units WHERE id = ? AND marked_for_deletion = 0", (item_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return {"success": True, "data": dict(row)}


@router.put("/units/{item_id}")
async def update_unit(
    item_id: int,
    data: UnitUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update unit"""
    cursor = db.cursor()
    
    # Check if exists and check UUID
    cursor.execute("SELECT uuid FROM units WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
         raise HTTPException(status_code=404, detail="Unit not found")
         
    if not row['uuid']:
        new_uuid = str(uuid.uuid4())
        cursor.execute("UPDATE units SET uuid = ? WHERE id = ?", (new_uuid, item_id))
        
    cursor.execute(
        "UPDATE units SET name = ?, description = ?, marked_for_deletion = ?, modified_at = CURRENT_TIMESTAMP WHERE id = ?",
        (data.name, data.description, data.marked_for_deletion, item_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM units WHERE id = ?", (item_id,))
    item = dict(cursor.fetchone())
    
    return {"success": True, "data": item}


@router.delete("/units/{item_id}")
async def delete_unit(
    item_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark unit as deleted"""
    cursor = db.cursor()
    cursor.execute("UPDATE units SET marked_for_deletion = 1 WHERE id = ?", (item_id,))
    db.commit()
    
    return {"success": True, "message": "Unit marked as deleted"}


# ============================================================================
# Bulk Operations
# ============================================================================

from api.models.bulk_operations import BulkDeleteRequest, BulkOperationResult
from api.services.bulk_operation_service import bulk_operation_service
from api.services.bulk_handlers import register_default_handlers

# Register handlers on module import
register_default_handlers()

@router.post("/counterparties/bulk-delete")
async def bulk_delete_counterparties(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete counterparties"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    return await bulk_operation_service.execute_operation(
        'counterparties:delete',
        request.ids,
        {'db': db}
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
    
    return await bulk_operation_service.execute_operation(
        'objects:delete',
        request.ids,
        {'db': db}
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
    
    return await bulk_operation_service.execute_operation(
        'works:delete',
        request.ids,
        {'db': db}
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
    
    return await bulk_operation_service.execute_operation(
        'persons:delete',
        request.ids,
        {'db': db}
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
    
    return await bulk_operation_service.execute_operation(
        'organizations:delete',
        request.ids,
        {'db': db}
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

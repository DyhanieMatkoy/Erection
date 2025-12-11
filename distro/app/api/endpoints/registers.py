"""
Register endpoints for work execution and other registers
"""
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import date
import math

from api.models.auth import UserInfo
from api.models.references import PaginationInfo
from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db_connection
from api.config import settings
from src.data.repositories.work_execution_register_repository import (
    WorkExecutionRegisterRepository,
)


router = APIRouter(prefix="/registers", tags=["Registers"])


def create_pagination_info(
    page: int, page_size: int, total_items: int
) -> PaginationInfo:
    """Create pagination info"""
    total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
    return PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


@router.get("/work-execution")
async def get_work_execution_register(
    period_from: Optional[date] = None,
    period_to: Optional[date] = None,
    object_id: Optional[int] = None,
    estimate_id: Optional[int] = None,
    work_id: Optional[int] = None,
    group_by: Optional[str] = Query(None, regex="^(object|estimate|work|period)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db_connection),
):
    """
    Get work execution register with filtering and grouping

    Returns movements with joined fields (object_name, estimate_number, work_name)
    and calculated balances (income - expense)
    """
    repo = WorkExecutionRegisterRepository()

    # Build filters
    filters = {}
    if period_to:
        filters["period_end"] = period_to.isoformat()
    if object_id:
        filters["object_id"] = object_id
    if estimate_id:
        filters["estimate_id"] = estimate_id
    if work_id:
        filters["work_id"] = work_id

    # Build grouping
    grouping = []
    if group_by:
        grouping = [group_by]
    else:
        # Default grouping
        grouping = ["estimate", "work"]

    # Get data
    if period_from and period_to:
        # Get turnovers for period
        data = repo.get_turnovers(
            period_from.isoformat(), period_to.isoformat(), filters, grouping
        )
    else:
        # Get balance
        data = repo.get_balance(filters, grouping)

    # Apply pagination
    total = len(data)
    offset = (page - 1) * page_size
    paginated_data = data[offset : offset + page_size]

    return {
        "success": True,
        "data": paginated_data,
        "pagination": create_pagination_info(page, page_size, total),
    }


@router.get("/work-execution/movements")
async def get_work_execution_movements(
    period_from: date,
    period_to: date,
    object_id: Optional[int] = None,
    estimate_id: Optional[int] = None,
    work_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db_connection),
):
    """
    Get detailed work execution movements (all records) with filtering

    Returns individual movement records with joined fields
    """
    cursor = db.cursor()

    # Build WHERE clause
    where_clauses = ["r.period >= ?", "r.period <= ?"]
    params = [period_from.isoformat(), period_to.isoformat()]

    if object_id:
        where_clauses.append("r.object_id = ?")
        params.append(object_id)

    if estimate_id:
        where_clauses.append("r.estimate_id = ?")
        params.append(estimate_id)

    if work_id:
        where_clauses.append("r.work_id = ?")
        params.append(work_id)

    where_sql = " AND ".join(where_clauses)

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as count
        FROM work_execution_register r
        WHERE {where_sql}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()["count"]

    # Get movements with pagination
    offset = (page - 1) * page_size
    query = f"""
        SELECT 
            r.*,
            o.name as object_name,
            e.number as estimate_number,
            w.name as work_name
        FROM work_execution_register r
        LEFT JOIN objects o ON r.object_id = o.id
        LEFT JOIN estimates e ON r.estimate_id = e.id
        LEFT JOIN works w ON r.work_id = w.id
        WHERE {where_sql}
        ORDER BY r.period, r.recorder_type, r.recorder_id, r.line_number
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)

    movements = [dict(row) for row in cursor.fetchall()]

    return {
        "success": True,
        "data": movements,
        "pagination": create_pagination_info(page, page_size, total),
    }

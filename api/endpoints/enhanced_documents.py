"""
Enhanced document endpoints with improved pagination, sorting, and filtering
Implements Task 5: API pagination and sorting endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import date

from api.models.documents import (
    Estimate, EstimateCreate, EstimateUpdate,
    DailyReport, DailyReportCreate, DailyReportUpdate
)
from api.models.auth import UserInfo
from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db_connection
from api.services.pagination_service import PaginationService, PaginationConfig
from api.services.sorting_service import SortingService
from api.services.date_filter_service import DateFilterService


router = APIRouter(prefix="/enhanced-documents", tags=["Enhanced Documents"])

# Initialize services
pagination_config = PaginationConfig(default_page_size=50, max_page_size=1000, min_page_size=1)
pagination_service = PaginationService(pagination_config)
sorting_service = SortingService()
date_filter_service = DateFilterService()


@router.get("/estimates")
async def list_estimates_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in number, customer, or object name"),
    object_id: Optional[int] = Query(None, description="Filter by object ID"),
    responsible_id: Optional[int] = Query(None, description="Filter by responsible person ID"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    estimate_type: Optional[str] = Query(None, regex="^(General|Plan)$", description="Filter by estimate type"),
    base_document_id: Optional[int] = Query(None, description="Filter by base document ID"),
    sort_by: str = Query("date", description="Sort column"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort direction"),
    use_default_date_filter: bool = Query(True, description="Use intelligent default date filter"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get list of estimates with enhanced pagination, sorting, and filtering
    
    Features:
    - Intelligent default date filtering based on most recent document
    - Configurable pagination with metadata
    - Column sorting with validation
    - Advanced search and filtering options
    """
    
    # Handle date filtering
    if use_default_date_filter and not date_from and not date_to:
        # Use intelligent default date range
        default_range = date_filter_service.get_default_date_range(db, 'estimates')
        date_from = default_range.start_date
        date_to = default_range.end_date
        applied_range = default_range
    else:
        # Use user-specified dates
        applied_range = date_filter_service.DateRange(date_from, date_to, is_default=False)
        default_range = date_filter_service.get_default_date_range(db, 'estimates')
    
    # Validate sort parameters
    is_valid_sort, sort_config, sort_error = sorting_service.validate_sort_params('estimates', sort_by, sort_order)
    if not is_valid_sort:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort parameters: {sort_error}"
        )
    
    # Build base query
    base_query = """
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            org.name as contractor_name,
            p.full_name as responsible_name,
            base.number as base_document_number,
            base.number as base_document_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN organizations org ON e.contractor_id = org.id
        LEFT JOIN persons p ON e.responsible_id = p.id
        LEFT JOIN estimates base ON e.base_document_id = base.id
    """
    
    # Build WHERE clauses and parameters
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    # Apply search filter
    if search:
        where_clauses.append("(e.number LIKE ? OR c.name LIKE ? OR o.name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    # Apply specific filters
    if estimate_type:
        where_clauses.append("e.estimate_type = ?")
        params.append(estimate_type)
        
    if base_document_id:
        where_clauses.append("e.base_document_id = ?")
        params.append(base_document_id)
    
    if object_id:
        where_clauses.append("e.object_id = ?")
        params.append(object_id)
    
    if responsible_id:
        where_clauses.append("e.responsible_id = ?")
        params.append(responsible_id)
    
    # Apply date filter
    base_query, where_clauses, params, date_error = date_filter_service.apply_date_filter_to_query(
        base_query, 'estimates', date_from, date_to, where_clauses, params
    )
    
    if date_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date filter: {date_error}"
        )
    
    # Build complete query with WHERE clause
    where_sql = " AND ".join(where_clauses)
    complete_query = f"{base_query} WHERE {where_sql}"
    
    # Apply sorting
    sorted_query, sort_error = sorting_service.apply_sorting_to_query(
        complete_query, 'estimates', sort_by, sort_order
    )
    
    if sort_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sorting error: {sort_error}"
        )
    
    # Execute paginated query
    try:
        result = pagination_service.paginate_query_result(
            db, sorted_query, params, page, page_size
        )
        
        # Create response with enhanced metadata
        response = {
            "success": True,
            "data": result.items,
            "pagination": pagination_service.create_pagination_info_dict(result),
            "sorting": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "available_columns": sorting_service.get_sortable_columns('estimates')
            },
            "filtering": {
                "search": search,
                "filters_applied": {
                    "object_id": object_id,
                    "responsible_id": responsible_id,
                    "estimate_type": estimate_type,
                    "base_document_id": base_document_id
                },
                "date_filter": date_filter_service.create_date_filter_info(applied_range, default_range)
            }
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve estimates: {str(e)}"
        )


@router.get("/daily-reports")
async def list_daily_reports_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in estimate number or foreman name"),
    estimate_id: Optional[int] = Query(None, description="Filter by estimate ID"),
    foreman_id: Optional[int] = Query(None, description="Filter by foreman ID"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    sort_by: str = Query("date", description="Sort column"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort direction"),
    use_default_date_filter: bool = Query(True, description="Use intelligent default date filter"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get list of daily reports with enhanced pagination, sorting, and filtering
    """
    
    # Handle date filtering
    if use_default_date_filter and not date_from and not date_to:
        default_range = date_filter_service.get_default_date_range(db, 'daily_reports')
        date_from = default_range.start_date
        date_to = default_range.end_date
        applied_range = default_range
    else:
        applied_range = date_filter_service.DateRange(date_from, date_to, is_default=False)
        default_range = date_filter_service.get_default_date_range(db, 'daily_reports')
    
    # Validate sort parameters
    is_valid_sort, sort_config, sort_error = sorting_service.validate_sort_params('daily_reports', sort_by, sort_order)
    if not is_valid_sort:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort parameters: {sort_error}"
        )
    
    # Build base query
    base_query = """
        SELECT 
            dr.*,
            e.number as estimate_number,
            p.full_name as foreman_name
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        LEFT JOIN persons p ON dr.foreman_id = p.id
    """
    
    # Build WHERE clauses and parameters
    where_clauses = ["dr.marked_for_deletion = 0"]
    params = []
    
    # Apply search filter
    if search:
        where_clauses.append("(e.number LIKE ? OR p.full_name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # Apply specific filters
    if estimate_id:
        where_clauses.append("dr.estimate_id = ?")
        params.append(estimate_id)
    
    if foreman_id:
        where_clauses.append("dr.foreman_id = ?")
        params.append(foreman_id)
    
    # Apply date filter
    base_query, where_clauses, params, date_error = date_filter_service.apply_date_filter_to_query(
        base_query, 'daily_reports', date_from, date_to, where_clauses, params
    )
    
    if date_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date filter: {date_error}"
        )
    
    # Build complete query with WHERE clause
    where_sql = " AND ".join(where_clauses)
    complete_query = f"{base_query} WHERE {where_sql}"
    
    # Apply sorting
    sorted_query, sort_error = sorting_service.apply_sorting_to_query(
        complete_query, 'daily_reports', sort_by, sort_order
    )
    
    if sort_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sorting error: {sort_error}"
        )
    
    # Execute paginated query
    try:
        result = pagination_service.paginate_query_result(
            db, sorted_query, params, page, page_size
        )
        
        # Create response with enhanced metadata
        response = {
            "success": True,
            "data": result.items,
            "pagination": pagination_service.create_pagination_info_dict(result),
            "sorting": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "available_columns": sorting_service.get_sortable_columns('daily_reports')
            },
            "filtering": {
                "search": search,
                "filters_applied": {
                    "estimate_id": estimate_id,
                    "foreman_id": foreman_id
                },
                "date_filter": date_filter_service.create_date_filter_info(applied_range, default_range)
            }
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily reports: {str(e)}"
        )


@router.get("/sorting-info/{table_name}")
async def get_sorting_info(
    table_name: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """Get available sorting columns and default sort for a table"""
    
    if table_name not in ['estimates', 'daily_reports', 'timesheets']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sorting info not available for table: {table_name}"
        )
    
    sortable_columns = sorting_service.get_sortable_columns(table_name)
    default_sort_by, default_sort_order = sorting_service.get_default_sort(table_name)
    
    return {
        "success": True,
        "data": {
            "table_name": table_name,
            "sortable_columns": sortable_columns,
            "default_sort": {
                "sort_by": default_sort_by,
                "sort_order": default_sort_order
            }
        }
    }


@router.get("/pagination-config")
async def get_pagination_config(
    current_user: UserInfo = Depends(get_current_user)
):
    """Get current pagination configuration"""
    
    return {
        "success": True,
        "data": {
            "default_page_size": pagination_config.default_page_size,
            "max_page_size": pagination_config.max_page_size,
            "min_page_size": pagination_config.min_page_size
        }
    }


@router.get("/date-filter-defaults/{table_name}")
async def get_date_filter_defaults(
    table_name: str,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get intelligent default date range for a table"""
    
    if table_name not in ['estimates', 'daily_reports', 'timesheets']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Date filter defaults not available for table: {table_name}"
        )
    
    try:
        default_range = date_filter_service.get_default_date_range(db, table_name)
        
        return {
            "success": True,
            "data": {
                "table_name": table_name,
                "default_range": {
                    "start_date": default_range.start_date.isoformat() if default_range.start_date else None,
                    "end_date": default_range.end_date.isoformat() if default_range.end_date else None,
                    "is_default": default_range.is_default,
                    "summary": date_filter_service.get_date_range_summary(default_range)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get date filter defaults: {str(e)}"
        )
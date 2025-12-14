"""
Document endpoints for estimates and daily reports
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from typing import List, Optional
from datetime import date
import math
import tempfile
import os as os_module

from api.models.documents import (
    Estimate, EstimateCreate, EstimateUpdate,
    EstimateLine, EstimateLineCreate,
    DailyReport, DailyReportCreate, DailyReportUpdate,
    DailyReportLine, DailyReportLineCreate
)
from api.models.auth import UserInfo
from api.models.references import PaginationInfo
from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db_connection
from api.config import settings


router = APIRouter(prefix="/documents", tags=["Documents"])


def create_pagination_info(page: int, page_size: int, total_items: int) -> PaginationInfo:
    """Create pagination info"""
    total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
    return PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages
    )


def calculate_totals(lines: List[EstimateLineCreate]) -> tuple[float, float]:
    """Calculate total sum and labor from estimate lines"""
    total_sum = 0.0
    total_labor = 0.0
    
    for line in lines:
        if not line.is_group:  # Only count non-group lines
            total_sum += line.sum
            total_labor += line.planned_labor
    
    return total_sum, total_labor


def get_estimate_with_joins(db, estimate_id: int) -> Optional[dict]:
    """Get estimate with joined reference names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            org.name as contractor_name,
            p.full_name as responsible_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN organizations org ON e.contractor_id = org.id
        LEFT JOIN persons p ON e.responsible_id = p.id
        WHERE e.id = ?
    """, (estimate_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return dict(row)


def get_estimate_lines_with_joins(db, estimate_id: int) -> List[dict]:
    """Get estimate lines with joined work names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            el.*,
            w.name as work_name
        FROM estimate_lines el
        LEFT JOIN works w ON el.work_id = w.id
        WHERE el.estimate_id = ?
        ORDER BY el.line_number
    """, (estimate_id,))
    
    return [dict(row) for row in cursor.fetchall()]


# Estimate endpoints
@router.get("/estimates")
async def list_estimates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    object_id: Optional[int] = None,
    responsible_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("date", regex="^(date|number|id)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of estimates with pagination and filtering"""
    offset = (page - 1) * page_size
    
    # Build query
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    if search:
        where_clauses.append("(e.number LIKE ? OR c.name LIKE ? OR o.name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    if object_id:
        where_clauses.append("e.object_id = ?")
        params.append(object_id)
    
    if responsible_id:
        where_clauses.append("e.responsible_id = ?")
        params.append(responsible_id)
    
    if date_from:
        where_clauses.append("e.date >= ?")
        params.append(date_from.isoformat())
    
    if date_to:
        where_clauses.append("e.date <= ?")
        params.append(date_to.isoformat())
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    cursor = db.cursor()
    count_query = f"""
        SELECT COUNT(*) as count
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        WHERE {where_sql}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            org.name as contractor_name,
            p.full_name as responsible_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN organizations org ON e.contractor_id = org.id
        LEFT JOIN persons p ON e.responsible_id = p.id
        WHERE {where_sql}
        ORDER BY e.{sort_by} {sort_order.upper()}
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


@router.post("/estimates/import-excel", status_code=status.HTTP_201_CREATED)
async def import_estimate_from_excel(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Import estimate from Excel file"""
    # Check file extension
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате Excel (.xlsx или .xls)"
        )
    
    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Import estimate using service
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.services.excel_import_service import ExcelImportService
        
        import_service = ExcelImportService()
        estimate, error = import_service.import_estimate(tmp_file_path)
        
        # Clean up temp file
        os_module.unlink(tmp_file_path)
        
        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Не удалось импортировать смету"
            )
        
        # Save estimate to database
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO estimates (
                number, date, customer_id, object_id, contractor_id, 
                responsible_id, total_sum, total_labor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            estimate.number, estimate.date.isoformat(), estimate.customer_id, estimate.object_id,
            estimate.contractor_id, estimate.responsible_id, estimate.total_sum, estimate.total_labor
        ))
        
        estimate_id = cursor.lastrowid
        
        # Insert lines
        for line in estimate.lines:
            cursor.execute("""
                INSERT INTO estimate_lines (
                    estimate_id, line_number, work_id, quantity, unit, price,
                    labor_rate, sum, planned_labor, is_group, group_name,
                    parent_group_id, is_collapsed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                estimate_id, line.line_number, line.work_id, line.quantity,
                line.unit, line.price, line.labor_rate, line.sum, line.planned_labor,
                1 if line.is_group else 0, line.group_name, line.parent_group_id,
                1 if line.is_collapsed else 0
            ))
        
        db.commit()
        
        # Get created estimate with joins
        estimate_data = get_estimate_with_joins(db, estimate_id)
        estimate_data['lines'] = get_estimate_lines_with_joins(db, estimate_id)
        
        return {"success": True, "data": estimate_data, "message": "Смета успешно импортирована"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os_module.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при импорте: {str(e)}"
        )


@router.post("/daily-reports/import-excel", status_code=status.HTTP_201_CREATED)
async def import_daily_report_from_excel(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Import daily report from Excel file"""
    # Check file extension
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате Excel (.xlsx или .xls)"
        )
    
    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Import daily report using service
        from src.services.excel_daily_report_import_service import ExcelDailyReportImportService
        
        import_service = ExcelDailyReportImportService()
        daily_report, error = import_service.import_daily_report(tmp_file_path)
        
        # Clean up temp file
        os_module.unlink(tmp_file_path)
        
        if not daily_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Не удалось импортировать ежедневный отчет"
            )
        
        # Generate number if not set
        if not daily_report.number:
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM daily_reports WHERE date = ?", (daily_report.date.isoformat(),))
            count = cursor.fetchone()['count']
            daily_report.number = f"ЕО-{daily_report.date.strftime('%Y%m%d')}-{count + 1:03d}"
        
        # Save daily report to database
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO daily_reports (
                number, date, estimate_id, foreman_id
            )
            VALUES (?, ?, ?, ?)
        """, (
            daily_report.number, daily_report.date.isoformat(), 
            daily_report.estimate_id, daily_report.foreman_id
        ))
        
        report_id = cursor.lastrowid
        
        # Insert lines
        for line in daily_report.lines:
            cursor.execute("""
                INSERT INTO daily_report_lines (
                    daily_report_id, line_number, work_id, planned_labor, actual_labor, deviation_percent
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id, line.line_number, line.work_id, 
                line.planned_labor, line.actual_labor, line.deviation_percent
            ))
        
        db.commit()
        
        # Get created daily report with joins
        cursor.execute("""
            SELECT 
                dr.id, dr.number, dr.date, dr.estimate_id, dr.foreman_id, dr.is_posted,
                e.number as estimate_number,
                p.full_name as foreman_name
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            LEFT JOIN persons p ON dr.foreman_id = p.id
            WHERE dr.id = ?
        """, (report_id,))
        
        report_data = cursor.fetchone()
        if report_data:
            report_dict = dict(report_data)
            
            # Get lines
            cursor.execute("""
                SELECT 
                    drl.id, drl.line_number, drl.work_id, drl.planned_labor, 
                    drl.actual_labor, drl.deviation_percent,
                    w.name as work_name, w.code as work_code
                FROM daily_report_lines drl
                LEFT JOIN works w ON drl.work_id = w.id
                WHERE drl.daily_report_id = ?
                ORDER BY drl.line_number
            """, (report_id,))
            
            report_dict['lines'] = [dict(row) for row in cursor.fetchall()]
        
        return {"success": True, "data": report_dict, "message": "Ежедневный отчет успешно импортирован"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os_module.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при импорте: {str(e)}"
        )


@router.post("/estimates", status_code=status.HTTP_201_CREATED)
async def create_estimate(
    data: EstimateCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new estimate with lines"""
    cursor = db.cursor()
    
    try:
        # Calculate totals
        total_sum, total_labor = calculate_totals(data.lines)
        
        # Insert estimate
        cursor.execute("""
            INSERT INTO estimates (
                number, date, customer_id, object_id, contractor_id, 
                responsible_id, total_sum, total_labor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.number, data.date.isoformat(), data.customer_id, data.object_id,
            data.contractor_id, data.responsible_id, total_sum, total_labor
        ))
        
        estimate_id = cursor.lastrowid
        
        # Insert lines
        for line in data.lines:
            cursor.execute("""
                INSERT INTO estimate_lines (
                    estimate_id, line_number, work_id, quantity, unit, price,
                    labor_rate, sum, planned_labor, is_group, group_name,
                    parent_group_id, is_collapsed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                estimate_id, line.line_number, line.work_id, line.quantity,
                line.unit, line.price, line.labor_rate, line.sum, line.planned_labor,
                1 if line.is_group else 0, line.group_name, line.parent_group_id,
                1 if line.is_collapsed else 0
            ))
        
        db.commit()
        
        # Get created estimate with joins
        estimate = get_estimate_with_joins(db, estimate_id)
        estimate['lines'] = get_estimate_lines_with_joins(db, estimate_id)
        
        return {"success": True, "data": estimate}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create estimate: {str(e)}"
        )


@router.get("/estimates/{estimate_id}")
async def get_estimate(
    estimate_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get estimate by ID with lines and joined fields"""
    estimate = get_estimate_with_joins(db, estimate_id)
    
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get('marked_for_deletion'):
        raise HTTPException(status_code=404, detail="Estimate is marked for deletion")
    
    # Get lines
    estimate['lines'] = get_estimate_lines_with_joins(db, estimate_id)
    
    return {"success": True, "data": estimate}


@router.put("/estimates/{estimate_id}")
async def update_estimate(
    estimate_id: int,
    data: EstimateUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update estimate"""
    cursor = db.cursor()
    
    # Check if estimate exists
    cursor.execute("SELECT id FROM estimates WHERE id = ? AND marked_for_deletion = 0", (estimate_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    try:
        # Calculate totals if lines provided
        if data.lines is not None:
            total_sum, total_labor = calculate_totals(data.lines)
        else:
            # Keep existing totals
            cursor.execute("SELECT total_sum, total_labor FROM estimates WHERE id = ?", (estimate_id,))
            row = cursor.fetchone()
            total_sum, total_labor = row['total_sum'], row['total_labor']
        
        # Update estimate
        cursor.execute("""
            UPDATE estimates
            SET number = ?, date = ?, customer_id = ?, object_id = ?,
                contractor_id = ?, responsible_id = ?, total_sum = ?, total_labor = ?,
                modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.number, data.date.isoformat(), data.customer_id, data.object_id,
            data.contractor_id, data.responsible_id, total_sum, total_labor,
            estimate_id
        ))
        
        # Update lines if provided
        if data.lines is not None:
            # Delete existing lines
            cursor.execute("DELETE FROM estimate_lines WHERE estimate_id = ?", (estimate_id,))
            
            # Insert new lines
            for line in data.lines:
                cursor.execute("""
                    INSERT INTO estimate_lines (
                        estimate_id, line_number, work_id, quantity, unit, price,
                        labor_rate, sum, planned_labor, is_group, group_name,
                        parent_group_id, is_collapsed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    estimate_id, line.line_number, line.work_id, line.quantity,
                    line.unit, line.price, line.labor_rate, line.sum, line.planned_labor,
                    1 if line.is_group else 0, line.group_name, line.parent_group_id,
                    1 if line.is_collapsed else 0
                ))
        
        db.commit()
        
        # Get updated estimate with joins
        estimate = get_estimate_with_joins(db, estimate_id)
        estimate['lines'] = get_estimate_lines_with_joins(db, estimate_id)
        
        return {"success": True, "data": estimate}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update estimate: {str(e)}"
        )


@router.delete("/estimates/{estimate_id}")
async def delete_estimate(
    estimate_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark estimate as deleted"""
    cursor = db.cursor()
    
    # Check if estimate exists
    cursor.execute("SELECT id FROM estimates WHERE id = ? AND marked_for_deletion = 0", (estimate_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    try:
        cursor.execute("""
            UPDATE estimates
            SET marked_for_deletion = 1, modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (estimate_id,))
        
        db.commit()
        
        return {"success": True, "message": "Estimate marked as deleted"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete estimate: {str(e)}"
        )


# Daily Report helper functions
def get_daily_report_with_joins(db, report_id: int) -> Optional[dict]:
    """Get daily report with joined reference names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            dr.*,
            e.number as estimate_number,
            p.full_name as foreman_name
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        LEFT JOIN persons p ON dr.foreman_id = p.id
        WHERE dr.id = ?
    """, (report_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return dict(row)


def get_daily_report_lines_with_joins(db, report_id: int) -> List[dict]:
    """Get daily report lines with joined work names and executor names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            drl.*,
            w.name as work_name
        FROM daily_report_lines drl
        LEFT JOIN works w ON drl.work_id = w.id
        WHERE drl.daily_report_id = ?
        ORDER BY drl.line_number
    """, (report_id,))
    
    lines = []
    for row in cursor.fetchall():
        line = dict(row)
        
        # Map deviation_percent to deviation for frontend compatibility
        if 'labor_deviation_percent' in line:
            line['deviation'] = line['labor_deviation_percent']
        elif 'deviation_percent' in line:
            line['deviation'] = line['deviation_percent']
        
        # Get executor names for this line
        cursor.execute("""
            SELECT p.full_name
            FROM daily_report_executors dre
            JOIN persons p ON dre.executor_id = p.id
            WHERE dre.report_line_id = ?
        """, (line['id'],))
        
        line['executor_names'] = [r['full_name'] for r in cursor.fetchall()]
        
        # Get executor IDs
        cursor.execute("""
            SELECT executor_id
            FROM daily_report_executors
            WHERE report_line_id = ?
        """, (line['id'],))
        
        line['executor_ids'] = [r['executor_id'] for r in cursor.fetchall()]
        
        lines.append(line)
    
    return lines


# Daily Report endpoints
@router.get("/daily-reports")
async def list_daily_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    estimate_id: Optional[int] = None,
    foreman_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("date", regex="^(date|id)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of daily reports with pagination and filtering"""
    offset = (page - 1) * page_size
    
    # Build query
    where_clauses = ["dr.marked_for_deletion = 0"]
    params = []
    
    if search:
        where_clauses.append("(e.number LIKE ? OR p.full_name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    if estimate_id:
        where_clauses.append("dr.estimate_id = ?")
        params.append(estimate_id)
    
    if foreman_id:
        where_clauses.append("dr.foreman_id = ?")
        params.append(foreman_id)
    
    if date_from:
        where_clauses.append("dr.date >= ?")
        params.append(date_from.isoformat())
    
    if date_to:
        where_clauses.append("dr.date <= ?")
        params.append(date_to.isoformat())
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    cursor = db.cursor()
    count_query = f"""
        SELECT COUNT(*) as count
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        LEFT JOIN persons p ON dr.foreman_id = p.id
        WHERE {where_sql}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    
    # Get items
    query = f"""
        SELECT 
            dr.*,
            e.number as estimate_number,
            p.full_name as foreman_name
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        LEFT JOIN persons p ON dr.foreman_id = p.id
        WHERE {where_sql}
        ORDER BY dr.{sort_by} {sort_order.upper()}
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


@router.get("/daily-reports/autofill/{estimate_id}")
async def autofill_daily_report_from_estimate(
    estimate_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get auto-filled daily report lines from estimate"""
    cursor = db.cursor()
    
    # Check if estimate exists
    cursor.execute("SELECT id FROM estimates WHERE id = ? AND marked_for_deletion = 0", (estimate_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get estimate lines
    cursor.execute("""
        SELECT 
            el.line_number,
            el.work_id,
            el.planned_labor,
            el.is_group,
            el.group_name,
            el.parent_group_id,
            el.is_collapsed,
            w.name as work_name
        FROM estimate_lines el
        LEFT JOIN works w ON el.work_id = w.id
        WHERE el.estimate_id = ?
        ORDER BY el.line_number
    """, (estimate_id,))
    
    lines = []
    for row in cursor.fetchall():
        line = {
            'line_number': row['line_number'],
            'work_id': row['work_id'],
            'work_name': row['work_name'],
            'planned_labor': row['planned_labor'],
            'actual_labor': 0.0,  # To be filled by user
            'deviation_percent': 0.0,
            'executor_ids': [],  # To be filled by user
            'executor_names': [],
            'is_group': bool(row['is_group']),
            'group_name': row['group_name'],
            'parent_group_id': row['parent_group_id'],
            'is_collapsed': bool(row['is_collapsed'])
        }
        lines.append(line)
    
    return {"success": True, "data": lines}


@router.post("/daily-reports", status_code=status.HTTP_201_CREATED)
async def create_daily_report(
    data: DailyReportCreate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Create new daily report with lines"""
    cursor = db.cursor()
    
    try:
        # Insert daily report
        cursor.execute("""
            INSERT INTO daily_reports (date, estimate_id, foreman_id)
            VALUES (?, ?, ?)
        """, (data.date.isoformat(), data.estimate_id, data.foreman_id))
        
        report_id = cursor.lastrowid
        
        # Insert lines
        for line in data.lines:
            # Calculate deviation percent
            deviation = 0.0
            if line.planned_labor > 0:
                deviation = ((line.actual_labor - line.planned_labor) / line.planned_labor) * 100
            
            cursor.execute("""
                INSERT INTO daily_report_lines (
                    daily_report_id, line_number, work_id, planned_labor, actual_labor,
                    labor_deviation_percent, is_group, group_name, parent_group_id, is_collapsed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, line.line_number, line.work_id, line.planned_labor,
                line.actual_labor, deviation, 1 if line.is_group else 0,
                line.group_name, line.parent_group_id, 1 if line.is_collapsed else 0
            ))
            
            line_id = cursor.lastrowid
            
            # Insert executors
            for executor_id in line.executor_ids:
                cursor.execute("""
                    INSERT INTO daily_report_executors (report_line_id, executor_id)
                    VALUES (?, ?)
                """, (line_id, executor_id))
        
        db.commit()
        
        # Get created report with joins
        report = get_daily_report_with_joins(db, report_id)
        report['lines'] = get_daily_report_lines_with_joins(db, report_id)
        
        return {"success": True, "data": report}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create daily report: {str(e)}"
        )


@router.get("/daily-reports/{report_id}")
async def get_daily_report(
    report_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get daily report by ID with lines and joined fields"""
    report = get_daily_report_with_joins(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
    
    if report.get('marked_for_deletion'):
        raise HTTPException(status_code=404, detail="Daily report is marked for deletion")
    
    # Get lines
    report['lines'] = get_daily_report_lines_with_joins(db, report_id)
    
    return {"success": True, "data": report}


@router.put("/daily-reports/{report_id}")
async def update_daily_report(
    report_id: int,
    data: DailyReportUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Update daily report"""
    cursor = db.cursor()
    
    # Check if report exists
    cursor.execute("SELECT id FROM daily_reports WHERE id = ? AND marked_for_deletion = 0", (report_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Daily report not found")
    
    try:
        # Update daily report
        cursor.execute("""
            UPDATE daily_reports
            SET date = ?, estimate_id = ?, foreman_id = ?, modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.date.isoformat(), data.estimate_id, data.foreman_id, report_id))
        
        # Update lines if provided
        if data.lines is not None:
            # Delete existing executors and lines
            cursor.execute("""
                DELETE FROM daily_report_executors 
                WHERE report_line_id IN (
                    SELECT id FROM daily_report_lines WHERE daily_report_id = ?
                )
            """, (report_id,))
            cursor.execute("DELETE FROM daily_report_lines WHERE daily_report_id = ?", (report_id,))
            
            # Insert new lines
            for line in data.lines:
                # Calculate deviation percent
                deviation = 0.0
                if line.planned_labor > 0:
                    deviation = ((line.actual_labor - line.planned_labor) / line.planned_labor) * 100
                
                cursor.execute("""
                    INSERT INTO daily_report_lines (
                        daily_report_id, line_number, work_id, planned_labor, actual_labor,
                        labor_deviation_percent, is_group, group_name, parent_group_id, is_collapsed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id, line.line_number, line.work_id, line.planned_labor,
                    line.actual_labor, deviation, 1 if line.is_group else 0,
                    line.group_name, line.parent_group_id, 1 if line.is_collapsed else 0
                ))
                
                line_id = cursor.lastrowid
                
                # Insert executors
                for executor_id in line.executor_ids:
                    cursor.execute("""
                        INSERT INTO daily_report_executors (report_line_id, executor_id)
                        VALUES (?, ?)
                    """, (line_id, executor_id))
        
        db.commit()
        
        # Get updated report with joins
        report = get_daily_report_with_joins(db, report_id)
        report['lines'] = get_daily_report_lines_with_joins(db, report_id)
        
        return {"success": True, "data": report}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update daily report: {str(e)}"
        )


@router.delete("/daily-reports/{report_id}")
async def delete_daily_report(
    report_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Mark daily report as deleted"""
    cursor = db.cursor()
    
    # Check if report exists
    cursor.execute("SELECT id FROM daily_reports WHERE id = ? AND marked_for_deletion = 0", (report_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Daily report not found")
    
    try:
        cursor.execute("""
            UPDATE daily_reports
            SET marked_for_deletion = 1, modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (report_id,))
        
        db.commit()
        
        return {"success": True, "message": "Daily report marked as deleted"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete daily report: {str(e)}"
        )


# Document Posting endpoints
@router.post("/estimates/{estimate_id}/post")
async def post_estimate(
    estimate_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Post (проведение) estimate document"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can post documents"
        )
    
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    success, error = posting_service.post_estimate(estimate_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get updated estimate
    estimate = get_estimate_with_joins(db, estimate_id)
    estimate['lines'] = get_estimate_lines_with_joins(db, estimate_id)
    
    return {"success": True, "data": estimate, "message": "Смета успешно проведена"}


@router.post("/estimates/{estimate_id}/unpost")
async def unpost_estimate(
    estimate_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Unpost (отмена проведения) estimate document"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can unpost documents"
        )
    
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    success, error = posting_service.unpost_estimate(estimate_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get updated estimate
    estimate = get_estimate_with_joins(db, estimate_id)
    estimate['lines'] = get_estimate_lines_with_joins(db, estimate_id)
    
    return {"success": True, "data": estimate, "message": "Проведение сметы отменено"}


@router.post("/daily-reports/{report_id}/post")
async def post_daily_report(
    report_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Post (проведение) daily report document"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can post documents"
        )
    
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    success, error = posting_service.post_daily_report(report_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get updated report
    report = get_daily_report_with_joins(db, report_id)
    report['lines'] = get_daily_report_lines_with_joins(db, report_id)
    
    return {"success": True, "data": report, "message": "Отчет успешно проведен"}


@router.post("/daily-reports/{report_id}/unpost")
async def unpost_daily_report(
    report_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Unpost (отмена проведения) daily report document"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can unpost documents"
        )
    
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    success, error = posting_service.unpost_daily_report(report_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get updated report
    report = get_daily_report_with_joins(db, report_id)
    report['lines'] = get_daily_report_lines_with_joins(db, report_id)
    
    return {"success": True, "data": report, "message": "Проведение отчета отменено"}


# Print Form endpoints
from fastapi.responses import Response


@router.get("/estimates/{estimate_id}/print")
async def print_estimate(
    estimate_id: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Generate print form for estimate"""
    # Check if estimate exists
    cursor = db.cursor()
    cursor.execute("SELECT number FROM estimates WHERE id = ? AND marked_for_deletion = 0", (estimate_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    estimate_number = row['number']
    
    # Import print form services
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    try:
        if format == "pdf":
            from src.services.estimate_print_form import EstimatePrintForm
            print_service = EstimatePrintForm()
            content = print_service.generate(estimate_id)
            
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate PDF"
                )
            
            filename = f"estimate_{estimate_number}.pdf"
            media_type = "application/pdf"
            
        else:  # excel
            from src.services.excel_estimate_print_form import ExcelEstimatePrintForm
            print_service = ExcelEstimatePrintForm()
            content = print_service.generate(estimate_id)
            
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate Excel file"
                )
            
            filename = f"estimate_{estimate_number}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Return file with proper headers
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate print form: {str(e)}"
        )


@router.get("/daily-reports/{report_id}/print")
async def print_daily_report(
    report_id: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Generate print form for daily report"""
    # Check if report exists
    cursor = db.cursor()
    cursor.execute("""
        SELECT dr.date, e.number as estimate_number
        FROM daily_reports dr
        LEFT JOIN estimates e ON dr.estimate_id = e.id
        WHERE dr.id = ? AND dr.marked_for_deletion = 0
    """, (report_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Daily report not found")
    
    report_date = row['date']
    estimate_number = row['estimate_number'] or "unknown"
    
    # Import print form services
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    try:
        if format == "pdf":
            from src.services.daily_report_print_form import DailyReportPrintForm
            print_service = DailyReportPrintForm()
            content = print_service.generate(report_id)
            
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate PDF"
                )
            
            filename = f"daily_report_{report_date}_{estimate_number}.pdf"
            media_type = "application/pdf"
            
        else:  # excel
            from src.services.excel_daily_report_print_form import ExcelDailyReportPrintForm
            print_service = ExcelDailyReportPrintForm()
            content = print_service.generate(report_id)
            
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate Excel file"
                )
            
            filename = f"daily_report_{report_date}_{estimate_number}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Return file with proper headers
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate print form: {str(e)}"
        )



# ==================== Timesheet Endpoints ====================

from api.models.documents import (
    Timesheet, TimesheetCreate, TimesheetUpdate,
    TimesheetLine, TimesheetLineCreate
)


def get_timesheet_with_joins(db, timesheet_id: int) -> Optional[dict]:
    """Get timesheet with joined reference names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            t.*,
            o.name as object_name,
            e.number as estimate_number,
            p.full_name as foreman_name
        FROM timesheets t
        LEFT JOIN objects o ON t.object_id = o.id
        LEFT JOIN estimates e ON t.estimate_id = e.id
        LEFT JOIN persons p ON t.foreman_id = p.id
        WHERE t.id = ?
    """, (timesheet_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return dict(row)


def get_timesheet_lines_with_joins(db, timesheet_id: int) -> List[dict]:
    """Get timesheet lines with joined employee names"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            tl.*,
            p.full_name as employee_name
        FROM timesheet_lines tl
        LEFT JOIN persons p ON tl.employee_id = p.id
        WHERE tl.timesheet_id = ?
        ORDER BY tl.line_number
    """, (timesheet_id,))
    
    lines = []
    for row in cursor.fetchall():
        line = dict(row)
        # Convert day columns to days dict
        days = {}
        for day in range(1, 32):
            day_col = f'day_{day:02d}'
            if day_col in line and line[day_col] > 0:
                days[day] = line[day_col]
        line['days'] = days
        lines.append(line)
    
    return lines


@router.get("/timesheets", response_model=List[Timesheet])
async def get_timesheets(
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get all timesheets for current user"""
    cursor = db.cursor()
    
    # Build query based on role
    if current_user.role == 'admin':
        cursor.execute("""
            SELECT 
                t.*,
                o.name as object_name,
                e.number as estimate_number,
                p.full_name as foreman_name
            FROM timesheets t
            LEFT JOIN objects o ON t.object_id = o.id
            LEFT JOIN estimates e ON t.estimate_id = e.id
            LEFT JOIN persons p ON t.foreman_id = p.id
            WHERE t.marked_for_deletion = 0
            ORDER BY t.date DESC, t.number DESC
        """)
    else:
        # Get foreman's person_id
        cursor.execute("SELECT id FROM persons WHERE user_id = ?", (current_user.id,))
        person_row = cursor.fetchone()
        
        if not person_row:
            return []
        
        person_id = person_row['id']
        
        cursor.execute("""
            SELECT 
                t.*,
                o.name as object_name,
                e.number as estimate_number,
                p.full_name as foreman_name
            FROM timesheets t
            LEFT JOIN objects o ON t.object_id = o.id
            LEFT JOIN estimates e ON t.estimate_id = e.id
            LEFT JOIN persons p ON t.foreman_id = p.id
            WHERE t.marked_for_deletion = 0
              AND t.foreman_id = ?
            ORDER BY t.date DESC, t.number DESC
        """, (person_id,))
    
    timesheets = []
    for row in cursor.fetchall():
        timesheet_dict = dict(row)
        # Get lines
        timesheet_dict['lines'] = get_timesheet_lines_with_joins(db, timesheet_dict['id'])
        timesheets.append(Timesheet(**timesheet_dict))
    
    return timesheets


@router.get("/timesheets/{timesheet_id}", response_model=Timesheet)
async def get_timesheet(
    timesheet_id: int,
    db=Depends(get_db_connection)
):
    """Get timesheet by ID"""
    timesheet_dict = get_timesheet_with_joins(db, timesheet_id)
    
    if not timesheet_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    # Get lines
    timesheet_dict['lines'] = get_timesheet_lines_with_joins(db, timesheet_id)
    
    return Timesheet(**timesheet_dict)


@router.post("/timesheets", status_code=status.HTTP_201_CREATED)
async def create_timesheet(
    data: TimesheetCreate,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Create new timesheet"""
    cursor = db.cursor()
    
    # Get foreman's person_id (optional for admins)
    cursor.execute("SELECT id FROM persons WHERE user_id = ?", (current_user.id,))
    person_row = cursor.fetchone()
    
    foreman_id = None
    if person_row:
        foreman_id = person_row['id']
    elif current_user.role != 'admin':
        # Non-admin users must have an associated person record
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no associated person record. Please contact administrator."
        )
    
    # Insert timesheet
    cursor.execute("""
        INSERT INTO timesheets (
            number, date, object_id, estimate_id, foreman_id, month_year,
            created_at, modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (
        data.number,
        data.date.isoformat(),
        data.object_id,
        data.estimate_id,
        foreman_id,
        data.month_year
    ))
    
    timesheet_id = cursor.lastrowid
    
    # Insert lines
    for line in data.lines:
        # Calculate totals
        total_hours = sum(line.days.values())
        total_amount = total_hours * line.hourly_rate
        
        # Prepare day values
        day_values = {}
        for day in range(1, 32):
            day_values[f'day_{day:02d}'] = line.days.get(day, 0)
        
        cursor.execute(f"""
            INSERT INTO timesheet_lines (
                timesheet_id, line_number, employee_id, hourly_rate,
                day_01, day_02, day_03, day_04, day_05, day_06, day_07,
                day_08, day_09, day_10, day_11, day_12, day_13, day_14,
                day_15, day_16, day_17, day_18, day_19, day_20, day_21,
                day_22, day_23, day_24, day_25, day_26, day_27, day_28,
                day_29, day_30, day_31, total_hours, total_amount
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """, (
            timesheet_id, line.line_number, line.employee_id, line.hourly_rate,
            day_values['day_01'], day_values['day_02'], day_values['day_03'],
            day_values['day_04'], day_values['day_05'], day_values['day_06'],
            day_values['day_07'], day_values['day_08'], day_values['day_09'],
            day_values['day_10'], day_values['day_11'], day_values['day_12'],
            day_values['day_13'], day_values['day_14'], day_values['day_15'],
            day_values['day_16'], day_values['day_17'], day_values['day_18'],
            day_values['day_19'], day_values['day_20'], day_values['day_21'],
            day_values['day_22'], day_values['day_23'], day_values['day_24'],
            day_values['day_25'], day_values['day_26'], day_values['day_27'],
            day_values['day_28'], day_values['day_29'], day_values['day_30'],
            day_values['day_31'], total_hours, total_amount
        ))
    
    db.commit()
    
    # Get created timesheet with joins
    timesheet = get_timesheet_with_joins(db, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Failed to retrieve created timesheet")
    
    # Get lines
    timesheet['lines'] = get_timesheet_lines_with_joins(db, timesheet_id)
    
    return timesheet


@router.put("/timesheets/{timesheet_id}")
async def update_timesheet(
    timesheet_id: int,
    data: TimesheetUpdate,
    db=Depends(get_db_connection)
):
    """Update timesheet"""
    cursor = db.cursor()
    
    # Check if timesheet exists
    cursor.execute("SELECT id, is_posted FROM timesheets WHERE id = ?", (timesheet_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    if row['is_posted']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update posted timesheet"
        )
    
    # Update timesheet
    cursor.execute("""
        UPDATE timesheets
        SET number = ?, date = ?, object_id = ?, estimate_id = ?,
            month_year = ?, modified_at = datetime('now')
        WHERE id = ?
    """, (
        data.number,
        data.date.isoformat(),
        data.object_id,
        data.estimate_id,
        data.month_year,
        timesheet_id
    ))
    
    # Delete old lines
    cursor.execute("DELETE FROM timesheet_lines WHERE timesheet_id = ?", (timesheet_id,))
    
    # Insert new lines
    if data.lines:
        for line in data.lines:
            # Calculate totals
            total_hours = sum(line.days.values())
            total_amount = total_hours * line.hourly_rate
            
            # Prepare day values
            day_values = {}
            for day in range(1, 32):
                day_values[f'day_{day:02d}'] = line.days.get(day, 0)
            
            cursor.execute(f"""
                INSERT INTO timesheet_lines (
                    timesheet_id, line_number, employee_id, hourly_rate,
                    day_01, day_02, day_03, day_04, day_05, day_06, day_07,
                    day_08, day_09, day_10, day_11, day_12, day_13, day_14,
                    day_15, day_16, day_17, day_18, day_19, day_20, day_21,
                    day_22, day_23, day_24, day_25, day_26, day_27, day_28,
                    day_29, day_30, day_31, total_hours, total_amount
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, (
                timesheet_id, line.line_number, line.employee_id, line.hourly_rate,
                day_values['day_01'], day_values['day_02'], day_values['day_03'],
                day_values['day_04'], day_values['day_05'], day_values['day_06'],
                day_values['day_07'], day_values['day_08'], day_values['day_09'],
                day_values['day_10'], day_values['day_11'], day_values['day_12'],
                day_values['day_13'], day_values['day_14'], day_values['day_15'],
                day_values['day_16'], day_values['day_17'], day_values['day_18'],
                day_values['day_19'], day_values['day_20'], day_values['day_21'],
                day_values['day_22'], day_values['day_23'], day_values['day_24'],
                day_values['day_25'], day_values['day_26'], day_values['day_27'],
                day_values['day_28'], day_values['day_29'], day_values['day_30'],
                day_values['day_31'], total_hours, total_amount
            ))
    
    db.commit()
    
    # Return updated timesheet
    return await get_timesheet(timesheet_id, db)


@router.delete("/timesheets/{timesheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet(
    timesheet_id: int,
    db=Depends(get_db_connection)
):
    """Delete timesheet (soft delete)"""
    cursor = db.cursor()
    
    # Check if timesheet exists
    cursor.execute("SELECT id, is_posted FROM timesheets WHERE id = ?", (timesheet_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    if row['is_posted']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete posted timesheet. Unpost it first."
        )
    
    # Soft delete
    cursor.execute("""
        UPDATE timesheets
        SET marked_for_deletion = 1
        WHERE id = ?
    """, (timesheet_id,))
    
    db.commit()


@router.post("/timesheets/{timesheet_id}/post")
async def post_timesheet(
    timesheet_id: int,
    db=Depends(get_db_connection)
):
    """Post timesheet"""
    from src.services.timesheet_posting_service import TimesheetPostingService
    
    posting_service = TimesheetPostingService()
    success, message = posting_service.post_timesheet(timesheet_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"success": True, "message": message}


@router.post("/timesheets/{timesheet_id}/unpost")
async def unpost_timesheet(
    timesheet_id: int,
    db=Depends(get_db_connection)
):
    """Unpost timesheet"""
    from src.services.timesheet_posting_service import TimesheetPostingService
    
    posting_service = TimesheetPostingService()
    success, message = posting_service.unpost_timesheet(timesheet_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"success": True, "message": message}


@router.post("/timesheets/autofill")
async def autofill_from_daily_reports(
    object_id: int = Query(...),
    estimate_id: int = Query(...),
    month_year: str = Query(...),
    db=Depends(get_db_connection)
):
    """Get timesheet lines from daily reports"""
    from src.services.auto_fill_service import AutoFillService
    
    auto_fill_service = AutoFillService()
    lines = auto_fill_service.fill_from_daily_reports(
        object_id, estimate_id, month_year
    )
    
    return {"lines": lines}


# ==================== Bulk Operations ====================

from pydantic import BaseModel

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class BulkPostRequest(BaseModel):
    ids: List[int]


@router.post("/estimates/bulk-delete")
async def bulk_delete_estimates(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete estimates"""
    cursor = db.cursor()
    deleted_count = 0
    errors = []
    
    try:
        for estimate_id in request.ids:
            # Check if estimate exists and is not posted
            cursor.execute("""
                SELECT id, number, is_posted 
                FROM estimates 
                WHERE id = ? AND marked_for_deletion = 0
            """, (estimate_id,))
            row = cursor.fetchone()
            
            if not row:
                errors.append(f"Смета ID {estimate_id} не найдена")
                continue
            
            if row['is_posted']:
                errors.append(f"Смета {row['number']} проведена, удаление невозможно")
                continue
            
            # Mark as deleted
            cursor.execute("""
                UPDATE estimates
                SET marked_for_deletion = 1, modified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (estimate_id,))
            deleted_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "errors": errors,
            "message": f"Удалено документов: {deleted_count}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при групповом удалении: {str(e)}"
        )


@router.post("/estimates/bulk-post")
async def bulk_post_estimates(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk post estimates"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут проводить документы"
        )
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    posted_count = 0
    errors = []
    
    for estimate_id in request.ids:
        success, error = posting_service.post_estimate(estimate_id)
        if success:
            posted_count += 1
        else:
            errors.append(f"Смета ID {estimate_id}: {error}")
    
    return {
        "success": True,
        "posted_count": posted_count,
        "errors": errors,
        "message": f"Проведено документов: {posted_count}"
    }


@router.post("/estimates/bulk-unpost")
async def bulk_unpost_estimates(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk unpost estimates"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут отменять проведение документов"
        )
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    unposted_count = 0
    errors = []
    
    for estimate_id in request.ids:
        success, error = posting_service.unpost_estimate(estimate_id)
        if success:
            unposted_count += 1
        else:
            errors.append(f"Смета ID {estimate_id}: {error}")
    
    return {
        "success": True,
        "unposted_count": unposted_count,
        "errors": errors,
        "message": f"Отменено проведение: {unposted_count}"
    }


@router.post("/daily-reports/bulk-delete")
async def bulk_delete_daily_reports(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete daily reports"""
    cursor = db.cursor()
    deleted_count = 0
    errors = []
    
    try:
        for report_id in request.ids:
            # Check if report exists and is not posted
            cursor.execute("""
                SELECT id, date, is_posted 
                FROM daily_reports 
                WHERE id = ? AND marked_for_deletion = 0
            """, (report_id,))
            row = cursor.fetchone()
            
            if not row:
                errors.append(f"Отчет ID {report_id} не найден")
                continue
            
            if row['is_posted']:
                errors.append(f"Отчет от {row['date']} проведен, удаление невозможно")
                continue
            
            # Mark as deleted
            cursor.execute("""
                UPDATE daily_reports
                SET marked_for_deletion = 1, modified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (report_id,))
            deleted_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "errors": errors,
            "message": f"Удалено документов: {deleted_count}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при групповом удалении: {str(e)}"
        )


@router.post("/daily-reports/bulk-post")
async def bulk_post_daily_reports(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk post daily reports"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут проводить документы"
        )
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    posted_count = 0
    errors = []
    
    for report_id in request.ids:
        success, error = posting_service.post_daily_report(report_id)
        if success:
            posted_count += 1
        else:
            errors.append(f"Отчет ID {report_id}: {error}")
    
    return {
        "success": True,
        "posted_count": posted_count,
        "errors": errors,
        "message": f"Проведено документов: {posted_count}"
    }


@router.post("/daily-reports/bulk-unpost")
async def bulk_unpost_daily_reports(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk unpost daily reports"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут отменять проведение документов"
        )
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.services.document_posting_service import DocumentPostingService
    
    posting_service = DocumentPostingService()
    unposted_count = 0
    errors = []
    
    for report_id in request.ids:
        success, error = posting_service.unpost_daily_report(report_id)
        if success:
            unposted_count += 1
        else:
            errors.append(f"Отчет ID {report_id}: {error}")
    
    return {
        "success": True,
        "unposted_count": unposted_count,
        "errors": errors,
        "message": f"Отменено проведение: {unposted_count}"
    }


@router.post("/timesheets/bulk-delete")
async def bulk_delete_timesheets(
    request: BulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete timesheets"""
    cursor = db.cursor()
    deleted_count = 0
    errors = []
    
    try:
        for timesheet_id in request.ids:
            # Check if timesheet exists and is not posted
            cursor.execute("""
                SELECT id, number, is_posted 
                FROM timesheets 
                WHERE id = ? AND marked_for_deletion = 0
            """, (timesheet_id,))
            row = cursor.fetchone()
            
            if not row:
                errors.append(f"Табель ID {timesheet_id} не найден")
                continue
            
            if row['is_posted']:
                errors.append(f"Табель {row['number']} проведен, удаление невозможно")
                continue
            
            # Mark as deleted
            cursor.execute("""
                UPDATE timesheets
                SET marked_for_deletion = 1
                WHERE id = ?
            """, (timesheet_id,))
            deleted_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "errors": errors,
            "message": f"Удалено документов: {deleted_count}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при групповом удалении: {str(e)}"
        )


@router.post("/timesheets/bulk-post")
async def bulk_post_timesheets(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk post timesheets"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут проводить документы"
        )
    
    from src.services.timesheet_posting_service import TimesheetPostingService
    
    posting_service = TimesheetPostingService()
    posted_count = 0
    errors = []
    
    for timesheet_id in request.ids:
        success, message = posting_service.post_timesheet(timesheet_id)
        if success:
            posted_count += 1
        else:
            errors.append(f"Табель ID {timesheet_id}: {message}")
    
    return {
        "success": True,
        "posted_count": posted_count,
        "errors": errors,
        "message": f"Проведено документов: {posted_count}"
    }


@router.post("/timesheets/bulk-unpost")
async def bulk_unpost_timesheets(
    request: BulkPostRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk unpost timesheets"""
    # Check admin role
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут отменять проведение документов"
        )
    
    from src.services.timesheet_posting_service import TimesheetPostingService
    
    posting_service = TimesheetPostingService()
    unposted_count = 0
    errors = []
    
    for timesheet_id in request.ids:
        success, message = posting_service.unpost_timesheet(timesheet_id)
        if success:
            unposted_count += 1
        else:
            errors.append(f"Табель ID {timesheet_id}: {message}")
    
    return {
        "success": True,
        "unposted_count": unposted_count,
        "errors": errors,
        "message": f"Отменено проведение: {unposted_count}"
    }

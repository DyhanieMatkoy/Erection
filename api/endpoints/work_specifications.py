import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db_manager
from api.models.work_specification import WorkSpecification, WorkSpecificationCreate, WorkSpecificationUpdate, WorkSpecificationSummary
from src.data.repositories.work_specification_repository import WorkSpecificationRepository
from src.data.repositories.work_repository import WorkRepository
from src.data.database_manager import DatabaseManager
from api.models.auth import UserInfo

router = APIRouter(prefix="/works", tags=["Work Specifications"])

@router.get("/{work_id}/specifications", response_model=WorkSpecificationSummary)
async def get_work_specifications(
    work_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all specifications for a work"""
    spec_repo = WorkSpecificationRepository(db_manager)
    work_repo = WorkRepository(db_manager)
    
    # Get work details
    work = work_repo.find_by_id(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
        
    # Get specifications and totals
    specs = spec_repo.get_by_work_id(work_id)
    totals_decimal = spec_repo.get_totals_by_type(work_id)
    
    # Convert Decimals to floats for JSON response
    totals = {k: float(v) for k, v in totals_decimal.items()}
    total_cost = sum(totals.values())
    
    return WorkSpecificationSummary(
        work_id=work_id,
        work_name=work['name'],
        work_code=work.get('code'),
        specifications=specs,
        totals_by_type=totals,
        total_cost=total_cost
    )

@router.post("/{work_id}/specifications", response_model=int)
async def create_specification(
    work_id: int,
    spec: WorkSpecificationCreate,
    current_user: UserInfo = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Create a new specification entry"""
    if spec.work_id != work_id:
        raise HTTPException(status_code=400, detail="Work ID mismatch")
        
    repo = WorkSpecificationRepository(db_manager)
    # Ensure dict has all keys
    data = spec.model_dump()
    spec_id = repo.create(data)
    if not spec_id:
        raise HTTPException(status_code=500, detail="Failed to create specification")
    return spec_id

@router.put("/{work_id}/specifications/{spec_id}", response_model=bool)
async def update_specification(
    work_id: int,
    spec_id: int,
    spec: WorkSpecificationUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Update a specification entry"""
    repo = WorkSpecificationRepository(db_manager)
    data = spec.model_dump(exclude_unset=True)
    success = repo.update(spec_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Specification not found or update failed")
    return True

@router.delete("/{work_id}/specifications/{spec_id}", response_model=bool)
async def delete_specification(
    work_id: int,
    spec_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Delete a specification entry"""
    repo = WorkSpecificationRepository(db_manager)
    success = repo.delete(spec_id)
    if not success:
        raise HTTPException(status_code=404, detail="Specification not found or delete failed")
    return True

@router.post("/{work_id}/specifications/copy-from/{source_work_id}", response_model=bool)
async def copy_specifications(
    work_id: int,
    source_work_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Copy specifications from another work"""
    repo = WorkSpecificationRepository(db_manager)
    success = repo.copy_from_work(work_id, source_work_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to copy specifications")
    return True

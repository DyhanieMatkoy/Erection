"""
Costs and Materials API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
import math

from ..models.costs_materials import (
    Unit, UnitCreate, UnitUpdate,
    CostItem, CostItemCreate, CostItemUpdate,
    Material, MaterialCreate, MaterialUpdate,
    CostItemMaterial, CostItemMaterialSimple, CostItemMaterialCreate, CostItemMaterialUpdate,
    WorkComposition, WorkCompositionDetail
)
from api.dependencies.database import get_db
from api.validation import (
    validate_quantity,
    check_duplicate_cost_item,
    check_duplicate_material,
    check_cost_item_has_materials,
    validate_work_exists,
    validate_cost_item_exists,
    validate_material_exists
)
from src.data.models.sqlalchemy_models import (
    Unit as UnitModel,
    CostItem as CostItemModel,
    Material as MaterialModel,
    CostItemMaterial as CostItemMaterialModel,
    Work as WorkModel
)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

def create_pagination_response(items: List, page: int, limit: int, total: int):
    """Create paginated response with metadata"""
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


# ============================================================================
# Units Endpoints
# ============================================================================

@router.get("/units", response_model=List[Unit])
async def get_units(
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    """Get all units"""
    query = db.query(UnitModel)
    if not include_deleted:
        query = query.filter(UnitModel.marked_for_deletion == False)
    return query.order_by(UnitModel.name).all()


@router.get("/units/{unit_id}", response_model=Unit)
async def get_unit(unit_id: int, db: Session = Depends(get_db)):
    """Get unit by ID"""
    unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.post("/units", response_model=Unit, status_code=status.HTTP_201_CREATED)
async def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    """Create new unit"""
    # Check if unit with same name exists
    existing = db.query(UnitModel).filter(UnitModel.name == unit.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Unit with this name already exists")
    
    db_unit = UnitModel(**unit.dict())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit


@router.put("/units/{unit_id}", response_model=Unit)
async def update_unit(
    unit_id: int,
    unit: UnitUpdate,
    db: Session = Depends(get_db)
):
    """Update unit"""
    db_unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    for key, value in unit.dict(exclude_unset=True).items():
        setattr(db_unit, key, value)
    
    db.commit()
    db.refresh(db_unit)
    return db_unit


@router.delete("/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    """Soft delete unit"""
    db_unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    db_unit.marked_for_deletion = True
    db.commit()


# ============================================================================
# Cost Items Endpoints
# ============================================================================

@router.get("/cost-items")
async def get_cost_items(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by code or description"),
    parent_id: Optional[int] = Query(None, description="Filter by parent ID"),
    is_folder: Optional[bool] = Query(None, description="Filter by folder status"),
    include_deleted: bool = Query(False, description="Include deleted items"),
    db: Session = Depends(get_db)
):
    """Get cost items with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 1000)
    - search: Search term for code or description
    - parent_id: Filter by parent ID (hierarchical)
    - is_folder: Filter by folder status (true/false)
    - include_deleted: Include soft-deleted items
    
    Returns:
    - data: List of cost items
    - pagination: Metadata (page, limit, total, total_pages)
    """
    # Build base query
    query = db.query(CostItemModel).options(joinedload(CostItemModel.unit_ref))
    
    # Apply filters
    if not include_deleted:
        query = query.filter(CostItemModel.marked_for_deletion == False)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                CostItemModel.code.ilike(search_term),
                CostItemModel.description.ilike(search_term)
            )
        )
    
    if parent_id is not None:
        query = query.filter(CostItemModel.parent_id == parent_id)
    
    if is_folder is not None:
        query = query.filter(CostItemModel.is_folder == is_folder)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    items = query.order_by(CostItemModel.code).offset(offset).limit(limit).all()
    
    # Format results with unit_name
    result = []
    for item in items:
        item_dict = {
            "id": item.id,
            "parent_id": item.parent_id,
            "code": item.code,
            "description": item.description,
            "is_folder": item.is_folder,
            "price": item.price,
            "unit": item.unit,
            "unit_id": item.unit_id,
            "unit_name": item.unit_ref.name if item.unit_ref else None,
            "labor_coefficient": item.labor_coefficient,
            "marked_for_deletion": item.marked_for_deletion,
            "created_at": item.created_at,
            "modified_at": item.modified_at
        }
        result.append(item_dict)
    
    return create_pagination_response(result, page, limit, total)


@router.get("/cost-items/{cost_item_id}", response_model=CostItem)
async def get_cost_item(cost_item_id: int, db: Session = Depends(get_db)):
    """Get cost item by ID"""
    item = db.query(CostItemModel)\
        .options(joinedload(CostItemModel.unit_ref))\
        .filter(CostItemModel.id == cost_item_id)\
        .first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    
    return {
        "id": item.id,
        "parent_id": item.parent_id,
        "code": item.code,
        "description": item.description,
        "is_folder": item.is_folder,
        "price": item.price,
        "unit": item.unit,
        "unit_id": item.unit_id,
        "unit_name": item.unit_ref.name if item.unit_ref else None,
        "labor_coefficient": item.labor_coefficient,
        "marked_for_deletion": item.marked_for_deletion,
        "created_at": item.created_at,
        "modified_at": item.modified_at
    }


@router.post("/cost-items", response_model=CostItem, status_code=status.HTTP_201_CREATED)
async def create_cost_item(item: CostItemCreate, db: Session = Depends(get_db)):
    """Create new cost item"""
    db_item = CostItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/cost-items/{cost_item_id}", response_model=CostItem)
async def update_cost_item(
    cost_item_id: int,
    item: CostItemUpdate,
    db: Session = Depends(get_db)
):
    """Update cost item"""
    db_item = db.query(CostItemModel).filter(CostItemModel.id == cost_item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/cost-items/{cost_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_item(cost_item_id: int, db: Session = Depends(get_db)):
    """Soft delete cost item"""
    db_item = db.query(CostItemModel).filter(CostItemModel.id == cost_item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    
    db_item.marked_for_deletion = True
    db.commit()


# ============================================================================
# Materials Endpoints
# ============================================================================

@router.get("/materials")
async def get_materials(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by code or description"),
    unit_id: Optional[int] = Query(None, description="Filter by unit ID"),
    include_deleted: bool = Query(False, description="Include deleted items"),
    db: Session = Depends(get_db)
):
    """Get materials with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 1000)
    - search: Search term for code or description
    - unit_id: Filter by unit ID
    - include_deleted: Include soft-deleted items
    
    Returns:
    - data: List of materials
    - pagination: Metadata (page, limit, total, total_pages)
    """
    # Build base query
    query = db.query(MaterialModel).options(joinedload(MaterialModel.unit_ref))
    
    # Apply filters
    if not include_deleted:
        query = query.filter(MaterialModel.marked_for_deletion == False)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                MaterialModel.code.ilike(search_term),
                MaterialModel.description.ilike(search_term)
            )
        )
    
    if unit_id is not None:
        query = query.filter(MaterialModel.unit_id == unit_id)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    materials = query.order_by(MaterialModel.code).offset(offset).limit(limit).all()
    
    # Format results with unit_name
    result = []
    for material in materials:
        material_dict = {
            "id": material.id,
            "code": material.code,
            "description": material.description,
            "price": material.price,
            "unit": material.unit,
            "unit_id": material.unit_id,
            "unit_name": material.unit_ref.name if material.unit_ref else None,
            "marked_for_deletion": material.marked_for_deletion,
            "created_at": material.created_at,
            "modified_at": material.modified_at
        }
        result.append(material_dict)
    
    return create_pagination_response(result, page, limit, total)


@router.get("/materials/{material_id}", response_model=Material)
async def get_material(material_id: int, db: Session = Depends(get_db)):
    """Get material by ID"""
    material = db.query(MaterialModel)\
        .options(joinedload(MaterialModel.unit_ref))\
        .filter(MaterialModel.id == material_id)\
        .first()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return {
        "id": material.id,
        "code": material.code,
        "description": material.description,
        "price": material.price,
        "unit": material.unit,
        "unit_id": material.unit_id,
        "unit_name": material.unit_ref.name if material.unit_ref else None,
        "marked_for_deletion": material.marked_for_deletion,
        "created_at": material.created_at,
        "modified_at": material.modified_at
    }


@router.post("/materials", response_model=Material, status_code=status.HTTP_201_CREATED)
async def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    """Create new material"""
    db_material = MaterialModel(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


@router.put("/materials/{material_id}", response_model=Material)
async def update_material(
    material_id: int,
    material: MaterialUpdate,
    db: Session = Depends(get_db)
):
    """Update material"""
    db_material = db.query(MaterialModel).filter(MaterialModel.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    for key, value in material.dict(exclude_unset=True).items():
        setattr(db_material, key, value)
    
    db.commit()
    db.refresh(db_material)
    return db_material


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: int, db: Session = Depends(get_db)):
    """Soft delete material"""
    db_material = db.query(MaterialModel).filter(MaterialModel.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    db_material.marked_for_deletion = True
    db.commit()


# ============================================================================
# Work Composition Endpoints
# ============================================================================

@router.get("/works/{work_id}/composition", response_model=WorkCompositionDetail)
async def get_work_composition(work_id: int, db: Session = Depends(get_db)):
    """Get complete work composition with cost items and materials"""
    work = db.query(WorkModel).filter(WorkModel.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Get all associations for this work
    associations = db.query(CostItemMaterialModel)\
        .options(
            joinedload(CostItemMaterialModel.cost_item).joinedload(CostItemModel.unit_ref),
            joinedload(CostItemMaterialModel.material).joinedload(MaterialModel.unit_ref)
        )\
        .filter(CostItemMaterialModel.work_id == work_id)\
        .all()
    
    # Separate cost items (material_id is NULL) and materials
    cost_items = []
    materials = []
    total_cost_items_price = 0.0
    total_materials_cost = 0.0
    
    for assoc in associations:
        assoc_dict = {
            "id": assoc.id,
            "work_id": assoc.work_id,
            "cost_item_id": assoc.cost_item_id,
            "material_id": assoc.material_id,
            "quantity_per_unit": assoc.quantity_per_unit,
            "cost_item": {
                "id": assoc.cost_item.id,
                "code": assoc.cost_item.code,
                "description": assoc.cost_item.description,
                "price": assoc.cost_item.price,
                "unit_name": assoc.cost_item.unit_ref.name if assoc.cost_item.unit_ref else None,
                "labor_coefficient": assoc.cost_item.labor_coefficient
            } if assoc.cost_item else None,
            "material": {
                "id": assoc.material.id,
                "code": assoc.material.code,
                "description": assoc.material.description,
                "price": assoc.material.price,
                "unit_name": assoc.material.unit_ref.name if assoc.material.unit_ref else None
            } if assoc.material else None
        }
        
        if assoc.material_id is None:
            # Cost item only
            cost_items.append(assoc_dict)
            if assoc.cost_item:
                total_cost_items_price += assoc.cost_item.price
        else:
            # Material
            materials.append(assoc_dict)
            if assoc.material:
                total_materials_cost += assoc.material.price * assoc.quantity_per_unit
    
    return {
        "work_id": work.id,
        "work_name": work.name,
        "work_code": work.code,
        "work_unit": work.unit_ref.name if work.unit_ref else None,
        "work_price": work.price,
        "work_labor_rate": work.labor_rate,
        "cost_items": cost_items,
        "materials": materials,
        "total_cost_items_price": total_cost_items_price,
        "total_materials_cost": total_materials_cost,
        "total_cost": total_cost_items_price + total_materials_cost
    }


@router.post("/works/{work_id}/cost-items", response_model=CostItemMaterialSimple, status_code=status.HTTP_201_CREATED)
async def add_cost_item_to_work(
    work_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """Add cost item to work
    
    Request body: {"cost_item_id": int}
    
    Validation:
    - Work must exist (Req 13.1)
    - Cost item must exist (Req 13.2)
    - No duplicate cost items (Req 2.5)
    """
    cost_item_id = request.get("cost_item_id")
    if not cost_item_id:
        raise HTTPException(status_code=400, detail="cost_item_id is required")
    
    # Validate work exists
    validate_work_exists(db, work_id)
    
    # Validate cost item exists
    validate_cost_item_exists(db, cost_item_id)
    
    # Check for duplicate
    check_duplicate_cost_item(db, work_id, cost_item_id)
    
    # Create association
    association = CostItemMaterialModel(
        work_id=work_id,
        cost_item_id=cost_item_id,
        material_id=None,
        quantity_per_unit=0.0
    )
    db.add(association)
    db.commit()
    db.refresh(association)
    return association


@router.post("/works/{work_id}/materials", response_model=CostItemMaterialSimple, status_code=status.HTTP_201_CREATED)
async def add_material_to_work(
    work_id: int,
    association: CostItemMaterialCreate,
    db: Session = Depends(get_db)
):
    """Add material to work with cost item linkage
    
    Validation:
    - Work must exist (Req 13.1)
    - Cost item must already be added to the work
    - Material must exist (Req 13.3)
    - Quantity must be greater than zero (Req 4.4, 5.2, 11.3)
    - No duplicate material-cost item combinations (Req 4.4)
    """
    # Validate material_id is provided
    if not association.material_id:
        raise HTTPException(status_code=400, detail="material_id is required")
    
    # Validate quantity
    validate_quantity(association.quantity_per_unit)
    
    # Validate work exists
    validate_work_exists(db, work_id)
    
    # Verify cost item exists and is already added to work
    cost_item_assoc = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.cost_item_id == association.cost_item_id,
            CostItemMaterialModel.material_id.is_(None)
        )\
        .first()
    
    if not cost_item_assoc:
        raise HTTPException(status_code=400, detail="Cost item must be added to work first")
    
    # Validate material exists
    validate_material_exists(db, association.material_id)
    
    # Check for duplicate
    check_duplicate_material(db, work_id, association.cost_item_id, association.material_id)
    
    # Create association
    db_association = CostItemMaterialModel(
        work_id=work_id,
        cost_item_id=association.cost_item_id,
        material_id=association.material_id,
        quantity_per_unit=association.quantity_per_unit
    )
    db.add(db_association)
    db.commit()
    db.refresh(db_association)
    return db_association


@router.put("/works/{work_id}/materials/{association_id}", response_model=CostItemMaterialSimple)
async def update_material_association(
    work_id: int,
    association_id: int,
    update: CostItemMaterialUpdate,
    db: Session = Depends(get_db)
):
    """Update material quantity or cost item in work
    
    Can update:
    - quantity_per_unit: The quantity of material per unit of work (Req 5.2, 5.3)
    - cost_item_id: Change which cost item this material is associated with (Req 6.3)
    
    Validation:
    - Quantity must be greater than zero (Req 4.4, 5.2, 11.3)
    - No duplicate material-cost item combinations (Req 4.4)
    """
    association = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.id == association_id,
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.material_id.isnot(None)
        )\
        .first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Material association not found")
    
    # Validate quantity if provided
    if update.quantity_per_unit is not None:
        validate_quantity(update.quantity_per_unit)
        association.quantity_per_unit = update.quantity_per_unit
    
    # Validate and update cost_item_id if provided
    if update.cost_item_id is not None:
        # Verify the new cost item exists and is added to this work
        cost_item_assoc = db.query(CostItemMaterialModel)\
            .filter(
                CostItemMaterialModel.work_id == work_id,
                CostItemMaterialModel.cost_item_id == update.cost_item_id,
                CostItemMaterialModel.material_id.is_(None)
            )\
            .first()
        
        if not cost_item_assoc:
            raise HTTPException(
                status_code=400, 
                detail="Cost item must be added to work before assigning materials to it"
            )
        
        # Check for duplicate (same work, cost_item, material combination)
        existing = db.query(CostItemMaterialModel)\
            .filter(
                CostItemMaterialModel.work_id == work_id,
                CostItemMaterialModel.cost_item_id == update.cost_item_id,
                CostItemMaterialModel.material_id == association.material_id,
                CostItemMaterialModel.id != association_id
            )\
            .first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="This material is already associated with the selected cost item in this work"
            )
        
        association.cost_item_id = update.cost_item_id
    
    db.commit()
    db.refresh(association)
    return association


@router.delete("/works/{work_id}/cost-items/{cost_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cost_item_from_work(
    work_id: int,
    cost_item_id: int,
    db: Session = Depends(get_db)
):
    """Remove cost item from work
    
    Validation:
    - Cannot delete if cost item has associated materials (Req 3.1, 3.2)
    """
    # Check if cost item has materials
    check_cost_item_has_materials(db, work_id, cost_item_id)
    
    # Delete cost item association
    db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.cost_item_id == cost_item_id,
            CostItemMaterialModel.material_id.is_(None)
        )\
        .delete()
    
    db.commit()


@router.delete("/works/{work_id}/materials/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_material_from_work(
    work_id: int,
    association_id: int,
    db: Session = Depends(get_db)
):
    """Remove material from work"""
    result = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.id == association_id,
            CostItemMaterialModel.work_id == work_id
        )\
        .delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Association not found")
    
    db.commit()

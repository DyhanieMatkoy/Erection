"""
Work composition validation utilities

This module provides validation functions for work composition operations
according to the requirements in the work-composition-form spec.
"""
from typing import Optional, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.data.models.sqlalchemy_models import (
    Work as WorkModel,
    CostItemMaterial as CostItemMaterialModel,
    CostItem as CostItemModel,
    Material as MaterialModel
)


def validate_work_name(name: Optional[str]) -> None:
    """
    Validate work name is not empty or whitespace-only.
    
    Requirements: 1.2, 11.1
    
    Args:
        name: The work name to validate
        
    Raises:
        HTTPException: If name is empty or whitespace-only
    """
    if not name or not name.strip():
        raise HTTPException(
            status_code=400,
            detail="Work name is required and cannot be empty or whitespace-only"
        )


def validate_group_work_constraints(is_group: bool, price: Optional[float], labor_rate: Optional[float]) -> None:
    """
    Validate that group works cannot have price or labor_rate.
    
    Requirements: 1.3, 11.2
    
    Args:
        is_group: Whether the work is a group
        price: The work price
        labor_rate: The work labor rate
        
    Raises:
        HTTPException: If group work has non-zero price or labor_rate
    """
    if is_group:
        if price and price != 0.0:
            raise HTTPException(
                status_code=400,
                detail="Group works cannot have a price. Set price to 0 or null."
            )
        if labor_rate and labor_rate != 0.0:
            raise HTTPException(
                status_code=400,
                detail="Group works cannot have a labor rate. Set labor_rate to 0 or null."
            )


def validate_quantity(quantity: Optional[float]) -> None:
    """
    Validate that quantity is greater than zero and numeric.
    
    Requirements: 4.4, 5.2, 11.3
    
    Args:
        quantity: The quantity to validate
        
    Raises:
        HTTPException: If quantity is not valid
    """
    if quantity is None:
        raise HTTPException(
            status_code=400,
            detail="Quantity is required"
        )
    
    try:
        quantity_float = float(quantity)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Quantity must be a valid number"
        )
    
    if quantity_float <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )


def check_duplicate_cost_item(db: Session, work_id: int, cost_item_id: int) -> None:
    """
    Check if cost item is already added to work.
    
    Requirements: 2.5
    
    Args:
        db: Database session
        work_id: The work ID
        cost_item_id: The cost item ID
        
    Raises:
        HTTPException: If cost item is already added to this work
    """
    existing = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.cost_item_id == cost_item_id,
            CostItemMaterialModel.material_id.is_(None)
        )\
        .first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This cost item is already added to this work"
        )


def check_duplicate_material(db: Session, work_id: int, cost_item_id: int, material_id: int) -> None:
    """
    Check if material is already added to this cost item in this work.
    
    Requirements: 4.4
    
    Args:
        db: Database session
        work_id: The work ID
        cost_item_id: The cost item ID
        material_id: The material ID
        
    Raises:
        HTTPException: If material is already added to this cost item in this work
    """
    existing = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.cost_item_id == cost_item_id,
            CostItemMaterialModel.material_id == material_id
        )\
        .first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This material is already added to this cost item in this work"
        )


def check_cost_item_has_materials(db: Session, work_id: int, cost_item_id: int) -> None:
    """
    Check if cost item has associated materials before deletion.
    
    Requirements: 3.1, 3.2
    
    Args:
        db: Database session
        work_id: The work ID
        cost_item_id: The cost item ID
        
    Raises:
        HTTPException: If cost item has associated materials
    """
    materials_count = db.query(CostItemMaterialModel)\
        .filter(
            CostItemMaterialModel.work_id == work_id,
            CostItemMaterialModel.cost_item_id == cost_item_id,
            CostItemMaterialModel.material_id.isnot(None)
        )\
        .count()
    
    if materials_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete cost item with associated materials. Delete materials first."
        )


def validate_parent_circular_reference(db: Session, work_id: Optional[int], parent_id: Optional[int]) -> None:
    """
    Validate that parent_id does not create a circular reference.
    
    A circular reference occurs when:
    - A work is set as its own parent
    - A work is set as a parent of one of its ancestors
    
    Requirements: 1.4, 15.3
    
    Args:
        db: Database session
        work_id: The work ID (None for new works)
        parent_id: The proposed parent ID
        
    Raises:
        HTTPException: If circular reference would be created
    """
    if parent_id is None:
        # No parent, no circular reference possible
        return
    
    if work_id is None:
        # New work, no circular reference possible
        return
    
    if work_id == parent_id:
        raise HTTPException(
            status_code=400,
            detail="A work cannot be its own parent"
        )
    
    # Check if parent_id is a descendant of work_id
    # We need to traverse up the tree from parent_id to see if we reach work_id
    visited: Set[int] = set()
    current_id = parent_id
    
    while current_id is not None:
        if current_id in visited:
            # We've hit a cycle in the existing data, but not involving our work
            break
        
        if current_id == work_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot set parent: would create circular reference. The selected parent is a descendant of this work."
            )
        
        visited.add(current_id)
        
        # Get the parent of current_id
        parent_work = db.query(WorkModel).filter(WorkModel.id == current_id).first()
        if parent_work:
            current_id = parent_work.parent_id
        else:
            # Parent doesn't exist, stop traversal
            break


def validate_work_exists(db: Session, work_id: int) -> WorkModel:
    """
    Validate that a work exists.
    
    Requirements: 13.1
    
    Args:
        db: Database session
        work_id: The work ID
        
    Returns:
        The work model
        
    Raises:
        HTTPException: If work doesn't exist
    """
    work = db.query(WorkModel).filter(WorkModel.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work


def validate_cost_item_exists(db: Session, cost_item_id: int) -> CostItemModel:
    """
    Validate that a cost item exists.
    
    Requirements: 13.2
    
    Args:
        db: Database session
        cost_item_id: The cost item ID
        
    Returns:
        The cost item model
        
    Raises:
        HTTPException: If cost item doesn't exist
    """
    cost_item = db.query(CostItemModel).filter(CostItemModel.id == cost_item_id).first()
    if not cost_item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    return cost_item


def validate_material_exists(db: Session, material_id: int) -> MaterialModel:
    """
    Validate that a material exists.
    
    Requirements: 13.3
    
    Args:
        db: Database session
        material_id: The material ID
        
    Returns:
        The material model
        
    Raises:
        HTTPException: If material doesn't exist
    """
    material = db.query(MaterialModel).filter(MaterialModel.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

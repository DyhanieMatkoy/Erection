"""
Work composition validation utilities for direct DB connections

This module provides validation functions for work composition operations
using direct database connections (not SQLAlchemy).
"""
from typing import Optional, Set
from fastapi import HTTPException


def validate_work_name_direct(name: Optional[str]) -> None:
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


def validate_group_work_constraints_direct(is_group: bool, price: Optional[float], labor_rate: Optional[float]) -> None:
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


def validate_parent_circular_reference_direct(db, work_id: Optional[int], parent_id: Optional[int]) -> None:
    """
    Validate that parent_id does not create a circular reference.
    
    A circular reference occurs when:
    - A work is set as its own parent
    - A work is set as a parent of one of its ancestors
    
    Requirements: 1.4, 15.3
    
    Args:
        db: Database connection
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
    cursor = db.cursor()
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
        cursor.execute("SELECT parent_id FROM works WHERE id = ?", (current_id,))
        row = cursor.fetchone()
        if row and row['parent_id']:
            current_id = row['parent_id']
        else:
            # No parent or parent doesn't exist, stop traversal
            break

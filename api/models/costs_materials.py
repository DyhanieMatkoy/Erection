"""
Cost Items and Materials models for API

This module defines Pydantic models for costs and materials related endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Unit Models
# ============================================================================

class UnitBase(BaseModel):
    """Base model for unit"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class UnitCreate(UnitBase):
    """Model for creating unit"""
    pass


class UnitUpdate(UnitBase):
    """Model for updating unit"""
    pass


class Unit(UnitBase):
    """Model for unit with ID"""
    id: int
    marked_for_deletion: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Cost Item Models
# ============================================================================

class CostItemBase(BaseModel):
    """Base model for cost item"""
    parent_id: Optional[int] = None
    code: Optional[str] = None
    description: str = Field(..., max_length=500)
    is_folder: bool = False
    price: float = Field(default=0.0, ge=0)
    unit: Optional[str] = None  # Legacy
    unit_id: Optional[int] = None
    labor_coefficient: float = Field(default=0.0, ge=0)


class CostItemCreate(CostItemBase):
    """Model for creating cost item"""
    pass


class CostItemUpdate(CostItemBase):
    """Model for updating cost item"""
    pass


class CostItem(CostItemBase):
    """Model for cost item with ID"""
    id: int
    unit_name: Optional[str] = None  # Joined from units table
    marked_for_deletion: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Material Models
# ============================================================================

class MaterialBase(BaseModel):
    """Base model for material"""
    code: Optional[str] = None
    description: str = Field(..., max_length=500)
    price: float = Field(default=0.0, ge=0)
    unit: Optional[str] = None  # Legacy
    unit_id: Optional[int] = None


class MaterialCreate(MaterialBase):
    """Model for creating material"""
    pass


class MaterialUpdate(MaterialBase):
    """Model for updating material"""
    pass


class Material(MaterialBase):
    """Model for material with ID"""
    id: int
    unit_name: Optional[str] = None  # Joined from units table
    marked_for_deletion: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Cost Item Material Association Models
# ============================================================================

class CostItemMaterialBase(BaseModel):
    """Base model for cost item material association"""
    work_id: int
    cost_item_id: int
    material_id: Optional[int] = None
    quantity_per_unit: float = Field(default=0.0, ge=0)


class CostItemMaterialCreate(CostItemMaterialBase):
    """Model for creating cost item material association"""
    pass


class CostItemMaterialUpdate(BaseModel):
    """Model for updating cost item material association"""
    quantity_per_unit: Optional[float] = Field(None, gt=0)
    cost_item_id: Optional[int] = None


class CostItemMaterialSimple(CostItemMaterialBase):
    """Simple model for cost item material association with ID (no nested objects)"""
    id: int
    
    class Config:
        from_attributes = True


class CostItemMaterial(CostItemMaterialBase):
    """Model for cost item material association with ID and nested objects"""
    id: int
    cost_item: Optional[CostItem] = None
    material: Optional[Material] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Work Composition Models
# ============================================================================

class WorkComposition(BaseModel):
    """Complete work composition with cost items and materials"""
    work_id: int
    work_name: str
    cost_items: List[CostItemMaterial] = []
    materials: List[CostItemMaterial] = []
    total_cost: float = 0.0


class WorkCompositionDetail(BaseModel):
    """Detailed work composition for UI"""
    work_id: int
    work_name: str
    work_code: Optional[str] = None
    work_unit: Optional[str] = None
    work_price: float = 0.0
    work_labor_rate: float = 0.0
    
    # Cost items (where material_id is NULL)
    cost_items: List[CostItemMaterial] = []
    
    # Materials (where material_id is NOT NULL)
    materials: List[CostItemMaterial] = []
    
    # Calculated totals
    total_cost_items_price: float = 0.0
    total_materials_cost: float = 0.0
    total_cost: float = 0.0

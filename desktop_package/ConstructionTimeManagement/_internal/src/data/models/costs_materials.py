"""Costs and Materials models"""
from dataclasses import dataclass


@dataclass
class CostItem:
    id: int = 0
    parent_id: int = None
    code: str = ""
    description: str = ""
    is_folder: bool = False
    price: float = 0.0
    unit: str = ""
    labor_coefficient: float = 0.0
    marked_for_deletion: bool = False


@dataclass
class Material:
    id: int = 0
    code: str = ""
    description: str = ""
    price: float = 0.0
    unit: str = ""
    marked_for_deletion: bool = False


@dataclass
class CostItemMaterial:
    id: int = 0
    work_id: int = 0
    cost_item_id: int = 0
    material_id: int = 0
    quantity_per_unit: float = 0.0
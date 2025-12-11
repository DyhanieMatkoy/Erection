"""Estimate model"""
from dataclasses import dataclass, field
from datetime import date
from typing import List
from .base_model import BaseModel


@dataclass
class EstimateLine:
    id: int = 0
    estimate_id: int = 0
    line_number: int = 0
    work_id: int = 0
    quantity: float = 0.0
    unit: str = ""
    price: float = 0.0
    labor_rate: float = 0.0
    sum: float = 0.0
    planned_labor: float = 0.0
    is_group: bool = False
    group_name: str = ""
    parent_group_id: int = 0
    is_collapsed: bool = False


@dataclass
class Estimate(BaseModel):
    number: str = ""
    date: date = field(default_factory=date.today)
    customer_id: int = 0
    object_id: int = 0
    contractor_id: int = 0
    responsible_id: int = 0
    total_sum: float = 0.0
    total_labor: float = 0.0
    lines: List[EstimateLine] = field(default_factory=list)

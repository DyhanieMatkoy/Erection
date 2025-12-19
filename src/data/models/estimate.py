"""Estimate model"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum
from .base_model import BaseModel


class EstimateType(Enum):
    """Estimate type enumeration"""
    GENERAL = "General"
    PLAN = "Plan"


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

    # Display fields (populated via joins)
    customer_name: str = ""
    object_name: str = ""
    contractor_name: str = ""
    responsible_name: str = ""
    
    # Hierarchy fields
    base_document_id: Optional[int] = None
    estimate_type: str = EstimateType.GENERAL.value
    
    total_sum: float = 0.0
    total_labor: float = 0.0
    lines: List[EstimateLine] = field(default_factory=list)
    
    # Hierarchy relationships (populated when needed)
    base_document: Optional['Estimate'] = None
    plan_estimates: List['Estimate'] = field(default_factory=list)
    
    @property
    def is_general(self) -> bool:
        """Check if this is a general estimate"""
        return self.estimate_type == EstimateType.GENERAL.value
    
    @property
    def is_plan(self) -> bool:
        """Check if this is a plan estimate"""
        return self.estimate_type == EstimateType.PLAN.value


@dataclass
class HierarchyNode:
    """Node in estimate hierarchy tree"""
    estimate: Estimate
    children: List['HierarchyNode'] = field(default_factory=list)
    depth: int = 0


@dataclass
class HierarchyTree:
    """Estimate hierarchy tree structure"""
    root: HierarchyNode
    total_nodes: int = 0
    max_depth: int = 0

"""Daily report model"""
from dataclasses import dataclass, field
from datetime import date
from typing import List
from .base_model import BaseModel


@dataclass
class DailyReportLine:
    id: int = 0
    daily_report_id: int = 0
    line_number: int = 0
    work_id: int = 0
    planned_labor: float = 0.0
    actual_labor: float = 0.0
    deviation_percent: float = 0.0
    executor_ids: List[int] = field(default_factory=list)
    is_group: bool = False
    group_name: str = ""
    parent_group_id: int = 0
    is_collapsed: bool = False


@dataclass
class DailyReport(BaseModel):
    date: date = field(default_factory=date.today)
    estimate_id: int = 0
    foreman_id: int = 0
    lines: List[DailyReportLine] = field(default_factory=list)

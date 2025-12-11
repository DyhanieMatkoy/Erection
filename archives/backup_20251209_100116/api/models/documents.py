"""
Document models for estimates and daily reports

This module defines Pydantic models for document-related API endpoints.
These models handle validation, serialization, and documentation for:
- Estimates (сметы) and their lines
- Daily reports (ежедневные отчеты) and their lines

The models follow a pattern of Base -> Create/Update -> Full model with ID.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


# Estimate Line Models
class EstimateLineBase(BaseModel):
    """Base model for estimate line"""
    line_number: int = Field(..., ge=1)
    work_id: Optional[int] = None
    quantity: float = Field(default=0, ge=0)
    unit: Optional[str] = None
    price: float = Field(default=0, ge=0)
    labor_rate: float = Field(default=0, ge=0)
    sum: float = Field(default=0, ge=0)
    planned_labor: float = Field(default=0, ge=0)
    is_group: bool = False
    group_name: Optional[str] = None
    parent_group_id: Optional[int] = None
    is_collapsed: bool = False


class EstimateLineCreate(EstimateLineBase):
    """Model for creating estimate line"""
    pass


class EstimateLine(EstimateLineBase):
    """Model for estimate line with ID"""
    id: int
    estimate_id: int
    work_name: Optional[str] = None  # Joined from works table
    
    class Config:
        from_attributes = True


# Estimate Models
class EstimateBase(BaseModel):
    """Base model for estimate"""
    number: str = Field(..., min_length=1, max_length=100)
    date: date
    customer_id: Optional[int] = None
    object_id: Optional[int] = None
    contractor_id: Optional[int] = None
    responsible_id: Optional[int] = None


class EstimateCreate(EstimateBase):
    """Model for creating estimate"""
    lines: List[EstimateLineCreate] = []


class EstimateUpdate(EstimateBase):
    """Model for updating estimate"""
    lines: Optional[List[EstimateLineCreate]] = None


class Estimate(EstimateBase):
    """Model for estimate with ID and computed fields"""
    id: int
    total_sum: float = 0
    total_labor: float = 0
    is_posted: bool = False
    posted_at: Optional[datetime] = None
    marked_for_deletion: bool = False
    created_at: datetime
    modified_at: datetime
    lines: List[EstimateLine] = []
    
    # Joined fields for display
    customer_name: Optional[str] = None
    object_name: Optional[str] = None
    contractor_name: Optional[str] = None
    responsible_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Daily Report Line Models
class DailyReportLineBase(BaseModel):
    """Base model for daily report line"""
    line_number: int = Field(..., ge=1)
    work_id: Optional[int] = None
    planned_labor: float = Field(default=0, ge=0)
    actual_labor: float = Field(default=0, ge=0)
    deviation_percent: float = 0
    executor_ids: List[int] = []
    is_group: bool = False
    group_name: Optional[str] = None
    parent_group_id: Optional[int] = None
    is_collapsed: bool = False
    
    @field_validator('planned_labor', 'actual_labor', 'deviation_percent', mode='before')
    @classmethod
    def convert_to_float(cls, v):
        """Convert non-numeric values to float"""
        if v is None or v == '':
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class DailyReportLineCreate(DailyReportLineBase):
    """Model for creating daily report line"""
    pass


class DailyReportLine(DailyReportLineBase):
    """Model for daily report line with ID"""
    id: int
    report_id: int
    work_name: Optional[str] = None  # Joined from works table
    executor_names: List[str] = []  # Joined from persons table
    
    class Config:
        from_attributes = True


# Daily Report Models
class DailyReportBase(BaseModel):
    """Base model for daily report"""
    date: date
    estimate_id: Optional[int] = None
    foreman_id: Optional[int] = None


class DailyReportCreate(DailyReportBase):
    """Model for creating daily report"""
    lines: List[DailyReportLineCreate] = []


class DailyReportUpdate(DailyReportBase):
    """Model for updating daily report"""
    lines: Optional[List[DailyReportLineCreate]] = None


class DailyReport(DailyReportBase):
    """Model for daily report with ID and computed fields"""
    id: int
    is_posted: bool = False
    posted_at: Optional[datetime] = None
    marked_for_deletion: bool = False
    created_at: datetime
    modified_at: datetime
    lines: List[DailyReportLine] = []
    
    # Joined fields for display
    estimate_number: Optional[str] = None
    foreman_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Timesheet Line Models
class TimesheetLineBase(BaseModel):
    """Base model for timesheet line"""
    line_number: int = Field(..., ge=1)
    employee_id: int
    hourly_rate: float = Field(default=0, ge=0)
    # Days dictionary: {1: 8.0, 2: 7.5, ...}
    days: dict[int, float] = Field(default_factory=dict)


class TimesheetLineCreate(TimesheetLineBase):
    """Model for creating timesheet line"""
    pass


class TimesheetLine(TimesheetLineBase):
    """Model for timesheet line with ID"""
    id: int
    timesheet_id: int
    total_hours: float = 0
    total_amount: float = 0
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Timesheet Models
class TimesheetBase(BaseModel):
    """Base model for timesheet"""
    number: str = Field(..., min_length=1, max_length=100)
    date: date
    object_id: Optional[int] = None
    estimate_id: Optional[int] = None
    foreman_id: Optional[int] = None
    month_year: str  # "YYYY-MM"


class TimesheetCreate(TimesheetBase):
    """Model for creating timesheet"""
    lines: List[TimesheetLineCreate] = []


class TimesheetUpdate(TimesheetBase):
    """Model for updating timesheet"""
    lines: Optional[List[TimesheetLineCreate]] = None


class Timesheet(TimesheetBase):
    """Model for timesheet with ID and computed fields"""
    id: int
    is_posted: bool = False
    posted_at: Optional[datetime] = None
    marked_for_deletion: bool = False
    created_at: datetime
    modified_at: datetime
    lines: List[TimesheetLine] = []
    
    # Joined fields for display
    object_name: Optional[str] = None
    estimate_number: Optional[str] = None
    foreman_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Payroll Register Models
class PayrollRecord(BaseModel):
    """Model for payroll register record"""
    recorder_type: str
    recorder_id: int
    line_number: int
    period: date
    object_id: Optional[int] = None
    estimate_id: Optional[int] = None
    employee_id: int
    work_date: date
    hours_worked: float = Field(default=0, ge=0)
    amount: float = Field(default=0, ge=0)

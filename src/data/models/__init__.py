"""Data models package

This package contains both dataclass models (for backward compatibility)
and SQLAlchemy ORM models (for multi-database support).
"""

# Dataclass models (existing)
from .user import User as UserDataclass
from .references import (
    Person as PersonDataclass,
    Organization as OrganizationDataclass,
    Counterparty as CounterpartyDataclass,
    Object as ObjectDataclass,
    Work as WorkDataclass
)
from .estimate import Estimate as EstimateDataclass, EstimateLine as EstimateLineDataclass
from .daily_report import DailyReport as DailyReportDataclass, DailyReportLine as DailyReportLineDataclass

# SQLAlchemy ORM models
from .sqlalchemy_models import (
    Base,
    User,
    Person,
    Organization,
    Counterparty,
    Object,
    Work,
    Estimate,
    EstimateLine,
    DailyReport,
    DailyReportLine,
    DailyReportExecutor,
    Timesheet,
    TimesheetLine,
    WorkExecutionRegister,
    PayrollRegister,
    UserSetting,
    Constant,
    Material,
    CostItem,
    Unit,
    WorkSpecification
)

# Synchronization models
from .sync_models import (
    SyncNode,
    SyncChange,
    ObjectVersionHistory,
    SyncOperation
)

__all__ = [
    # SQLAlchemy Base
    'Base',
    
    # SQLAlchemy ORM Models
    'User',
    'Person',
    'Organization',
    'Counterparty',
    'Object',
    'Work',
    'Estimate',
    'EstimateLine',
    'DailyReport',
    'DailyReportLine',
    'DailyReportExecutor',
    'Timesheet',
    'TimesheetLine',
    'WorkExecutionRegister',
    'PayrollRegister',
    'UserSetting',
    'Constant',
    'Material',
    'CostItem',
    'Unit',
    'WorkSpecification',
    
    # Synchronization Models
    'SyncNode',
    'SyncChange',
    'ObjectVersionHistory',
    'SyncOperation',
    
    # Dataclass Models (for backward compatibility)
    'UserDataclass',
    'PersonDataclass',
    'OrganizationDataclass',
    'CounterpartyDataclass',
    'ObjectDataclass',
    'WorkDataclass',
    'EstimateDataclass',
    'EstimateLineDataclass',
    'DailyReportDataclass',
    'DailyReportLineDataclass',
]

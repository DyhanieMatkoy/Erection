"""SQLAlchemy ORM models for all database tables

This module defines all database tables as SQLAlchemy ORM models,
providing a unified interface for database operations across
SQLite, PostgreSQL, and Microsoft SQL Server backends.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean,
    ForeignKey, Text, UniqueConstraint, Index, DECIMAL, Computed
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum
import uuid

from ..sqlalchemy_base import Base


class EstimateType(Enum):
    """Estimate type enumeration"""
    GENERAL = "General"
    PLAN = "Plan"


# ============================================================================
# User and Authentication Models
# ============================================================================

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # TODO: Add synchronization fields after migration
    # uuid = Column(String(36), unique=True, nullable=False, default=uuid.uuid4, index=True)
    # updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    # is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    person = relationship("Person", back_populates="user", uselist=False)
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


# ============================================================================
# Reference Models (Справочники)
# ============================================================================

class Person(Base):
    """Person model (employees, foremen, etc.)"""
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    position = Column(String(255))
    phone = Column(String(50))
    hourly_rate = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey('users.id'))
    parent_id = Column(Integer, ForeignKey('persons.id'))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    user = relationship("User", back_populates="person")
    parent = relationship("Person", remote_side=[id], backref="children")
    
    # Documents where person is responsible
    estimates_responsible = relationship("Estimate", foreign_keys="Estimate.responsible_id", back_populates="responsible")
    daily_reports_foreman = relationship("DailyReport", foreign_keys="DailyReport.foreman_id", back_populates="foreman")
    timesheets_foreman = relationship("Timesheet", foreign_keys="Timesheet.foreman_id", back_populates="foreman")
    
    # Register entries
    payroll_entries = relationship("PayrollRegister", back_populates="employee")
    timesheet_lines = relationship("TimesheetLine", back_populates="employee")
    
    def __repr__(self):
        return f"<Person(id={self.id}, full_name='{self.full_name}')>"


class Organization(Base):
    """Organization model (contractors, companies)"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(50))
    default_responsible_id = Column(Integer, ForeignKey('persons.id'))
    parent_id = Column(Integer, ForeignKey('organizations.id'))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    default_responsible = relationship("Person", foreign_keys=[default_responsible_id])
    parent = relationship("Organization", remote_side=[id], backref="children")
    estimates = relationship("Estimate", back_populates="contractor")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class Counterparty(Base):
    """Counterparty model (customers, suppliers)"""
    __tablename__ = 'counterparties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(50))
    contact_person = Column(String(255))
    phone = Column(String(50))
    parent_id = Column(Integer, ForeignKey('counterparties.id'))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    parent = relationship("Counterparty", remote_side=[id], backref="children")
    estimates = relationship("Estimate", back_populates="customer")
    objects = relationship("Object", back_populates="owner")
    
    def __repr__(self):
        return f"<Counterparty(id={self.id}, name='{self.name}')>"


class Object(Base):
    """Construction object model"""
    __tablename__ = 'objects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey('counterparties.id'))
    address = Column(Text)
    parent_id = Column(Integer, ForeignKey('objects.id'))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    owner = relationship("Counterparty", back_populates="objects")
    parent = relationship("Object", remote_side=[id], backref="children")
    estimates = relationship("Estimate", back_populates="object")
    timesheets = relationship("Timesheet", back_populates="object")
    work_execution_entries = relationship("WorkExecutionRegister", back_populates="object")
    payroll_entries = relationship("PayrollRegister", back_populates="object")
    
    def __repr__(self):
        return f"<Object(id={self.id}, name='{self.name}')>"


class Work(Base):
    """Work type model (types of construction work)"""
    __tablename__ = 'works'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    code = Column(String(50))
    # Legacy unit column removed - use unit_id foreign key relationship instead
    unit_id = Column(Integer, ForeignKey('units.id'), index=True)  # Primary unit reference
    price = Column(Float, default=0.0)
    labor_rate = Column(Float, default=0.0)
    parent_id = Column(Integer, ForeignKey('works.id'), index=True)
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    parent = relationship("Work", remote_side=[id], backref="children")
    unit_ref = relationship("Unit", foreign_keys=[unit_id], overlaps="works")
    estimate_lines = relationship("EstimateLine", back_populates="work")
    daily_report_lines = relationship("DailyReportLine", back_populates="work")
    work_execution_entries = relationship("WorkExecutionRegister", back_populates="work")
    cost_item_materials = relationship("CostItemMaterial", back_populates="work",
                                      cascade="all, delete, delete-orphan")
    specifications = relationship("WorkSpecification", back_populates="work",
                                 cascade="all, delete, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_works_unit_id', 'unit_id'),
        Index('idx_works_parent_id', 'parent_id'),
        Index('idx_works_uuid', 'uuid'),
        Index('idx_works_name', 'name'),
    )
    
    @property
    def effective_unit_name(self):
        """Get the unit name from unit_id foreign key relationship"""
        if self.unit_ref:
            return self.unit_ref.name
        return None
    
    @property
    def has_unit_reference(self):
        """Check if work has a proper unit reference (unit_id)"""
        return self.unit_id is not None
    
    @property
    def needs_unit_migration(self):
        """Migration is complete - all works should use unit_id"""
        return False  # Migration completed, legacy unit column removed
    
    def validate_unit_reference(self):
        """Validate that unit_id references a valid unit record"""
        if self.unit_id is not None and self.unit_ref is None:
            raise ValueError(f"Work {self.id} has invalid unit_id {self.unit_id}")
    
    def validate_hierarchy(self):
        """Validate that parent-child relationships don't create circular references"""
        if self.parent_id is None:
            return True
        
        visited = set()
        current_id = self.parent_id
        
        while current_id is not None:
            if current_id == self.id:
                raise ValueError(f"Circular reference detected: Work {self.id} cannot be its own ancestor")
            if current_id in visited:
                raise ValueError(f"Circular reference detected in work hierarchy involving work {current_id}")
            
            visited.add(current_id)
            # This would need to be implemented with a database query in practice
            # For now, we'll assume the validation is done at the service layer
            break
        
        return True
    
    def __repr__(self):
        return f"<Work(id={self.id}, name='{self.name}', unit_id={self.unit_id})>"


# ============================================================================
# Document Models (Документы)
# ============================================================================

class Estimate(Base):
    """Estimate document model (Смета)"""
    __tablename__ = 'estimates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('counterparties.id'))
    object_id = Column(Integer, ForeignKey('objects.id'))
    contractor_id = Column(Integer, ForeignKey('organizations.id'))
    responsible_id = Column(Integer, ForeignKey('persons.id'), index=True)
    
    # Hierarchy fields
    base_document_id = Column(Integer, ForeignKey('estimates.id'), nullable=True, index=True)
    estimate_type = Column(String(20), nullable=False, default='General', index=True)
    
    total_sum = Column(Float, default=0.0)
    total_labor = Column(Float, default=0.0)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    customer = relationship("Counterparty", back_populates="estimates")
    object = relationship("Object", back_populates="estimates")
    contractor = relationship("Organization", back_populates="estimates")
    responsible = relationship("Person", foreign_keys=[responsible_id], back_populates="estimates_responsible")
    
    # Hierarchy relationships
    base_document = relationship("Estimate", remote_side=[id], backref="plan_estimates")
    
    lines = relationship("EstimateLine", back_populates="estimate", cascade="all, delete-orphan", order_by="EstimateLine.line_number")
    daily_reports = relationship("DailyReport", back_populates="estimate")
    timesheets = relationship("Timesheet", back_populates="estimate")
    work_execution_entries = relationship("WorkExecutionRegister", back_populates="estimate")
    payroll_entries = relationship("PayrollRegister", back_populates="estimate")
    
    @property
    def is_general(self) -> bool:
        """Check if this is a general estimate"""
        return self.estimate_type == EstimateType.GENERAL.value
    
    @property
    def is_plan(self) -> bool:
        """Check if this is a plan estimate"""
        return self.estimate_type == EstimateType.PLAN.value
    
    def __repr__(self):
        return f"<Estimate(id={self.id}, number='{self.number}', date={self.date}, type='{self.estimate_type}')>"


class EstimateLine(Base):
    """Estimate line model (line item in estimate)"""
    __tablename__ = 'estimate_lines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    estimate_id = Column(Integer, ForeignKey('estimates.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    work_id = Column(Integer, ForeignKey('works.id'))
    quantity = Column(Float, default=0.0)
    unit = Column(String(50))
    price = Column(Float, default=0.0)
    labor_rate = Column(Float, default=0.0)
    sum = Column(Float, default=0.0)
    planned_labor = Column(Float, default=0.0)
    is_group = Column(Boolean, default=False)
    group_name = Column(String(500))
    parent_group_id = Column(Integer, ForeignKey('estimate_lines.id'))
    is_collapsed = Column(Boolean, default=False)
    material_id = Column(Integer, ForeignKey('materials.id'))
    material_quantity = Column(Float, default=0.0)
    material_price = Column(Float, default=0.0)
    material_sum = Column(Float, default=0.0)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    estimate = relationship("Estimate", back_populates="lines")
    work = relationship("Work", back_populates="estimate_lines")
    parent_group = relationship("EstimateLine", remote_side=[id], backref="children")
    material = relationship("Material", back_populates="estimate_lines")
    
    def __repr__(self):
        return f"<EstimateLine(id={self.id}, estimate_id={self.estimate_id}, line_number={self.line_number})>"


class DailyReport(Base):
    """Daily report document model (Ежедневный отчет)"""
    __tablename__ = 'daily_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(50))
    date = Column(Date, nullable=False, index=True)
    estimate_id = Column(Integer, ForeignKey('estimates.id'), index=True)
    foreman_id = Column(Integer, ForeignKey('persons.id'))
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    estimate = relationship("Estimate", back_populates="daily_reports")
    foreman = relationship("Person", foreign_keys=[foreman_id], back_populates="daily_reports_foreman")
    lines = relationship("DailyReportLine", back_populates="report", cascade="all, delete-orphan", order_by="DailyReportLine.line_number")
    
    def __repr__(self):
        return f"<DailyReport(id={self.id}, date={self.date}, estimate_id={self.estimate_id})>"


class DailyReportLine(Base):
    """Daily report line model"""
    __tablename__ = 'daily_report_lines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_report_id = Column(Integer, ForeignKey('daily_reports.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    work_id = Column(Integer, ForeignKey('works.id'))
    planned_labor = Column(Float, default=0.0)
    actual_labor = Column(Float, default=0.0)
    deviation_percent = Column(Float, default=0.0)
    is_group = Column(Boolean, default=False)
    group_name = Column(String(500))
    parent_group_id = Column(Integer, ForeignKey('daily_report_lines.id'))
    is_collapsed = Column(Boolean, default=False)
    material_id = Column(Integer, ForeignKey('materials.id'))
    planned_material_quantity = Column(Float, default=0.0)
    actual_material_quantity = Column(Float, default=0.0)
    material_deviation_percent = Column(Float, default=0.0)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    report = relationship("DailyReport", back_populates="lines")
    work = relationship("Work", back_populates="daily_report_lines")
    parent_group = relationship("DailyReportLine", remote_side=[id], backref="children")
    executors = relationship("DailyReportExecutor", back_populates="report_line", cascade="all, delete-orphan")
    material = relationship("Material", back_populates="daily_report_lines")
    
    def __repr__(self):
        return f"<DailyReportLine(id={self.id}, daily_report_id={self.daily_report_id}, line_number={self.line_number})>"


class DailyReportExecutor(Base):
    """Daily report executor association (many-to-many between report lines and persons)"""
    __tablename__ = 'daily_report_executors'
    
    report_line_id = Column(Integer, ForeignKey('daily_report_lines.id', ondelete='CASCADE'), primary_key=True)
    executor_id = Column(Integer, ForeignKey('persons.id'), primary_key=True)
    
    # Relationships
    report_line = relationship("DailyReportLine", back_populates="executors")
    executor = relationship("Person")
    
    def __repr__(self):
        return f"<DailyReportExecutor(report_line_id={self.report_line_id}, executor_id={self.executor_id})>"


class Timesheet(Base):
    """Timesheet document model (Табель учета рабочего времени)"""
    __tablename__ = 'timesheets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True)
    object_id = Column(Integer, ForeignKey('objects.id'), index=True)
    estimate_id = Column(Integer, ForeignKey('estimates.id'), index=True)
    foreman_id = Column(Integer, ForeignKey('persons.id'), index=True)
    month_year = Column(String(20), nullable=False)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    object = relationship("Object", back_populates="timesheets")
    estimate = relationship("Estimate", back_populates="timesheets")
    foreman = relationship("Person", foreign_keys=[foreman_id], back_populates="timesheets_foreman")
    lines = relationship("TimesheetLine", back_populates="timesheet", cascade="all, delete-orphan", order_by="TimesheetLine.line_number")
    
    def __repr__(self):
        return f"<Timesheet(id={self.id}, number='{self.number}', month_year='{self.month_year}')>"


class TimesheetLine(Base):
    """Timesheet line model (employee hours for each day of month)"""
    __tablename__ = 'timesheet_lines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timesheet_id = Column(Integer, ForeignKey('timesheets.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    employee_id = Column(Integer, ForeignKey('persons.id'), index=True)
    hourly_rate = Column(Float, default=0.0)
    
    # Days of the month (31 columns for each day)
    day_01 = Column(Float, default=0.0)
    day_02 = Column(Float, default=0.0)
    day_03 = Column(Float, default=0.0)
    day_04 = Column(Float, default=0.0)
    day_05 = Column(Float, default=0.0)
    day_06 = Column(Float, default=0.0)
    day_07 = Column(Float, default=0.0)
    day_08 = Column(Float, default=0.0)
    day_09 = Column(Float, default=0.0)
    day_10 = Column(Float, default=0.0)
    day_11 = Column(Float, default=0.0)
    day_12 = Column(Float, default=0.0)
    day_13 = Column(Float, default=0.0)
    day_14 = Column(Float, default=0.0)
    day_15 = Column(Float, default=0.0)
    day_16 = Column(Float, default=0.0)
    day_17 = Column(Float, default=0.0)
    day_18 = Column(Float, default=0.0)
    day_19 = Column(Float, default=0.0)
    day_20 = Column(Float, default=0.0)
    day_21 = Column(Float, default=0.0)
    day_22 = Column(Float, default=0.0)
    day_23 = Column(Float, default=0.0)
    day_24 = Column(Float, default=0.0)
    day_25 = Column(Float, default=0.0)
    day_26 = Column(Float, default=0.0)
    day_27 = Column(Float, default=0.0)
    day_28 = Column(Float, default=0.0)
    day_29 = Column(Float, default=0.0)
    day_30 = Column(Float, default=0.0)
    day_31 = Column(Float, default=0.0)
    
    total_hours = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    timesheet = relationship("Timesheet", back_populates="lines")
    employee = relationship("Person", back_populates="timesheet_lines")
    
    def __repr__(self):
        return f"<TimesheetLine(id={self.id}, timesheet_id={self.timesheet_id}, employee_id={self.employee_id})>"


# ============================================================================
# Register Models (Регистры накопления)
# ============================================================================

class WorkExecutionRegister(Base):
    """Work execution accumulation register (Регистр накопления ВыполнениеРабот)"""
    __tablename__ = 'work_execution_register'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recorder_type = Column(String(50), nullable=False, index=True)
    recorder_id = Column(Integer, nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    period = Column(Date, nullable=False, index=True)
    object_id = Column(Integer, ForeignKey('objects.id'), index=True)
    estimate_id = Column(Integer, ForeignKey('estimates.id'), index=True)
    work_id = Column(Integer, ForeignKey('works.id'), index=True)
    quantity_income = Column(Float, default=0.0)
    quantity_expense = Column(Float, default=0.0)
    sum_income = Column(Float, default=0.0)
    sum_expense = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    object = relationship("Object", back_populates="work_execution_entries")
    estimate = relationship("Estimate", back_populates="work_execution_entries")
    work = relationship("Work", back_populates="work_execution_entries")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_register_recorder', 'recorder_type', 'recorder_id'),
        Index('idx_register_dimensions', 'period', 'object_id', 'estimate_id', 'work_id'),
    )
    
    def __repr__(self):
        return f"<WorkExecutionRegister(id={self.id}, recorder_type='{self.recorder_type}', recorder_id={self.recorder_id})>"


class PayrollRegister(Base):
    """Payroll accumulation register (Регистр начислений и удержаний)"""
    __tablename__ = 'payroll_register'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recorder_type = Column(String(50), nullable=False, index=True)
    recorder_id = Column(Integer, nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    period = Column(Date, nullable=False, index=True)
    object_id = Column(Integer, ForeignKey('objects.id'), index=True)
    estimate_id = Column(Integer, ForeignKey('estimates.id'), index=True)
    employee_id = Column(Integer, ForeignKey('persons.id'), index=True)
    work_date = Column(Date, nullable=False, index=True)
    hours_worked = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    object = relationship("Object", back_populates="payroll_entries")
    estimate = relationship("Estimate", back_populates="payroll_entries")
    employee = relationship("Person", back_populates="payroll_entries")
    
    # Composite indices and constraints
    __table_args__ = (
        Index('idx_payroll_recorder', 'recorder_type', 'recorder_id'),
        Index('idx_payroll_dimensions', 'period', 'object_id', 'estimate_id', 'employee_id'),
        UniqueConstraint('object_id', 'estimate_id', 'employee_id', 'work_date', name='uq_payroll_entry'),
    )
    
    def __repr__(self):
        return f"<PayrollRegister(id={self.id}, employee_id={self.employee_id}, work_date={self.work_date})>"


# ============================================================================
# System Models
# ============================================================================

class UserSetting(Base):
    """User settings model (form preferences, etc.)"""
    __tablename__ = 'user_settings'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    form_name = Column(String(100), primary_key=True)
    setting_key = Column(String(100), primary_key=True)
    setting_value = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSetting(user_id={self.user_id}, form_name='{self.form_name}', key='{self.setting_key}')>"


class UserTablePartSettings(Base):
    """User table part settings model for document table parts configuration"""
    __tablename__ = 'user_table_part_settings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True)
    table_part_id = Column(String(100), nullable=False, index=True)
    settings_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Unique constraint for user + document_type + table_part_id
    __table_args__ = (
        UniqueConstraint('user_id', 'document_type', 'table_part_id', name='uq_user_table_part_settings'),
        Index('idx_user_table_part_settings_lookup', 'user_id', 'document_type', 'table_part_id'),
    )
    
    def __repr__(self):
        return f"<UserTablePartSettings(id='{self.id}', user_id={self.user_id}, document_type='{self.document_type}', table_part_id='{self.table_part_id}')>"


class TablePartCommandConfig(Base):
    """Table part command configuration for customizing command panels"""
    __tablename__ = 'table_part_command_config'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_type = Column(String(100), nullable=False, index=True)
    table_part_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # NULL for global settings
    command_id = Column(String(100), nullable=False, index=True)
    is_visible = Column(Boolean, default=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    is_in_more_menu = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Unique constraint for user + document_type + table_part_id + command_id
    __table_args__ = (
        UniqueConstraint('document_type', 'table_part_id', 'user_id', 'command_id', name='uq_table_part_command_config'),
        Index('idx_table_part_command_config_lookup', 'document_type', 'table_part_id', 'user_id'),
    )
    
    def __repr__(self):
        return f"<TablePartCommandConfig(id='{self.id}', document_type='{self.document_type}', table_part_id='{self.table_part_id}', command_id='{self.command_id}')>"


class Constant(Base):
    """System constants model (key-value configuration)"""
    __tablename__ = 'constants'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    
    def __repr__(self):
        return f"<Constant(key='{self.key}', value='{self.value}')>"


# ============================================================================
# Costs and Materials Models
# ============================================================================

class CostItem(Base):
    """Cost item model (Элементы затрат)"""
    __tablename__ = 'cost_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('cost_items.id'))
    code = Column(String(50))
    description = Column(String(500))
    is_folder = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    unit = Column(String(50))  # Сохраняем для обратной совместимости
    unit_id = Column(Integer, ForeignKey('units.id'))
    labor_coefficient = Column(Float, default=0.0)
    marked_for_deletion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    parent = relationship("CostItem", remote_side=[id], backref="children")
    materials = relationship("Material", secondary="cost_item_materials", backref="cost_items")
    unit_ref = relationship("Unit", back_populates="cost_items")
    
    def __repr__(self):
        return f"<CostItem(id={self.id}, code='{self.code}', description='{self.description}')>"


class Material(Base):
    """Material model (Материалы)"""
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50))
    description = Column(String(500))
    price = Column(Float, default=0.0)
    unit = Column(String(50))  # Сохраняем для обратной совместимости
    unit_id = Column(Integer, ForeignKey('units.id'))
    marked_for_deletion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    estimate_lines = relationship("EstimateLine", back_populates="material")
    daily_report_lines = relationship("DailyReportLine", back_populates="material")
    unit_ref = relationship("Unit", back_populates="materials")
    
    def __repr__(self):
        return f"<Material(id={self.id}, code='{self.code}', description='{self.description}')>"


class Unit(Base):
    """Unit model (Единицы измерения)"""
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    marked_for_deletion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    materials = relationship("Material", back_populates="unit_ref")
    cost_items = relationship("CostItem", back_populates="unit_ref")
    works = relationship("Work", foreign_keys="Work.unit_id", overlaps="unit_ref")
    
    def __repr__(self):
        return f"<Unit(id={self.id}, name='{self.name}')>"


class CostItemMaterial(Base):
    """Association table for work, cost items and materials"""
    __tablename__ = 'cost_item_materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False, index=True)
    cost_item_id = Column(Integer, ForeignKey('cost_items.id', ondelete='CASCADE'), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('materials.id', ondelete='CASCADE'), index=True)
    quantity_per_unit = Column(Float, default=0.0)
    
    # Relationships
    work = relationship("Work", back_populates="cost_item_materials")
    cost_item = relationship("CostItem", overlaps="cost_items,materials")
    material = relationship("Material", overlaps="cost_items,materials")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('work_id', 'cost_item_id', 'material_id', name='uq_work_cost_item_material'),
        Index('idx_cost_item_material_work', 'work_id'),
        Index('idx_cost_item_material_cost_item', 'cost_item_id'),
        Index('idx_cost_item_material_material', 'material_id'),
    )
    
    def __repr__(self):
        return f"<CostItemMaterial(id={self.id}, work_id={self.work_id}, cost_item_id={self.cost_item_id}, material_id={self.material_id})>"


class WorkSpecification(Base):
    """Work specification model (components required for work execution)"""
    __tablename__ = 'work_specifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    component_type = Column(String(20), nullable=False) # 'Material', 'Labor', 'Equipment', 'Other'
    component_name = Column(String(500), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'))
    material_id = Column(Integer, ForeignKey('materials.id'))
    consumption_rate = Column(DECIMAL(15,6), nullable=False, default=0)
    unit_price = Column(DECIMAL(15,2), nullable=False, default=0)
    total_cost = Column(DECIMAL(15,2), Computed('consumption_rate * unit_price', persisted=True))
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    marked_for_deletion = Column(Boolean, default=False)
    
    # Synchronization fields
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    work = relationship("Work", back_populates="specifications")
    unit_ref = relationship("Unit")
    material_ref = relationship("Material")
    
    __table_args__ = (
        Index('idx_work_specifications_work_id', 'work_id'),
        Index('idx_work_specifications_component_type', 'component_type'),
        Index('idx_work_specifications_material_id', 'material_id'),
    )
    
    def __repr__(self):
        return f"<WorkSpecification(id={self.id}, work_id={self.work_id}, name='{self.component_name}')>"


class WorkUnitMigration(Base):
    """Work unit migration tracking table"""
    __tablename__ = 'work_unit_migration'
    
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    legacy_unit = Column(String(50))
    matched_unit_id = Column(Integer, ForeignKey('units.id'))
    migration_status = Column(String(20), nullable=False, default='pending')  # 'pending', 'matched', 'manual', 'completed'
    confidence_score = Column(Float, default=0.0)  # Matching confidence (0.0 to 1.0)
    manual_review_reason = Column(String(255))  # Reason for manual review
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    work = relationship("Work")
    matched_unit = relationship("Unit", foreign_keys=[matched_unit_id])
    
    __table_args__ = (
        Index('idx_work_unit_migration_status', 'migration_status'),
        Index('idx_work_unit_migration_legacy_unit', 'legacy_unit'),
    )
    
    def __repr__(self):
        return f"<WorkUnitMigration(work_id={self.work_id}, legacy_unit='{self.legacy_unit}', status='{self.migration_status}')>"

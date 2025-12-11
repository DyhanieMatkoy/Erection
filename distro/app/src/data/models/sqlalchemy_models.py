"""SQLAlchemy ORM models for all database tables

This module defines all database tables as SQLAlchemy ORM models,
providing a unified interface for database operations across
SQLite, PostgreSQL, and Microsoft SQL Server backends.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date

from ..sqlalchemy_base import Base


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
    unit = Column(String(50))
    price = Column(Float, default=0.0)
    labor_rate = Column(Float, default=0.0)
    parent_id = Column(Integer, ForeignKey('works.id'))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    parent = relationship("Work", remote_side=[id], backref="children")
    estimate_lines = relationship("EstimateLine", back_populates="work")
    daily_report_lines = relationship("DailyReportLine", back_populates="work")
    work_execution_entries = relationship("WorkExecutionRegister", back_populates="work")
    
    def __repr__(self):
        return f"<Work(id={self.id}, name='{self.name}')>"


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
    total_sum = Column(Float, default=0.0)
    total_labor = Column(Float, default=0.0)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    marked_for_deletion = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Counterparty", back_populates="estimates")
    object = relationship("Object", back_populates="estimates")
    contractor = relationship("Organization", back_populates="estimates")
    responsible = relationship("Person", foreign_keys=[responsible_id], back_populates="estimates_responsible")
    lines = relationship("EstimateLine", back_populates="estimate", cascade="all, delete-orphan", order_by="EstimateLine.line_number")
    daily_reports = relationship("DailyReport", back_populates="estimate")
    timesheets = relationship("Timesheet", back_populates="estimate")
    work_execution_entries = relationship("WorkExecutionRegister", back_populates="estimate")
    payroll_entries = relationship("PayrollRegister", back_populates="estimate")
    
    def __repr__(self):
        return f"<Estimate(id={self.id}, number='{self.number}', date={self.date})>"


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
    
    # Relationships
    estimate = relationship("Estimate", back_populates="lines")
    work = relationship("Work", back_populates="estimate_lines")
    parent_group = relationship("EstimateLine", remote_side=[id], backref="children")
    
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
    report_id = Column(Integer, ForeignKey('daily_reports.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    work_id = Column(Integer, ForeignKey('works.id'))
    planned_labor = Column(Float, default=0.0)
    actual_labor = Column(Float, default=0.0)
    deviation_percent = Column(Float, default=0.0)
    is_group = Column(Boolean, default=False)
    group_name = Column(String(500))
    parent_group_id = Column(Integer, ForeignKey('daily_report_lines.id'))
    is_collapsed = Column(Boolean, default=False)
    
    # Relationships
    report = relationship("DailyReport", back_populates="lines")
    work = relationship("Work", back_populates="daily_report_lines")
    parent_group = relationship("DailyReportLine", remote_side=[id], backref="children")
    executors = relationship("DailyReportExecutor", back_populates="report_line", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DailyReportLine(id={self.id}, report_id={self.report_id}, line_number={self.line_number})>"


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


class Constant(Base):
    """System constants model (key-value configuration)"""
    __tablename__ = 'constants'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    
    def __repr__(self):
        return f"<Constant(key='{self.key}', value='{self.value}')>"

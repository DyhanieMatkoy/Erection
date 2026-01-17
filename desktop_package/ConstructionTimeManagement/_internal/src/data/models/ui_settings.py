from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..sqlalchemy_base import Base

class UserFormSettings(Base):
    """
    User form settings table
    Stores configuration for columns, filters, etc.
    """
    __tablename__ = 'user_form_settings'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    form_id = Column(String(100), nullable=False)
    settings_type = Column(String(50), nullable=False) # 'columns', 'filters', 'commands', 'daterange'
    settings_data = Column(JSON, nullable=False) # JSONB in Postgres, JSON in SQLite/others
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to User
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'form_id', 'settings_type', name='uq_user_form_settings'),
        Index('idx_user_form_settings_lookup', 'user_id', 'form_id'),
    )

    def __repr__(self):
        return f"<UserFormSettings(user_id={self.user_id}, form_id='{self.form_id}', type='{self.settings_type}')>"


class FormCommandConfiguration(Base):
    """
    Command configuration table
    Stores visibility and ordering of commands in forms
    """
    __tablename__ = 'form_command_configuration'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # NULL for global/default config
    command_id = Column(String(100), nullable=False)
    is_visible = Column(Boolean, default=True)
    is_enabled = Column(Boolean, default=True)
    position = Column(Integer, nullable=True)
    is_in_more_menu = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to User
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('form_id', 'user_id', 'command_id', name='uq_form_command_config'),
        Index('idx_form_command_config', 'form_id', 'user_id'),
    )

    def __repr__(self):
        return f"<FormCommandConfiguration(form_id='{self.form_id}', command_id='{self.command_id}')>"


class FormColumnRule(Base):
    """
    Admin rules for form columns (access control and mandatory status).
    """
    __tablename__ = 'form_column_rules'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = Column(String(100), nullable=False)
    column_id = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False) # 'all', 'admin', 'manager', 'foreman', 'executor'
    
    # Rule types
    is_mandatory = Column(Boolean, default=False) # User cannot hide
    is_restricted = Column(Boolean, default=False) # User cannot see (access denied)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('form_id', 'column_id', 'role', name='uq_form_column_rules'),
        Index('idx_form_column_rules', 'form_id', 'role'),
    )

    def __repr__(self):
        return f"<FormColumnRule(form='{self.form_id}', col='{self.column_id}', role='{self.role}')>"


class FormFormattingRule(Base):
    """
    Admin conditional formatting rules.
    Requirement 6.3.
    """
    __tablename__ = 'form_formatting_rules'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    
    # Condition: {"field": "status", "operator": "eq", "value": "Draft"}
    condition = Column(JSON, nullable=False)
    
    # Style: {"background": "#FF0000", "font_bold": True}
    style = Column(JSON, nullable=False)
    
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_form_formatting_rules', 'form_id'),
    )

    def __repr__(self):
        return f"<FormFormattingRule(form='{self.form_id}', name='{self.name}')>"

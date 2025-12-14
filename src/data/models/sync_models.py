"""Synchronization models for data sync system

This module defines the database models for the synchronization system,
including nodes, change tracking, and version history.
"""

from sqlalchemy import (
    Column, String, DateTime, BigInteger, Text, Enum, JSON, Index,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..sqlalchemy_base import Base


class SyncOperation(enum.Enum):
    """Enumeration for sync operation types"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SyncNode(Base):
    """Represents a node in the synchronization network"""
    __tablename__ = 'sync_nodes'
    
    # Use String(36) for compatibility across all databases
    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    last_sync_in = Column(DateTime(timezone=True), nullable=True)
    last_sync_out = Column(DateTime(timezone=True), nullable=True)
    received_packet_no = Column(BigInteger, nullable=True)
    sent_packet_no = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    outgoing_changes = relationship("SyncChange", foreign_keys="SyncChange.node_id", back_populates="target_node")
    incoming_changes = relationship("ObjectVersionHistory", foreign_keys="ObjectVersionHistory.source_node_id", back_populates="source_node")
    
    def __repr__(self):
        return f"<SyncNode(id='{self.id}', code='{self.code}', name='{self.name}')>"


class SyncChange(Base):
    """Tracks changes that need to be synchronized"""
    __tablename__ = 'sync_changes'
    
    id = Column(BigInteger, primary_key=True)
    node_id = Column(String(36), ForeignKey('sync_nodes.id'), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_uuid = Column(String(36), nullable=False)
    operation = Column(Enum(SyncOperation), nullable=False)
    packet_no = Column(BigInteger, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    target_node = relationship("SyncNode", foreign_keys=[node_id], back_populates="outgoing_changes")
    
    # Composite indices
    __table_args__ = (
        Index('idx_sync_changes_entity', 'entity_type', 'entity_uuid'),
        Index('idx_sync_changes_node_operation', 'node_id', 'operation'),
    )
    
    def __repr__(self):
        return f"<SyncChange(id={self.id}, entity_type='{self.entity_type}', operation='{self.operation.value}')>"


class ObjectVersionHistory(Base):
    """Stores conflicting object versions when versioning is enabled"""
    __tablename__ = 'object_version_history'
    
    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    entity_uuid = Column(String(36), nullable=False)
    entity_type = Column(String(100), nullable=False)
    source_node_id = Column(String(36), ForeignKey('sync_nodes.id'), nullable=False, index=True)
    arrival_time = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    serialized_data = Column(JSON, nullable=False)
    conflict_resolution = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    source_node = relationship("SyncNode", foreign_keys=[source_node_id], back_populates="incoming_changes")
    
    # Composite indices
    __table_args__ = (
        Index('idx_object_version_entity', 'entity_type', 'entity_uuid'),
        Index('idx_object_version_conflict', 'entity_type', 'entity_uuid', 'resolved_at'),
    )
    
    def __repr__(self):
        return f"<ObjectVersionHistory(id='{self.id}', entity_type='{self.entity_type}', source_node='{self.source_node_id}')>"
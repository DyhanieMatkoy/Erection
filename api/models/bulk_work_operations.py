"""
API models for bulk work operations
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class BulkUnitAssignmentRequest(BaseModel):
    """Request model for bulk unit assignments"""
    work_unit_mappings: List[Dict[str, Any]] = Field(
        ..., 
        description="List of work-unit mappings with work_id and unit_id keys"
    )
    validate_integrity: bool = Field(
        True, 
        description="Whether to validate referential integrity"
    )
    batch_size: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of records to process in each batch"
    )


class BulkValidationRequest(BaseModel):
    """Request model for bulk validation"""
    work_ids: List[int] = Field(..., description="List of work IDs to validate")
    check_units: bool = Field(True, description="Whether to validate unit references")
    check_hierarchy: bool = Field(True, description="Whether to validate hierarchy relationships")
    batch_size: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of records to process in each batch"
    )


class BulkMigrationRequest(BaseModel):
    """Request model for bulk legacy unit migration"""
    work_ids: List[int] = Field(..., description="List of work IDs to migrate")
    auto_apply_threshold: float = Field(
        0.8, 
        ge=0.0, 
        le=1.0, 
        description="Confidence threshold for automatic application"
    )
    batch_size: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of records to process in each batch"
    )


class HierarchyQueryRequest(BaseModel):
    """Request model for hierarchical queries"""
    root_id: Optional[int] = Field(None, description="Root work ID (None for all root works)")
    max_depth: int = Field(10, ge=1, le=20, description="Maximum depth to traverse")
    include_unit_info: bool = Field(True, description="Whether to include unit information")
    include_deleted: bool = Field(False, description="Whether to include deleted works")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(1000, ge=1, le=10000, description="Number of records per page")


class BulkOperationResult(BaseModel):
    """Result model for bulk operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    success_count: int = Field(0, description="Number of successful operations")
    failure_count: int = Field(0, description="Number of failed operations")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    processed_batches: Optional[int] = Field(None, description="Number of batches processed")
    total_records: Optional[int] = Field(None, description="Total number of records")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional result data")


class ValidationResult(BaseModel):
    """Result model for validation operations"""
    success: bool = Field(..., description="Whether the validation was successful")
    valid_count: int = Field(0, description="Number of valid records")
    invalid_count: int = Field(0, description="Number of invalid records")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    processed_batches: Optional[int] = Field(None, description="Number of batches processed")
    total_records: Optional[int] = Field(None, description="Total number of records")


class MigrationResult(BaseModel):
    """Result model for migration operations"""
    success: bool = Field(..., description="Whether the migration was successful")
    migrated_count: int = Field(0, description="Number of migrated records")
    pending_count: int = Field(0, description="Number of records pending manual review")
    error_count: int = Field(0, description="Number of records with errors")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    processed_batches: Optional[int] = Field(None, description="Number of batches processed")
    total_records: Optional[int] = Field(None, description="Total number of records")


class HierarchyResult(BaseModel):
    """Result model for hierarchical queries"""
    success: bool = Field(..., description="Whether the query was successful")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Hierarchical work data")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    error: Optional[str] = Field(None, description="Error message if query failed")


class StatisticsResult(BaseModel):
    """Result model for statistics queries"""
    success: bool = Field(..., description="Whether the query was successful")
    statistics: Dict[str, Any] = Field(..., description="Statistics data")
    error: Optional[str] = Field(None, description="Error message if query failed")


class OptimizationResult(BaseModel):
    """Result model for optimization analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    suggestions: Dict[str, Any] = Field(..., description="Optimization suggestions")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
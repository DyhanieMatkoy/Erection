"""
Bulk Work Operations API Endpoints

This module provides API endpoints for bulk operations on work records,
including bulk unit assignments, validation, and hierarchical queries.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from api.models.auth import UserInfo
from api.models.bulk_work_operations import (
    BulkUnitAssignmentRequest, BulkValidationRequest, BulkMigrationRequest,
    HierarchyQueryRequest, BulkOperationResult, ValidationResult, 
    MigrationResult, HierarchyResult, StatisticsResult, OptimizationResult
)
from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db_connection

router = APIRouter(prefix="/bulk-work-operations", tags=["Bulk Work Operations"])


@router.post("/unit-assignments", response_model=BulkOperationResult)
async def bulk_update_unit_assignments(
    request: BulkUnitAssignmentRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Bulk update work unit assignments
    
    Performs bulk updates of unit_id assignments for work records with
    optional integrity validation and batch processing for performance.
    
    Validates: Requirements 5.3, 5.4 - Bulk operations with integrity checks
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required for bulk operations"
        )
    
    try:
        # Import service
        from src.services.bulk_work_operations_service import BulkWorkOperationsService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        bulk_service = BulkWorkOperationsService(db_manager)
        
        # Execute bulk unit assignment
        result = bulk_service.bulk_update_unit_assignments(
            work_unit_mappings=request.work_unit_mappings,
            validate_integrity=request.validate_integrity,
            batch_size=request.batch_size
        )
        
        return BulkOperationResult(
            success=result['failure_count'] == 0,
            message=f"Processed {result['total_records']} records: {result['success_count']} successful, {result['failure_count']} failed",
            success_count=result['success_count'],
            failure_count=result['failure_count'],
            errors=result['errors'],
            processed_batches=result['processed_batches'],
            total_records=result['total_records']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk unit assignment failed: {str(e)}"
        )


@router.post("/validate", response_model=ValidationResult)
async def bulk_validate_works(
    request: BulkValidationRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Bulk validate work referential integrity
    
    Validates unit references and hierarchy relationships for multiple
    work records with batch processing for performance.
    
    Validates: Requirements 5.1, 5.2 - Data integrity validation
    """
    try:
        # Import service
        from src.services.bulk_work_operations_service import BulkWorkOperationsService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        bulk_service = BulkWorkOperationsService(db_manager)
        
        # Execute bulk validation
        result = bulk_service.bulk_validate_referential_integrity(
            work_ids=request.work_ids,
            check_units=request.check_units,
            check_hierarchy=request.check_hierarchy,
            batch_size=request.batch_size
        )
        
        return ValidationResult(
            success=result['invalid_count'] == 0,
            valid_count=result['valid_count'],
            invalid_count=result['invalid_count'],
            validation_errors=result['validation_errors'],
            processed_batches=result['processed_batches'],
            total_records=result['total_records']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk validation failed: {str(e)}"
        )


@router.post("/migrate-legacy-units", response_model=MigrationResult)
async def bulk_migrate_legacy_units(
    request: BulkMigrationRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Bulk migrate legacy unit strings to unit_id references
    
    Migrates legacy unit column data to proper unit_id foreign key
    references with automatic matching and manual review capabilities.
    
    Validates: Requirements 1.3, 1.5 - Legacy unit migration
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required for migration operations"
        )
    
    try:
        # Import service
        from src.services.bulk_work_operations_service import BulkWorkOperationsService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        bulk_service = BulkWorkOperationsService(db_manager)
        
        # Execute bulk migration
        result = bulk_service.bulk_migrate_legacy_units(
            work_ids=request.work_ids,
            auto_apply_threshold=request.auto_apply_threshold,
            batch_size=request.batch_size
        )
        
        return MigrationResult(
            success=result['error_count'] == 0,
            migrated_count=result['migrated_count'],
            pending_count=result['pending_count'],
            error_count=result['error_count'],
            errors=result['errors'],
            processed_batches=result['processed_batches'],
            total_records=result['total_records']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk migration failed: {str(e)}"
        )


@router.post("/hierarchy", response_model=HierarchyResult)
async def get_hierarchical_works(
    request: HierarchyQueryRequest,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get hierarchical work data with optimized queries
    
    Retrieves work hierarchy using database-specific optimized recursive
    queries with pagination support for large datasets.
    
    Validates: Requirement 2.5 - Efficient hierarchical queries
    """
    try:
        # Import service
        from src.services.hierarchical_query_service import HierarchicalQueryService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        # Execute hierarchical query
        result = hierarchy_service.get_work_hierarchy_tree(
            root_id=request.root_id,
            max_depth=request.max_depth,
            include_unit_info=request.include_unit_info,
            include_deleted=request.include_deleted,
            page=request.page,
            page_size=request.page_size
        )
        
        return HierarchyResult(
            success=result['success'],
            data=result['data'],
            pagination=result['pagination'],
            error=result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hierarchical query failed: {str(e)}"
        )


@router.get("/statistics", response_model=StatisticsResult)
async def get_bulk_operation_statistics(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get statistics about bulk operations and data integrity
    
    Returns comprehensive statistics about work data, migration status,
    and integrity issues for monitoring and reporting purposes.
    """
    try:
        # Import service
        from src.services.bulk_work_operations_service import BulkWorkOperationsService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        bulk_service = BulkWorkOperationsService(db_manager)
        
        # Get statistics
        stats = bulk_service.get_bulk_operation_statistics()
        
        return StatisticsResult(
            success='error' not in stats,
            statistics=stats,
            error=stats.get('error')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics query failed: {str(e)}"
        )


@router.get("/hierarchy-statistics", response_model=StatisticsResult)
async def get_hierarchy_statistics(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get statistics about the work hierarchy structure
    
    Returns detailed statistics about hierarchy depth, distribution,
    and potential issues for performance optimization.
    """
    try:
        # Import service
        from src.services.hierarchical_query_service import HierarchicalQueryService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        # Get hierarchy statistics
        stats = hierarchy_service.get_hierarchy_statistics()
        
        return StatisticsResult(
            success='error' not in stats,
            statistics=stats,
            error=stats.get('error')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hierarchy statistics query failed: {str(e)}"
        )


@router.get("/optimization-analysis", response_model=OptimizationResult)
async def get_optimization_analysis(
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Analyze and suggest optimizations for hierarchy performance
    
    Provides recommendations for database indexes, query optimizations,
    and data cleanup to improve bulk operation performance.
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required for optimization analysis"
        )
    
    try:
        # Import service
        from src.services.hierarchical_query_service import HierarchicalQueryService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        # Get optimization suggestions
        suggestions = hierarchy_service.optimize_hierarchy_performance()
        
        return OptimizationResult(
            success='error' not in suggestions,
            suggestions=suggestions,
            error=suggestions.get('error')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization analysis failed: {str(e)}"
        )


@router.get("/work/{work_id}/ancestors")
async def get_work_ancestors(
    work_id: int,
    include_self: bool = True,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get all ancestors of a work in hierarchical order
    
    Returns the complete path from root to the specified work,
    useful for breadcrumb navigation and hierarchy display.
    """
    try:
        # Import service
        from src.services.hierarchical_query_service import HierarchicalQueryService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        # Get ancestors
        ancestors = hierarchy_service.get_work_ancestors(work_id, include_self)
        
        return {
            "success": True,
            "data": ancestors,
            "work_id": work_id,
            "path_length": len(ancestors)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get work ancestors: {str(e)}"
        )


@router.get("/work/{work_id}/descendants")
async def get_work_descendants(
    work_id: int,
    max_depth: int = 10,
    include_deleted: bool = False,
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    Get all descendants of a work
    
    Returns all child works recursively up to the specified depth,
    useful for tree expansion and bulk operations on subtrees.
    """
    try:
        # Import service
        from src.services.hierarchical_query_service import HierarchicalQueryService
        from src.data.database_manager import DatabaseManager
        
        # Initialize service
        db_manager = DatabaseManager()
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        # Get descendants
        descendants = hierarchy_service.get_work_descendants(
            work_id, max_depth, include_deleted
        )
        
        return {
            "success": True,
            "data": descendants,
            "work_id": work_id,
            "descendant_count": len(descendants),
            "max_depth": max_depth
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get work descendants: {str(e)}"
        )
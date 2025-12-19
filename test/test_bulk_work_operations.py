"""
Tests for bulk work operations service

This module tests the bulk operations functionality for work records,
including unit assignments, validation, and hierarchical queries.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.bulk_work_operations_service import BulkWorkOperationsService
from src.services.hierarchical_query_service import HierarchicalQueryService
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work, Unit, WorkUnitMigration


class TestBulkWorkOperationsService:
    """Test cases for BulkWorkOperationsService"""
    
    @pytest.fixture
    def db_manager(self):
        """Create test database manager"""
        db_manager = DatabaseManager()
        try:
            db_manager.initialize()
        except Exception:
            # If initialization fails, tests will handle it gracefully
            pass
        return db_manager
    
    @pytest.fixture
    def bulk_service(self, db_manager):
        """Create bulk operations service"""
        return BulkWorkOperationsService(db_manager)
    
    @pytest.fixture
    def hierarchy_service(self, db_manager):
        """Create hierarchical query service"""
        return HierarchicalQueryService(db_manager)
    
    def test_bulk_update_unit_assignments_empty_list(self, bulk_service):
        """Test bulk unit assignment with empty list"""
        result = bulk_service.bulk_update_unit_assignments([])
        
        assert result['success_count'] == 0
        assert result['failure_count'] == 0
        assert result['total_records'] == 0
        assert len(result['errors']) == 0
    
    def test_bulk_update_unit_assignments_invalid_mapping(self, bulk_service):
        """Test bulk unit assignment with invalid mapping"""
        mappings = [
            {'work_id': None, 'unit_id': 1},  # Invalid work_id
            {'unit_id': 1},  # Missing work_id
        ]
        
        result = bulk_service.bulk_update_unit_assignments(mappings, validate_integrity=False)
        
        assert result['success_count'] == 0
        assert result['failure_count'] == 2
        assert result['total_records'] == 2
        assert len(result['errors']) == 2
    
    def test_bulk_validate_referential_integrity_empty_list(self, bulk_service):
        """Test bulk validation with empty list"""
        result = bulk_service.bulk_validate_referential_integrity([])
        
        assert result['valid_count'] == 0
        assert result['invalid_count'] == 0
        assert result['total_records'] == 0
        assert len(result['validation_errors']) == 0
    
    def test_bulk_migrate_legacy_units_empty_list(self, bulk_service):
        """Test bulk migration with empty list"""
        result = bulk_service.bulk_migrate_legacy_units([])
        
        assert result['migrated_count'] == 0
        assert result['pending_count'] == 0
        assert result['error_count'] == 0
        assert result['total_records'] == 0
        assert len(result['errors']) == 0
    
    def test_get_bulk_operation_statistics(self, bulk_service):
        """Test getting bulk operation statistics"""
        stats = bulk_service.get_bulk_operation_statistics()
        
        # Should return basic structure even if no data
        assert 'total_works' in stats
        assert 'works_with_unit_id' in stats
        assert 'works_with_legacy_unit' in stats
        assert 'works_needing_migration' in stats
        assert 'migration_status_breakdown' in stats
        assert 'integrity_issues' in stats
        
        # All counts should be non-negative
        assert stats['total_works'] >= 0
        assert stats['works_with_unit_id'] >= 0
        assert stats['works_with_legacy_unit'] >= 0
        assert stats['works_needing_migration'] >= 0


class TestHierarchicalQueryService:
    """Test cases for HierarchicalQueryService"""
    
    @pytest.fixture
    def db_manager(self):
        """Create test database manager"""
        db_manager = DatabaseManager()
        try:
            db_manager.initialize()
        except Exception:
            # If initialization fails, tests will handle it gracefully
            pass
        return db_manager
    
    @pytest.fixture
    def hierarchy_service(self, db_manager):
        """Create hierarchical query service"""
        return HierarchicalQueryService(db_manager)
    
    def test_get_work_hierarchy_tree_basic(self, hierarchy_service):
        """Test basic hierarchy tree retrieval"""
        result = hierarchy_service.get_work_hierarchy_tree()
        
        # Should return valid structure
        assert 'success' in result
        assert 'data' in result
        assert 'pagination' in result
        
        # Pagination should have required fields
        pagination = result['pagination']
        assert 'page' in pagination
        assert 'page_size' in pagination
        assert 'total_items' in pagination
        assert 'total_pages' in pagination
    
    def test_get_work_ancestors_invalid_id(self, hierarchy_service):
        """Test getting ancestors for invalid work ID"""
        ancestors = hierarchy_service.get_work_ancestors(99999)
        
        # Should return empty list for non-existent work
        assert isinstance(ancestors, list)
        assert len(ancestors) == 0
    
    def test_get_work_descendants_invalid_id(self, hierarchy_service):
        """Test getting descendants for invalid work ID"""
        descendants = hierarchy_service.get_work_descendants(99999)
        
        # Should return empty list for non-existent work
        assert isinstance(descendants, list)
        assert len(descendants) == 0
    
    def test_get_hierarchy_statistics(self, hierarchy_service):
        """Test getting hierarchy statistics"""
        stats = hierarchy_service.get_hierarchy_statistics()
        
        # Should return basic structure
        assert 'total_works' in stats
        assert 'root_works' in stats
        assert 'max_depth' in stats
        assert 'avg_children_per_parent' in stats
        assert 'works_by_level' in stats
        assert 'orphaned_works' in stats
        
        # All counts should be non-negative
        assert stats['total_works'] >= 0
        assert stats['root_works'] >= 0
        assert stats['max_depth'] >= 0
        assert stats['avg_children_per_parent'] >= 0.0
        assert stats['orphaned_works'] >= 0
    
    def test_optimize_hierarchy_performance(self, hierarchy_service):
        """Test hierarchy performance optimization analysis"""
        suggestions = hierarchy_service.optimize_hierarchy_performance()
        
        # Should return optimization structure
        assert 'index_recommendations' in suggestions
        assert 'query_optimizations' in suggestions
        assert 'data_issues' in suggestions
        assert 'performance_metrics' in suggestions
        
        # Should be lists or dicts
        assert isinstance(suggestions['index_recommendations'], list)
        assert isinstance(suggestions['query_optimizations'], list)
        assert isinstance(suggestions['data_issues'], list)
        assert isinstance(suggestions['performance_metrics'], dict)


class TestBulkOperationsIntegration:
    """Integration tests for bulk operations"""
    
    @pytest.fixture
    def db_manager(self):
        """Create test database manager"""
        db_manager = DatabaseManager()
        try:
            db_manager.initialize()
        except Exception:
            # If initialization fails, tests will handle it gracefully
            pass
        return db_manager
    
    def test_services_initialization(self, db_manager):
        """Test that services can be initialized properly"""
        bulk_service = BulkWorkOperationsService(db_manager)
        hierarchy_service = HierarchicalQueryService(db_manager)
        
        assert bulk_service is not None
        assert hierarchy_service is not None
        assert bulk_service.db_manager is not None
        assert hierarchy_service.db_manager is not None
    
    def test_batch_size_validation(self):
        """Test that batch sizes are handled correctly"""
        bulk_service = BulkWorkOperationsService()
        
        # Test with various batch sizes
        for batch_size in [1, 10, 100, 1000]:
            result = bulk_service.bulk_update_unit_assignments(
                [], batch_size=batch_size
            )
            assert result['total_records'] == 0
    
    def test_error_handling(self):
        """Test error handling in bulk operations"""
        bulk_service = BulkWorkOperationsService()
        
        # Test with invalid data that should trigger error handling
        invalid_mappings = [
            {'invalid_key': 'invalid_value'}
        ]
        
        result = bulk_service.bulk_update_unit_assignments(invalid_mappings)
        
        # Should handle errors gracefully
        assert result['failure_count'] > 0
        assert len(result['errors']) > 0


if __name__ == '__main__':
    pytest.main([__file__])
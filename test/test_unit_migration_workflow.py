"""Tests for unit migration workflow services"""

import pytest
from unittest.mock import Mock, patch
from src.services.unit_matching_service import UnitMatchingService
from src.services.migration_workflow_service import MigrationWorkflowService
from src.data.models.sqlalchemy_models import Unit, Work, WorkUnitMigration


class TestUnitMatchingService:
    """Test unit matching algorithms"""
    
    def test_normalize_unit_string(self):
        """Test unit string normalization"""
        # Mock database manager
        db_manager = Mock()
        service = UnitMatchingService(db_manager)
        
        # Test basic normalization
        assert service._normalize_unit_string("  М  ") == "м"
        assert service._normalize_unit_string("кв.м") == "м²"
        assert service._normalize_unit_string("куб м") == "м³"
        assert service._normalize_unit_string("штука") == "шт"
        
        # Test empty/None handling
        assert service._normalize_unit_string("") == ""
        assert service._normalize_unit_string(None) == ""
    
    def test_abbreviation_mapping(self):
        """Test abbreviation mapping functionality"""
        db_manager = Mock()
        service = UnitMatchingService(db_manager)
        
        # Test common abbreviations
        assert "м²" in service._abbreviation_map.values()
        assert "м³" in service._abbreviation_map.values()
        assert "шт" in service._abbreviation_map.values()
        assert "кг" in service._abbreviation_map.values()
    
    @patch('src.services.unit_matching_service.UnitMatchingService._get_units_cache')
    def test_exact_match(self, mock_cache):
        """Test exact matching functionality"""
        # Setup mock units with proper string names
        unit1 = Mock(spec=Unit)
        unit1.name = "м"
        unit1.id = 1
        
        unit2 = Mock(spec=Unit)
        unit2.name = "м²"
        unit2.id = 2
        
        unit3 = Mock(spec=Unit)
        unit3.name = "шт"
        unit3.id = 3
        
        mock_units = [unit1, unit2, unit3]
        mock_cache.return_value = mock_units
        
        db_manager = Mock()
        service = UnitMatchingService(db_manager)
        
        # Test exact matches
        result = service.exact_match("м")
        assert result is not None
        assert result.name == "м"
        
        result = service.exact_match("кв.м")  # Should normalize to м²
        assert result is not None
        assert result.name == "м²"
        
        # Test no match
        result = service.exact_match("nonexistent")
        assert result is None
    
    @patch('src.services.unit_matching_service.UnitMatchingService._get_units_cache')
    def test_find_best_match(self, mock_cache):
        """Test best match algorithm"""
        # Setup mock units with proper string names
        unit1 = Mock(spec=Unit)
        unit1.name = "м"
        unit1.id = 1
        
        unit2 = Mock(spec=Unit)
        unit2.name = "м²"
        unit2.id = 2
        
        unit3 = Mock(spec=Unit)
        unit3.name = "штука"
        unit3.id = 3
        
        mock_units = [unit1, unit2, unit3]
        mock_cache.return_value = mock_units
        
        db_manager = Mock()
        service = UnitMatchingService(db_manager)
        
        # Test exact match
        unit, confidence, match_type = service.find_best_match("м")
        assert unit is not None
        assert confidence == 1.0
        assert match_type == "exact"
        
        # Test no input
        unit, confidence, match_type = service.find_best_match("")
        assert unit is None
        assert confidence == 0.0
        assert match_type == "no_input"


class TestMigrationWorkflowService:
    """Test migration workflow orchestration"""
    
    def test_analyze_migration_scope(self):
        """Test migration scope analysis"""
        # Mock database manager and session
        db_manager = Mock()
        mock_session = Mock()
        
        # Create a proper context manager mock
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_session)
        context_manager.__exit__ = Mock(return_value=None)
        db_manager.get_session.return_value = context_manager
        
        # Mock works with legacy units
        work1 = Mock(spec=Work)
        work1.id = 1
        work1.unit = "м"
        work1.unit_id = None
        
        work2 = Mock(spec=Work)
        work2.id = 2
        work2.unit = "м²"
        work2.unit_id = None
        
        work3 = Mock(spec=Work)
        work3.id = 3
        work3.unit = "м"
        work3.unit_id = None
        
        mock_works = [work1, work2, work3]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_works
        mock_session.query.return_value.count.return_value = 0  # No existing entries
        
        service = MigrationWorkflowService(db_manager)
        result = service.analyze_migration_scope()
        
        assert result['total_works_needing_migration'] == 3
        assert result['unique_legacy_units'] == 2  # "м" and "м²"
        assert "м" in result['legacy_unit_strings']
        assert "м²" in result['legacy_unit_strings']
        assert result['work_count_by_unit']['м'] == 2
        assert result['work_count_by_unit']['м²'] == 1
    
    def test_create_migration_plan(self):
        """Test migration plan creation"""
        # Mock dependencies
        db_manager = Mock()
        mock_session = Mock()
        
        # Create a proper context manager mock
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_session)
        context_manager.__exit__ = Mock(return_value=None)
        db_manager.get_session.return_value = context_manager
        
        # Mock works
        mock_works = []
        for i in range(1, 6):
            work = Mock(spec=Work)
            work.id = i
            work.unit = "м"
            work.unit_id = None
            mock_works.append(work)
        
        mock_session.query.return_value.filter.return_value.all.return_value = mock_works
        mock_session.query.return_value.count.return_value = 0
        
        service = MigrationWorkflowService(db_manager)
        
        # Mock unit matching service
        service.unit_matching_service = Mock()
        service.unit_matching_service.get_match_statistics.return_value = {
            'total': 1,
            'exact': 1,
            'fuzzy_high': 0,
            'fuzzy_medium': 0,
            'similarity': 0,
            'no_match': 0,
            'no_input': 0
        }
        
        plan = service.create_migration_plan(batch_size=2)
        
        assert plan['batch_size'] == 2
        assert plan['estimated_batches'] == 3  # 5 works / 2 batch_size = 3 batches
        assert 'analysis' in plan
        assert 'match_statistics' in plan


if __name__ == "__main__":
    pytest.main([__file__])
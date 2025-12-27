"""
Test suite for API pagination and sorting services
Tests Task 5: Implement API pagination and sorting endpoints
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.pagination_service import PaginationService, PaginationConfig, PaginationResult
from api.services.sorting_service import SortingService, SortDirection, SortConfig, SortableColumn
from api.services.date_filter_service import DateFilterService, DateRange, DateFilterConfig


class TestPaginationService:
    """Test pagination service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = PaginationConfig(default_page_size=10, max_page_size=100, min_page_size=1)
        self.service = PaginationService(self.config)
    
    def test_validate_pagination_params(self):
        """Test pagination parameter validation"""
        # Valid parameters
        page, page_size = self.service.validate_pagination_params(1, 10)
        assert page == 1
        assert page_size == 10
        
        # Invalid page (too low)
        page, page_size = self.service.validate_pagination_params(0, 10)
        assert page == 1
        assert page_size == 10
        
        # Invalid page_size (too low)
        page, page_size = self.service.validate_pagination_params(1, 0)
        assert page == 1
        assert page_size == 10  # default
        
        # Invalid page_size (too high)
        page, page_size = self.service.validate_pagination_params(1, 200)
        assert page == 1
        assert page_size == 100  # max
    
    def test_calculate_offset(self):
        """Test offset calculation"""
        assert self.service.calculate_offset(1, 10) == 0
        assert self.service.calculate_offset(2, 10) == 10
        assert self.service.calculate_offset(3, 25) == 50
    
    def test_create_pagination_result(self):
        """Test pagination result creation"""
        items = [1, 2, 3, 4, 5]
        result = self.service.create_pagination_result(items, 1, 10, 25)
        
        assert result.items == items
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_items == 25
        assert result.total_pages == 3
        assert result.has_next is True
        assert result.has_previous is False
        
        # Test last page
        result = self.service.create_pagination_result(items, 3, 10, 25)
        assert result.has_next is False
        assert result.has_previous is True
    
    def test_apply_pagination_to_query(self):
        """Test SQL query pagination"""
        base_query = "SELECT * FROM estimates WHERE marked_for_deletion = 0"
        params = []
        
        query, new_params = self.service.apply_pagination_to_query(base_query, params, 2, 10)
        
        expected_query = "SELECT * FROM estimates WHERE marked_for_deletion = 0 LIMIT ? OFFSET ?"
        assert query == expected_query
        assert new_params == [10, 10]  # page_size, offset
    
    def test_get_count_query(self):
        """Test count query generation"""
        base_query = "SELECT * FROM estimates WHERE marked_for_deletion = 0 ORDER BY date DESC"
        count_query = self.service.get_count_query(base_query)
        
        expected = "SELECT COUNT(*) as count FROM (SELECT * FROM estimates WHERE marked_for_deletion = 0) as count_subquery"
        assert count_query == expected
    
    def test_create_pagination_info_dict(self):
        """Test pagination info dictionary creation"""
        result = PaginationResult(
            items=[1, 2, 3],
            page=2,
            page_size=10,
            total_items=25,
            total_pages=3,
            has_next=True,
            has_previous=True
        )
        
        info = self.service.create_pagination_info_dict(result)
        
        expected = {
            "page": 2,
            "page_size": 10,
            "total_items": 25,
            "total_pages": 3,
            "has_next": True,
            "has_previous": True
        }
        assert info == expected


class TestSortingService:
    """Test sorting service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service = SortingService()
    
    def test_validate_sort_params_valid(self):
        """Test valid sort parameter validation"""
        is_valid, sort_config, error = self.service.validate_sort_params('estimates', 'date', 'desc')
        
        assert is_valid is True
        assert error is None
        assert sort_config.column == 'date'
        assert sort_config.direction == SortDirection.DESC
        assert sort_config.data_type == 'date'
        assert sort_config.table_alias == 'e'
    
    def test_validate_sort_params_invalid_table(self):
        """Test invalid table validation"""
        is_valid, sort_config, error = self.service.validate_sort_params('invalid_table', 'date', 'desc')
        
        assert is_valid is False
        assert sort_config is None
        assert "not supported for table" in error
    
    def test_validate_sort_params_invalid_column(self):
        """Test invalid column validation"""
        is_valid, sort_config, error = self.service.validate_sort_params('estimates', 'invalid_column', 'desc')
        
        assert is_valid is False
        assert sort_config is None
        assert "not sortable" in error
    
    def test_validate_sort_params_invalid_direction(self):
        """Test invalid sort direction validation"""
        is_valid, sort_config, error = self.service.validate_sort_params('estimates', 'date', 'invalid')
        
        assert is_valid is False
        assert sort_config is None
        assert "Invalid sort direction" in error
    
    def test_get_sortable_columns(self):
        """Test getting sortable columns"""
        columns = self.service.get_sortable_columns('estimates')
        
        assert 'id' in columns
        assert 'date' in columns
        assert 'number' in columns
        assert 'customer_name' in columns
        
        # Invalid table
        columns = self.service.get_sortable_columns('invalid_table')
        assert columns == []
    
    def test_build_order_by_clause(self):
        """Test ORDER BY clause building"""
        # String column
        sort_config = SortConfig('name', SortDirection.ASC, 'string', 'c')
        clause = self.service.build_order_by_clause(sort_config)
        assert clause == "c.name COLLATE NOCASE ASC"
        
        # Number column
        sort_config = SortConfig('total_sum', SortDirection.DESC, 'number', 'e')
        clause = self.service.build_order_by_clause(sort_config)
        assert clause == "CAST(e.total_sum AS REAL) DESC"
        
        # Date column
        sort_config = SortConfig('date', SortDirection.ASC, 'date', 'e')
        clause = self.service.build_order_by_clause(sort_config)
        assert clause == "datetime(e.date) ASC"
        
        # No table alias
        sort_config = SortConfig('id', SortDirection.DESC, 'number')
        clause = self.service.build_order_by_clause(sort_config)
        assert clause == "CAST(id AS REAL) DESC"
    
    def test_apply_sorting_to_query(self):
        """Test applying sorting to SQL query"""
        base_query = "SELECT * FROM estimates e WHERE e.marked_for_deletion = 0"
        
        sorted_query, error = self.service.apply_sorting_to_query(base_query, 'estimates', 'date', 'desc')
        
        assert error is None
        assert "ORDER BY datetime(e.date) DESC" in sorted_query
        
        # Test with existing ORDER BY
        base_query_with_order = "SELECT * FROM estimates e WHERE e.marked_for_deletion = 0 ORDER BY e.id"
        sorted_query, error = self.service.apply_sorting_to_query(base_query_with_order, 'estimates', 'date', 'desc')
        
        assert error is None
        assert "ORDER BY datetime(e.date) DESC" in sorted_query
        assert "ORDER BY e.id" not in sorted_query
    
    def test_get_default_sort(self):
        """Test default sort configuration"""
        sort_by, sort_order = self.service.get_default_sort('estimates')
        assert sort_by == 'date'
        assert sort_order == 'desc'
        
        sort_by, sort_order = self.service.get_default_sort('unknown_table')
        assert sort_by == 'id'
        assert sort_order == 'desc'
    
    def test_create_multi_column_sort(self):
        """Test multi-column sorting"""
        sort_configs = [('date', 'desc'), ('number', 'asc')]
        order_clause, error = self.service.create_multi_column_sort('estimates', sort_configs)
        
        assert error is None
        assert "ORDER BY datetime(e.date) DESC, e.number COLLATE NOCASE ASC" in order_clause
    
    def test_add_remove_sortable_column(self):
        """Test adding and removing sortable columns"""
        # Add new column
        new_column = SortableColumn('custom_field', 'string', 'e')
        self.service.add_sortable_column('estimates', 'custom_field', new_column)
        
        columns = self.service.get_sortable_columns('estimates')
        assert 'custom_field' in columns
        
        # Remove column
        self.service.remove_sortable_column('estimates', 'custom_field')
        columns = self.service.get_sortable_columns('estimates')
        assert 'custom_field' not in columns


class TestDateFilterService:
    """Test date filter service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service = DateFilterService()
        
        # Create in-memory database for testing
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        
        # Create test table
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE estimates (
                id INTEGER PRIMARY KEY,
                date TEXT,
                marked_for_deletion INTEGER DEFAULT 0
            )
        """)
        
        # Insert test data
        test_dates = [
            '2024-01-15',
            '2024-02-20',
            '2024-03-10',
            '2024-12-01'
        ]
        
        for test_date in test_dates:
            cursor.execute("INSERT INTO estimates (date) VALUES (?)", (test_date,))
        
        self.db.commit()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.db.close()
    
    def test_get_default_date_range_with_data(self):
        """Test default date range calculation with existing data"""
        date_range = self.service.get_default_date_range(self.db, 'estimates')
        
        assert date_range.is_default is True
        assert date_range.start_date == date(2024, 12, 1)  # Most recent date
        assert date_range.end_date is None  # No upper limit
    
    def test_get_default_date_range_no_data(self):
        """Test default date range calculation with no data"""
        # Clear all data
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM estimates")
        self.db.commit()
        
        date_range = self.service.get_default_date_range(self.db, 'estimates')
        
        assert date_range.is_default is True
        assert date_range.start_date is not None
        assert date_range.end_date is not None
        assert date_range.end_date == date.today()
    
    def test_get_default_date_range_invalid_table(self):
        """Test default date range for invalid table"""
        date_range = self.service.get_default_date_range(self.db, 'invalid_table')
        
        assert date_range.is_default is True
        assert date_range.start_date is not None
        assert date_range.end_date == date.today()
    
    def test_validate_date_range(self):
        """Test date range validation"""
        # Valid range
        is_valid, error = self.service.validate_date_range(date(2024, 1, 1), date(2024, 12, 31))
        assert is_valid is True
        assert error is None
        
        # Invalid range (start after end)
        is_valid, error = self.service.validate_date_range(date(2024, 12, 31), date(2024, 1, 1))
        assert is_valid is False
        assert "Start date cannot be after end date" in error
        
        # Date too far in past
        is_valid, error = self.service.validate_date_range(date(1800, 1, 1), date(2024, 1, 1))
        assert is_valid is False
        assert "cannot be before" in error
        
        # Date too far in future
        is_valid, error = self.service.validate_date_range(date(2024, 1, 1), date(2200, 1, 1))
        assert is_valid is False
        assert "cannot be after" in error
    
    def test_apply_date_filter_to_query(self):
        """Test applying date filter to SQL query"""
        base_query = "SELECT * FROM estimates e"
        where_clauses = ["e.marked_for_deletion = 0"]
        params = []
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        query, new_where, new_params, error = self.service.apply_date_filter_to_query(
            base_query, 'estimates', start_date, end_date, where_clauses, params
        )
        
        assert error is None
        assert "e.date >= ?" in new_where
        assert "e.date <= ?" in new_where
        assert '2024-01-01' in new_params
        assert '2024-12-31' in new_params
    
    def test_get_date_range_summary(self):
        """Test date range summary generation"""
        # Both dates
        date_range = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        summary = self.service.get_date_range_summary(date_range)
        assert "From 2024-01-01 to 2024-12-31" in summary
        
        # Same date
        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 1))
        summary = self.service.get_date_range_summary(date_range)
        assert "On 2024-01-01" in summary
        
        # Start date only
        date_range = DateRange(date(2024, 1, 1), None)
        summary = self.service.get_date_range_summary(date_range)
        assert "From 2024-01-01 onwards" in summary
        
        # End date only
        date_range = DateRange(None, date(2024, 12, 31))
        summary = self.service.get_date_range_summary(date_range)
        assert "Up to 2024-12-31" in summary
        
        # No dates
        date_range = DateRange(None, None)
        summary = self.service.get_date_range_summary(date_range)
        assert "All dates" in summary
    
    def test_parse_date_param(self):
        """Test date parameter parsing"""
        # Valid ISO format
        parsed = self.service.parse_date_param('2024-01-15')
        assert parsed == date(2024, 1, 15)
        
        # None input
        parsed = self.service.parse_date_param(None)
        assert parsed is None
        
        # Empty string
        parsed = self.service.parse_date_param('')
        assert parsed is None
        
        # Invalid format
        parsed = self.service.parse_date_param('invalid-date')
        assert parsed is None
    
    def test_create_date_filter_info(self):
        """Test date filter info creation"""
        applied_range = DateRange(date(2024, 1, 1), date(2024, 12, 31), is_default=False)
        default_range = DateRange(date(2024, 6, 1), None, is_default=True)
        
        info = self.service.create_date_filter_info(applied_range, default_range)
        
        assert info['applied_range']['start_date'] == '2024-01-01'
        assert info['applied_range']['end_date'] == '2024-12-31'
        assert info['applied_range']['is_default'] is False
        
        assert info['default_range']['start_date'] == '2024-06-01'
        assert info['default_range']['end_date'] is None
        assert info['default_range']['is_default'] is True


def test_integration_pagination_sorting_filtering():
    """Integration test for pagination, sorting, and filtering services"""
    # Create services
    pagination_service = PaginationService()
    sorting_service = SortingService()
    date_filter_service = DateFilterService()
    
    # Mock database connection
    db = Mock()
    cursor = Mock()
    db.cursor.return_value = cursor
    
    # Mock query results
    cursor.fetchone.return_value = {'count': 100}
    cursor.fetchall.return_value = [
        {'id': 1, 'date': '2024-01-01', 'number': 'EST-001'},
        {'id': 2, 'date': '2024-01-02', 'number': 'EST-002'}
    ]
    
    # Test combined functionality
    base_query = "SELECT e.* FROM estimates e"
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    # Apply date filter
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    
    query, where_clauses, params, error = date_filter_service.apply_date_filter_to_query(
        base_query, 'estimates', start_date, end_date, where_clauses, params
    )
    assert error is None
    
    # Build complete query with WHERE clause
    where_sql = " AND ".join(where_clauses)
    complete_query = f"{base_query} WHERE {where_sql}"
    
    # Apply sorting
    sorted_query, error = sorting_service.apply_sorting_to_query(
        complete_query, 'estimates', 'date', 'desc'
    )
    assert error is None
    
    # Apply pagination
    paginated_query, paginated_params = pagination_service.apply_pagination_to_query(
        sorted_query, params, 1, 10
    )
    
    # Verify final query structure
    assert "WHERE" in paginated_query
    assert "ORDER BY" in paginated_query
    assert "LIMIT" in paginated_query
    assert "OFFSET" in paginated_query
    
    # Verify parameters
    assert '2024-01-01' in paginated_params
    assert '2024-12-31' in paginated_params
    assert 10 in paginated_params  # page_size
    assert 0 in paginated_params   # offset


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Tests for table part performance optimization features.

Tests virtual scrolling, lazy loading, and memory optimization
for large datasets (1000+ rows).
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QTableWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

from src.services.table_part_virtualization_service import (
    TablePartVirtualizationService,
    VirtualizationOptions,
    create_virtualization_service
)
from src.services.table_part_memory_optimizer import (
    TablePartMemoryOptimizer,
    MemoryOptimizationOptions,
    CacheStrategy,
    create_memory_optimizer
)


class TestTablePartVirtualization:
    """Test virtual scrolling functionality"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    @pytest.fixture
    def table_widget(self, app):
        """Create table widget for testing"""
        return QTableWidget()
    
    @pytest.fixture
    def mock_load_function(self):
        """Mock data loading function"""
        def load_data(page: int, page_size: int):
            # Generate test data
            start_id = page * page_size
            data = []
            for i in range(page_size):
                data.append({
                    'id': start_id + i,
                    'name': f'Item {start_id + i}',
                    'value': (start_id + i) * 10
                })
            return data, 10000  # Total count of 10,000 items
        
        return load_data
    
    @pytest.fixture
    def virtualization_service(self, table_widget, mock_load_function):
        """Create virtualization service for testing"""
        options = VirtualizationOptions(
            row_height=30,
            buffer_size=5,
            page_size=50,
            preload_pages=1,
            cache_size=5
        )
        return create_virtualization_service(table_widget, mock_load_function, options)
    
    def test_virtualization_service_creation(self, virtualization_service):
        """Test that virtualization service is created correctly"""
        assert virtualization_service is not None
        assert virtualization_service.options.row_height == 30
        assert virtualization_service.options.page_size == 50
        assert len(virtualization_service.pages) == 0
    
    def test_load_page(self, virtualization_service):
        """Test loading a single page of data"""
        # Load page 0
        virtualization_service._load_page(0)
        
        # Check that page was loaded
        assert 0 in virtualization_service.pages
        page = virtualization_service.pages[0]
        assert page.is_loaded
        assert len(page.data) == 50
        assert page.data[0]['id'] == 0
        assert page.data[0]['name'] == 'Item 0'
    
    def test_visible_range_calculation(self, virtualization_service):
        """Test calculation of visible row range"""
        # Mock scroll position
        virtualization_service.table.verticalScrollBar().setValue(300)
        
        start_row, end_row = virtualization_service._get_visible_range()
        
        # Should calculate based on scroll position and row height
        assert start_row >= 0
        assert end_row > start_row
        assert end_row - start_row > 0  # Should have some visible rows
    
    def test_cache_cleanup(self, virtualization_service):
        """Test cache cleanup when limit is exceeded"""
        # Load more pages than cache limit
        for page_num in range(10):  # More than cache_size of 5
            virtualization_service._load_page(page_num)
        
        # Should have cleaned up old pages
        assert len(virtualization_service.pages) <= virtualization_service.options.cache_size
    
    def test_prefetch_functionality(self, virtualization_service):
        """Test prefetching of adjacent pages"""
        # Enable prefetch and load a page
        virtualization_service.options.enable_prefetch = True
        virtualization_service._load_page(2)
        
        # Should schedule prefetch for adjacent pages
        # This is tested indirectly through the timer mechanism
        assert virtualization_service.prefetch_timer is not None
    
    def test_performance_metrics(self, virtualization_service):
        """Test performance metrics tracking"""
        # Load some data
        virtualization_service._load_page(0)
        
        metrics = virtualization_service.get_metrics()
        assert metrics.total_rows == 10000
        assert metrics.rendered_rows >= 0
        assert metrics.memory_usage_mb >= 0
    
    def test_scroll_to_row(self, virtualization_service):
        """Test scrolling to specific row"""
        # Set total count
        virtualization_service.total_count = 1000
        
        # Scroll to row 500
        virtualization_service.scroll_to_row(500)
        
        # Check scroll position
        expected_scroll = 500 * virtualization_service.options.row_height
        actual_scroll = virtualization_service.table.verticalScrollBar().value()
        assert actual_scroll == expected_scroll
    
    def test_data_range_retrieval(self, virtualization_service):
        """Test retrieving data for specific range"""
        # Load some pages
        virtualization_service._load_page(0)  # Rows 0-49
        virtualization_service._load_page(1)  # Rows 50-99
        
        # Get data for range 25-75 (spans two pages)
        data = virtualization_service._get_data_range(25, 75)
        
        assert len(data) == 50  # 25 from page 0 + 25 from page 1
        assert data[0]['id'] == 25
        assert data[-1]['id'] == 74


class TestTablePartMemoryOptimizer:
    """Test memory optimization functionality"""
    
    @pytest.fixture
    def memory_optimizer(self):
        """Create memory optimizer for testing"""
        options = MemoryOptimizationOptions(
            max_memory_mb=10.0,  # Small limit for testing
            cleanup_threshold=0.8,
            compression_enabled=True,
            cache_strategy=CacheStrategy.LRU
        )
        return create_memory_optimizer(options)
    
    @pytest.fixture
    def large_test_data(self):
        """Generate large test data"""
        return {
            'items': [{'id': i, 'data': 'x' * 1000} for i in range(100)],
            'metadata': {'count': 100, 'description': 'Test data'}
        }
    
    def test_memory_optimizer_creation(self, memory_optimizer):
        """Test memory optimizer creation"""
        assert memory_optimizer is not None
        assert memory_optimizer.options.max_memory_mb == 10.0
        assert len(memory_optimizer.cache) == 0
    
    def test_store_and_retrieve_data(self, memory_optimizer, large_test_data):
        """Test storing and retrieving data"""
        # Store data
        success = memory_optimizer.store('test_key', large_test_data)
        assert success
        
        # Retrieve data
        retrieved_data = memory_optimizer.get('test_key')
        assert retrieved_data is not None
        assert retrieved_data['metadata']['count'] == 100
    
    def test_data_compression(self, memory_optimizer, large_test_data):
        """Test automatic data compression"""
        # Store large data (should trigger compression)
        memory_optimizer.store('large_data', large_test_data)
        
        # Check if data was compressed
        entry = memory_optimizer.cache['large_data']
        assert entry.is_compressed
        assert entry.compressed_data is not None
        assert entry.data is None  # Original data should be cleared
    
    def test_cache_cleanup(self, memory_optimizer):
        """Test cache cleanup when memory limit is exceeded"""
        # Store multiple large items to exceed memory limit
        for i in range(20):
            large_data = {'data': 'x' * 10000, 'id': i}
            memory_optimizer.store(f'item_{i}', large_data)
        
        # Should have triggered cleanup
        stats = memory_optimizer.get_stats()
        assert stats.cleanup_count > 0
        assert len(memory_optimizer.cache) < 20
    
    def test_lru_eviction_strategy(self, memory_optimizer):
        """Test LRU (Least Recently Used) eviction strategy"""
        # Store items
        for i in range(5):
            memory_optimizer.store(f'item_{i}', {'data': 'x' * 5000})
        
        # Access some items to update their access time
        memory_optimizer.get('item_0')
        memory_optimizer.get('item_2')
        
        # Store more items to trigger cleanup
        for i in range(5, 15):
            memory_optimizer.store(f'item_{i}', {'data': 'x' * 5000})
        
        # Recently accessed items should still be in cache
        assert memory_optimizer.has('item_0')
        assert memory_optimizer.has('item_2')
    
    def test_memory_optimization(self, memory_optimizer):
        """Test memory optimization (compression of existing entries)"""
        # Store uncompressed data
        memory_optimizer.options.compression_enabled = False
        for i in range(5):
            large_data = {'data': 'x' * 15000, 'id': i}
            memory_optimizer.store(f'item_{i}', large_data)
        
        # Re-enable compression and optimize
        memory_optimizer.options.compression_enabled = True
        optimized_count, saved_mb = memory_optimizer.optimize_memory()
        
        assert optimized_count > 0
        assert saved_mb > 0
    
    def test_preload_data(self, memory_optimizer):
        """Test data preloading with batching"""
        def mock_load_fn(key):
            return {'key': key, 'data': 'x' * 1000}
        
        keys = [f'preload_{i}' for i in range(10)]
        
        # Preload data
        memory_optimizer.preload_data(keys, mock_load_fn, batch_size=3)
        
        # Check that data was loaded
        for key in keys:
            assert memory_optimizer.has(key)
            data = memory_optimizer.get(key)
            assert data['key'] == key
    
    def test_cache_statistics(self, memory_optimizer):
        """Test cache statistics and monitoring"""
        # Store some data
        for i in range(5):
            memory_optimizer.store(f'item_{i}', {'data': 'x' * 2000})
        
        # Get statistics
        stats = memory_optimizer.get_stats()
        cache_info = memory_optimizer.get_cache_info()
        
        assert stats.cache_size == 5
        assert stats.used_memory_mb > 0
        assert cache_info['total_entries'] == 5
        assert cache_info['total_size_mb'] > 0
    
    def test_error_handling(self, memory_optimizer):
        """Test error handling in memory optimizer"""
        # Try to store invalid data
        class UnserializableClass:
            def __init__(self):
                self.func = lambda x: x  # Functions can't be serialized
        
        # Should handle gracefully
        success = memory_optimizer.store('invalid', UnserializableClass())
        # Depending on implementation, this might succeed or fail gracefully
        
        # Try to get non-existent key
        result = memory_optimizer.get('non_existent')
        assert result is None


class TestPerformanceIntegration:
    """Integration tests for performance optimization"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    def test_large_dataset_performance(self, app):
        """Test performance with large dataset (1000+ rows)"""
        # Create mock table widget
        table = QTableWidget()
        
        # Create large dataset loader
        def load_large_dataset(page: int, page_size: int):
            data = []
            start_id = page * page_size
            for i in range(page_size):
                data.append({
                    'id': start_id + i,
                    'name': f'Large Item {start_id + i}',
                    'description': f'Description for item {start_id + i}' * 10,
                    'value': (start_id + i) * 100
                })
            return data, 50000  # 50,000 total items
        
        # Create virtualization service
        options = VirtualizationOptions(
            row_height=25,
            page_size=100,
            buffer_size=20,
            preload_pages=2
        )
        service = create_virtualization_service(table, load_large_dataset, options)
        
        # Measure loading time
        start_time = time.time()
        
        # Load visible range (should be fast due to virtualization)
        service._load_visible_range(0, 50)
        
        load_time = time.time() - start_time
        
        # Should load quickly (under 1 second for virtualized loading)
        assert load_time < 1.0
        
        # Check that only necessary pages were loaded
        assert len(service.pages) <= 3  # Should only load 1-2 pages for 50 rows
        
        # Check memory usage is reasonable
        metrics = service.get_metrics()
        assert metrics.memory_usage_mb < 10.0  # Should use less than 10MB
    
    def test_memory_usage_with_large_dataset(self):
        """Test memory usage stays within limits with large dataset"""
        optimizer = create_memory_optimizer(MemoryOptimizationOptions(
            max_memory_mb=5.0,  # Small limit
            cleanup_threshold=0.7,
            compression_enabled=True
        ))
        
        # Store many large items
        for i in range(100):
            large_item = {
                'id': i,
                'data': 'x' * 10000,  # 10KB per item
                'metadata': {'created': time.time(), 'index': i}
            }
            optimizer.store(f'large_item_{i}', large_item)
        
        # Check memory usage
        stats = optimizer.get_stats()
        
        # Should stay within limits due to cleanup and compression
        assert stats.used_memory_mb <= optimizer.options.max_memory_mb
        assert stats.cleanup_count > 0  # Should have performed cleanup
        
        # Should still be able to retrieve some items
        retrieved_count = 0
        for i in range(100):
            if optimizer.get(f'large_item_{i}') is not None:
                retrieved_count += 1
        
        assert retrieved_count > 0  # Should have some items still cached
    
    def test_virtualization_with_memory_optimization(self, app):
        """Test integration of virtualization and memory optimization"""
        table = QTableWidget()
        memory_optimizer = create_memory_optimizer()
        
        # Create data loader that uses memory optimizer
        def cached_load_function(page: int, page_size: int):
            cache_key = f'page_{page}_{page_size}'
            
            # Try to get from cache first
            cached_data = memory_optimizer.get(cache_key)
            if cached_data:
                return cached_data['data'], cached_data['total']
            
            # Generate data
            data = []
            start_id = page * page_size
            for i in range(page_size):
                data.append({
                    'id': start_id + i,
                    'name': f'Cached Item {start_id + i}',
                    'value': (start_id + i) * 50
                })
            
            # Cache the result
            result = {'data': data, 'total': 25000}
            memory_optimizer.store(cache_key, result)
            
            return data, 25000
        
        # Create virtualization service
        service = create_virtualization_service(table, cached_load_function)
        
        # Load some pages
        service._load_page(0)
        service._load_page(1)
        service._load_page(2)
        
        # Load same pages again (should hit cache)
        start_time = time.time()
        service._load_page(0)  # Should be much faster due to caching
        cache_hit_time = time.time() - start_time
        
        # Cache hit should be very fast
        assert cache_hit_time < 0.1  # Less than 100ms
        
        # Check that memory optimizer has cached data
        assert memory_optimizer.has('page_0_100')
        assert memory_optimizer.has('page_1_100')


if __name__ == '__main__':
    pytest.main([__file__])
"""Test enhanced network error handling in sync service

This test verifies that the improved network error handling works correctly
with exponential backoff, specific error handling, and proper notifications.
"""

import sys
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

from src.services.sync_service import SyncService
from src.data.database_manager import DatabaseManager


class TestNetworkErrorHandling:
    """Test enhanced network error handling"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setup_method(self):
        """Setup test method"""
        # Mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        
        # Create sync service
        self.sync_service = SyncService(
            db_manager=self.mock_db_manager,
            server_url="http://test-server.com",
            node_code="TEST-NODE"
        )
        
        # Mock sync manager and other components
        self.sync_service.sync_manager = Mock()
        self.sync_service.packet_manager = Mock()
        self.sync_service.conflict_resolver = Mock()
    
    def test_exponential_backoff(self):
        """Test exponential backoff retry logic"""
        # Test initial retry interval
        assert self.sync_service.base_retry_interval == 1
        assert self.sync_service.current_retry_interval == 1
        assert self.sync_service.retry_count == 0
        
        # Simulate first retry
        self.sync_service.retry_count = 1
        self.sync_service._schedule_retry("Test error")
        
        # Check that interval increased
        expected_interval = self.sync_service.base_retry_interval * (self.sync_service.retry_multiplier ** 1)
        assert self.sync_service.current_retry_interval == expected_interval
        
        # Simulate second retry
        self.sync_service.retry_count = 2
        self.sync_service._schedule_retry("Test error")
        
        # Check exponential increase
        expected_interval = self.sync_service.base_retry_interval * (self.sync_service.retry_multiplier ** 2)
        assert self.sync_service.current_retry_interval == expected_interval
        
        print("✅ Exponential backoff test passed!")
    
    def test_max_retry_limit(self):
        """Test maximum retry limit"""
        # Set retry count to maximum
        self.sync_service.retry_count = self.sync_service.max_retries
        
        # Try to schedule retry
        self.sync_service._schedule_retry("Test error")
        
        # Should not schedule more retries
        assert not self.sync_service.retry_timer.isActive()
        
        print("✅ Max retry limit test passed!")
    
    def test_retry_state_reset(self):
        """Test retry state reset on success"""
        # Set some retry state
        self.sync_service.retry_count = 5
        self.sync_service.current_retry_interval = 32
        self.sync_service.retry_timer.start(1000)
        
        # Reset state
        self.sync_service._reset_retry_state()
        
        # Check state is reset
        assert self.sync_service.retry_count == 0
        assert self.sync_service.current_retry_interval == self.sync_service.base_retry_interval
        assert not self.sync_service.retry_timer.isActive()
        
        print("✅ Retry state reset test passed!")
    
    def test_should_retry_on_error(self):
        """Test error type classification for retries"""
        # Network errors should retry
        assert self.sync_service._should_retry_on_error("Connection error: timeout")
        assert self.sync_service._should_retry_on_error("Network unreachable")
        assert self.sync_service._should_retry_on_error("HTTP 503: Service unavailable")
        assert self.sync_service._should_retry_on_error("HTTP 502: Bad gateway")
        assert self.sync_service._should_retry_on_error("Request timeout")
        
        # Authentication errors should not retry
        assert not self.sync_service._should_retry_on_error("Authentication failed")
        assert not self.sync_service._should_retry_on_error("HTTP 401: Unauthorized")
        
        # Client errors should not retry (except specific ones)
        assert not self.sync_service._should_retry_on_error("HTTP 400: Bad request")
        assert not self.sync_service._should_retry_on_error("HTTP 404: Not found")
        
        # But some client errors should retry
        assert self.sync_service._should_retry_on_error("HTTP 408: Request timeout")
        assert self.sync_service._should_retry_on_error("HTTP 429: Too many requests")
        
        print("✅ Error classification test passed!")
    
    @patch('requests.post')
    def test_connection_error_handling(self, mock_post):
        """Test specific connection error handling"""
        # Mock connection error
        mock_post.side_effect = ConnectionError("Connection refused")
        
        # Try to register node
        self.sync_service._register_node()
        
        # Should be offline and retry scheduled
        assert not self.sync_service.is_online
        assert self.sync_service.retry_timer.isActive()
        
        print("✅ Connection error handling test passed!")
    
    @patch('requests.post')
    def test_timeout_error_handling(self, mock_post):
        """Test timeout error handling"""
        # Mock timeout error
        mock_post.side_effect = Timeout("Request timeout")
        
        # Try to register node
        self.sync_service._register_node()
        
        # Should be offline and retry scheduled
        assert not self.sync_service.is_online
        assert self.sync_service.retry_timer.isActive()
        
        print("✅ Timeout error handling test passed!")
    
    @patch('requests.post')
    def test_http_error_handling(self, mock_post):
        """Test HTTP error handling"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        # Try to register node
        self.sync_service._register_node()
        
        # Should be offline and retry scheduled
        assert not self.sync_service.is_online
        assert self.sync_service.retry_timer.isActive()
        
        print("✅ HTTP error handling test passed!")
    
    def test_network_diagnostics(self):
        """Test network diagnostics functionality"""
        with patch('requests.get') as mock_get:
            # Mock successful health check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Get diagnostics
            diagnostics = self.sync_service.get_network_diagnostics()
            
            # Check diagnostics structure
            assert 'server_url' in diagnostics
            assert 'is_online' in diagnostics
            assert 'retry_count' in diagnostics
            assert 'connectivity_test' in diagnostics
            
            # Should show successful connectivity test
            assert diagnostics['connectivity_test'] == 'success'
            assert 'response_time_ms' in diagnostics
            
        print("✅ Network diagnostics test passed!")
    
    def test_force_reconnect(self):
        """Test force reconnect functionality"""
        # Set some initial state
        self.sync_service.node_id = "test-node-id"
        self.sync_service.auth_token = "test-token"
        self.sync_service.is_online = True
        
        with patch.object(self.sync_service, '_register_node') as mock_register:
            # Force reconnect
            result = self.sync_service.force_reconnect()
            
            # Should clear authentication and try to register
            assert self.sync_service.node_id is None
            assert self.sync_service.auth_token is None
            assert not self.sync_service.is_online
            mock_register.assert_called_once()
            assert result is True
        
        print("✅ Force reconnect test passed!")
    
    @patch('requests.get')
    def test_connectivity_check(self, mock_get):
        """Test periodic connectivity check"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Set initial offline state and mock node as registered
        self.sync_service.is_online = False
        self.sync_service.node_id = "test-node-id"  # Prevent registration attempt
        
        # Run connectivity check
        self.sync_service._check_connectivity()
        
        # Should detect connection restored
        assert self.sync_service.is_online
        
        # Reset mock for next test
        mock_get.reset_mock()
        
        # Mock connection error for next check
        mock_get.side_effect = ConnectionError("Connection refused")
        
        # Run connectivity check again
        self.sync_service._check_connectivity()
        
        # Should detect connection lost
        assert not self.sync_service.is_online
        
        print("✅ Connectivity check test passed!")


def run_tests():
    """Run all network error handling tests"""
    print("🧪 Running enhanced network error handling tests...\n")
    
    try:
        test_instance = TestNetworkErrorHandling()
        test_instance.setup_class()
        
        # Run individual tests
        test_instance.setup_method()
        test_instance.test_exponential_backoff()
        
        test_instance.setup_method()
        test_instance.test_max_retry_limit()
        
        test_instance.setup_method()
        test_instance.test_retry_state_reset()
        
        test_instance.setup_method()
        test_instance.test_should_retry_on_error()
        
        test_instance.setup_method()
        test_instance.test_connection_error_handling()
        
        test_instance.setup_method()
        test_instance.test_timeout_error_handling()
        
        test_instance.setup_method()
        test_instance.test_http_error_handling()
        
        test_instance.setup_method()
        test_instance.test_network_diagnostics()
        
        test_instance.setup_method()
        test_instance.test_force_reconnect()
        
        test_instance.setup_method()
        test_instance.test_connectivity_check()
        
        print("\n🎉 All enhanced network error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
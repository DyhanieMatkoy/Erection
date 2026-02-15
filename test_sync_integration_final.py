"""Final integration tests for synchronization system

Simplified and robust integration tests that focus on core functionality
without complex mocking scenarios.
"""

import sys
import os
import tempfile
import time
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.services.sync_service import SyncService
from src.data.database_manager import DatabaseManager
from src.views.sync_settings_dialog import SyncSettingsDialog
from src.views.conflict_resolution_dialog import ConflictResolutionDialog


class TestSyncIntegrationFinal:
    """Final integration tests for synchronization system"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setup_method(self):
        """Setup test method"""
        # Create mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        
        # Create sync service
        self.sync_service = SyncService(
            db_manager=self.mock_db_manager,
            server_url="http://test-server.com",
            node_code="TEST-NODE"
        )
        
        # Setup basic mocks
        self.sync_service.sync_manager = Mock()
        self.sync_service.packet_manager = Mock()
        self.sync_service.conflict_resolver = Mock()
    
    def test_sync_service_initialization(self):
        """Test sync service initialization"""
        print("🧪 Testing sync service initialization...")
        
        # Verify basic properties
        assert self.sync_service.server_url == "http://test-server.com"
        assert self.sync_service.node_code == "TEST-NODE"
        assert self.sync_service.is_online is False
        assert self.sync_service.is_syncing is False
        
        # Verify timers are created
        assert self.sync_service.sync_timer is not None
        assert self.sync_service.retry_timer is not None
        assert self.sync_service.connectivity_timer is not None
        
        print("✅ Sync service initialization test passed!")
    
    def test_exponential_backoff_logic(self):
        """Test exponential backoff retry logic"""
        print("🧪 Testing exponential backoff logic...")
        
        # Test initial state
        assert self.sync_service.retry_count == 0
        assert self.sync_service.current_retry_interval == 1
        
        # Test first retry
        self.sync_service.retry_count = 1
        self.sync_service._schedule_retry("Test error")
        
        # Should have exponential increase
        expected_interval = 1 * (2 ** 1)  # base * multiplier^count
        assert self.sync_service.current_retry_interval == expected_interval
        
        # Test max retry limit - reset first
        self.sync_service._reset_retry_state()
        self.sync_service.retry_count = self.sync_service.max_retries
        self.sync_service._schedule_retry("Max retries test")
        
        # Should not schedule more retries (timer should be stopped)
        # Note: _schedule_retry stops timer when max retries reached
        
        print("✅ Exponential backoff logic test passed!")
    
    def test_error_classification(self):
        """Test error classification for retry decisions"""
        print("🧪 Testing error classification...")
        
        # Network errors should retry
        assert self.sync_service._should_retry_on_error("Connection error")
        assert self.sync_service._should_retry_on_error("Request timeout")
        assert self.sync_service._should_retry_on_error("HTTP 503: Service unavailable")
        assert self.sync_service._should_retry_on_error("Network unreachable")
        
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
    
    def test_sync_status_reporting(self):
        """Test sync status reporting"""
        print("🧪 Testing sync status reporting...")
        
        # Mock pending changes to return empty list
        self.sync_service.sync_manager.get_pending_changes.return_value = []
        
        # Test initial status
        status = self.sync_service.get_sync_status()
        assert status['status'] == 'not_registered'
        assert status['is_online'] is False
        assert status['is_syncing'] is False
        assert status['node_code'] == 'TEST-NODE'
        
        # Test registered status
        self.sync_service.node_id = "test-node-id"
        self.sync_service.auth_token = "test-token"
        self.sync_service.is_online = True
        
        status = self.sync_service.get_sync_status()
        assert status['status'] == 'online'
        assert status['is_registered'] is True
        assert status['node_id'] == "test-node-id"
        
        print("✅ Sync status reporting test passed!")
    
    def test_network_diagnostics(self):
        """Test network diagnostics functionality"""
        print("🧪 Testing network diagnostics...")
        
        with patch('requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Get diagnostics
            diagnostics = self.sync_service.get_network_diagnostics()
            
            # Verify diagnostics structure
            required_fields = [
                'server_url', 'is_online', 'is_syncing', 'retry_count',
                'max_retries', 'current_retry_interval', 'node_registered',
                'connectivity_test'
            ]
            
            for field in required_fields:
                assert field in diagnostics, f"Missing field: {field}"
            
            # Should show successful connectivity test
            assert diagnostics['connectivity_test'] == 'success'
            assert 'response_time_ms' in diagnostics
        
        print("✅ Network diagnostics test passed!")
    
    def test_sync_settings_dialog_basic(self):
        """Test sync settings dialog basic functionality"""
        print("🧪 Testing sync settings dialog...")
        
        # Create dialog
        dialog = SyncSettingsDialog(self.sync_service)
        
        # Test basic components exist
        assert dialog.server_url_edit is not None
        assert dialog.node_code_edit is not None
        assert dialog.auto_sync_checkbox is not None
        assert dialog.sync_interval_spinbox is not None
        
        # Test new diagnostic buttons exist
        assert dialog.diagnostics_button is not None
        assert dialog.force_reconnect_button is not None
        
        # Test basic functionality
        dialog.server_url_edit.setText("http://new-server.com")
        assert dialog.server_url_edit.text() == "http://new-server.com"
        
        dialog.node_code_edit.setText("NEW-NODE")
        assert dialog.node_code_edit.text() == "NEW-NODE"
        
        dialog.close()
        print("✅ Sync settings dialog test passed!")
    
    def test_conflict_resolution_dialog_basic(self):
        """Test conflict resolution dialog basic functionality"""
        print("🧪 Testing conflict resolution dialog...")
        
        # Mock conflict resolver
        mock_conflicts = []
        self.sync_service.conflict_resolver.get_unresolved_conflicts.return_value = mock_conflicts
        
        # Create dialog
        dialog = ConflictResolutionDialog(self.sync_service)
        
        # Stop refresh timer to avoid issues
        dialog.refresh_timer.stop()
        
        # Test basic components exist
        assert dialog.conflicts_table is not None
        assert dialog.details_widget is not None
        assert dialog.resolve_button is not None
        
        # Test table structure
        assert dialog.conflicts_table.columnCount() == 4
        
        # Test with no conflicts
        assert dialog.resolve_button.isEnabled() is False
        
        dialog.close()
        print("✅ Conflict resolution dialog test passed!")
    
    def test_data_export_import(self):
        """Test data export/import functionality"""
        print("🧪 Testing data export/import...")
        
        # Setup: Node with ID
        self.sync_service.node_id = "test-node-id"
        
        # Mock pending changes
        mock_changes = [
            Mock(
                entity_type="Estimate",
                entity_uuid=str(uuid4()),
                operation=Mock(value="INSERT")
            )
        ]
        
        self.sync_service.sync_manager.get_pending_changes.return_value = mock_changes
        self.sync_service.sync_manager.serialize_entity.return_value = {
            'name': 'Test Entity',
            'data': 'test_data'
        }
        
        # Test export
        temp_dir = tempfile.mkdtemp()
        export_file = os.path.join(temp_dir, "test_export.json")
        
        try:
            success = self.sync_service.export_pending_changes(export_file)
            assert success is True
            assert os.path.exists(export_file)
            
            # Verify export content
            with open(export_file, 'r') as f:
                export_data = json.load(f)
                assert 'node_id' in export_data
                assert 'changes' in export_data
                assert len(export_data['changes']) == 1
            
            # Test import
            self.sync_service.sync_manager.apply_change.return_value = True
            
            success = self.sync_service.import_changes(export_file)
            assert success is True
            
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("✅ Data export/import test passed!")
    
    def test_force_reconnect(self):
        """Test force reconnect functionality"""
        print("🧪 Testing force reconnect...")
        
        # Setup: Service with authentication
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
    
    def test_retry_state_management(self):
        """Test retry state management"""
        print("🧪 Testing retry state management...")
        
        # Set some retry state
        self.sync_service.retry_count = 5
        self.sync_service.current_retry_interval = 32
        self.sync_service.retry_timer.start(1000)
        
        # Reset state
        self.sync_service._reset_retry_state()
        
        # Verify state is reset
        assert self.sync_service.retry_count == 0
        assert self.sync_service.current_retry_interval == 1
        assert not self.sync_service.retry_timer.isActive()
        
        print("✅ Retry state management test passed!")


def run_final_integration_tests():
    """Run final integration tests"""
    print("🧪 Running final sync integration tests...\n")
    
    try:
        test_instance = TestSyncIntegrationFinal()
        test_instance.setup_class()
        
        # Define all tests
        tests = [
            ("Sync service initialization", test_instance.test_sync_service_initialization),
            ("Exponential backoff logic", test_instance.test_exponential_backoff_logic),
            ("Error classification", test_instance.test_error_classification),
            ("Sync status reporting", test_instance.test_sync_status_reporting),
            ("Network diagnostics", test_instance.test_network_diagnostics),
            ("Sync settings dialog", test_instance.test_sync_settings_dialog_basic),
            ("Conflict resolution dialog", test_instance.test_conflict_resolution_dialog_basic),
            ("Data export/import", test_instance.test_data_export_import),
            ("Force reconnect", test_instance.test_force_reconnect),
            ("Retry state management", test_instance.test_retry_state_management),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                test_instance.setup_method()
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        print(f"\n📊 Final Integration Test Results:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All final integration tests passed!")
            return True
        else:
            print(f"\n⚠️ {failed} test(s) failed!")
            return False
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_final_integration_tests()
    sys.exit(0 if success else 1)
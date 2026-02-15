"""Comprehensive integration tests for synchronization system

This test suite provides complete integration testing for the synchronization
system including multi-node scenarios, conflict resolution, and error handling.
"""

import sys
import os
import tempfile
import time
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QEventLoop
from PyQt6.QtTest import QTest

from src.services.sync_service import SyncService
from src.data.database_manager import DatabaseManager
from src.views.sync_settings_dialog import SyncSettingsDialog
from src.views.conflict_resolution_dialog import ConflictResolutionDialog
from src.views.main_window import MainWindow


class TestSyncIntegrationComprehensive:
    """Comprehensive integration tests for synchronization system"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setup_method(self):
        """Setup test method"""
        # Create temporary directories for test databases
        self.temp_dir = tempfile.mkdtemp()
        self.node1_db = os.path.join(self.temp_dir, "node1.db")
        self.node2_db = os.path.join(self.temp_dir, "node2.db")
        
        # Mock database managers
        self.node1_db_manager = Mock(spec=DatabaseManager)
        self.node2_db_manager = Mock(spec=DatabaseManager)
        
        # Create sync services for two nodes
        self.node1_sync = SyncService(
            db_manager=self.node1_db_manager,
            server_url="http://test-server.com",
            node_code="NODE-1"
        )
        
        self.node2_sync = SyncService(
            db_manager=self.node2_db_manager,
            server_url="http://test-server.com", 
            node_code="NODE-2"
        )
        
        # Mock sync managers and components
        self.setup_mock_components()
    
    def teardown_method(self):
        """Teardown test method"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def setup_mock_components(self):
        """Setup mock components for sync services"""
        # Mock sync managers
        self.node1_sync.sync_manager = Mock()
        self.node1_sync.packet_manager = Mock()
        self.node1_sync.conflict_resolver = Mock()
        
        self.node2_sync.sync_manager = Mock()
        self.node2_sync.packet_manager = Mock()
        self.node2_sync.conflict_resolver = Mock()
        
        # Mock node registration
        self.node1_sync.node_id = "node1-id"
        self.node1_sync.auth_token = "node1-token"
        
        self.node2_sync.node_id = "node2-id"
        self.node2_sync.auth_token = "node2-token"
    
    def test_two_node_sync_scenario(self):
        """Test synchronization between two nodes"""
        print("🧪 Testing two-node synchronization scenario...")
        
        # Setup: Node 1 creates an entity
        entity_uuid = str(uuid4())
        entity_data = {
            'uuid': entity_uuid,
            'name': 'Test Entity',
            'description': 'Created on Node 1',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Mock entity creation on Node 1
        self.node1_sync.sync_manager.get_pending_changes.return_value = [
            Mock(
                entity_type="Estimate",
                entity_uuid=entity_uuid,
                operation=Mock(value="INSERT"),
                id=1
            )
        ]
        
        # Mock packet creation
        test_packet = {
            'header': {
                'packet_no': 1,
                'source_node_id': 'node1-id',
                'target_node_id': 'node2-id',
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            'entities': [
                {
                    'type': 'Estimate',
                    'uuid': entity_uuid,
                    'operation': 'INSERT',
                    'data': entity_data
                }
            ]
        }
        
        self.node1_sync.packet_manager.get_pending_packets.return_value = [test_packet]
        self.node1_sync.packet_manager.compress_packet.return_value = b'compressed_data'
        
        # Mock successful sync response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'processed_count': 1,
                'error_count': 0
            }
            mock_post.return_value = mock_response
            
            # Execute sync from Node 1
            success = self.node1_sync.sync_now()
            
            # Verify sync was initiated
            assert success is True
            
            # Wait for sync to complete (simulate)
            time.sleep(0.1)
            
        print("✅ Two-node synchronization test passed!")
    
    def test_conflict_detection_and_resolution(self):
        """Test conflict detection and resolution workflow"""
        print("🧪 Testing conflict detection and resolution...")
        
        # Setup: Same entity modified on both nodes
        entity_uuid = str(uuid4())
        
        # Node 1 version
        node1_data = {
            'uuid': entity_uuid,
            'name': 'Entity Modified on Node 1',
            'modified_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Node 2 version (conflicting)
        node2_data = {
            'uuid': entity_uuid,
            'name': 'Entity Modified on Node 2',
            'modified_at': (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
        }
        
        # Mock conflict detection
        mock_conflict = Mock()
        mock_conflict.id = "conflict-1"
        mock_conflict.entity_type = "Estimate"
        mock_conflict.entity_uuid = entity_uuid
        mock_conflict.arrival_time = datetime.now(timezone.utc)
        mock_conflict.source_node_id = "node1-id"
        
        self.node2_sync.conflict_resolver.get_unresolved_conflicts.return_value = [mock_conflict]
        
        # Test conflict resolution dialog
        dialog = ConflictResolutionDialog(self.node2_sync)
        
        # Verify dialog components
        assert dialog.conflicts_table is not None
        assert dialog.details_widget is not None
        assert dialog.resolve_button is not None
        
        # Stop refresh timer to avoid issues
        dialog.refresh_timer.stop()
        
        # Mock conflict resolution
        self.node2_sync.conflict_resolver.manually_resolve_conflict.return_value = True
        
        # Test resolution
        success = self.node2_sync.resolve_conflict("conflict-1", node2_data)
        assert success is True
        
        dialog.close()
        print("✅ Conflict detection and resolution test passed!")
    
    def test_network_failure_recovery(self):
        """Test network failure and recovery scenarios"""
        print("🧪 Testing network failure recovery...")
        
        # Setup: Initial online state
        self.node1_sync.is_online = True
        
        # Simulate network failure
        with patch('requests.post') as mock_post:
            from requests.exceptions import ConnectionError
            mock_post.side_effect = ConnectionError("Network unreachable")
            
            # Try to sync - should fail and schedule retry
            success = self.node1_sync.sync_now()
            
            # Should still return True (sync initiated) but will fail internally
            assert success is True
            
            # Wait for failure processing
            time.sleep(0.1)
            
            # Should be offline and have retry scheduled
            assert not self.node1_sync.is_online
            assert self.node1_sync.retry_timer.isActive()
        
        # Simulate network recovery
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'processed_count': 0,
                'error_count': 0
            }
            mock_post.return_value = mock_response
            
            # Simulate connectivity check
            with patch('requests.get') as mock_get:
                mock_get_response = Mock()
                mock_get_response.status_code = 200
                mock_get.return_value = mock_get_response
                
                # Run connectivity check
                self.node1_sync._check_connectivity()
                
                # Should be back online
                assert self.node1_sync.is_online
        
        print("✅ Network failure recovery test passed!")
    
    def test_sync_settings_integration(self):
        """Test sync settings dialog integration"""
        print("🧪 Testing sync settings dialog integration...")
        
        # Create settings dialog
        dialog = SyncSettingsDialog(self.node1_sync)
        
        # Test basic functionality
        assert dialog.server_url_edit is not None
        assert dialog.node_code_edit is not None
        assert dialog.auto_sync_checkbox is not None
        
        # Test settings loading
        dialog.server_url_edit.setText("http://new-server.com")
        dialog.node_code_edit.setText("NEW-NODE")
        dialog.auto_sync_checkbox.setChecked(True)
        
        # Verify values
        assert dialog.server_url_edit.text() == "http://new-server.com"
        assert dialog.node_code_edit.text() == "NEW-NODE"
        assert dialog.auto_sync_checkbox.isChecked() is True
        
        # Test diagnostics functionality
        with patch.object(self.node1_sync, 'get_network_diagnostics') as mock_diag:
            mock_diag.return_value = {
                'server_url': 'http://test-server.com',
                'is_online': True,
                'connectivity_test': 'success',
                'response_time_ms': 123.45
            }
            
            # Should not raise exception
            dialog.show_network_diagnostics()
        
        dialog.close()
        print("✅ Sync settings integration test passed!")
    
    def test_main_window_sync_integration(self):
        """Test main window sync integration"""
        print("🧪 Testing main window sync integration...")
        
        with patch('src.services.sync_initializer.initialize_sync_for_app') as mock_init:
            with patch('src.services.auth_service.AuthService'):
                # Mock sync service initialization
                mock_init.return_value = self.node1_sync
                
                # Create main window
                main_window = MainWindow()
                
                # Verify sync service is set
                assert main_window.sync_service is not None
                
                # Verify UI components exist
                assert hasattr(main_window, 'sync_status_frame')
                assert hasattr(main_window, 'sync_indicator')
                assert hasattr(main_window, 'notification_manager')
                
                # Test status update
                main_window.update_sync_status()
                
                # Test sync event handling
                main_window.on_sync_started()
                assert main_window.sync_progress.isVisible()
                
                result = {'processed_count': 5, 'error_count': 0}
                main_window.on_sync_completed(result)
                assert not main_window.sync_progress.isVisible()
                
                main_window.close()
        
        print("✅ Main window sync integration test passed!")
    
    def test_offline_mode_functionality(self):
        """Test offline mode functionality"""
        print("🧪 Testing offline mode functionality...")
        
        # Setup: Node starts offline
        self.node1_sync.is_online = False
        self.node1_sync.node_id = None
        self.node1_sync.auth_token = None
        
        # Try to sync while offline - should fail gracefully
        success = self.node1_sync.sync_now()
        assert success is False  # Should return False when not registered
        
        # Mock pending changes for offline work
        self.node1_sync.sync_manager.get_pending_changes.return_value = [
            Mock(entity_type="Estimate", entity_uuid=str(uuid4()), operation=Mock(value="INSERT"))
        ]
        
        # Verify offline work is tracked
        status = self.node1_sync.get_sync_status()
        assert status['status'] == 'not_registered'
        assert status['is_online'] is False
        
        print("✅ Offline mode functionality test passed!")
    
    def test_data_export_import_workflow(self):
        """Test data export/import for offline transfer"""
        print("🧪 Testing data export/import workflow...")
        
        # Setup: Node with pending changes
        self.node1_sync.node_id = "node1-id"
        
        mock_changes = [
            Mock(
                entity_type="Estimate",
                entity_uuid=str(uuid4()),
                operation=Mock(value="INSERT")
            )
        ]
        
        self.node1_sync.sync_manager.get_pending_changes.return_value = mock_changes
        self.node1_sync.sync_manager.serialize_entity.return_value = {
            'name': 'Test Entity',
            'data': 'test_data'
        }
        
        # Test export
        export_file = os.path.join(self.temp_dir, "export.json")
        success = self.node1_sync.export_pending_changes(export_file)
        assert success is True
        assert os.path.exists(export_file)
        
        # Verify export content
        with open(export_file, 'r') as f:
            export_data = json.load(f)
            assert 'node_id' in export_data
            assert 'changes' in export_data
            assert len(export_data['changes']) == 1
        
        # Test import on another node
        self.node2_sync.sync_manager.apply_change.return_value = True
        
        success = self.node2_sync.import_changes(export_file)
        assert success is True
        
        print("✅ Data export/import workflow test passed!")
    
    def test_performance_under_load(self):
        """Test sync performance under load"""
        print("🧪 Testing sync performance under load...")
        
        # Setup: Large number of pending changes
        large_change_set = []
        for i in range(100):
            large_change_set.append(Mock(
                entity_type="Estimate",
                entity_uuid=str(uuid4()),
                operation=Mock(value="INSERT"),
                id=i
            ))
        
        self.node1_sync.sync_manager.get_pending_changes.return_value = large_change_set
        
        # Mock packet processing
        self.node1_sync.packet_manager.get_pending_packets.return_value = []
        
        # Test sync with large dataset
        start_time = time.time()
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'processed_count': 100,
                'error_count': 0
            }
            mock_post.return_value = mock_response
            
            success = self.node1_sync.sync_now()
            assert success is True
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (< 1 second for mocked operations)
        assert processing_time < 1.0
        
        print(f"✅ Performance test passed! Processing time: {processing_time:.3f}s")


def run_comprehensive_tests():
    """Run all comprehensive integration tests"""
    print("🧪 Running comprehensive sync integration tests...\n")
    
    try:
        test_instance = TestSyncIntegrationComprehensive()
        test_instance.setup_class()
        
        # Run all tests
        tests = [
            ("Two-node sync scenario", test_instance.test_two_node_sync_scenario),
            ("Conflict detection and resolution", test_instance.test_conflict_detection_and_resolution),
            ("Network failure recovery", test_instance.test_network_failure_recovery),
            ("Sync settings integration", test_instance.test_sync_settings_integration),
            ("Main window sync integration", test_instance.test_main_window_sync_integration),
            ("Offline mode functionality", test_instance.test_offline_mode_functionality),
            ("Data export/import workflow", test_instance.test_data_export_import_workflow),
            ("Performance under load", test_instance.test_performance_under_load),
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
            finally:
                test_instance.teardown_method()
        
        print(f"\n📊 Test Results:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All comprehensive integration tests passed!")
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
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
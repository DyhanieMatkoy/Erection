"""Test sync UI integration

This test verifies that the sync UI components work correctly
and integrate properly with the sync service.
"""

import sys
import os
import tempfile
import configparser
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

from src.views.main_window import MainWindow
from src.views.sync_settings_dialog import SyncSettingsDialog
from src.views.conflict_resolution_dialog import ConflictResolutionDialog
from src.views.sync_notification_widget import SyncNotificationManager
from src.services.sync_initializer import SyncInitializer
from src.data.database_manager import DatabaseManager


class TestSyncUIIntegration:
    """Test sync UI integration"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setup_method(self):
        """Setup test method"""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "env.ini")
        
        # Mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        
        # Create test config
        self.create_test_config()
    
    def teardown_method(self):
        """Teardown test method"""
        # Clean up temporary files
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def create_test_config(self):
        """Create test configuration file"""
        config = configparser.ConfigParser()
        config.add_section('Sync')
        config['Sync']['enabled'] = 'true'
        config['Sync']['server_url'] = 'http://test-server.com'
        config['Sync']['node_code'] = 'TEST-NODE'
        config['Sync']['auto_sync'] = 'true'
        config['Sync']['sync_interval'] = '300'
        config['Sync']['compression_enabled'] = 'true'
        config['Sync']['conflict_resolution'] = 'server_wins'
        
        with open(self.config_path, 'w') as f:
            config.write(f)
    
    @patch('src.services.sync_initializer.initialize_sync_for_app')
    @patch('src.services.auth_service.AuthService')
    def test_main_window_sync_initialization(self, mock_auth_service, mock_init_sync):
        """Test that main window initializes sync service correctly"""
        # Mock sync service
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status.return_value = {
            'status': 'offline',
            'is_registered': False,
            'pending_changes': 0
        }
        mock_init_sync.return_value = mock_sync_service
        
        # Create main window
        with patch('os.getcwd', return_value=self.temp_dir):
            main_window = MainWindow()
        
        # Verify sync service was initialized
        mock_init_sync.assert_called_once()
        assert main_window.sync_service is not None
        
        # Verify UI components are set up
        assert hasattr(main_window, 'sync_status_frame')
        assert hasattr(main_window, 'sync_indicator')
        assert hasattr(main_window, 'sync_status_label')
        assert hasattr(main_window, 'conflicts_button')
        assert hasattr(main_window, 'notification_manager')
        
        main_window.close()
    
    def test_sync_initializer_with_config(self):
        """Test sync initializer with configuration"""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            initializer = SyncInitializer(self.mock_db_manager)
            
            # Test config loading
            config = initializer._load_sync_config()
            assert config is not None
            assert config['enabled'] is True
            assert config['server_url'] == 'http://test-server.com'
            assert config['node_code'] == 'TEST-NODE'
        finally:
            os.chdir(original_cwd)
    
    def test_sync_initializer_without_config(self):
        """Test sync initializer without configuration"""
        # Remove config file
        os.remove(self.config_path)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            initializer = SyncInitializer(self.mock_db_manager)
            
            # Test config loading
            config = initializer._load_sync_config()
            assert config is None
            
            # Test default config creation
            initializer.create_default_config()
            assert os.path.exists("env.ini")  # Check in current directory
            
            # Verify default config
            config = initializer._load_sync_config()
            assert config is not None
            assert config['enabled'] is False  # Default is disabled
        finally:
            os.chdir(original_cwd)
    
    @patch('src.services.sync_service.SyncService')
    def test_sync_settings_dialog(self, mock_sync_service_class):
        """Test sync settings dialog"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status.return_value = {
            'status': 'offline',
            'is_registered': False,
            'pending_changes': 0,
            'last_sync_time': None
        }
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            dialog = SyncSettingsDialog(mock_sync_service)
        
            # Verify dialog components
            assert dialog.server_url_edit is not None
            assert dialog.node_code_edit is not None
            assert dialog.auto_sync_checkbox is not None
            assert dialog.sync_interval_spinbox is not None
            
            # Test loading settings
            dialog.load_settings()
            assert dialog.server_url_edit.text() == 'http://test-server.com'
            assert dialog.node_code_edit.text() == 'TEST-NODE'
            assert dialog.auto_sync_checkbox.isChecked() is True
            
            dialog.close()
        finally:
            os.chdir(original_cwd)
    
    def test_conflict_resolution_dialog(self):
        """Test conflict resolution dialog"""
        mock_sync_service = Mock()
        mock_conflict_resolver = Mock()
        mock_conflict_resolver.get_unresolved_conflicts.return_value = []
        mock_sync_service.conflict_resolver = mock_conflict_resolver
        
        dialog = ConflictResolutionDialog(mock_sync_service)
        
        # Verify dialog components
        assert dialog.conflicts_table is not None
        assert dialog.details_widget is not None
        assert dialog.resolve_button is not None
        
        # Stop the refresh timer to avoid multiple calls
        dialog.refresh_timer.stop()
        
        # Test loading conflicts (called once in __init__ and once manually)
        dialog.load_conflicts()
        assert mock_conflict_resolver.get_unresolved_conflicts.call_count >= 1
        
        dialog.close()
    
    def test_sync_notification_manager(self):
        """Test sync notification manager"""
        # Create a real QWidget as parent
        from PyQt6.QtWidgets import QWidget
        parent_widget = QWidget()
        parent_widget.setGeometry(0, 0, 1000, 800)
        
        manager = SyncNotificationManager(parent_widget)
        
        # Test showing notifications
        manager.show_notification("Test Title", "Test Message", "info")
        assert len(manager.notifications) == 1
        
        manager.show_sync_started()
        assert len(manager.notifications) == 2
        
        manager.show_sync_completed(10, 0)
        assert len(manager.notifications) == 3
        
        manager.show_sync_failed("Test error")
        assert len(manager.notifications) == 4
        
        manager.show_conflict_detected(2)
        assert len(manager.notifications) == 5
        
        # Test notification limit
        manager.show_notification("Extra", "Extra message", "info")
        assert len(manager.notifications) == 5  # Should still be 5 (limit)
        
        manager.clear_all_notifications()
        # Note: notifications are cleared asynchronously, so we can't assert count immediately
        
        parent_widget.close()
    
    @patch('src.services.sync_service.SyncService')
    def test_sync_status_updates(self, mock_sync_service_class):
        """Test sync status updates in main window"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status.return_value = {
            'status': 'online',
            'is_registered': True,
            'pending_changes': 5,
            'last_sync_time': '2024-01-01T12:00:00'
        }
        
        with patch('src.services.sync_initializer.initialize_sync_for_app', return_value=mock_sync_service):
            with patch('src.services.auth_service.AuthService'):
                main_window = MainWindow()
        
        # Test status update
        main_window.update_sync_status()
        
        # Verify status is reflected in UI
        assert "Онлайн" in main_window.sync_status_label.text()
        assert "green" in main_window.sync_indicator.styleSheet()
        
        # Test offline status
        mock_sync_service.get_sync_status.return_value['status'] = 'offline'
        mock_sync_service.get_sync_status.return_value['is_registered'] = True
        
        main_window.update_sync_status()
        assert "Офлайн" in main_window.sync_status_label.text()
        assert "orange" in main_window.sync_indicator.styleSheet()
        
        main_window.close()
    
    def test_sync_progress_indication(self):
        """Test sync progress indication"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status.return_value = {
            'status': 'offline',
            'is_registered': False,
            'pending_changes': 0
        }
        
        with patch('src.services.sync_initializer.initialize_sync_for_app', return_value=mock_sync_service):
            with patch('src.services.auth_service.AuthService'):
                main_window = MainWindow()
        
        # Test sync started
        main_window.on_sync_started()
        assert main_window.sync_progress.isVisible()
        assert main_window.sync_progress.maximum() == 0  # Indeterminate
        
        # Test sync completed
        result = {'processed_count': 10, 'error_count': 0}
        main_window.on_sync_completed(result)
        assert not main_window.sync_progress.isVisible()
        
        # Test sync failed
        main_window.on_sync_started()  # Start again
        main_window.on_sync_failed("Test error")
        assert not main_window.sync_progress.isVisible()
        
        main_window.close()


def run_tests():
    """Run all tests"""
    import pytest
    
    # Run tests
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
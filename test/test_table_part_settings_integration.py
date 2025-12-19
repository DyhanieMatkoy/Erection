"""
Integration tests for table part settings system.

Tests the complete settings workflow including storage, retrieval,
migration, and UI integration.
"""

import pytest
import json
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.services.table_part_settings_service import TablePartSettingsService
from src.services.table_part_settings_migration import TablePartSettingsMigrator
from src.data.models.table_part_models import (
    TablePartSettingsData, PanelSettings, ShortcutSettings
)
from src.data.models.sqlalchemy_models import UserTablePartSettings, User


class TestTablePartSettingsIntegration:
    """Test table part settings integration"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def settings_service(self, mock_db_session):
        """Create settings service with mock session"""
        return TablePartSettingsService(mock_db_session)
    
    @pytest.fixture
    def sample_settings(self):
        """Create sample settings data"""
        panel_settings = PanelSettings(
            visible_commands=['add_row', 'delete_row', 'move_up', 'move_down'],
            button_size='medium',
            show_tooltips=True,
            compact_mode=False
        )
        
        shortcuts = ShortcutSettings(
            enabled=True,
            custom_mappings={'Ctrl+D': 'duplicate_row'}
        )
        
        return TablePartSettingsData(
            column_widths={'name': 200, 'quantity': 100},
            column_order=['name', 'quantity', 'price'],
            hidden_columns=[],
            panel_settings=panel_settings,
            shortcuts=shortcuts,
            sort_column='name',
            sort_direction='asc'
        )
    
    def test_settings_serialization_round_trip(self, sample_settings):
        """Test settings can be serialized and deserialized correctly"""
        # Serialize to JSON
        json_str = sample_settings.to_json()
        
        # Deserialize back
        restored_settings = TablePartSettingsData.from_json(json_str)
        
        # Verify all data is preserved
        assert restored_settings.column_widths == sample_settings.column_widths
        assert restored_settings.column_order == sample_settings.column_order
        assert restored_settings.panel_settings.visible_commands == sample_settings.panel_settings.visible_commands
        assert restored_settings.shortcuts.enabled == sample_settings.shortcuts.enabled
        assert restored_settings.shortcuts.custom_mappings == sample_settings.shortcuts.custom_mappings
    
    def test_save_and_load_user_settings(self, settings_service, mock_db_session, sample_settings):
        """Test saving and loading user settings"""
        user_id = 1
        document_type = 'estimate'
        table_part_id = 'lines'
        
        # Mock database query for existing settings (none found)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test saving new settings
        success = settings_service.save_user_settings(
            user_id, document_type, table_part_id, sample_settings
        )
        
        assert success
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_get_default_settings(self, settings_service):
        """Test getting default settings"""
        document_type = 'estimate'
        table_part_id = 'lines'
        
        default_settings = settings_service.get_default_settings(document_type, table_part_id)
        
        assert isinstance(default_settings, TablePartSettingsData)
        assert default_settings.panel_settings.button_size == 'medium'
        assert default_settings.shortcuts.enabled is True
        assert 'add_row' in default_settings.panel_settings.visible_commands
    
    def test_settings_validation(self, settings_service, sample_settings):
        """Test settings validation"""
        # Valid settings
        is_valid, errors = settings_service.validate_settings_data(sample_settings.to_json())
        assert is_valid
        assert len(errors) == 0
        
        # Invalid settings - missing required field
        invalid_data = sample_settings.to_dict()
        del invalid_data['panel_settings']
        invalid_json = json.dumps(invalid_data)
        
        is_valid, errors = settings_service.validate_settings_data(invalid_json)
        assert not is_valid
        assert len(errors) > 0
        assert any('panel_settings' in error for error in errors)
    
    def test_settings_migration(self, mock_db_session):
        """Test settings migration from old version"""
        migrator = TablePartSettingsMigrator(mock_db_session)
        
        # Create old version settings (0.9)
        old_settings = {
            'visible_commands': ['add_row', 'delete_row'],
            'button_size': 'medium'
        }
        
        # Apply migration
        migrated = migrator.settings_service._apply_settings_migrations(
            old_settings, '0.9', '1.0'
        )
        
        # Verify migration results
        assert 'panel_settings' in migrated
        assert 'shortcuts' in migrated
        assert migrated['panel_settings']['visible_commands'] == ['add_row', 'delete_row', 'move_up', 'move_down']
        assert migrated['shortcuts']['enabled'] is True
    
    def test_export_import_settings(self, settings_service, mock_db_session, sample_settings):
        """Test settings export and import"""
        user_id = 1
        
        # Mock database records for export
        mock_record = Mock()
        mock_record.document_type = 'estimate'
        mock_record.table_part_id = 'lines'
        mock_record.settings_data = sample_settings.to_json()
        mock_record.created_at = Mock()
        mock_record.updated_at = Mock()
        mock_record.created_at.isoformat.return_value = '2024-01-01T00:00:00'
        mock_record.updated_at.isoformat.return_value = '2024-01-01T00:00:00'
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_record]
        
        # Test export
        export_data = settings_service.export_user_settings(user_id)
        
        assert export_data['user_id'] == user_id
        assert len(export_data['settings']) == 1
        assert export_data['settings'][0]['document_type'] == 'estimate'
        
        # Test import
        import_result = settings_service.import_user_settings(
            user_id, export_data, overwrite_existing=True
        )
        
        assert import_result['success']
        assert import_result['imported_count'] == 1
    
    def test_reset_settings(self, settings_service, mock_db_session):
        """Test resetting settings to defaults"""
        user_id = 1
        document_type = 'estimate'
        table_part_id = 'lines'
        
        # Mock successful deletion
        mock_db_session.query.return_value.filter.return_value.delete.return_value = 1
        
        success = settings_service.reset_user_settings(user_id, document_type, table_part_id)
        
        assert success
        mock_db_session.commit.assert_called_once()
    
    @patch('src.views.widgets.base_table_part.TablePartSettingsService')
    def test_base_table_part_settings_integration(self, mock_settings_service_class):
        """Test base table part widget settings integration"""
        from src.views.widgets.base_table_part import BaseTablePart, TablePartConfiguration
        from src.data.models.table_part_models import TablePartCommand
        
        # Mock settings service
        mock_settings_service = Mock()
        mock_settings_service_class.return_value = mock_settings_service
        
        # Create sample configuration
        config = TablePartConfiguration(
            table_id='lines',
            document_type='estimate',
            available_commands=[],
            visible_commands=['add_row', 'delete_row'],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=True,
            drag_drop_enabled=True
        )
        
        # Mock database session and user ID
        mock_db_session = Mock()
        user_id = 1
        
        # Mock settings loading
        sample_settings = TablePartSettingsData(
            panel_settings=PanelSettings(
                visible_commands=['add_row', 'delete_row', 'import_data'],
                button_size='large'
            ),
            shortcuts=ShortcutSettings(enabled=False)
        )
        mock_settings_service.get_user_settings.return_value = sample_settings
        
        # This would normally create a QWidget, but we'll mock it for testing
        with patch('src.views.widgets.base_table_part.QWidget'):
            # Create table part with settings
            table_part = BaseTablePart(config, db_session=mock_db_session, user_id=user_id)
            
            # Verify settings were loaded
            mock_settings_service.get_user_settings.assert_called_once_with(
                user_id, 'estimate', 'lines'
            )
            
            # Verify settings were applied to configuration
            assert table_part.config.visible_commands == ['add_row', 'delete_row', 'import_data']
            assert table_part.config.keyboard_shortcuts_enabled is False
    
    def test_settings_version_handling(self, settings_service):
        """Test settings version handling and migration triggers"""
        # Test current version settings (no migration needed)
        current_settings = {
            'version': '1.0',
            'panel_settings': {'visible_commands': ['add_row']},
            'shortcuts': {'enabled': True}
        }
        
        migrated_json, was_migrated = settings_service.migrate_settings_if_needed(
            json.dumps(current_settings)
        )
        
        assert not was_migrated
        
        # Test old version settings (migration needed)
        old_settings = {
            'visible_commands': ['add_row']  # Old format, no version
        }
        
        migrated_json, was_migrated = settings_service.migrate_settings_if_needed(
            json.dumps(old_settings)
        )
        
        assert was_migrated
        migrated_data = json.loads(migrated_json)
        assert migrated_data['version'] == '1.0'
        assert 'panel_settings' in migrated_data
        assert 'shortcuts' in migrated_data


if __name__ == '__main__':
    pytest.main([__file__])
"""
Tests for panel configuration functionality.

This module tests the panel configuration dialog and settings persistence
to ensure proper functionality according to requirements.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.panel_configuration_service import PanelConfigurationService
from src.data.models.table_part_models import (
    TablePartCommand, PanelSettings, TablePartFactory, CommandType
)


class TestPanelConfigurationService:
    """Test panel configuration service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.service = PanelConfigurationService(self.mock_db_session)
        
        # Create test commands
        self.test_commands = [
            TablePartCommand(
                id='add_row',
                name='Добавить',
                icon='➕',
                tooltip='Добавить новую строку',
                enabled=True,
                visible=True,
                position=1
            ),
            TablePartCommand(
                id='delete_row',
                name='Удалить',
                icon='🗑',
                tooltip='Удалить выбранные строки',
                enabled=True,
                visible=True,
                position=2,
                requires_selection=True
            ),
            TablePartCommand(
                id='import_data',
                name='Импорт',
                icon='📥',
                tooltip='Импортировать данные',
                enabled=True,
                visible=False,
                position=3
            )
        ]
        
        # Create test panel settings
        self.test_panel_settings = PanelSettings(
            visible_commands=['add_row', 'delete_row'],
            hidden_commands=['import_data'],
            button_size='medium',
            show_tooltips=True,
            compact_mode=False
        )
    
    @patch('src.services.panel_configuration_service.TablePartSettingsService')
    def test_save_panel_configuration_success(self, mock_settings_service_class):
        """Test successful panel configuration save"""
        # Arrange
        mock_settings_service = Mock()
        mock_settings_service_class.return_value = mock_settings_service
        mock_settings_service.save_user_settings.return_value = True
        mock_settings_service.save_command_configuration.return_value = True
        
        # Act
        result = self.service.save_panel_configuration(
            user_id=1,
            document_type='estimate',
            commands=self.test_commands,
            panel_settings=self.test_panel_settings,
            apply_to_all_table_parts=True
        )
        
        # Assert
        assert result is True
        mock_settings_service.save_user_settings.assert_called()
        mock_settings_service.save_command_configuration.assert_called()
    
    @patch('src.services.panel_configuration_service.TablePartSettingsService')
    def test_load_panel_configuration_with_existing_settings(self, mock_settings_service_class):
        """Test loading panel configuration with existing user settings"""
        # Arrange
        mock_settings_service = Mock()
        mock_settings_service_class.return_value = mock_settings_service
        
        # Mock existing settings
        from src.data.models.table_part_models import TablePartSettingsData
        mock_settings_data = TablePartSettingsData(
            panel_settings=self.test_panel_settings
        )
        mock_settings_service.get_user_settings.return_value = mock_settings_data
        mock_settings_service.get_command_configuration.return_value = self.test_commands
        
        # Act
        commands, panel_settings = self.service.load_panel_configuration(
            user_id=1,
            document_type='estimate',
            table_part_id='lines'
        )
        
        # Assert
        assert len(commands) == 3
        assert commands[0].id == 'add_row'
        assert panel_settings.visible_commands == ['add_row', 'delete_row']
        assert panel_settings.button_size == 'medium'
    
    @patch('src.services.panel_configuration_service.TablePartSettingsService')
    def test_load_panel_configuration_with_defaults(self, mock_settings_service_class):
        """Test loading panel configuration returns defaults when no settings exist"""
        # Arrange
        mock_settings_service = Mock()
        mock_settings_service_class.return_value = mock_settings_service
        mock_settings_service.get_user_settings.return_value = None
        
        # Act
        commands, panel_settings = self.service.load_panel_configuration(
            user_id=1,
            document_type='estimate'
        )
        
        # Assert
        assert len(commands) > 0  # Should return default commands
        assert isinstance(panel_settings, PanelSettings)
        assert panel_settings.button_size == 'medium'
        assert panel_settings.show_tooltips is True
    
    @patch('src.services.panel_configuration_service.TablePartSettingsService')
    def test_reset_panel_configuration(self, mock_settings_service_class):
        """Test resetting panel configuration to defaults"""
        # Arrange
        mock_settings_service = Mock()
        mock_settings_service_class.return_value = mock_settings_service
        mock_settings_service.reset_user_settings.return_value = True
        
        # Act
        result = self.service.reset_panel_configuration(
            user_id=1,
            document_type='estimate',
            apply_to_all_table_parts=True
        )
        
        # Assert
        assert result is True
        mock_settings_service.reset_user_settings.assert_called()
    
    def test_get_table_part_ids_for_document_type(self):
        """Test getting table part IDs for different document types"""
        # Test estimate document type
        estimate_parts = self.service._get_table_part_ids_for_document_type('estimate')
        assert 'lines' in estimate_parts
        assert 'materials' in estimate_parts
        
        # Test daily report document type
        report_parts = self.service._get_table_part_ids_for_document_type('daily_report')
        assert 'works' in report_parts
        assert 'materials' in report_parts
        
        # Test unknown document type
        unknown_parts = self.service._get_table_part_ids_for_document_type('unknown')
        assert unknown_parts == ['main']
    
    def test_get_main_table_part_id(self):
        """Test getting main table part ID for document types"""
        assert self.service._get_main_table_part_id('estimate') == 'lines'
        assert self.service._get_main_table_part_id('daily_report') == 'works'
        assert self.service._get_main_table_part_id('timesheet') == 'entries'
        assert self.service._get_main_table_part_id('unknown') == 'main'
    
    def test_get_default_commands(self):
        """Test getting default commands"""
        commands = self.service._get_default_commands('estimate')
        
        assert len(commands) > 0
        assert any(cmd.id == CommandType.ADD_ROW.value for cmd in commands)
        assert any(cmd.id == CommandType.DELETE_ROW.value for cmd in commands)
        assert any(cmd.id == CommandType.MOVE_UP.value for cmd in commands)
        assert any(cmd.id == CommandType.MOVE_DOWN.value for cmd in commands)
    
    def test_get_default_panel_settings(self):
        """Test getting default panel settings"""
        settings = self.service._get_default_panel_settings('estimate')
        
        assert isinstance(settings, PanelSettings)
        assert len(settings.visible_commands) == 4  # First 4 commands by default
        assert settings.button_size == 'medium'
        assert settings.show_tooltips is True
        assert settings.compact_mode is False
    
    def test_apply_version_migration(self):
        """Test version migration functionality"""
        # Test migration from 1.0 to 1.1 (adds compact_mode)
        old_settings = {
            'panel_settings': {
                'visible_commands': ['add_row', 'delete_row'],
                'button_size': 'medium',
                'show_tooltips': True
            }
        }
        
        migrated = self.service._apply_version_migration(old_settings, '1.0', '1.1')
        
        assert 'compact_mode' in migrated['panel_settings']
        assert migrated['panel_settings']['compact_mode'] is False
        
        # Test migration from 1.1 to 1.2 (converts button size)
        old_settings_v11 = {
            'panel_settings': {
                'visible_commands': ['add_row', 'delete_row'],
                'button_size': 1,  # Old numeric value
                'show_tooltips': True,
                'compact_mode': False
            }
        }
        
        migrated_v12 = self.service._apply_version_migration(old_settings_v11, '1.1', '1.2')
        
        assert migrated_v12['panel_settings']['button_size'] == 'medium'


class TestTablePartFactory:
    """Test table part factory functionality"""
    
    def test_create_standard_commands(self):
        """Test creating standard commands"""
        commands = TablePartFactory.create_standard_commands()
        
        assert len(commands) == 7  # Standard number of commands
        
        # Check that all required commands are present
        command_ids = [cmd.id for cmd in commands]
        assert CommandType.ADD_ROW.value in command_ids
        assert CommandType.DELETE_ROW.value in command_ids
        assert CommandType.MOVE_UP.value in command_ids
        assert CommandType.MOVE_DOWN.value in command_ids
        assert CommandType.IMPORT_DATA.value in command_ids
        assert CommandType.EXPORT_DATA.value in command_ids
        assert CommandType.PRINT_DATA.value in command_ids
        
        # Check command properties
        add_command = next(cmd for cmd in commands if cmd.id == CommandType.ADD_ROW.value)
        assert add_command.name == 'Добавить'
        assert add_command.icon == '➕'
        assert add_command.requires_selection is False
        
        delete_command = next(cmd for cmd in commands if cmd.id == CommandType.DELETE_ROW.value)
        assert delete_command.name == 'Удалить'
        assert delete_command.icon == '🗑'
        assert delete_command.requires_selection is True
    
    def test_create_default_configuration(self):
        """Test creating default table part configuration"""
        config = TablePartFactory.create_default_configuration('estimate', 'lines')
        
        assert config.table_id == 'lines'
        assert config.document_type == 'estimate'
        assert len(config.available_commands) == 7
        assert len(config.visible_commands) == 4  # First 4 commands visible by default
        assert config.keyboard_shortcuts_enabled is True
        assert config.auto_calculation_enabled is True
        assert config.drag_drop_enabled is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
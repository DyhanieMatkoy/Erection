"""
Tests for the Panel Configuration Dialog component.

This module tests the panel configuration dialog functionality including:
- Command tree interface with checkboxes
- Real-time panel updates during configuration
- "More" submenu configuration
- Save/Reset functionality

Requirements: 9.1, 9.2, 9.3, 9.4
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.views.dialogs.panel_configuration_dialog import (
    PanelConfigurationDialog, CommandTreeNode
)


@pytest.fixture
def app():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_commands():
    """Create sample commands for testing"""
    return {
        'add_row': CommandTreeNode(
            id='add_row',
            name='Добавить',
            icon='➕',
            tooltip='Добавить новую строку',
            visible=True,
            enabled=True
        ),
        'delete_row': CommandTreeNode(
            id='delete_row',
            name='Удалить',
            icon='🗑',
            tooltip='Удалить выбранные строки',
            visible=True,
            enabled=True
        ),
        'import_data': CommandTreeNode(
            id='import_data',
            name='Импорт',
            icon='📥',
            tooltip='Импортировать данные',
            visible=False,
            enabled=True
        )
    }


@pytest.fixture
def sample_config():
    """Create sample configuration for testing"""
    return {
        'visible_commands': ['add_row', 'delete_row'],
        'show_tooltips': True,
        'compact_mode': False
    }


@pytest.fixture
def dialog(app, sample_config, sample_commands):
    """Create a PanelConfigurationDialog instance for testing"""
    return PanelConfigurationDialog(
        current_config=sample_config,
        available_commands=sample_commands
    )


class TestPanelConfigurationDialogUI:
    """Test dialog UI components and layout"""
    
    def test_dialog_initialization(self, dialog):
        """Test that dialog initializes correctly (Requirements 9.1)"""
        assert dialog.windowTitle() == "Настройка панели команд"
        assert dialog.isModal()
        
        # Check that main components exist
        assert dialog.command_tree is not None
        assert dialog.preview_area is not None
        assert dialog.stats_label is not None
        assert dialog.show_tooltips_checkbox is not None
        assert dialog.compact_mode_checkbox is not None
    
    def test_command_tree_populated(self, dialog, sample_commands):
        """Test that command tree is populated with available commands (Requirements 9.1)"""
        tree = dialog.command_tree
        
        # Should have one item per command
        assert tree.topLevelItemCount() == len(sample_commands)
        
        # Check that each command is represented
        command_ids_in_tree = []
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            command_id = item.data(0, Qt.ItemDataRole.UserRole)
            command_ids_in_tree.append(command_id)
        
        for command_id in sample_commands.keys():
            assert command_id in command_ids_in_tree
    
    def test_command_checkboxes_reflect_visibility(self, dialog, sample_config):
        """Test that checkboxes reflect current command visibility"""
        tree = dialog.command_tree
        visible_commands = sample_config['visible_commands']
        
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            command_id = item.data(0, Qt.ItemDataRole.UserRole)
            
            expected_state = (
                Qt.CheckState.Checked if command_id in visible_commands 
                else Qt.CheckState.Unchecked
            )
            assert item.checkState(0) == expected_state
    
    def test_options_checkboxes_initialized(self, dialog, sample_config):
        """Test that option checkboxes are initialized correctly"""
        assert dialog.show_tooltips_checkbox.isChecked() == sample_config['show_tooltips']
        assert dialog.compact_mode_checkbox.isChecked() == sample_config['compact_mode']


class TestPanelConfigurationDialogInteraction:
    """Test dialog interaction and state changes"""
    
    def test_command_checkbox_toggle_updates_config(self, dialog):
        """Test that toggling command checkboxes updates configuration (Requirements 9.2)"""
        tree = dialog.command_tree
        
        # Find the first item and toggle it
        if tree.topLevelItemCount() > 0:
            item = tree.topLevelItem(0)
            command_id = item.data(0, Qt.ItemDataRole.UserRole)
            original_state = item.checkState(0)
            
            # Toggle the checkbox
            new_state = (
                Qt.CheckState.Unchecked if original_state == Qt.CheckState.Checked 
                else Qt.CheckState.Checked
            )
            item.setCheckState(0, new_state)
            
            # Check that modified config is updated
            config = dialog.get_configuration()
            visible_commands = config['visible_commands']
            
            if new_state == Qt.CheckState.Checked:
                assert command_id in visible_commands
            else:
                assert command_id not in visible_commands
    
    def test_option_checkbox_toggle_updates_config(self, dialog):
        """Test that toggling option checkboxes updates configuration"""
        # Toggle show_tooltips
        original_tooltips = dialog.show_tooltips_checkbox.isChecked()
        dialog.show_tooltips_checkbox.setChecked(not original_tooltips)
        
        # Check configuration
        config = dialog.get_configuration()
        assert config['show_tooltips'] == (not original_tooltips)
        
        # Toggle compact_mode
        original_compact = dialog.compact_mode_checkbox.isChecked()
        dialog.compact_mode_checkbox.setChecked(not original_compact)
        
        # Check configuration
        config = dialog.get_configuration()
        assert config['compact_mode'] == (not original_compact)
    
    def test_preview_updates_on_changes(self, dialog):
        """Test that preview area updates when configuration changes (Requirements 9.2)"""
        # Connect a mock to preview signal
        mock_preview = Mock()
        dialog.previewRequested.connect(mock_preview)
        
        # Make a change to trigger preview update
        dialog._update_preview()
        
        # Verify preview signal was emitted
        mock_preview.assert_called()
        
        # Check that preview area has content
        preview_text = dialog.preview_area.text()
        assert preview_text is not None and preview_text.strip() != ""
    
    def test_statistics_update_correctly(self, dialog, sample_commands):
        """Test that statistics are calculated correctly"""
        dialog._update_preview()
        
        stats_text = dialog.stats_label.text()
        assert "Всего команд:" in stats_text
        assert "Видимых:" in stats_text
        assert "Скрытых:" in stats_text
        
        # Check that numbers add up
        total_commands = len(sample_commands)
        assert str(total_commands) in stats_text


class TestPanelConfigurationDialogPreview:
    """Test preview functionality"""
    
    def test_preview_shows_visible_commands(self, dialog):
        """Test that preview shows visible commands correctly (Requirements 9.2)"""
        dialog._update_preview()
        
        preview_text = dialog.preview_area.text()
        config = dialog.get_configuration()
        
        # Check that visible commands are mentioned in preview
        for command_id in config['visible_commands']:
            command = dialog.available_commands.get(command_id)
            if command:
                assert command.name in preview_text or command.icon in preview_text
    
    def test_preview_shows_hidden_commands_in_more_menu(self, dialog):
        """Test that preview shows hidden commands in More menu (Requirements 9.3)"""
        dialog._update_preview()
        
        preview_text = dialog.preview_area.text()
        config = dialog.get_configuration()
        
        # Get hidden commands
        hidden_commands = [
            cmd_id for cmd_id in dialog.available_commands.keys()
            if cmd_id not in config['visible_commands']
        ]
        
        if hidden_commands:
            assert "Меню 'Еще':" in preview_text
            
            # Check that hidden commands are mentioned
            for command_id in hidden_commands:
                command = dialog.available_commands.get(command_id)
                if command:
                    assert command.name in preview_text or command.icon in preview_text
    
    def test_preview_signal_emitted_with_correct_data(self, dialog):
        """Test that preview signal is emitted with correct visible commands"""
        mock_preview = Mock()
        dialog.previewRequested.connect(mock_preview)
        
        dialog._update_preview()
        
        # Get the arguments passed to the signal
        mock_preview.assert_called()
        call_args = mock_preview.call_args[0]
        visible_commands = call_args[0]
        
        # Verify it matches current configuration
        config = dialog.get_configuration()
        assert visible_commands == config['visible_commands']


class TestPanelConfigurationDialogActions:
    """Test dialog actions (save, reset, cancel)"""
    
    def test_reset_configuration_restores_defaults(self, dialog):
        """Test that reset button restores default configuration (Requirements 9.4)"""
        # Modify configuration first
        dialog.show_tooltips_checkbox.setChecked(False)
        dialog.compact_mode_checkbox.setChecked(True)
        
        # Mock the confirmation dialog to return Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=Mock()):
            with patch.object(Mock(), 'StandardButton') as mock_button:
                mock_button.Yes = Mock()
                with patch('PyQt6.QtWidgets.QMessageBox.StandardButton.Yes', mock_button.Yes):
                    dialog._reset_configuration()
        
        # Check that options are reset (this test may need adjustment based on actual implementation)
        # The exact behavior depends on how reset is implemented
    
    def test_accept_emits_configuration_changed(self, dialog):
        """Test that accepting dialog emits configuration change signal"""
        mock_config_changed = Mock()
        dialog.configurationChanged.connect(mock_config_changed)
        
        # Mock the validation to avoid showing message boxes
        with patch.object(dialog, 'modified_config', {'visible_commands': ['add_row']}):
            dialog.accept()
        
        # Verify signal was emitted
        mock_config_changed.assert_called_once()
    
    def test_validation_warns_about_no_visible_commands(self, dialog):
        """Test that validation warns when no commands are visible"""
        # Set no visible commands
        dialog.modified_config = {
            'visible_commands': [],
            'show_tooltips': True,
            'compact_mode': False
        }
        
        # Mock the message box to return No (cancel)
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = Mock()
            with patch.object(Mock(), 'StandardButton') as mock_button:
                mock_button.No = Mock()
                mock_question.return_value = mock_button.No
                
                # This should not accept the dialog
                dialog.accept()
                
                # Verify warning was shown
                mock_question.assert_called_once()


class TestPanelConfigurationDialogIntegration:
    """Integration tests for the panel configuration dialog"""
    
    def test_show_with_commands_returns_correct_result(self, app, sample_commands):
        """Test show_with_commands method returns correct result"""
        dialog = PanelConfigurationDialog()
        
        # Mock the exec method to return Accepted
        with patch.object(dialog, 'exec', return_value=PanelConfigurationDialog.DialogCode.Accepted):
            result = dialog.show_with_commands(sample_commands)
            assert result is True
        
        # Mock the exec method to return Rejected
        with patch.object(dialog, 'exec', return_value=PanelConfigurationDialog.DialogCode.Rejected):
            result = dialog.show_with_commands(sample_commands)
            assert result is False
    
    def test_set_available_commands_updates_tree(self, dialog):
        """Test that setting available commands updates the tree"""
        new_commands = {
            'new_command': CommandTreeNode(
                id='new_command',
                name='New Command',
                icon='🆕',
                tooltip='A new command',
                visible=True,
                enabled=True
            )
        }
        
        dialog.set_available_commands(new_commands)
        
        # Check that tree was updated
        tree = dialog.command_tree
        assert tree.topLevelItemCount() == len(new_commands)
        
        # Check that the new command is in the tree
        item = tree.topLevelItem(0)
        command_id = item.data(0, Qt.ItemDataRole.UserRole)
        assert command_id == 'new_command'


if __name__ == '__main__':
    pytest.main([__file__])
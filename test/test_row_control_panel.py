"""
Tests for the Row Control Panel component.

This module tests the row control panel functionality including:
- Button presence and configuration
- State management based on selection
- Command triggering
- Customization support

Requirements: 1.1, 1.2, 1.3
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.views.widgets.row_control_panel import RowControlPanel


@pytest.fixture
def app():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def panel(app):
    """Create a RowControlPanel instance for testing"""
    return RowControlPanel()


class TestRowControlPanelButtons:
    """Test button presence and configuration"""
    
    def test_panel_contains_all_required_buttons(self, panel):
        """Test that panel contains all required buttons as per Requirements 1.2"""
        required_buttons = [
            'add_row',      # Добавить
            'delete_row',   # Удалить
            'move_up',      # Переместить выше
            'move_down',    # Переместить ниже
            'import_data',  # Импорт
            'export_data',  # Экспорт
            'print_data'    # Печать
        ]
        
        # Check that all required buttons are present
        for button_id in required_buttons:
            assert button_id in panel.buttons, f"Button {button_id} not found in panel"
    
    def test_button_tooltips_are_present(self, panel):
        """Test that all buttons have tooltips as per Requirements 1.3"""
        for button_id, action in panel.buttons.items():
            tooltip = action.toolTip()
            assert tooltip is not None and tooltip.strip() != "", \
                f"Button {button_id} missing tooltip"
    
    def test_button_icons_are_present(self, panel):
        """Test that all buttons have icons"""
        expected_icons = {
            'add_row': '➕',
            'delete_row': '🗑',
            'move_up': '↑',
            'move_down': '↓',
            'import_data': '📥',
            'export_data': '📤',
            'print_data': '🖨'
        }
        
        for button_id, expected_icon in expected_icons.items():
            if button_id in panel.buttons:
                action_text = panel.buttons[button_id].text()
                assert expected_icon in action_text, \
                    f"Button {button_id} missing expected icon {expected_icon}"


class TestRowControlPanelStateManagement:
    """Test button state management based on row selection"""
    
    def test_delete_button_disabled_without_selection(self, panel):
        """Test that delete button is disabled when no rows are selected (Requirements 1.4)"""
        panel.update_button_states(
            has_selection=False,
            has_rows=True
        )
        
        delete_action = panel.buttons.get('delete_row')
        assert delete_action is not None
        assert not delete_action.isEnabled(), "Delete button should be disabled without selection"
    
    def test_delete_button_enabled_with_selection(self, panel):
        """Test that delete button is enabled when rows are selected"""
        panel.update_button_states(
            has_selection=True,
            has_rows=True
        )
        
        delete_action = panel.buttons.get('delete_row')
        assert delete_action is not None
        assert delete_action.isEnabled(), "Delete button should be enabled with selection"
    
    def test_move_up_disabled_for_first_row(self, panel):
        """Test that move up button is disabled when first row is selected (Requirements 1.5)"""
        panel.update_button_states(
            has_selection=True,
            has_rows=True,
            is_first_row_selected=True
        )
        
        move_up_action = panel.buttons.get('move_up')
        assert move_up_action is not None
        assert not move_up_action.isEnabled(), \
            "Move up button should be disabled when first row is selected"
    
    def test_move_down_disabled_for_last_row(self, panel):
        """Test that move down button is disabled when last row is selected (Requirements 1.6)"""
        panel.update_button_states(
            has_selection=True,
            has_rows=True,
            is_last_row_selected=True
        )
        
        move_down_action = panel.buttons.get('move_down')
        assert move_down_action is not None
        assert not move_down_action.isEnabled(), \
            "Move down button should be disabled when last row is selected"
    
    def test_export_button_disabled_without_rows(self, panel):
        """Test that export button is disabled when table has no rows"""
        panel.update_button_states(
            has_selection=False,
            has_rows=False
        )
        
        export_action = panel.buttons.get('export_data')
        assert export_action is not None
        assert not export_action.isEnabled(), \
            "Export button should be disabled when table has no rows"
    
    def test_add_button_always_enabled(self, panel):
        """Test that add button is always enabled regardless of selection"""
        # Test with no selection and no rows
        panel.update_button_states(
            has_selection=False,
            has_rows=False
        )
        
        add_action = panel.buttons.get('add_row')
        assert add_action is not None
        assert add_action.isEnabled(), "Add button should always be enabled"
        
        # Test with selection
        panel.update_button_states(
            has_selection=True,
            has_rows=True
        )
        
        assert add_action.isEnabled(), "Add button should remain enabled with selection"


class TestRowControlPanelCommands:
    """Test command triggering functionality"""
    
    def test_command_signal_emitted_on_button_click(self, panel):
        """Test that commandTriggered signal is emitted when button is clicked"""
        # Connect a mock slot to capture the signal
        mock_slot = Mock()
        panel.commandTriggered.connect(mock_slot)
        
        # Simulate clicking the add button
        add_action = panel.buttons.get('add_row')
        assert add_action is not None
        
        # Trigger the action
        add_action.trigger()
        
        # Verify signal was emitted with correct command ID
        mock_slot.assert_called_once_with('add_row')
    
    def test_customize_signal_emitted(self, panel):
        """Test that customizeRequested signal is emitted"""
        # Connect a mock slot to capture the signal
        mock_slot = Mock()
        panel.customizeRequested.connect(mock_slot)
        
        # Find and trigger the customize action
        customize_actions = [
            action for action in panel.toolbar.actions()
            if action.text() == "⚙️"
        ]
        assert len(customize_actions) == 1, "Should have exactly one customize action"
        
        customize_actions[0].trigger()
        
        # Verify signal was emitted
        mock_slot.assert_called_once()


class TestRowControlPanelCustomization:
    """Test panel customization functionality"""
    
    def test_set_visible_commands(self, panel):
        """Test setting visible commands updates the panel"""
        # Set a subset of commands as visible
        new_visible_commands = ['add_row', 'delete_row']
        panel.set_visible_commands(new_visible_commands)
        
        # Check that only specified commands are visible
        assert panel.get_visible_commands() == new_visible_commands
        
        # Check that the specified buttons exist
        for command_id in new_visible_commands:
            assert command_id in panel.buttons
    
    def test_enable_disable_command(self, panel):
        """Test enabling and disabling specific commands"""
        # Disable a command
        panel.enable_command('add_row', False)
        
        add_action = panel.buttons.get('add_row')
        assert add_action is not None
        assert not add_action.isEnabled(), "Command should be disabled"
        
        # Re-enable the command
        panel.enable_command('add_row', True)
        assert add_action.isEnabled(), "Command should be re-enabled"
    
    def test_more_menu_created_for_hidden_commands(self, panel):
        """Test that More menu is created when commands are hidden"""
        # Set only some commands as visible
        visible_commands = ['add_row', 'delete_row']
        panel.set_visible_commands(visible_commands)
        
        # Check that hidden commands are accessible through buttons dict
        hidden_commands = ['move_up', 'move_down', 'import_data', 'export_data', 'print_data']
        for command_id in hidden_commands:
            assert command_id in panel.buttons, \
                f"Hidden command {command_id} should still be accessible"


class TestRowControlPanelIntegration:
    """Integration tests for the row control panel"""
    
    def test_panel_initialization_with_custom_commands(self, app):
        """Test panel initialization with custom visible commands"""
        custom_commands = ['add_row', 'delete_row', 'export_data']
        panel = RowControlPanel(visible_commands=custom_commands)
        
        assert panel.get_visible_commands() == custom_commands
        
        # Check that all custom commands have buttons
        for command_id in custom_commands:
            assert command_id in panel.buttons
    
    def test_panel_initialization_with_default_commands(self, app):
        """Test panel initialization with default commands"""
        panel = RowControlPanel()
        
        # Should have all standard commands visible by default
        expected_default = [
            'add_row', 'delete_row', 'move_up', 'move_down',
            'import_data', 'export_data', 'print_data'
        ]
        
        assert panel.get_visible_commands() == expected_default


if __name__ == '__main__':
    pytest.main([__file__])
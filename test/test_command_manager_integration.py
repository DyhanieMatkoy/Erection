"""
Tests for Command Manager Integration with Row Control Panel.

This module tests the integration between the row control panel and
the command manager, including form command discovery, registration,
and execution.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication

from src.views.widgets.row_control_panel import RowControlPanel
from src.services.table_part_command_manager import (
    TablePartCommandManager, CommandContext, FormCommand, 
    CommandAvailability, table_command, CommandResult
)


@pytest.fixture
def app():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def command_manager():
    """Create a command manager for testing"""
    return TablePartCommandManager()


@pytest.fixture
def panel_with_manager(app, command_manager):
    """Create a row control panel with command manager"""
    return RowControlPanel(command_manager=command_manager)


class MockFormWithCommands:
    """Mock form class with table commands for testing"""
    
    def __init__(self):
        self.add_row_called = False
        self.delete_row_called = False
        self.selected_rows_param = None
    
    @table_command(command_id='add_row', name='Add Row')
    def add_table_row(self, context: CommandContext):
        """Add a new row to the table"""
        self.add_row_called = True
        return CommandResult(success=True, message="Row added")
    
    @table_command(
        command_id='delete_row', 
        name='Delete Rows',
        availability=CommandAvailability.REQUIRES_SELECTION
    )
    def delete_selected_rows(self, context: CommandContext):
        """Delete selected rows"""
        self.delete_row_called = True
        self.selected_rows_param = context.selected_rows
        return CommandResult(
            success=True, 
            message=f"Deleted {len(context.selected_rows)} rows",
            affected_rows=context.selected_rows
        )
    
    # Method without decorator (should be discovered by naming convention)
    def move_up(self):
        """Move rows up"""
        return True
    
    def move_down(self):
        """Move rows down"""
        return True


class TestCommandDiscovery:
    """Test command discovery functionality"""
    
    def test_discover_commands_from_form_instance(self, command_manager):
        """Test discovering commands from form instance (Requirements 2.1, 2.2)"""
        form = MockFormWithCommands()
        
        # Discover and register commands
        discovered = command_manager.discover_and_register_commands(form)
        
        # Should discover decorated commands
        command_ids = [cmd.id for cmd in discovered]
        assert 'add_row' in command_ids
        assert 'delete_row' in command_ids
        
        # Should also discover naming convention commands
        assert 'move_up' in command_ids
        assert 'move_down' in command_ids
    
    def test_register_form_instance_with_panel(self, panel_with_manager):
        """Test registering form instance with panel"""
        form = MockFormWithCommands()
        
        # Register form instance
        discovered = panel_with_manager.register_form_instance(form)
        
        # Should have discovered commands
        assert len(discovered) > 0
        
        # Commands should be registered in manager
        registered = panel_with_manager.command_manager.get_registered_commands()
        assert 'add_row' in registered
        assert 'delete_row' in registered
    
    def test_command_availability_configuration(self, command_manager):
        """Test that command availability is properly configured"""
        form = MockFormWithCommands()
        command_manager.discover_and_register_commands(form)
        
        # Get registered commands
        commands = command_manager.get_registered_commands()
        
        # Check availability settings
        add_command = commands.get('add_row')
        assert add_command is not None
        assert add_command.availability == CommandAvailability.ALWAYS
        
        delete_command = commands.get('delete_row')
        assert delete_command is not None
        assert delete_command.availability == CommandAvailability.REQUIRES_SELECTION


class TestCommandExecution:
    """Test command execution through manager"""
    
    def test_execute_form_command_through_manager(self, command_manager):
        """Test executing form command through manager (Requirements 2.3, 2.4)"""
        form = MockFormWithCommands()
        command_manager.discover_and_register_commands(form)
        
        # Create context and execute command
        context = CommandContext(selected_rows=[], table_data=[])
        result = command_manager.execute_command('add_row', context)
        
        # Should execute successfully
        assert result.success
        assert form.add_row_called
    
    def test_execute_command_with_selection_requirement(self, command_manager):
        """Test executing command that requires selection"""
        form = MockFormWithCommands()
        command_manager.discover_and_register_commands(form)
        
        # Try to execute delete without selection
        context = CommandContext(selected_rows=[], table_data=[])
        result = command_manager.execute_command('delete_row', context)
        
        # Should fail due to no selection
        assert not result.success
        assert not form.delete_row_called
        
        # Execute with selection
        context = CommandContext(selected_rows=[0, 1], table_data=[{}, {}])
        result = command_manager.execute_command('delete_row', context)
        
        # Should succeed
        assert result.success
        assert form.delete_row_called
        assert form.selected_rows_param == [0, 1]
    
    def test_panel_command_execution_integration(self, panel_with_manager):
        """Test command execution through panel integration"""
        form = MockFormWithCommands()
        panel_with_manager.register_form_instance(form)
        
        # Mock the context methods
        panel_with_manager._get_selected_rows = Mock(return_value=[])
        panel_with_manager._get_table_data = Mock(return_value=[])
        
        # Execute command through panel
        panel_with_manager._execute_command_with_manager('add_row')
        
        # Should have executed the form method
        assert form.add_row_called


class TestCommandStateManagement:
    """Test command state management and updates"""
    
    def test_update_command_states_based_on_context(self, command_manager):
        """Test updating command states based on context (Requirements 2.5)"""
        form = MockFormWithCommands()
        command_manager.discover_and_register_commands(form)
        
        # Update states with no selection
        context = CommandContext(selected_rows=[], table_data=[])
        states = command_manager.update_command_states(context)
        
        # Add should be available, delete should not
        assert states.get('add_row') is True
        assert states.get('delete_row') is False
        
        # Update states with selection
        context = CommandContext(selected_rows=[0], table_data=[{}])
        states = command_manager.update_command_states(context)
        
        # Both should be available now
        assert states.get('add_row') is True
        assert states.get('delete_row') is True
    
    def test_panel_updates_button_states_from_manager(self, panel_with_manager):
        """Test that panel updates button states from command manager"""
        form = MockFormWithCommands()
        panel_with_manager.register_form_instance(form)
        
        # Update context and states
        panel_with_manager.update_context_and_states(
            selected_rows=[],
            table_data=[],
            additional_data={}
        )
        
        # Check that delete button is disabled (no selection)
        if 'delete_row' in panel_with_manager.buttons:
            delete_action = panel_with_manager.buttons['delete_row']
            assert not delete_action.isEnabled()
        
        # Update with selection
        panel_with_manager.update_context_and_states(
            selected_rows=[0],
            table_data=[{}],
            additional_data={}
        )
        
        # Check that delete button is now enabled
        if 'delete_row' in panel_with_manager.buttons:
            delete_action = panel_with_manager.buttons['delete_row']
            assert delete_action.isEnabled()
    
    def test_cached_command_states(self, command_manager):
        """Test that command states are cached properly"""
        form = MockFormWithCommands()
        command_manager.discover_and_register_commands(form)
        
        # Update states
        context = CommandContext(selected_rows=[0], table_data=[{}])
        command_manager.update_command_states(context)
        
        # Check cached states
        assert command_manager.get_command_state('add_row') is True
        assert command_manager.get_command_state('delete_row') is True
        
        # Update with different context
        context = CommandContext(selected_rows=[], table_data=[])
        command_manager.update_command_states(context)
        
        # Check updated cached states
        assert command_manager.get_command_state('add_row') is True
        assert command_manager.get_command_state('delete_row') is False


class TestCommandManagerIntegration:
    """Integration tests for command manager with panel"""
    
    def test_full_integration_workflow(self, panel_with_manager):
        """Test complete integration workflow"""
        form = MockFormWithCommands()
        
        # 1. Register form instance
        discovered = panel_with_manager.register_form_instance(form)
        assert len(discovered) > 0
        
        # 2. Update context
        panel_with_manager.update_context_and_states(
            selected_rows=[0, 1],
            table_data=[{}, {}]
        )
        
        # 3. Execute command
        panel_with_manager._get_selected_rows = Mock(return_value=[0, 1])
        panel_with_manager._get_table_data = Mock(return_value=[{}, {}])
        
        panel_with_manager._execute_command_with_manager('delete_row')
        
        # 4. Verify execution
        assert form.delete_row_called
        assert form.selected_rows_param == [0, 1]
    
    def test_fallback_to_signal_emission(self, panel_with_manager):
        """Test fallback to signal emission when command not in manager"""
        # Mock signal emission
        signal_emitted = []
        panel_with_manager.commandTriggered.connect(lambda cmd_id: signal_emitted.append(cmd_id))
        
        # Execute command not in manager
        panel_with_manager._execute_command_with_manager('unknown_command')
        
        # Should emit signal as fallback
        assert 'unknown_command' in signal_emitted
    
    def test_error_handling_in_command_execution(self, command_manager):
        """Test error handling during command execution"""
        
        class FaultyForm:
            @table_command(command_id='faulty_command')
            def faulty_method(self, context):
                raise Exception("Something went wrong")
        
        form = FaultyForm()
        command_manager.discover_and_register_commands(form)
        
        # Execute faulty command
        context = CommandContext()
        result = command_manager.execute_command('faulty_command', context)
        
        # Should handle error gracefully
        assert not result.success
        assert "Something went wrong" in result.message


if __name__ == '__main__':
    pytest.main([__file__])
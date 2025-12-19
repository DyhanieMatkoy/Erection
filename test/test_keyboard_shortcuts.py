"""
Tests for table part keyboard shortcut handler.

Requirements: 3.1, 3.2, 7.3, 7.4
"""

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QKeySequence

from src.services.table_part_keyboard_handler import (
    TablePartKeyboardHandler,
    ShortcutAction,
    ShortcutContext,
    create_keyboard_handler,
    create_table_context
)


@pytest.fixture
def app():
    """Create QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def widget(app):
    """Create test widget"""
    widget = QWidget()
    widget.show()
    return widget


@pytest.fixture
def keyboard_handler(widget):
    """Create keyboard handler"""
    handler = create_keyboard_handler(widget)
    return handler


class TestKeyboardShortcutHandler:
    """Test keyboard shortcut handler functionality"""
    
    def test_handler_creation(self, keyboard_handler):
        """Test that keyboard handler is created successfully"""
        assert keyboard_handler is not None
        assert keyboard_handler.enabled is True
        assert len(keyboard_handler.shortcuts) > 0
    
    def test_standard_shortcuts_registered(self, keyboard_handler):
        """Test that all standard shortcuts are registered"""
        mappings = keyboard_handler.get_shortcut_mappings()
        
        # Check for required shortcuts
        required_actions = [
            ShortcutAction.ADD_ROW,
            ShortcutAction.DELETE_ROW,
            ShortcutAction.COPY_ROWS,
            ShortcutAction.PASTE_ROWS,
            ShortcutAction.MOVE_ROW_UP,
            ShortcutAction.MOVE_ROW_DOWN,
            ShortcutAction.OPEN_REFERENCE_SELECTOR
        ]
        
        registered_actions = [m.action for m in mappings]
        for action in required_actions:
            assert action in registered_actions, f"Missing shortcut: {action.value}"
    
    def test_hierarchical_shortcuts_registered(self, keyboard_handler):
        """Test that hierarchical navigation shortcuts are registered"""
        mappings = keyboard_handler.get_shortcut_mappings(context_filter="hierarchical")
        
        hierarchical_actions = [
            ShortcutAction.EXPAND_NODE,
            ShortcutAction.COLLAPSE_NODE,
            ShortcutAction.GO_TO_FIRST,
            ShortcutAction.GO_TO_LAST,
            ShortcutAction.PAGE_UP,
            ShortcutAction.PAGE_DOWN
        ]
        
        registered_actions = [m.action for m in mappings]
        for action in hierarchical_actions:
            assert action in registered_actions, f"Missing hierarchical shortcut: {action.value}"
    
    def test_action_handler_registration(self, keyboard_handler):
        """Test registering custom action handlers"""
        handler_called = []
        
        def custom_handler(context):
            handler_called.append(True)
        
        keyboard_handler.register_action_handler(ShortcutAction.ADD_ROW, custom_handler)
        
        # Verify handler is registered
        assert ShortcutAction.ADD_ROW in keyboard_handler.action_handlers
    
    def test_context_update(self, keyboard_handler, widget):
        """Test updating keyboard context"""
        context = create_table_context(
            widget=widget,
            selected_rows=[0, 1, 2],
            current_row=1,
            is_hierarchical=False,
            is_editing=False
        )
        
        keyboard_handler.update_context(context)
        
        assert keyboard_handler.current_context is not None
        assert keyboard_handler.current_context.selected_rows == [0, 1, 2]
        assert keyboard_handler.current_context.current_row == 1
    
    def test_enable_disable_shortcuts(self, keyboard_handler):
        """Test enabling and disabling shortcuts"""
        # Disable all shortcuts
        keyboard_handler.set_enabled(False)
        assert keyboard_handler.enabled is False
        
        # Enable all shortcuts
        keyboard_handler.set_enabled(True)
        assert keyboard_handler.enabled is True
    
    def test_enable_disable_specific_shortcut(self, keyboard_handler):
        """Test enabling and disabling specific shortcuts"""
        # Disable specific shortcut
        keyboard_handler.enable_shortcut(ShortcutAction.DELETE_ROW, False)
        
        # Check that shortcut is disabled
        for key, shortcut in keyboard_handler.shortcuts.items():
            if ShortcutAction.DELETE_ROW.value in key:
                assert not shortcut.isEnabled()
        
        # Re-enable shortcut
        keyboard_handler.enable_shortcut(ShortcutAction.DELETE_ROW, True)
        
        for key, shortcut in keyboard_handler.shortcuts.items():
            if ShortcutAction.DELETE_ROW.value in key:
                assert shortcut.isEnabled()
    
    def test_custom_shortcut_addition(self, keyboard_handler):
        """Test adding custom shortcuts"""
        initial_count = len(keyboard_handler.get_shortcut_mappings())
        
        keyboard_handler.add_custom_shortcut(
            key_sequence="Ctrl+K",
            action=ShortcutAction.ADD_ROW,
            description="Custom add row shortcut"
        )
        
        new_count = len(keyboard_handler.get_shortcut_mappings())
        assert new_count == initial_count + 1
    
    def test_shortcut_removal(self, keyboard_handler):
        """Test removing shortcuts"""
        # Add a custom shortcut
        keyboard_handler.add_custom_shortcut(
            key_sequence="Ctrl+K",
            action=ShortcutAction.ADD_ROW,
            description="Test shortcut"
        )
        
        initial_count = len(keyboard_handler.shortcuts)
        
        # Remove the shortcut
        keyboard_handler.remove_shortcut("Ctrl+K", ShortcutAction.ADD_ROW)
        
        # Verify removal
        new_count = len(keyboard_handler.shortcuts)
        assert new_count < initial_count
    
    def test_shortcut_help_text(self, keyboard_handler):
        """Test generating shortcut help text"""
        help_text = keyboard_handler.get_shortcut_help_text()
        
        assert help_text is not None
        assert len(help_text) > 0
        assert "Горячие клавиши" in help_text
        assert "Insert" in help_text
        assert "Delete" in help_text
    
    def test_context_filtering(self, keyboard_handler, widget):
        """Test shortcut applicability based on context"""
        # Create context with no selection
        context = create_table_context(
            widget=widget,
            selected_rows=[],
            is_editing=False
        )
        
        keyboard_handler.update_context(context)
        
        # Get mappings that require selection
        mappings = keyboard_handler.get_shortcut_mappings()
        delete_mapping = next(m for m in mappings if m.action == ShortcutAction.DELETE_ROW)
        
        # Check that delete is not applicable without selection
        assert not keyboard_handler._is_shortcut_applicable(delete_mapping, context)
        
        # Create context with selection
        context_with_selection = create_table_context(
            widget=widget,
            selected_rows=[0, 1],
            is_editing=False
        )
        
        # Check that delete is now applicable
        assert keyboard_handler._is_shortcut_applicable(delete_mapping, context_with_selection)
    
    def test_editing_blocks_shortcuts(self, keyboard_handler, widget):
        """Test that editing blocks certain shortcuts"""
        # Create editing context
        context = create_table_context(
            widget=widget,
            selected_rows=[0],
            is_editing=True
        )
        
        keyboard_handler.update_context(context)
        
        # Get mappings
        mappings = keyboard_handler.get_shortcut_mappings()
        delete_mapping = next(m for m in mappings if m.action == ShortcutAction.DELETE_ROW)
        
        # Check that delete is blocked while editing
        assert not keyboard_handler._is_shortcut_applicable(delete_mapping, context)
    
    def test_hierarchical_context_filtering(self, keyboard_handler, widget):
        """Test that hierarchical shortcuts only work in hierarchical context"""
        # Create non-hierarchical context
        context = create_table_context(
            widget=widget,
            is_hierarchical=False
        )
        
        keyboard_handler.update_context(context)
        
        # Get hierarchical mapping
        mappings = keyboard_handler.get_shortcut_mappings()
        expand_mapping = next(m for m in mappings if m.action == ShortcutAction.EXPAND_NODE)
        
        # Check that expand is not applicable in non-hierarchical context
        assert not keyboard_handler._is_shortcut_applicable(expand_mapping, context)
        
        # Create hierarchical context
        hierarchical_context = create_table_context(
            widget=widget,
            is_hierarchical=True
        )
        
        # Check that expand is now applicable
        assert keyboard_handler._is_shortcut_applicable(expand_mapping, hierarchical_context)
    
    def test_cleanup(self, keyboard_handler):
        """Test cleanup of keyboard handler"""
        initial_shortcut_count = len(keyboard_handler.shortcuts)
        assert initial_shortcut_count > 0
        
        keyboard_handler.cleanup()
        
        assert len(keyboard_handler.shortcuts) == 0
        assert len(keyboard_handler.action_handlers) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

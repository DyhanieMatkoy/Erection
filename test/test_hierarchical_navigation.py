"""
Test hierarchical navigation shortcuts for list forms v2.

This module tests the implementation of hierarchical navigation shortcuts
including Ctrl+→/← for expand/collapse nodes, Home/End navigation,
and Page Up/Down functionality.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.views.work_list_form_v2 import WorkListFormV2
from src.views.cost_item_list_form_v2 import CostItemListFormV2
from src.services.table_part_keyboard_handler import ShortcutAction, create_table_context
from src.data.models.sqlalchemy_models import Work, CostItem


class TestHierarchicalNavigation:
    """Test hierarchical navigation shortcuts in list forms v2"""
    
    @pytest.fixture
    def qapp(self):
        """Create QApplication instance"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # Don't quit the app as it might be used by other tests
    
    @pytest.fixture
    def mock_controller(self):
        """Create mock controller"""
        controller = Mock()
        controller.initialize = Mock()
        controller.get_selection = Mock(return_value=[])
        controller.set_filter = Mock()
        controller.filters = {}
        controller.selection = []  # Add selection attribute
        controller.data_service = Mock()
        controller.data_service.get_documents = Mock(return_value={'items': []})
        controller.filter_columns = Mock(side_effect=lambda x: x)  # Return columns as-is
        controller.column_settings = {}
        controller.get_available_commands = Mock(return_value=[])
        controller.update_selection = Mock()
        return controller
    
    @pytest.fixture
    def work_list_form(self, qapp, mock_controller):
        """Create WorkListFormV2 instance with mocked dependencies"""
        with patch('src.controllers.list_form_controller.ListFormController', return_value=mock_controller):
            form = WorkListFormV2(user_id=1)
            form.show()
            return form
    
    @pytest.fixture
    def cost_item_list_form(self, qapp, mock_controller):
        """Create CostItemListFormV2 instance with mocked dependencies"""
        with patch('src.controllers.list_form_controller.ListFormController', return_value=mock_controller):
            form = CostItemListFormV2(user_id=1)
            form.show()
            return form
    
    def test_hierarchical_navigation_enabled(self, work_list_form):
        """Test that hierarchical navigation is enabled for hierarchical forms"""
        assert work_list_form.is_hierarchical is True
        assert work_list_form.keyboard_handler is not None
    
    def test_expand_node_shortcut_ctrl_right(self, work_list_form):
        """Test Ctrl+→ shortcut for expanding nodes"""
        # Setup mock data with a group
        mock_group = Mock()
        mock_group.id = 1
        mock_group.is_group = True
        mock_group.name = "Test Group"
        
        work_list_form.table.data_map = [mock_group]
        work_list_form.controller.get_selection = Mock(return_value=[1])
        
        # Mock the enter_group method
        work_list_form.enter_group = Mock()
        
        # Update context and trigger shortcut
        work_list_form.update_keyboard_context()
        
        # Simulate Ctrl+Right key press
        context = create_table_context(
            widget=work_list_form,
            selected_rows=[0],
            current_row=0,
            is_hierarchical=True
        )
        
        work_list_form.on_expand_node(context)
        
        # Verify enter_group was called
        work_list_form.enter_group.assert_called_once_with(1, mock_group)
    
    def test_collapse_node_shortcut_ctrl_left(self, work_list_form):
        """Test Ctrl+← shortcut for collapsing nodes (going up)"""
        # Setup form in a group
        work_list_form.current_parent_id = 1
        work_list_form.navigation_path = [None]
        
        # Mock go_up method
        work_list_form.go_up = Mock()
        
        # Simulate Ctrl+Left key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_collapse_node(context)
        
        # Verify go_up was called
        work_list_form.go_up.assert_called_once()
    
    def test_go_to_first_shortcut_home(self, work_list_form):
        """Test Home shortcut for going to first item"""
        # Setup table with multiple rows
        work_list_form.table.setRowCount(5)
        work_list_form.table.selectRow = Mock()
        work_list_form.table.scrollToTop = Mock()
        
        # Simulate Home key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_go_to_first(context)
        
        # Verify first row was selected
        work_list_form.table.selectRow.assert_called_once_with(0)
        work_list_form.table.scrollToTop.assert_called_once()
    
    def test_go_to_last_shortcut_end(self, work_list_form):
        """Test End shortcut for going to last item"""
        # Setup table with multiple rows
        work_list_form.table.setRowCount(5)
        work_list_form.table.selectRow = Mock()
        work_list_form.table.scrollToBottom = Mock()
        
        # Simulate End key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_go_to_last(context)
        
        # Verify last row was selected
        work_list_form.table.selectRow.assert_called_once_with(4)
        work_list_form.table.scrollToBottom.assert_called_once()
    
    def test_go_to_root_shortcut_ctrl_home(self, work_list_form):
        """Test Ctrl+Home shortcut for going to root"""
        # Setup form in a nested group
        work_list_form.current_parent_id = 5
        work_list_form.navigation_path = [None, 1, 3]
        
        # Mock filter bar
        work_list_form.filter_bar.set_navigation_state = Mock()
        
        # Simulate Ctrl+Home key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_go_to_root(context)
        
        # Verify navigation to root
        assert work_list_form.current_parent_id is None
        assert len(work_list_form.navigation_path) == 0
        work_list_form.controller.set_filter.assert_called_with('parent_id', None)
        work_list_form.filter_bar.set_navigation_state.assert_called_with(False, "Корень")
    
    def test_page_up_shortcut(self, work_list_form):
        """Test Page Up shortcut for scrolling up"""
        # Setup table
        work_list_form.table.setRowCount(20)
        work_list_form.table.height = Mock(return_value=400)
        work_list_form.table.rowHeight = Mock(return_value=20)
        work_list_form.table.currentRow = Mock(return_value=15)
        work_list_form.table.selectRow = Mock()
        work_list_form.table.scrollToItem = Mock()
        work_list_form.table.item = Mock(return_value=Mock())
        
        # Simulate Page Up key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_page_up(context)
        
        # Verify page up navigation (visible_rows = 400/20 = 20, new_row = max(0, 15-20) = 0)
        work_list_form.table.selectRow.assert_called_once_with(0)
    
    def test_page_down_shortcut(self, work_list_form):
        """Test Page Down shortcut for scrolling down"""
        # Setup table
        work_list_form.table.setRowCount(20)
        work_list_form.table.height = Mock(return_value=400)
        work_list_form.table.rowHeight = Mock(return_value=20)
        work_list_form.table.currentRow = Mock(return_value=5)
        work_list_form.table.selectRow = Mock()
        work_list_form.table.scrollToItem = Mock()
        work_list_form.table.item = Mock(return_value=Mock())
        
        # Simulate Page Down key press
        context = create_table_context(
            widget=work_list_form,
            is_hierarchical=True
        )
        
        work_list_form.on_page_down(context)
        
        # Verify page down navigation (visible_rows = 400/20 = 20, new_row = min(19, 5+20) = 19)
        work_list_form.table.selectRow.assert_called_once_with(19)
    
    def test_navigation_path_management(self, work_list_form):
        """Test navigation path is properly managed during drill down and up"""
        # Start at root
        assert work_list_form.current_parent_id is None
        assert len(work_list_form.navigation_path) == 0
        
        # Mock filter bar
        work_list_form.filter_bar.set_navigation_state = Mock()
        
        # Enter first group
        work_list_form.enter_group(1, "Group 1")
        assert work_list_form.current_parent_id == 1
        assert work_list_form.navigation_path == [None]
        
        # Enter nested group
        work_list_form.enter_group(2, "Group 2")
        assert work_list_form.current_parent_id == 2
        assert work_list_form.navigation_path == [None, 1]
        
        # Go up one level
        work_list_form.go_up()
        assert work_list_form.current_parent_id == 1
        assert work_list_form.navigation_path == [None]
        
        # Go up to root
        work_list_form.go_up()
        assert work_list_form.current_parent_id is None
        assert work_list_form.navigation_path == []
    
    def test_cost_item_hierarchical_navigation(self, cost_item_list_form):
        """Test hierarchical navigation works for cost item list form"""
        assert cost_item_list_form.is_hierarchical is True
        assert cost_item_list_form.keyboard_handler is not None
        
        # Test expand node with folder
        mock_folder = Mock()
        mock_folder.id = 1
        mock_folder.is_folder = True
        mock_folder.description = "Test Folder"
        
        cost_item_list_form.table.data_map = [mock_folder]
        cost_item_list_form.controller.get_selection = Mock(return_value=[1])
        cost_item_list_form.enter_group = Mock()
        
        # Update context and trigger shortcut
        cost_item_list_form.update_keyboard_context()
        
        context = create_table_context(
            widget=cost_item_list_form,
            selected_rows=[0],
            current_row=0,
            is_hierarchical=True
        )
        
        cost_item_list_form.on_expand_node(context)
        
        # Verify enter_group was called
        cost_item_list_form.enter_group.assert_called_once_with(1, mock_folder)
    
    def test_keyboard_context_updates_on_selection_change(self, work_list_form):
        """Test that keyboard context is updated when selection changes"""
        # Mock table data
        mock_item = Mock()
        mock_item.id = 1
        work_list_form.table.data_map = [mock_item]
        
        # Mock controller selection
        work_list_form.controller.get_selection = Mock(return_value=[1])
        work_list_form.controller.update_selection = Mock()
        work_list_form.refresh_commands = Mock()
        
        # Trigger selection change
        work_list_form.on_selection_change([1])
        
        # Verify context was updated
        work_list_form.controller.update_selection.assert_called_once_with([1])
        assert work_list_form.keyboard_handler.current_context is not None
        assert work_list_form.keyboard_handler.current_context.is_hierarchical is True
    
    def test_non_hierarchical_forms_dont_respond_to_hierarchical_shortcuts(self, qapp, mock_controller):
        """Test that non-hierarchical forms don't respond to hierarchical shortcuts"""
        with patch('src.controllers.list_form_controller.ListFormController', return_value=mock_controller):
            # Create a generic form without hierarchical navigation
            from src.views.generic_list_form import GenericListForm
            from src.data.models.sqlalchemy_models import User
            
            form = GenericListForm("test", 1, User, mock_controller)
            form.show()
            
            # Verify hierarchical navigation is disabled
            assert form.is_hierarchical is False
            
            # Test that hierarchical shortcuts don't work
            context = create_table_context(
                widget=form,
                is_hierarchical=False
            )
            
            # These should not do anything
            form.on_expand_node(context)
            form.on_collapse_node(context)
            form.on_go_to_root(context)
            
            # No exceptions should be raised and no navigation should occur
            assert form.current_parent_id is None


if __name__ == "__main__":
    pytest.main([__file__])
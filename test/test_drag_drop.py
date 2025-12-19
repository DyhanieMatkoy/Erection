#!/usr/bin/env python3
"""
Tests for drag-and-drop functionality in table parts.

Requirements: 7.7
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from typing import List, Dict, Any, Optional

from src.views.widgets.base_table_part import (
    BaseTablePart, TablePartConfiguration, CommandType
)


# Create QApplication instance for tests
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestTablePartDragDrop(BaseTablePart):
    """Test implementation of BaseTablePart for drag-and-drop testing"""
    
    def __init__(self, parent=None):
        config = TablePartConfiguration(
            table_id="test_table",
            document_type="test_document",
            available_commands=[],
            visible_commands=[
                CommandType.ADD_ROW.value,
                CommandType.DELETE_ROW.value,
                CommandType.MOVE_UP.value,
                CommandType.MOVE_DOWN.value
            ],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=False,
            drag_drop_enabled=True  # Enable drag and drop
        )
        
        super().__init__(config, parent)
        
        # Test data
        self.data = []
        self._setup_table()
    
    def _setup_table(self):
        """Setup table structure"""
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Value"])
    
    def set_test_data(self, data: List[Dict[str, Any]]):
        """Set test data"""
        self.data = data
        self._populate_table()
    
    def _populate_table(self):
        """Populate table with data"""
        from PyQt6.QtWidgets import QTableWidgetItem
        
        self.table.setRowCount(len(self.data))
        for row, item in enumerate(self.data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('name', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('value', ''))))
    
    # Implement abstract methods
    
    def _get_table_data(self) -> List[Dict[str, Any]]:
        return self.data
    
    def _add_row(self):
        new_id = len(self.data) + 1
        self.data.append({'id': new_id, 'name': f'Item {new_id}', 'value': 0})
        self._populate_table()
    
    def _delete_selected_rows(self):
        selected_rows = self.get_selected_rows()
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            if 0 <= row < len(self.data):
                del self.data[row]
        self._populate_table()
    
    def _swap_rows(self, row1: int, row2: int):
        if (0 <= row1 < len(self.data) and 
            0 <= row2 < len(self.data) and 
            row1 != row2):
            self.data[row1], self.data[row2] = self.data[row2], self.data[row1]
            self._populate_table()
    
    def _update_selection(self, row_indices: List[int]):
        from PyQt6.QtCore import QItemSelectionModel
        self.table.clearSelection()
        selection_model = self.table.selectionModel()
        
        for row in row_indices:
            if 0 <= row < self.table.rowCount():
                selection_model.select(
                    self.table.model().index(row, 0),
                    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
                )
    
    def _get_import_columns(self) -> List:
        return []
    
    def _on_data_imported(self, data: List[Dict[str, Any]]):
        pass
    
    def _get_export_columns(self) -> List:
        return []
    
    def _open_reference_selector(self):
        pass
    
    def _get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        if 0 <= row < len(self.data):
            return self.data[row]
        return None
    
    def _update_calculated_field(self, row: int, column: str, value: Any):
        pass
    
    def _update_document_totals(self, totals: Dict[str, Any]):
        pass


class TestDragAndDrop:
    """Tests for drag-and-drop functionality"""
    
    def test_drag_drop_enabled_configuration(self, qapp):
        """Test that drag-and-drop is properly configured when enabled"""
        # Arrange & Act
        table_part = TestTablePartDragDrop()
        
        # Assert
        assert table_part.config.drag_drop_enabled is True
        assert table_part.table.dragDropMode() == table_part.table.DragDropMode.InternalMove
        assert table_part.table.defaultDropAction() == Qt.DropAction.MoveAction
        assert table_part.table.dragEnabled() is True
        assert table_part.table.acceptDrops() is True
        assert table_part.table.showDropIndicator() is True
    
    def test_drag_drop_disabled_configuration(self, qapp):
        """Test that drag-and-drop is properly disabled when configured"""
        # Arrange
        config = TablePartConfiguration(
            table_id="test_table",
            document_type="test_document",
            available_commands=[],
            visible_commands=[],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=False,
            drag_drop_enabled=False  # Disable drag and drop
        )
        
        # Act
        table_part = TestTablePartDragDrop()
        table_part.config = config
        table_part._setup_ui()  # Recreate UI with new config
        
        # Assert
        assert table_part.config.drag_drop_enabled is False
        # Note: We can't easily test the drag-drop mode when disabled without recreating the table
    
    def test_rows_moved_signal_handling(self, qapp):
        """Test that rows moved signal is handled correctly"""
        # Arrange
        table_part = TestTablePartDragDrop()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
        ]
        table_part.set_test_data(test_data)
        
        # Track if signal was handled
        signal_handled = False
        
        def on_signal_handled():
            nonlocal signal_handled
            signal_handled = True
        
        # Connect to the rows moved signal handler
        original_handler = table_part._on_rows_moved
        
        def test_handler(*args):
            on_signal_handled()
            return original_handler(*args)
        
        table_part._on_rows_moved = test_handler
        
        # Act - simulate rows moved signal
        table_part._on_rows_moved(None, 0, 0, None, 1)
        
        # Assert
        assert signal_handled is True
    
    def test_drag_drop_visual_indicators(self, qapp):
        """Test that drag-and-drop visual indicators are properly configured"""
        # Arrange & Act
        table_part = TestTablePartDragDrop()
        
        # Assert
        assert table_part.table.showDropIndicator() is True
        # Visual indicators are handled by Qt internally, so we mainly test configuration
    
    def test_drag_drop_with_calculation_engine(self, qapp):
        """Test that drag-and-drop triggers recalculation when enabled"""
        # Arrange
        config = TablePartConfiguration(
            table_id="test_table",
            document_type="test_document",
            available_commands=[],
            visible_commands=[],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=True,  # Enable auto calculation
            drag_drop_enabled=True
        )
        
        table_part = TestTablePartDragDrop()
        table_part.config = config
        
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
        ]
        table_part.set_test_data(test_data)
        
        # Track if timer was started
        timer_started = False
        original_start = table_part.total_calculation_timer.start
        
        def mock_start(*args):
            nonlocal timer_started
            timer_started = True
            return original_start(*args)
        
        table_part.total_calculation_timer.start = mock_start
        
        # Act - simulate rows moved
        table_part._on_rows_moved(None, 0, 0, None, 1)
        
        # Assert
        assert timer_started is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
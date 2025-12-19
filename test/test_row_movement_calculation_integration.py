#!/usr/bin/env python3
"""
Tests for row movement integration with calculation engine.

Requirements: 7.6
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch

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


class TestTablePartCalculationIntegration(BaseTablePart):
    """Test implementation of BaseTablePart for calculation integration testing"""
    
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
            auto_calculation_enabled=True,  # Enable auto calculation
            drag_drop_enabled=True
        )
        
        super().__init__(config, parent)
        
        # Test data
        self.data = []
        self._setup_table()
    
    def _setup_table(self):
        """Setup table structure"""
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Quantity", "Price"])
    
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
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('price', ''))))
    
    # Implement abstract methods
    
    def _get_table_data(self) -> List[Dict[str, Any]]:
        return self.data
    
    def _add_row(self):
        new_id = len(self.data) + 1
        self.data.append({'id': new_id, 'name': f'Item {new_id}', 'quantity': 1, 'price': 10.0})
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


class TestRowMovementCalculationIntegration:
    """Tests for row movement integration with calculation engine"""
    
    def test_move_rows_up_triggers_calculation(self, qapp):
        """Test that moving rows up triggers recalculation"""
        # Arrange
        table_part = TestTablePartCalculationIntegration()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
            {'id': 3, 'name': 'Item 3', 'quantity': 15, 'price': 7.0},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Mock the timer to track if it was started
        timer_started = False
        original_start = table_part.total_calculation_timer.start
        
        def mock_start(timeout):
            nonlocal timer_started
            timer_started = True
            return original_start(timeout)
        
        table_part.total_calculation_timer.start = mock_start
        
        # Act
        table_part._move_rows_up()
        
        # Assert
        assert timer_started is True
        assert table_part.total_calculation_timer.interval() == table_part.config.total_calculation_timeout_ms
    
    def test_move_rows_down_triggers_calculation(self, qapp):
        """Test that moving rows down triggers recalculation"""
        # Arrange
        table_part = TestTablePartCalculationIntegration()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
            {'id': 3, 'name': 'Item 3', 'quantity': 15, 'price': 7.0},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Mock the timer to track if it was started
        timer_started = False
        original_start = table_part.total_calculation_timer.start
        
        def mock_start(timeout):
            nonlocal timer_started
            timer_started = True
            return original_start(timeout)
        
        table_part.total_calculation_timer.start = mock_start
        
        # Act
        table_part._move_rows_down()
        
        # Assert
        assert timer_started is True
        assert table_part.total_calculation_timer.interval() == table_part.config.total_calculation_timeout_ms
    
    def test_drag_drop_triggers_calculation(self, qapp):
        """Test that drag-and-drop triggers recalculation"""
        # Arrange
        table_part = TestTablePartCalculationIntegration()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
        ]
        table_part.set_test_data(test_data)
        
        # Mock the timer to track if it was started
        timer_started = False
        original_start = table_part.total_calculation_timer.start
        
        def mock_start(timeout):
            nonlocal timer_started
            timer_started = True
            return original_start(timeout)
        
        table_part.total_calculation_timer.start = mock_start
        
        # Act - simulate drag and drop
        table_part._on_rows_moved(None, 0, 0, None, 1)
        
        # Assert
        assert timer_started is True
        assert table_part.total_calculation_timer.interval() == table_part.config.total_calculation_timeout_ms
    
    def test_calculation_disabled_no_trigger(self, qapp):
        """Test that calculation is not triggered when disabled"""
        # Arrange
        config = TablePartConfiguration(
            table_id="test_table",
            document_type="test_document",
            available_commands=[],
            visible_commands=[],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=False,  # Disable auto calculation
            drag_drop_enabled=True
        )
        
        table_part = TestTablePartCalculationIntegration()
        table_part.config = config
        
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Mock the timer to track if it was started
        timer_started = False
        original_start = table_part.total_calculation_timer.start
        
        def mock_start(timeout):
            nonlocal timer_started
            timer_started = True
            return original_start(timeout)
        
        table_part.total_calculation_timer.start = mock_start
        
        # Act
        table_part._move_rows_up()
        
        # Assert - timer should not be started when calculation is disabled
        assert timer_started is False
    
    def test_calculation_performance_targets(self, qapp):
        """Test that calculation performance targets are met"""
        # Arrange
        table_part = TestTablePartCalculationIntegration()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
        ]
        table_part.set_test_data(test_data)
        
        # Act & Assert - check that timeout is set correctly
        assert table_part.config.total_calculation_timeout_ms == 200
        
        # The actual performance measurement would require integration with
        # the real calculation engine, which is beyond the scope of this test
    
    def test_multiple_moves_debounce_calculation(self, qapp):
        """Test that multiple rapid moves properly debounce calculations"""
        # Arrange
        table_part = TestTablePartCalculationIntegration()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'quantity': 10, 'price': 5.0},
            {'id': 2, 'name': 'Item 2', 'quantity': 20, 'price': 3.0},
            {'id': 3, 'name': 'Item 3', 'quantity': 15, 'price': 7.0},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Mock the timer to track calls
        start_call_count = 0
        stop_call_count = 0
        
        original_start = table_part.total_calculation_timer.start
        original_stop = table_part.total_calculation_timer.stop
        
        def mock_start(timeout):
            nonlocal start_call_count
            start_call_count += 1
            return original_start(timeout)
        
        def mock_stop():
            nonlocal stop_call_count
            stop_call_count += 1
            return original_stop()
        
        table_part.total_calculation_timer.start = mock_start
        table_part.total_calculation_timer.stop = mock_stop
        
        # Act - perform multiple moves rapidly
        table_part._move_rows_up()
        table_part._move_rows_down()
        table_part._move_rows_up()
        
        # Assert - timer should be stopped and restarted for each move
        assert stop_call_count >= 2  # Should stop before each restart
        assert start_call_count == 3  # Should start for each move


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
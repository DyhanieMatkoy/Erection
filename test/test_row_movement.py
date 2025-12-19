#!/usr/bin/env python3
"""
Tests for row movement functionality in table parts.

Requirements: 7.1, 7.2, 7.5
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
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


class TestTablePart(BaseTablePart):
    """Test implementation of BaseTablePart"""
    
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
            drag_drop_enabled=True
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
                # Select the entire row using the selection model
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


class TestRowMovement:
    """Tests for row movement functionality"""
    
    def test_move_single_row_up(self, qapp):
        """Test moving a single row up"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Act
        table_part._move_rows_up()
        
        # Assert
        data = table_part._get_table_data()
        assert data[0]['id'] == 2  # Item 2 moved to position 0
        assert data[1]['id'] == 1  # Item 1 moved to position 1
        assert data[2]['id'] == 3  # Item 3 stayed at position 2
        
        # Check selection followed the moved row
        selected = table_part.get_selected_rows()
        assert 0 in selected  # Row should now be selected at position 0
    
    def test_move_single_row_down(self, qapp):
        """Test moving a single row down"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Act
        table_part._move_rows_down()
        
        # Assert
        data = table_part._get_table_data()
        assert data[0]['id'] == 1  # Item 1 stayed at position 0
        assert data[1]['id'] == 3  # Item 3 moved to position 1
        assert data[2]['id'] == 2  # Item 2 moved to position 2
        
        # Check selection followed the moved row
        selected = table_part.get_selected_rows()
        assert 2 in selected  # Row should now be selected at position 2
    
    def test_move_multiple_rows_up(self, qapp):
        """Test moving multiple rows up"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
            {'id': 4, 'name': 'Item 4', 'value': 40},
        ]
        table_part.set_test_data(test_data)
        
        # Select rows 1 and 2 (Item 2 and Item 3) using proper multi-selection
        from PyQt6.QtCore import QItemSelectionModel
        selection_model = table_part.table.selectionModel()
        selection_model.select(
            table_part.table.model().index(1, 0),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        )
        selection_model.select(
            table_part.table.model().index(2, 0),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        )
        
        # Debug: Check what rows are selected before move
        selected_before = table_part.get_selected_rows()
        print(f"Selected rows before move: {selected_before}")
        
        # Act
        table_part._move_rows_up()
        
        # Debug: Check data and selection after move
        data = table_part._get_table_data()
        selected_after = table_part.get_selected_rows()
        print(f"Data after move: {[item['id'] for item in data]}")
        print(f"Selected rows after move: {selected_after}")
        
        # Assert
        assert data[0]['id'] == 2  # Item 2 moved to position 0
        assert data[1]['id'] == 3  # Item 3 moved to position 1
        assert data[2]['id'] == 1  # Item 1 moved to position 2
        assert data[3]['id'] == 4  # Item 4 stayed at position 3
        
        # Check selection followed the moved rows
        selected = table_part.get_selected_rows()
        assert 0 in selected
        assert 1 in selected
    
    def test_move_multiple_rows_down(self, qapp):
        """Test moving multiple rows down"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
            {'id': 4, 'name': 'Item 4', 'value': 40},
        ]
        table_part.set_test_data(test_data)
        
        # Select rows 1 and 2 (Item 2 and Item 3) using proper multi-selection
        from PyQt6.QtCore import QItemSelectionModel
        selection_model = table_part.table.selectionModel()
        selection_model.select(
            table_part.table.model().index(1, 0),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        )
        selection_model.select(
            table_part.table.model().index(2, 0),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        )
        
        # Act
        table_part._move_rows_down()
        
        # Assert
        data = table_part._get_table_data()
        assert data[0]['id'] == 1  # Item 1 stayed at position 0
        assert data[1]['id'] == 4  # Item 4 moved to position 1
        assert data[2]['id'] == 2  # Item 2 moved to position 2
        assert data[3]['id'] == 3  # Item 3 moved to position 3
        
        # Check selection followed the moved rows
        selected = table_part.get_selected_rows()
        assert 2 in selected
        assert 3 in selected
    
    def test_cannot_move_first_row_up(self, qapp):
        """Test that first row cannot be moved up"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 0 (Item 1)
        table_part.table.selectRow(0)
        
        # Act
        table_part._move_rows_up()
        
        # Assert - data should remain unchanged
        data = table_part._get_table_data()
        assert data[0]['id'] == 1
        assert data[1]['id'] == 2
    
    def test_cannot_move_last_row_down(self, qapp):
        """Test that last row cannot be moved down"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Act
        table_part._move_rows_down()
        
        # Assert - data should remain unchanged
        data = table_part._get_table_data()
        assert data[0]['id'] == 1
        assert data[1]['id'] == 2
    
    def test_move_with_no_selection(self, qapp):
        """Test that moving with no selection does nothing"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
        ]
        table_part.set_test_data(test_data)
        
        # No selection
        
        # Act
        table_part._move_rows_up()
        table_part._move_rows_down()
        
        # Assert - data should remain unchanged
        data = table_part._get_table_data()
        assert data[0]['id'] == 1
        assert data[1]['id'] == 2
    
    def test_selection_maintained_after_move(self, qapp):
        """Test that selection is maintained after row movement"""
        # Arrange
        table_part = TestTablePart()
        test_data = [
            {'id': 1, 'name': 'Item 1', 'value': 10},
            {'id': 2, 'name': 'Item 2', 'value': 20},
            {'id': 3, 'name': 'Item 3', 'value': 30},
        ]
        table_part.set_test_data(test_data)
        
        # Select row 1 (Item 2)
        table_part.table.selectRow(1)
        
        # Act - move up
        table_part._move_rows_up()
        
        # Assert - selection should follow the moved row
        selected = table_part.get_selected_rows()
        assert len(selected) == 1
        assert 0 in selected
        
        # Act - move down
        table_part._move_rows_down()
        
        # Assert - selection should follow the moved row back
        selected = table_part.get_selected_rows()
        assert len(selected) == 1
        assert 1 in selected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

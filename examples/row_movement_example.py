#!/usr/bin/env python3
"""
Row Movement Example for Table Parts.

This example demonstrates the row movement functionality in table parts,
including move up/down button actions and keyboard shortcuts.

Requirements: 7.1, 7.2, 7.5
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.views.widgets.base_table_part import (
    BaseTablePart, TablePartConfiguration, TablePartCommand, CommandType
)


@dataclass
class SampleRowData:
    """Sample data structure for demonstration"""
    id: int
    name: str
    quantity: float
    price: float
    sum: float = 0.0
    
    def __post_init__(self):
        self.sum = self.quantity * self.price


class SampleTablePart(BaseTablePart):
    """
    Sample implementation of BaseTablePart for testing row movement.
    """
    
    def __init__(self, parent=None):
        # Create configuration
        config = TablePartConfiguration(
            table_id="sample_table",
            document_type="sample_document",
            available_commands=[],
            visible_commands=[
                CommandType.ADD_ROW.value,
                CommandType.DELETE_ROW.value,
                CommandType.MOVE_UP.value,
                CommandType.MOVE_DOWN.value
            ],
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=True,
            drag_drop_enabled=True
        )
        
        super().__init__(config, parent)
        
        # Sample data
        self.data = [
            SampleRowData(1, "Item A", 10.0, 5.50),
            SampleRowData(2, "Item B", 20.0, 3.25),
            SampleRowData(3, "Item C", 15.0, 7.80),
            SampleRowData(4, "Item D", 8.0, 12.00),
            SampleRowData(5, "Item E", 25.0, 2.40),
        ]
        
        self._setup_table_columns()
        self._populate_table()
    
    def _setup_table_columns(self):
        """Setup table columns"""
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Наименование", "Количество", "Цена", "Сумма"
        ])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
    
    def _populate_table(self):
        """Populate table with sample data"""
        self.table.setRowCount(len(self.data))
        
        for row, item in enumerate(self.data):
            self.table.setItem(row, 0, self._create_item(str(item.id)))
            self.table.setItem(row, 1, self._create_item(item.name))
            self.table.setItem(row, 2, self._create_item(f"{item.quantity:.3f}"))
            self.table.setItem(row, 3, self._create_item(f"{item.price:.2f}"))
            self.table.setItem(row, 4, self._create_item(f"{item.sum:.2f}"))
    
    def _create_item(self, text: str):
        """Create a table widget item"""
        from PyQt6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        return item
    
    # Implementation of abstract methods
    
    def _get_table_data(self) -> List[Dict[str, Any]]:
        """Get current table data as list of dictionaries"""
        return [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'price': item.price,
                'sum': item.sum
            }
            for item in self.data
        ]
    
    def _add_row(self):
        """Add a new row to the table"""
        new_id = max(item.id for item in self.data) + 1 if self.data else 1
        new_item = SampleRowData(new_id, f"New Item {new_id}", 1.0, 0.0)
        
        self.data.append(new_item)
        self._populate_table()
        
        # Select the new row
        new_row = len(self.data) - 1
        self.table.selectRow(new_row)
        self.table.setCurrentCell(new_row, 1)  # Focus on name column
    
    def _delete_selected_rows(self):
        """Delete selected rows from the table"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return
        
        # Sort in reverse order to delete from bottom up
        selected_rows.sort(reverse=True)
        
        for row in selected_rows:
            if 0 <= row < len(self.data):
                del self.data[row]
        
        self._populate_table()
    
    def _swap_rows(self, row1: int, row2: int):
        """Swap two rows in the table data"""
        if (0 <= row1 < len(self.data) and 
            0 <= row2 < len(self.data) and 
            row1 != row2):
            
            # Swap in data
            self.data[row1], self.data[row2] = self.data[row2], self.data[row1]
            
            # Repopulate table to reflect changes
            self._populate_table()
    
    def _update_selection(self, row_indices: List[int]):
        """Update row selection"""
        self.table.clearSelection()
        for row in row_indices:
            if 0 <= row < self.table.rowCount():
                self.table.selectRow(row)
    
    def _get_import_columns(self) -> List:
        """Get import column definitions for this table part"""
        return []  # Not implemented for this example
    
    def _on_data_imported(self, data: List[Dict[str, Any]]):
        """Handle imported data"""
        pass  # Not implemented for this example
    
    def _get_export_columns(self) -> List:
        """Get export column definitions for this table part"""
        return []  # Not implemented for this example
    
    def _open_reference_selector(self):
        """Open reference selector for current cell"""
        pass  # Not implemented for this example
    
    def _get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific row"""
        if 0 <= row < len(self.data):
            item = self.data[row]
            return {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'price': item.price,
                'sum': item.sum
            }
        return None
    
    def _update_calculated_field(self, row: int, column: str, value: Any):
        """Update a calculated field in the table"""
        if 0 <= row < len(self.data):
            item = self.data[row]
            if column == 'sum':
                item.sum = value
                # Update table display
                self.table.setItem(row, 4, self._create_item(f"{value:.2f}"))
    
    def _update_document_totals(self, totals: Dict[str, Any]):
        """Update document totals display"""
        # For this example, just print totals
        print(f"Document totals updated: {totals}")


class RowMovementExampleWindow(QMainWindow):
    """Main window for row movement example"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Row Movement Example - Table Parts")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Row Movement Example")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add instructions
        instructions = QLabel(
            "Instructions:\n"
            "• Select one or more rows by clicking\n"
            "• Use Ctrl+Click for multi-select\n"
            "• Click 'Выше' button or press Ctrl+Shift+Up to move rows up\n"
            "• Click 'Ниже' button or press Ctrl+Shift+Down to move rows down\n"
            "• Use Insert to add new rows, Delete to remove selected rows"
        )
        instructions.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
        # Create table part
        self.table_part = SampleTablePart()
        layout.addWidget(self.table_part)
        
        # Connect signals for demonstration
        self.table_part.rowSelectionChanged.connect(self._on_selection_changed)
        self.table_part.commandExecuted.connect(self._on_command_executed)
    
    def _on_selection_changed(self, selected_rows: List[int]):
        """Handle selection changes"""
        print(f"Selection changed: {selected_rows}")
    
    def _on_command_executed(self, command_id: str, context: dict):
        """Handle command execution"""
        print(f"Command executed: {command_id} with context: {context}")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = RowMovementExampleWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
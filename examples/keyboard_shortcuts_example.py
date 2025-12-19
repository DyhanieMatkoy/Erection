"""
Example demonstrating keyboard shortcuts functionality in table parts.

This example shows how to use the TablePartKeyboardHandler to implement
standard keyboard shortcuts for table operations.

Requirements: 3.1, 3.2, 7.3, 7.4
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QLabel, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt

from src.services.table_part_keyboard_handler import (
    TablePartKeyboardHandler,
    ShortcutAction,
    ShortcutContext,
    create_keyboard_handler,
    create_table_context
)


class KeyboardShortcutsDemo(QMainWindow):
    """Demo window showing keyboard shortcuts functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Part Keyboard Shortcuts Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Table Part Keyboard Shortcuts Demo")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add instructions
        instructions = QLabel(
            "Try these keyboard shortcuts:\n"
            "• Insert - Add new row\n"
            "• Delete - Delete selected rows\n"
            "• Ctrl+C - Copy selected rows\n"
            "• Ctrl+V - Paste rows\n"
            "• Ctrl+Shift+Up/Down - Move rows\n"
            "• F4 - Open reference selector\n"
            "• Ctrl++ / Ctrl+- - Add/Delete rows (alternative)"
        )
        instructions.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
        # Create table
        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Description"])
        
        # Add sample data
        sample_data = [
            ["Item 1", "100", "First item"],
            ["Item 2", "200", "Second item"],
            ["Item 3", "300", "Third item"],
            ["Item 4", "400", "Fourth item"],
            ["Item 5", "500", "Fifth item"]
        ]
        
        for row, row_data in enumerate(sample_data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        
        # Create log area
        log_label = QLabel("Action Log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        layout.addWidget(self.log_area)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_log_btn)
        
        help_btn = QPushButton("Show Help")
        help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(help_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Setup keyboard handler
        self.setup_keyboard_handler()
        
        # Connect table signals
        self.table.itemSelectionChanged.connect(self.update_keyboard_context)
        
        self.log("Demo initialized. Try using keyboard shortcuts!")
    
    def setup_keyboard_handler(self):
        """Setup keyboard shortcut handler"""
        self.keyboard_handler = create_keyboard_handler(self)
        
        # Register action handlers
        self.keyboard_handler.register_action_handler(
            ShortcutAction.ADD_ROW, 
            self.handle_add_row
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.DELETE_ROW, 
            self.handle_delete_row
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.COPY_ROWS, 
            self.handle_copy_rows
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.PASTE_ROWS, 
            self.handle_paste_rows
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.MOVE_ROW_UP, 
            self.handle_move_row_up
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.MOVE_ROW_DOWN, 
            self.handle_move_row_down
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.OPEN_REFERENCE_SELECTOR, 
            self.handle_open_reference_selector
        )
        
        # Connect signals
        self.keyboard_handler.shortcutTriggered.connect(self.on_shortcut_triggered)
        self.keyboard_handler.shortcutBlocked.connect(self.on_shortcut_blocked)
        
        # Initial context update
        self.update_keyboard_context()
    
    def update_keyboard_context(self):
        """Update keyboard handler context based on table state"""
        selected_rows = []
        for item in self.table.selectedItems():
            if item.row() not in selected_rows:
                selected_rows.append(item.row())
        
        current_item = self.table.currentItem()
        current_row = current_item.row() if current_item else None
        
        # Check if editing
        is_editing = self.table.state() == self.table.State.EditingState
        
        context = create_table_context(
            widget=self,
            selected_rows=selected_rows,
            current_row=current_row,
            is_hierarchical=False,
            is_editing=is_editing
        )
        
        self.keyboard_handler.update_context(context)
    
    def handle_add_row(self, context: ShortcutContext):
        """Handle add row action"""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Add default data
        self.table.setItem(row_count, 0, QTableWidgetItem(f"New Item {row_count + 1}"))
        self.table.setItem(row_count, 1, QTableWidgetItem("0"))
        self.table.setItem(row_count, 2, QTableWidgetItem("New item description"))
        
        self.log(f"Added new row at position {row_count}")
    
    def handle_delete_row(self, context: ShortcutContext):
        """Handle delete row action"""
        if not context.selected_rows:
            self.log("No rows selected for deletion")
            return
        
        # Sort in reverse order to delete from bottom up
        rows_to_delete = sorted(context.selected_rows, reverse=True)
        
        for row in rows_to_delete:
            self.table.removeRow(row)
        
        self.log(f"Deleted {len(rows_to_delete)} row(s): {rows_to_delete}")
    
    def handle_copy_rows(self, context: ShortcutContext):
        """Handle copy rows action"""
        if not context.selected_rows:
            self.log("No rows selected for copying")
            return
        
        # Store copied data (simplified implementation)
        self.copied_data = []
        for row in context.selected_rows:
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            self.copied_data.append(row_data)
        
        self.log(f"Copied {len(context.selected_rows)} row(s)")
    
    def handle_paste_rows(self, context: ShortcutContext):
        """Handle paste rows action"""
        if not hasattr(self, 'copied_data') or not self.copied_data:
            self.log("No data to paste")
            return
        
        # Insert copied data at current position
        current_row = context.current_row or self.table.rowCount()
        
        for i, row_data in enumerate(self.copied_data):
            insert_row = current_row + i
            self.table.insertRow(insert_row)
            
            for col, value in enumerate(row_data):
                self.table.setItem(insert_row, col, QTableWidgetItem(value))
        
        self.log(f"Pasted {len(self.copied_data)} row(s) at position {current_row}")
    
    def handle_move_row_up(self, context: ShortcutContext):
        """Handle move row up action"""
        if not context.selected_rows:
            self.log("No rows selected for moving")
            return
        
        # Can't move up if first row is selected
        if 0 in context.selected_rows:
            self.log("Cannot move up: first row is selected")
            return
        
        # Move each selected row up
        for row in sorted(context.selected_rows):
            self.swap_rows(row, row - 1)
        
        self.log(f"Moved row(s) up: {context.selected_rows}")
    
    def handle_move_row_down(self, context: ShortcutContext):
        """Handle move row down action"""
        if not context.selected_rows:
            self.log("No rows selected for moving")
            return
        
        # Can't move down if last row is selected
        if (self.table.rowCount() - 1) in context.selected_rows:
            self.log("Cannot move down: last row is selected")
            return
        
        # Move each selected row down (in reverse order)
        for row in sorted(context.selected_rows, reverse=True):
            self.swap_rows(row, row + 1)
        
        self.log(f"Moved row(s) down: {context.selected_rows}")
    
    def handle_open_reference_selector(self, context: ShortcutContext):
        """Handle open reference selector action"""
        current_item = self.table.currentItem()
        if current_item:
            row, col = current_item.row(), current_item.column()
            self.log(f"Opening reference selector for cell ({row}, {col})")
        else:
            self.log("Opening reference selector (no specific cell)")
    
    def swap_rows(self, row1: int, row2: int):
        """Swap two rows in the table"""
        for col in range(self.table.columnCount()):
            item1 = self.table.takeItem(row1, col)
            item2 = self.table.takeItem(row2, col)
            
            if item1:
                self.table.setItem(row2, col, item1)
            if item2:
                self.table.setItem(row1, col, item2)
    
    def on_shortcut_triggered(self, action: ShortcutAction, context: ShortcutContext):
        """Handle shortcut triggered signal"""
        # This is called after the action handler, so we can log additional info
        pass
    
    def on_shortcut_blocked(self, action: ShortcutAction, reason: str):
        """Handle shortcut blocked signal"""
        self.log(f"Shortcut {action.value} blocked: {reason}")
    
    def log(self, message: str):
        """Add message to log area"""
        self.log_area.append(f"• {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear the log area"""
        self.log_area.clear()
        self.log("Log cleared")
    
    def show_help(self):
        """Show keyboard shortcuts help"""
        help_text = self.keyboard_handler.get_shortcut_help_text()
        self.log("=== Keyboard Shortcuts Help ===")
        for line in help_text.split('\n'):
            if line.strip():
                self.log(line)
        self.log("=== End Help ===")


def main():
    """Run the keyboard shortcuts demo"""
    app = QApplication(sys.argv)
    
    demo = KeyboardShortcutsDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
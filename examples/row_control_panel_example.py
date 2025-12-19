"""
Example demonstrating Row Control Panel with Command Manager Integration.

This example shows how to use the row control panel component with
form command integration for document table parts.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import pyqtSlot

from src.views.widgets.row_control_panel import RowControlPanel
from src.services.table_part_command_manager import (
    TablePartCommandManager, CommandContext, CommandResult, table_command, CommandAvailability
)


class ExampleDocumentForm(QMainWindow):
    """Example document form with table part and integrated commands"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Row Control Panel Example")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create command manager
        self.command_manager = TablePartCommandManager()
        
        # Create row control panel
        self.row_panel = RowControlPanel(command_manager=self.command_manager)
        layout.addWidget(self.row_panel)
        
        # Create table widget
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Quantity", "Price"])
        layout.addWidget(self.table)
        
        # Connect panel signals
        self.row_panel.commandTriggered.connect(self.handle_command)
        self.row_panel.customizeRequested.connect(self.customize_panel)
        
        # Register this form instance for command discovery
        self.row_panel.register_form_instance(self)
        
        # Add some sample data
        self.add_sample_data()
        
        # Update panel state
        self.update_panel_state()
    
    def add_sample_data(self):
        """Add some sample data to the table"""
        sample_data = [
            ("Item 1", "10", "25.50"),
            ("Item 2", "5", "15.00"),
            ("Item 3", "8", "30.75")
        ]
        
        for row_data in sample_data:
            self.add_table_row_with_data(row_data)
    
    def add_table_row_with_data(self, data=None):
        """Add a row to the table with optional data"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        if data:
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)
        else:
            # Add empty row
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem("")
                self.table.setItem(row, col, item)
        
        self.update_panel_state()
    
    # Form commands discovered by naming convention
    def add_row(self):
        """Add a new row (discovered by naming convention)"""
        print("Adding new row...")
        self.add_table_row_with_data()
        return True
    
    def delete_row(self):
        """Delete selected rows (discovered by naming convention)"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            print("No rows selected for deletion")
            return False
        
        print(f"Deleting {len(selected_rows)} rows...")
        
        # Remove rows in reverse order to maintain indices
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
        
        self.update_panel_state()
        return True
    
    def move_up(self):
        """Move selected rows up"""
        selected_rows = self.get_selected_rows()
        if not selected_rows or 0 in selected_rows:
            print("Cannot move up: no selection or first row selected")
            return False
        
        print("Moving rows up...")
        # Implementation would go here
        return True
    
    def move_down(self):
        """Move selected rows down"""
        selected_rows = self.get_selected_rows()
        if not selected_rows or (self.table.rowCount() - 1) in selected_rows:
            print("Cannot move down: no selection or last row selected")
            return False
        
        print("Moving rows down...")
        # Implementation would go here
        return True
    
    def import_data(self):
        """Import data from file"""
        print("Importing data...")
        # Implementation would go here
        return True
    
    def export_data(self):
        """Export data to file"""
        print("Exporting data...")
        # Implementation would go here
        return True
    
    def print_data(self):
        """Print table data"""
        print("Printing data...")
        # Implementation would go here
        return True
    
    # Form commands using decorator (alternative approach)
    @table_command(
        command_id='duplicate_row',
        name='Duplicate Row',
        availability=CommandAvailability.REQUIRES_SELECTION
    )
    def duplicate_selected_row(self, context: CommandContext):
        """Duplicate the selected row"""
        if not context.selected_rows:
            return CommandResult(success=False, message="No row selected")
        
        row_to_duplicate = context.selected_rows[0]
        print(f"Duplicating row {row_to_duplicate}...")
        
        # Get data from selected row
        row_data = []
        for col in range(self.table.columnCount()):
            item = self.table.item(row_to_duplicate, col)
            row_data.append(item.text() if item else "")
        
        # Add duplicated row
        self.add_table_row_with_data(tuple(row_data))
        
        return CommandResult(
            success=True,
            message="Row duplicated successfully",
            affected_rows=[self.table.rowCount() - 1]
        )
    
    def get_selected_rows(self):
        """Get list of selected row indices"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        return list(selected_rows)
    
    def get_table_data(self):
        """Get current table data"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col in range(self.table.columnCount()):
                header = self.table.horizontalHeaderItem(col).text()
                item = self.table.item(row, col)
                row_data[header] = item.text() if item else ""
            data.append(row_data)
        return data
    
    def update_panel_state(self):
        """Update panel button states based on current selection"""
        selected_rows = self.get_selected_rows()
        table_data = self.get_table_data()
        
        # Update panel with current context
        self.row_panel.update_context_and_states(
            selected_rows=selected_rows,
            table_data=table_data,
            additional_data={}
        )
    
    @pyqtSlot(str)
    def handle_command(self, command_id: str):
        """Handle command execution from panel"""
        print(f"Command triggered: {command_id}")
        self.update_panel_state()
    
    @pyqtSlot()
    def customize_panel(self):
        """Handle panel customization request"""
        print("Panel customization requested")
        # Here you would open a customization dialog
        
        # Example: Hide some commands
        current_commands = self.row_panel.get_visible_commands()
        if 'import_data' in current_commands:
            current_commands.remove('import_data')
            self.row_panel.set_visible_commands(current_commands)
            print("Hidden import command")
        else:
            current_commands.append('import_data')
            self.row_panel.set_visible_commands(current_commands)
            print("Shown import command")


def main():
    """Run the example application"""
    app = QApplication(sys.argv)
    
    # Create and show the example form
    form = ExampleDocumentForm()
    form.show()
    
    print("Row Control Panel Example")
    print("=" * 40)
    print("Features demonstrated:")
    print("- Row control panel with standard buttons")
    print("- Command discovery by naming convention")
    print("- Button state management based on selection")
    print("- Form command integration")
    print("- Panel customization")
    print()
    print("Try:")
    print("- Select rows and see button states change")
    print("- Click buttons to execute commands")
    print("- Click the gear icon to customize the panel")
    print()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
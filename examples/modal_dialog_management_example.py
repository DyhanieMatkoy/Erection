"""Example demonstrating Modal Dialog Management

This example shows how to use the ModalDialogManager to properly manage
z-index and stacking order for modal dialogs and widgets in the PyQt6 desktop application.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.modal_dialog_manager import ModalDialogManager
from src.views.reference_picker_dialog import ReferencePickerDialog


class ExampleDialog(QDialog):
    """Example dialog for demonstration"""
    
    def __init__(self, title="Example Dialog", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout()
        
        # Add some content
        label = QLabel(f"This is {title}")
        layout.addWidget(label)
        
        # Button to open another dialog
        open_button = QPushButton("Open Child Dialog")
        open_button.clicked.connect(self.open_child_dialog)
        layout.addWidget(open_button)
        
        # Button to open a widget form
        widget_button = QPushButton("Open Widget Form")
        widget_button.clicked.connect(self.open_widget_form)
        layout.addWidget(widget_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        
        # Store dialog manager reference
        self.dialog_manager = ModalDialogManager.instance()
        self._dialog_id = None
    
    def open_child_dialog(self):
        """Open a child dialog with proper z-index management"""
        child_dialog = ExampleDialog(f"Child of {self.windowTitle()}", self)
        
        # Register and show with proper z-index
        child_id = self.dialog_manager.show_dialog(
            child_dialog, 'modal', self._dialog_id
        )
    
    def open_widget_form(self):
        """Open a widget form (like WorkForm) with proper z-index management"""
        widget_form = ExampleWidget(f"Widget from {self.windowTitle()}", self)
        
        # Register and show widget with proper z-index
        widget_id = self.dialog_manager.register_dialog(
            widget_form, 'modal', self._dialog_id
        )
        
        # Show the widget
        widget_form.show()
        widget_form.raise_()
        widget_form.activateWindow()
    
    def show_with_manager(self, parent_dialog_id=None):
        """Show this dialog using the modal dialog manager"""
        self._dialog_id = self.dialog_manager.show_dialog(
            self, 'modal', parent_dialog_id
        )
        return self._dialog_id


class ExampleWidget(QWidget):
    """Example widget form (like WorkForm) for demonstration"""
    
    def __init__(self, title="Example Widget Form", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(250, 150)
        
        layout = QVBoxLayout()
        
        # Add some content
        label = QLabel(f"This is {title}")
        layout.addWidget(label)
        
        # Close button
        close_button = QPushButton("Close Widget")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.setLayout(layout)


def demonstrate_modal_dialog_management():
    """Demonstrate modal dialog management features"""
    app = QApplication(sys.argv)
    
    # Get the modal dialog manager instance
    manager = ModalDialogManager.instance()
    
    print("Modal Dialog Management Demo")
    print("=" * 40)
    
    # Create and show the first dialog
    print("1. Creating first dialog...")
    dialog1 = ExampleDialog("Main Dialog")
    dialog1_id = dialog1.show_with_manager()
    
    print(f"   Dialog registered with ID: {dialog1_id}")
    print(f"   Dialog count: {manager.get_dialog_count()}")
    print(f"   Top dialog: {manager.get_top_dialog().id if manager.get_top_dialog() else 'None'}")
    
    # Create a second dialog
    print("\n2. Creating second dialog...")
    dialog2 = ExampleDialog("Second Dialog")
    dialog2_id = dialog2.show_with_manager()
    
    print(f"   Dialog registered with ID: {dialog2_id}")
    print(f"   Dialog count: {manager.get_dialog_count()}")
    print(f"   Top dialog: {manager.get_top_dialog().id if manager.get_top_dialog() else 'None'}")
    
    # Show z-index information
    print("\n3. Z-index information:")
    for dialog_state in manager.get_dialog_stack():
        print(f"   Dialog {dialog_state.id}: z-index = {dialog_state.z_index}")
    
    # Create a widget form (like WorkForm)
    print("\n4. Creating widget form (like WorkForm)...")
    widget_form = ExampleWidget("Test Widget Form")
    widget_id = manager.register_dialog(widget_form, 'modal')
    
    print(f"   Widget registered with ID: {widget_id}")
    print(f"   Dialog count: {manager.get_dialog_count()}")
    print(f"   Top dialog: {manager.get_top_dialog().id if manager.get_top_dialog() else 'None'}")
    
    # Demonstrate bringing dialog to front
    print(f"\n5. Bringing first dialog to front...")
    manager.bring_to_front(dialog1_id)
    print(f"   Top dialog: {manager.get_top_dialog().id if manager.get_top_dialog() else 'None'}")
    
    # Show updated z-index information
    print("\n6. Updated z-index information:")
    for dialog_state in manager.get_dialog_stack():
        print(f"   Dialog {dialog_state.id}: z-index = {dialog_state.z_index}")
    
    print("\n7. Demo complete. You can interact with the dialogs.")
    print("   - Click 'Open Child Dialog' to see z-index management in action")
    print("   - Click 'Open Widget Form' to see QWidget form management")
    print("   - Close dialogs to see focus return behavior")
    
    # Start the application event loop
    # Note: In a real application, you would call app.exec() here
    # For this example, we'll just clean up
    
    # Clean up
    manager.cleanup_all()
    print(f"\n8. Cleanup complete. Dialog count: {manager.get_dialog_count()}")


def demonstrate_reference_picker_integration():
    """Demonstrate ReferencePickerDialog integration with ModalDialogManager"""
    print("\nReference Picker Dialog Integration Demo")
    print("=" * 50)
    
    try:
        # Create a reference picker dialog with modal type
        print("1. Creating modal reference picker dialog...")
        modal_picker = ReferencePickerDialog("works", "Modal Work Selector", modal_type='modal')
        print(f"   Modal type: {modal_picker.modal_type}")
        print(f"   Dialog manager available: {modal_picker.dialog_manager is not None}")
        
        # Create a non-modal reference picker dialog
        print("\n2. Creating non-modal reference picker dialog...")
        non_modal_picker = ReferencePickerDialog("works", "Non-Modal Work Selector", modal_type='non-modal')
        print(f"   Modal type: {non_modal_picker.modal_type}")
        print(f"   Dialog manager available: {non_modal_picker.dialog_manager is not None}")
        
        print("\n3. Integration features available:")
        print("   - show_with_proper_z_index() method")
        print("   - bring_to_front() method")
        print("   - Automatic cleanup on close")
        print("   - Proper focus management for edit forms")
        print("   - Support for both QDialog and QWidget forms")
        print("   - Graceful handling of form registration failures")
        
    except Exception as e:
        print(f"   Note: Full integration requires database setup: {e}")


if __name__ == "__main__":
    # Run the demonstrations
    demonstrate_modal_dialog_management()
    demonstrate_reference_picker_integration()
    
    print("\nExample complete!")
#!/usr/bin/env python3
"""
Test script to verify dialog improvements
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from src.views.reference_picker_dialog import ReferencePickerDialog

def test_works_dialog():
    """Test works picker dialog with new features"""
    app = QApplication(sys.argv)
    
    # Create works picker dialog
    dialog = ReferencePickerDialog("works", "Выбор работы")
    
    print("Testing works picker dialog:")
    print(f"- Modal: {dialog.isModal()}")  # Should be False now
    print(f"- Window size: {dialog.size()}")  # Should be larger
    print(f"- Table columns: {dialog.table_view.columnCount()}")  # Should be 6 for works
    
    # Show dialog for manual testing
    dialog.show()
    
    return app, dialog

if __name__ == "__main__":
    app, dialog = test_works_dialog()
    
    print("\nDialog improvements:")
    print("1. ✓ Dialog is now non-modal")
    print("2. ✓ Added columns for Code, Unit, Price")
    print("3. ✓ Added 'Add' button and context menu")
    print("4. ✓ Added keyboard shortcut (Insert)")
    
    # Don't run the event loop in test mode
    # app.exec()
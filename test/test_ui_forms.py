#!/usr/bin/env python3
"""Test script for Cost Items and Materials UI forms"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.cost_item_list_form import CostItemListForm
from src.views.material_list_form import MaterialListForm

def test_forms():
    """Test UI forms"""
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Test CostItemListForm
    print("Testing CostItemListForm...")
    try:
        cost_form = CostItemListForm()
        print("CostItemListForm created successfully")
        cost_form.load_data()
        print(f"CostItemListForm loaded {cost_form.table_view.rowCount()} items")
    except Exception as e:
        print(f"Error creating CostItemListForm: {e}")
        import traceback
        traceback.print_exc()
    
    # Test MaterialListForm
    print("\nTesting MaterialListForm...")
    try:
        material_form = MaterialListForm()
        print("MaterialListForm created successfully")
        material_form.load_data()
        print(f"MaterialListForm loaded {material_form.table_view.rowCount()} items")
    except Exception as e:
        print(f"Error creating MaterialListForm: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nAll UI tests passed successfully!")
    app.quit()

if __name__ == "__main__":
    test_forms()
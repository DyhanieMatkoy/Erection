import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Mock DatabaseManager and Repositories to avoid DB dependency
with patch('src.data.database_manager.DatabaseManager') as MockDB:
    from src.views.work_form import WorkForm
    from src.views.widgets.work_specification_widget import WorkSpecificationWidget

class TestWorkFormSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        # Mock repositories
        self.work_repo_mock = MagicMock()
        self.spec_repo_mock = MagicMock()
        self.unit_repo_mock = MagicMock()
        self.cim_repo_mock = MagicMock()
        
        # Patch the repositories in WorkForm
        with patch('src.views.work_form.WorkRepository', return_value=self.work_repo_mock), \
             patch('src.views.work_form.WorkSpecificationRepository', return_value=self.spec_repo_mock), \
             patch('src.views.work_form.UnitRepository', return_value=self.unit_repo_mock), \
             patch('src.views.work_form.CostItemMaterialRepository', return_value=self.cim_repo_mock):
            
            self.form = WorkForm()
            # Force use_simplified_specifications to True
            self.form.use_simplified_specifications = True
            # Re-setup UI to show the spec tab
            self.form.setup_ui() 
            
    def tearDown(self):
        self.form.close()

    def test_spec_widget_signals_connection(self):
        """Test that WorkSpecificationWidget signals are connected to WorkForm slots"""
        # Verify widget exists
        self.assertTrue(hasattr(self.form, 'spec_widget'))
        
        # We can't easily check "is connected" in PyQt without firing signals or using internal methods.
        # But we can verify that the methods exist.
        self.assertTrue(hasattr(self.form, 'on_add_spec'))
        self.assertTrue(hasattr(self.form, 'on_edit_spec'))
        self.assertTrue(hasattr(self.form, 'on_delete_spec'))
        self.assertTrue(hasattr(self.form, 'on_copy_spec'))
        self.assertTrue(hasattr(self.form, 'on_import_spec'))
        self.assertTrue(hasattr(self.form, 'on_export_spec'))
        self.assertTrue(hasattr(self.form, 'on_save_template'))
        
    def test_inline_edit_handling(self):
        """Test that inline edits in the table update the WorkForm data"""
        # Add some dummy data
        specs = [{
            'id': 1, 'work_id': 1, 'component_type': 'Material', 
            'component_name': 'Test', 'unit_id': 1, 
            'consumption_rate': 1.0, 'unit_price': 10.0, 'total_cost': 10.0
        }]
        self.form.specifications = specs
        self.form.spec_widget.load_data(specs)
        
        # Simulate inline edit in the table
        # We need to access the table inside the widget
        table = self.form.spec_widget.table
        
        # Simulate signal emission from table
        # entryChanged(row, column_name, new_value)
        # Column 3 is rate
        # We expect WorkForm to update its specs list.
        # BUT currently WorkForm does NOT connect to entryChanged!
        # So this test is expected to FAIL if I check for updates.
        
        # Emit signal
        table.entryChanged.emit(0, 'consumption_rate', 2.0)
        
        # Check if data in WorkForm is updated
        # It should be 2.0
        self.assertEqual(self.form.specifications[0]['consumption_rate'], 2.0, 
                         "WorkForm specifications should be updated after inline edit")
        
        # Check if total cost is recalculated
        # Original total was 10.0. New should be 2.0 * 10.0 = 20.0
        # self.form.calculate_spec_total() should be called
        # We can check the label text
        expected_text = "Общая стоимость: 20.00 руб."
        self.assertEqual(self.form.spec_total_label.text(), expected_text)
        
        # Check is_modified
        self.assertTrue(self.form.is_modified)

if __name__ == '__main__':
    unittest.main()

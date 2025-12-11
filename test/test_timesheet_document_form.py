"""Test timesheet document form - basic import and structure test"""
import sys


def test_timesheet_document_form():
    """Test timesheet document form imports and structure"""
    try:
        # Test imports
        print("Testing imports...")
        from src.views.timesheet_document_form import TimesheetDocumentForm, EmployeePickerDialog
        print("✓ TimesheetDocumentForm imported successfully")
        print("✓ EmployeePickerDialog imported successfully")
        
        from src.data.repositories.timesheet_repository import TimesheetRepository
        print("✓ TimesheetRepository imported successfully")
        
        from src.services.timesheet_posting_service import TimesheetPostingService
        print("✓ TimesheetPostingService imported successfully")
        
        from src.services.auto_fill_service import AutoFillService
        print("✓ AutoFillService imported successfully")
        
        # Check class structure
        print("\nChecking TimesheetDocumentForm class structure...")
        
        # Check methods exist
        methods = [
            'setup_ui',
            'setup_table_columns',
            'on_date_changed',
            'create_new_timesheet',
            'load_timesheet',
            'populate_table',
            'add_table_row',
            'on_add_employee',
            'on_fill_from_daily_reports',
            'on_cell_changed',
            'schedule_recalculation',
            'recalculate_totals',
            'get_table_data',
            'on_select_object',
            'on_select_estimate',
            'load_object',
            'load_estimate',
            'on_field_changed',
            'on_save',
            'on_post',
            'on_unpost',
            'update_posting_state',
            'on_print',
        ]
        
        for method in methods:
            assert hasattr(TimesheetDocumentForm, method), f"Missing method: {method}"
        
        print(f"✓ All {len(methods)} required methods present")
        
        # Check inheritance
        from src.views.base_document_form import BaseDocumentForm
        assert issubclass(TimesheetDocumentForm, BaseDocumentForm), "Should inherit from BaseDocumentForm"
        print("✓ Inherits from BaseDocumentForm")
        
        # Check EmployeePickerDialog structure
        print("\nChecking EmployeePickerDialog class structure...")
        picker_methods = [
            'setup_ui',
            'on_filter_changed',
            'load_data',
            'on_select',
            'get_selected',
        ]
        
        for method in picker_methods:
            assert hasattr(EmployeePickerDialog, method), f"Missing method: {method}"
        
        print(f"✓ All {len(picker_methods)} required methods present")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_timesheet_document_form()
    sys.exit(0 if success else 1)

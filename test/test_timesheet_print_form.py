"""Test timesheet print form generation"""
import sys


def test_timesheet_print_form():
    """Test timesheet print form imports and structure"""
    print("Testing timesheet print form...")
    
    try:
        # Test imports
        print("\n1. Testing imports...")
        from src.services.excel_timesheet_print_form import ExcelTimesheetPrintForm
        print("✓ ExcelTimesheetPrintForm imported successfully")
        
        from src.services.excel_print_form_generator import ExcelPrintFormGenerator
        print("✓ ExcelPrintFormGenerator imported successfully")
        
        # Check class structure
        print("\n2. Checking ExcelTimesheetPrintForm class structure...")
        
        # Check it inherits from base class
        if not issubclass(ExcelTimesheetPrintForm, ExcelPrintFormGenerator):
            print("✗ ExcelTimesheetPrintForm does not inherit from ExcelPrintFormGenerator")
            return False
        print("✓ Inherits from ExcelPrintFormGenerator")
        
        # Check methods exist
        methods = [
            'generate',
            '_load_timesheet_data',
            '_fill_template',
            '_fill_lines_in_template',
            '_create_from_scratch',
            'create_template'
        ]
        
        for method in methods:
            if not hasattr(ExcelTimesheetPrintForm, method):
                print(f"✗ Method '{method}' not found")
                return False
            print(f"✓ Method '{method}' exists")
        
        # Check TEMPLATE_NAME constant
        if not hasattr(ExcelTimesheetPrintForm, 'TEMPLATE_NAME'):
            print("✗ TEMPLATE_NAME constant not found")
            return False
        print(f"✓ TEMPLATE_NAME = '{ExcelTimesheetPrintForm.TEMPLATE_NAME}'")
        
        print("\n3. Checking integration with timesheet document form...")
        from src.views.timesheet_document_form import TimesheetDocumentForm
        print("✓ TimesheetDocumentForm imported successfully")
        
        # Check on_print method exists
        if not hasattr(TimesheetDocumentForm, 'on_print'):
            print("✗ on_print method not found in TimesheetDocumentForm")
            return False
        print("✓ on_print method exists in TimesheetDocumentForm")
        
        print("\n✓ All structure tests passed!")
        print("\nNote: To test actual print form generation, run the application")
        print("and use the 'Печать' button in a timesheet document.")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = test_timesheet_print_form()
        if success:
            print("\n✓ Test completed successfully")
        else:
            print("\n✗ Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

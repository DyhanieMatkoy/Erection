"""Test timesheet list form - basic import and structure test"""
import sys


def test_timesheet_list_form():
    """Test timesheet list form imports and structure"""
    try:
        # Test imports
        print("Testing imports...")
        from src.views.timesheet_list_form import TimesheetListForm
        print("✓ TimesheetListForm imported successfully")
        
        from src.services.timesheet_posting_service import TimesheetPostingService
        print("✓ TimesheetPostingService imported successfully")
        
        from src.data.repositories.timesheet_repository import TimesheetRepository
        print("✓ TimesheetRepository imported successfully")
        
        # Check class structure
        print("\nChecking class structure...")
        
        # Check methods exist
        methods = [
            'setup_ui',
            'load_data',
            'load_objects',
            'load_foremen',
            'on_clear_filters',
            'on_search_text_changed',
            'on_filter_changed',
            'can_create_timesheet',
            'can_edit_timesheet',
            'can_delete_timesheet',
            'can_post_timesheet',
            'on_insert_pressed',
            'on_enter_pressed',
            'on_delete_pressed',
            'on_search_activated',
            'on_context_menu',
            'on_post_selected',
            'on_unpost_selected',
        ]
        
        for method in methods:
            assert hasattr(TimesheetListForm, method), f"Missing method: {method}"
        
        print(f"✓ All {len(methods)} required methods present")
        
        # Check inheritance
        from src.views.base_list_form import BaseListForm
        assert issubclass(TimesheetListForm, BaseListForm), "TimesheetListForm should inherit from BaseListForm"
        print("✓ Correct inheritance from BaseListForm")
        
        # Test main window integration
        print("\nTesting main window integration...")
        from src.views.main_window import MainWindow
        
        # Check method exists
        assert hasattr(MainWindow, 'open_timesheets'), "Missing open_timesheets method in MainWindow"
        print("✓ open_timesheets method exists in MainWindow")
        
        # Check navigation items by reading the file
        with open('src/views/main_window.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'open_timesheets' in content, "open_timesheets not in main_window.py"
            assert '("Табели", "open_timesheets")' in content, "Timesheets not in navigation items"
        print("✓ Timesheets added to navigation items")
        
        # Check menu (already checked in content above)
        assert 'Ctrl+Shift+T' in content, "Keyboard shortcut not found"
        print("✓ Menu item and keyboard shortcut added")
        
        print("\n✅ All structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_timesheet_list_form()
    sys.exit(0 if success else 1)

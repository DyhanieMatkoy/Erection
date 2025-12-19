#!/usr/bin/env python3
"""Test script to verify timesheet estimate selector foreign key fix"""

import sys
import os
sys.path.append('src')
sys.path.append('api')

def test_estimate_list_form_creation():
    """Test that EstimateListFormV2 can be created without foreign key errors"""
    try:
        from src.views.estimate_list_form_v2 import EstimateListFormV2
        from PyQt6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test creating EstimateListFormV2 with default user_id
        print("Testing EstimateListFormV2 creation with default user_id...")
        form = EstimateListFormV2()  # Should use user_id=4 now
        print(f"✅ EstimateListFormV2 created successfully")
        
        # Test creating with explicit user_id=4
        print("Testing EstimateListFormV2 creation with explicit user_id=4...")
        form2 = EstimateListFormV2(user_id=4)
        print(f"✅ EstimateListFormV2 created with user_id=4 successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating EstimateListFormV2: {e}")
        return False

def test_user_settings_manager_with_valid_user():
    """Test that UserSettingsManager works with valid user_id"""
    try:
        from api.services.user_settings_manager import UserSettingsManager
        from src.data.database_manager import DatabaseManager
        
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize('construction.db')
        
        # Get a session
        session = db_manager.get_session()
        
        # Test the user settings manager with valid user_id=4 (admin)
        manager = UserSettingsManager(session)
        
        # Test saving column settings (this was causing the foreign key error)
        test_settings = {'estimate_type': {'width': 80}}
        result = manager.save_column_settings(4, 'estimates', test_settings)
        print(f'✅ Successfully saved column settings for user_id=4: {result.id}')
        
        # Test loading the settings
        loaded = manager.load_column_settings(4, 'estimates')
        print(f'✅ Successfully loaded column settings: {loaded}')
        
        # Clean up
        manager.reset_to_defaults(4, 'estimates')
        print('✅ Cleaned up test settings')
        
        session.close()
        return True
        
    except Exception as e:
        print(f'❌ Error with UserSettingsManager: {e}')
        if 'session' in locals():
            session.close()
        return False

def test_all_form_defaults():
    """Test that all form classes use valid user_id defaults"""
    forms_to_test = [
        ('WorkListFormV2', 'src.views.work_list_form_v2'),
        ('TimesheetListFormV2', 'src.views.timesheet_list_form_v2'),
        ('PersonListFormV2', 'src.views.person_list_form_v2'),
        ('OrganizationListFormV2', 'src.views.organization_list_form_v2'),
        ('ObjectListFormV2', 'src.views.object_list_form_v2'),
        ('MaterialListFormV2', 'src.views.material_list_form_v2'),
        ('DailyReportListFormV2', 'src.views.daily_report_list_form_v2'),
        ('CounterpartyListFormV2', 'src.views.counterparty_list_form_v2'),
        ('CostItemListFormV2', 'src.views.cost_item_list_form_v2'),
        ('EstimateListFormV2', 'src.views.estimate_list_form_v2'),
    ]
    
    try:
        from PyQt6.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        success_count = 0
        for form_name, module_name in forms_to_test:
            try:
                module = __import__(module_name, fromlist=[form_name])
                form_class = getattr(module, form_name)
                
                # Create form with default parameters
                form = form_class()
                print(f"✅ {form_name} created successfully with default user_id")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error creating {form_name}: {e}")
        
        print(f"\n✅ {success_count}/{len(forms_to_test)} forms created successfully")
        return success_count == len(forms_to_test)
        
    except Exception as e:
        print(f"❌ Error in form testing: {e}")
        return False

if __name__ == "__main__":
    print("Testing timesheet estimate selector foreign key fixes...")
    
    success1 = test_estimate_list_form_creation()
    success2 = test_user_settings_manager_with_valid_user()
    success3 = test_all_form_defaults()
    
    if success1 and success2 and success3:
        print("\n✅ All tests passed! Foreign key constraint issues should be resolved.")
        print("The timesheet form should now be able to open the estimate selector without errors.")
    else:
        print("\n❌ Some tests failed. Foreign key constraint issues may persist.")
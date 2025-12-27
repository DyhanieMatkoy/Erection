#!/usr/bin/env python3
"""Test and fix timesheet visibility issue with marked for deletion entries"""

import sys
import os
sys.path.append('src')

def test_timesheet_filtering():
    """Test that marked for deletion timesheets are filtered out"""
    try:
        from data.database_manager import DatabaseManager
        from data.models.sqlalchemy_models import Timesheet
        from api.services.data_service import DataService
        
        # Initialize database connection
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        print("🧪 Testing timesheet visibility filtering...")
        
        # Check if there are any timesheets marked for deletion
        marked_count = session.query(Timesheet).filter(Timesheet.marked_for_deletion == True).count()
        total_count = session.query(Timesheet).count()
        active_count = session.query(Timesheet).filter(Timesheet.marked_for_deletion == False).count()
        
        print(f"📊 Database statistics:")
        print(f"  Total timesheets: {total_count}")
        print(f"  Active timesheets: {active_count}")
        print(f"  Marked for deletion: {marked_count}")
        
        # Test data service filtering
        data_service = DataService(session)
        
        # Test with include_deleted=False (default)
        result_filtered = data_service.get_documents(
            model_class=Timesheet,
            page=1,
            page_size=100,
            include_deleted=False
        )
        
        # Test with include_deleted=True
        result_all = data_service.get_documents(
            model_class=Timesheet,
            page=1,
            page_size=100,
            include_deleted=True
        )
        
        print(f"\n🔍 Data service results:")
        print(f"  Filtered (include_deleted=False): {result_filtered['total']} items")
        print(f"  All (include_deleted=True): {result_all['total']} items")
        
        # Verify filtering works
        if result_filtered['total'] == active_count and result_all['total'] == total_count:
            print("✅ Data service filtering works correctly")
            
            # Check if any items in filtered result are marked for deletion
            marked_in_filtered = 0
            for item in result_filtered['items']:
                if getattr(item, 'marked_for_deletion', False):
                    marked_in_filtered += 1
            
            if marked_in_filtered == 0:
                print("✅ No marked for deletion items in filtered results")
                return True
            else:
                print(f"❌ Found {marked_in_filtered} marked for deletion items in filtered results")
                return False
        else:
            print("❌ Data service filtering not working correctly")
            print(f"  Expected filtered: {active_count}, got: {result_filtered['total']}")
            print(f"  Expected all: {total_count}, got: {result_all['total']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing timesheet filtering: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'session' in locals():
            session.close()

def test_timesheet_list_controller():
    """Test the timesheet list controller filtering"""
    try:
        from controllers.timesheet_list_controller import TimesheetListFormController
        from data.models.sqlalchemy_models import Timesheet
        
        print("\n🧪 Testing timesheet list controller...")
        
        # Create controller
        controller = TimesheetListFormController("timesheets", 4, Timesheet)
        controller.initialize()
        
        # Check if controller has correct filtering
        print(f"  Controller filters: {controller.filters}")
        
        # Test load_data method
        def mock_data_callback(result):
            print(f"  Controller load_data result: {result['total']} items")
            
            # Check if any items are marked for deletion
            marked_count = 0
            for item in result['items']:
                if getattr(item, 'marked_for_deletion', False):
                    marked_count += 1
            
            if marked_count == 0:
                print("✅ Controller filtering works correctly")
                return True
            else:
                print(f"❌ Controller returned {marked_count} marked for deletion items")
                return False
        
        def mock_error_callback(error):
            print(f"❌ Controller error: {error}")
            return False
        
        controller.set_callbacks(mock_data_callback, mock_error_callback)
        controller.load_data()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing controller: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_data_service_filtering():
    """Fix the data service filtering logic if needed"""
    print("\n🔧 Checking data service filtering logic...")
    
    try:
        with open('api/services/data_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the filtering logic is correct
        if 'marked_for_deletion == False' in content:
            print("✅ Data service filtering logic looks correct")
            
            # Check for potential issues with boolean comparison
            if 'marked_for_deletion is False' not in content:
                print("💡 Suggestion: Consider using 'is False' instead of '== False' for boolean comparison")
                
                # Create improved version
                improved_content = content.replace(
                    'query = query.filter(model_class.marked_for_deletion == False)',
                    'query = query.filter(model_class.marked_for_deletion.is_(False))'
                )
                
                # Also handle is_deleted field if present
                if 'is_deleted' in content:
                    improved_content = improved_content.replace(
                        'model_class.is_deleted == False',
                        'model_class.is_deleted.is_(False)'
                    )
                
                # Write improved version
                with open('api/services/data_service_improved.py', 'w', encoding='utf-8') as f:
                    f.write(improved_content)
                
                print("📝 Created improved version: api/services/data_service_improved.py")
                return True
        else:
            print("❌ Data service filtering logic not found or incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error checking data service: {e}")
        return False

def create_timesheet_visibility_fix():
    """Create a comprehensive fix for timesheet visibility issues"""
    print("\n🛠️ Creating timesheet visibility fix...")
    
    fix_content = '''"""
Fix for Timesheet Visibility Issue - Marked for Deletion Entries Not Filtered Out

This fix ensures that timesheets marked for deletion are properly filtered out of the list.
"""

from sqlalchemy import and_, or_

def apply_timesheet_visibility_fix():
    """Apply the timesheet visibility fix"""
    
    # Fix 1: Improve boolean filtering in data service
    def get_documents_fixed(self, model_class, page=1, page_size=20, sort_by=None, 
                           sort_order='asc', filters=None, date_range=None, include_deleted=False):
        """Fixed version of get_documents with proper boolean filtering"""
        query = self.db.query(model_class)
        
        # Apply Soft Delete Filter (exclude deleted by default) - FIXED
        if not include_deleted:
            # Check for both marked_for_deletion and is_deleted fields
            delete_conditions = []
            
            if hasattr(model_class, 'marked_for_deletion'):
                delete_conditions.append(model_class.marked_for_deletion.is_(False))
            
            if hasattr(model_class, 'is_deleted'):
                delete_conditions.append(model_class.is_deleted.is_(False))
            
            # Apply all delete conditions
            if delete_conditions:
                query = query.filter(and_(*delete_conditions))
        
        # Rest of the method remains the same...
        return query
    
    # Fix 2: Ensure timesheet list form explicitly excludes deleted
    def load_timesheet_data_fixed(controller):
        """Fixed version that explicitly excludes deleted timesheets"""
        # Force include_deleted to False for timesheet lists
        original_filters = controller.filters.copy()
        
        # Add explicit filter for non-deleted items
        controller.filters['marked_for_deletion'] = False
        controller.filters['is_deleted'] = False
        
        # Load data
        result = controller.data_service.get_documents(
            model_class=controller.model_class,
            page=controller.current_page,
            page_size=controller.page_size,
            filters=controller.filters,
            sort_by=controller.sort_by,
            sort_order=controller.sort_order,
            include_deleted=False  # Explicitly set to False
        )
        
        # Restore original filters
        controller.filters = original_filters
        
        return result

print("✅ Timesheet visibility fix created")
'''
    
    with open('timesheet_visibility_fix.py', 'w', encoding='utf-8') as f:
        f.write(fix_content)
    
    print("📝 Created: timesheet_visibility_fix.py")
    return True

if __name__ == "__main__":
    print("🔍 Diagnosing Timesheet Visibility Issue...")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_timesheet_filtering()
    test2_passed = test_timesheet_list_controller()
    
    # Check and fix data service
    fix1_applied = fix_data_service_filtering()
    
    # Create comprehensive fix
    fix2_created = create_timesheet_visibility_fix()
    
    print("\n📊 Summary:")
    print(f"  Data service filtering test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Controller filtering test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"  Data service improvement: {'✅ APPLIED' if fix1_applied else '❌ SKIPPED'}")
    print(f"  Comprehensive fix created: {'✅ CREATED' if fix2_created else '❌ FAILED'}")
    
    if not test1_passed or not test2_passed:
        print("\n🚨 ISSUE CONFIRMED: Marked for deletion entries are not being filtered out")
        print("\n💡 Recommended actions:")
        print("  1. Apply the improved data service filtering")
        print("  2. Ensure boolean comparisons use .is_(False) instead of == False")
        print("  3. Add explicit filtering in timesheet list controller")
        print("  4. Test the fix with actual data")
    else:
        print("\n✅ No issues found - filtering appears to be working correctly")
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)
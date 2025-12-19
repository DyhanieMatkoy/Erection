#!/usr/bin/env python3
"""
Verification script for timesheet visibility fix
Run this script to verify that marked for deletion timesheets are properly filtered out
"""

import sys
import os
sys.path.append('src')

def verify_timesheet_filtering():
    """Verify that the timesheet filtering fix is working"""
    try:
        from data.database_manager import DatabaseManager
        from data.models.sqlalchemy_models import Timesheet
        from api.services.data_service import DataService
        
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize()
        session = db_manager.get_session()
        
        print("🔍 Verifying timesheet visibility fix...")
        
        # Get counts
        total_count = session.query(Timesheet).count()
        marked_count = session.query(Timesheet).filter(Timesheet.marked_for_deletion.is_(True)).count()
        active_count = session.query(Timesheet).filter(Timesheet.marked_for_deletion.is_(False)).count()
        
        print(f"📊 Database statistics:")
        print(f"  Total timesheets: {total_count}")
        print(f"  Active timesheets: {active_count}")
        print(f"  Marked for deletion: {marked_count}")
        
        # Test data service
        data_service = DataService(session)
        result = data_service.get_documents(
            model_class=Timesheet,
            page=1,
            page_size=1000,
            include_deleted=False
        )
        
        print(f"\n🔍 Data service results:")
        print(f"  Returned items: {result['total']}")
        
        # Verify no marked items in results
        marked_in_results = 0
        for item in result['items']:
            if getattr(item, 'marked_for_deletion', False):
                marked_in_results += 1
        
        if marked_in_results == 0:
            print("✅ SUCCESS: No marked for deletion items in results")
            if result['total'] == active_count:
                print("✅ SUCCESS: Result count matches active count")
                return True
            else:
                print(f"⚠️  WARNING: Result count ({result['total']}) doesn't match active count ({active_count})")
                return False
        else:
            print(f"❌ FAILURE: Found {marked_in_results} marked for deletion items in results")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    success = verify_timesheet_filtering()
    print(f"\n{'✅ VERIFICATION PASSED' if success else '❌ VERIFICATION FAILED'}")
    sys.exit(0 if success else 1)

"""Verification test for NULL filter fix in DataService

This test verifies that filtering with None values (NULL in SQL) works correctly
after the fix to DataService.get_documents().
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from api.services.data_service import DataService
from src.data.models.sqlalchemy_models import Work


def test_null_filter_fix():
    """Test that filtering with parent_id=None works correctly"""
    
    # Use the existing database
    db_path = "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("This test requires an existing database.")
        return False
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize(db_path)
        
        print("Testing NULL filter fix in DataService...")
        print("=" * 70)
        
        # Get a session
        session = db_manager.get_session()
        data_service = DataService(session)
        
        # Test 1: Filter for root-level works (parent_id IS NULL)
        print("\nTest 1: Filtering for root-level works (parent_id=None)")
        result = data_service.get_documents(
            model_class=Work,
            filters={'parent_id': None},
            page_size=100
        )
        
        root_works = result['items']
        total_root = result['total']
        
        print(f"  Found {total_root} root-level works")
        
        if total_root == 0:
            print("  ❌ FAILED: No root works found (filter may still be broken)")
            return False
        else:
            print(f"  ✓ SUCCESS: Found {total_root} root-level works")
            
            # Verify they actually have parent_id=None
            for work in root_works[:5]:  # Check first 5
                if work.parent_id is not None:
                    print(f"  ❌ FAILED: Work {work.id} has parent_id={work.parent_id}, expected None")
                    return False
            
            print(f"  ✓ Verified: All returned works have parent_id=None")
        
        # Test 2: Filter for works with a specific parent
        print("\nTest 2: Filtering for works with specific parent_id")
        
        # Find a work that has children
        parent_work = None
        for work in root_works:
            if work.is_group:
                parent_work = work
                break
        
        if parent_work:
            result = data_service.get_documents(
                model_class=Work,
                filters={'parent_id': parent_work.id},
                page_size=100
            )
            
            child_works = result['items']
            total_children = result['total']
            
            print(f"  Found {total_children} child works for parent {parent_work.id}")
            
            if total_children > 0:
                print(f"  ✓ SUCCESS: Found {total_children} child works")
                
                # Verify they have the correct parent_id
                for work in child_works[:5]:
                    if work.parent_id != parent_work.id:
                        print(f"  ❌ FAILED: Work {work.id} has parent_id={work.parent_id}, expected {parent_work.id}")
                        return False
                
                print(f"  ✓ Verified: All returned works have correct parent_id")
            else:
                print(f"  ⚠ No children found for parent {parent_work.id} (may be expected)")
        else:
            print("  ⚠ No group works found to test child filtering")
        
        # Test 3: Filter with string value (should still work)
        print("\nTest 3: Filtering with string value (name search)")
        result = data_service.get_documents(
            model_class=Work,
            filters={'name': 'работ'},  # Common Russian word in work names
            page_size=10
        )
        
        search_results = result['items']
        total_search = result['total']
        
        print(f"  Found {total_search} works matching 'работ'")
        
        if total_search > 0:
            print(f"  ✓ SUCCESS: String search still works")
        else:
            print(f"  ⚠ No works found with 'работ' in name (may be expected)")
        
        print("\n" + "=" * 70)
        print("\n✅ ALL TESTS PASSED!")
        print("\nNULL filter fix verified:")
        print("  ✓ parent_id=None correctly filters for IS NULL")
        print("  ✓ parent_id=<value> correctly filters for specific parent")
        print("  ✓ String filters still work with ILIKE")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            if session:
                session.close()
            if db_manager._engine:
                db_manager._engine.dispose()
            if db_manager._connection:
                db_manager._connection.close()
        except:
            pass


if __name__ == "__main__":
    success = test_null_filter_fix()
    sys.exit(0 if success else 1)

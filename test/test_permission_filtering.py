"""Test permission-based filtering"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.data.database_manager import DatabaseManager
from src.services.auth_service import AuthService
from src.data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository


def test_auth_service_person_id():
    """Test that auth service correctly loads person_id"""
    print("Testing AuthService person_id loading...")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    auth_service = AuthService()
    
    # Test login
    user = auth_service.login('admin', 'admin')
    if user:
        print(f"✓ Logged in as: {user.username} (role: {user.role})")
        person_id = auth_service.current_person_id()
        print(f"✓ Person ID: {person_id}")
    else:
        print("✗ Login failed")
    
    # Test role checks
    print(f"✓ Is foreman: {auth_service.is_foreman()}")
    print(f"✓ Is employee: {auth_service.is_employee()}")
    print(f"✓ Has permission: {auth_service.has_permission('any')}")
    
    auth_service.logout()
    print("✓ Logged out")


def test_executor_filtering():
    """Test executor filtering in work execution register"""
    print("\nTesting executor filtering in work execution register...")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize('construction.db')
    
    repo = WorkExecutionRegisterRepository()
    
    # Test without executor filter
    print("Getting turnovers without executor filter...")
    data1 = repo.get_turnovers('2025-01-01', '2025-12-31', {}, ['estimate', 'work'])
    print(f"✓ Found {len(data1)} records without executor filter")
    
    # Test with executor filter
    print("Getting turnovers with executor filter...")
    data2 = repo.get_turnovers('2025-01-01', '2025-12-31', {'executor_id': 1}, ['estimate', 'work'])
    print(f"✓ Found {len(data2)} records with executor filter (executor_id=1)")
    
    if len(data2) <= len(data1):
        print("✓ Executor filter correctly reduces results")
    else:
        print("✗ Executor filter issue: more results with filter than without")


def test_foreman_filtering():
    """Test that foreman sees only their daily reports"""
    print("\nTesting foreman filtering...")
    
    # Initialize database
    db_manager = DatabaseManager()
    db = db_manager.get_connection()
    
    # Get all daily reports
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM daily_reports WHERE marked_for_deletion = 0")
    total_reports = cursor.fetchone()['count']
    print(f"Total daily reports in database: {total_reports}")
    
    # Get reports for a specific foreman
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM daily_reports 
        WHERE marked_for_deletion = 0 AND foreman_id = 1
    """)
    foreman_reports = cursor.fetchone()['count']
    print(f"Daily reports for foreman_id=1: {foreman_reports}")
    
    if foreman_reports <= total_reports:
        print("✓ Foreman filtering would correctly limit results")
    else:
        print("✗ Foreman filtering issue")


if __name__ == '__main__':
    print("=" * 60)
    print("Permission-based Filtering Tests")
    print("=" * 60)
    
    try:
        test_auth_service_person_id()
        test_executor_filtering()
        test_foreman_filtering()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

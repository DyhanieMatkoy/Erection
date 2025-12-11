"""Test access rights verification"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.data.database_manager import DatabaseManager
from src.data.models.user import User


def test_administrator_permissions():
    """Test administrator has full access"""
    print("\n=== Testing Administrator Permissions ===")
    
    auth = AuthService()
    
    # Create admin user
    admin = User(id=1, username="admin", role="Администратор", is_active=True)
    auth._current_user = admin
    auth._current_person_id = 1
    
    # Test all permissions
    assert auth.has_permission("view", "estimate"), "Admin should view estimates"
    assert auth.has_permission("create", "estimate"), "Admin should create estimates"
    assert auth.has_permission("edit", "estimate", 1), "Admin should edit estimates"
    assert auth.has_permission("delete", "estimate", 1), "Admin should delete estimates"
    assert auth.has_permission("post", "estimate", 1), "Admin should post estimates"
    
    assert auth.has_permission("view", "daily_report"), "Admin should view daily reports"
    assert auth.has_permission("create", "daily_report"), "Admin should create daily reports"
    assert auth.has_permission("edit", "daily_report", 1), "Admin should edit daily reports"
    
    assert auth.can_manage_references(), "Admin should manage references"
    assert auth.can_view_analytics(), "Admin should view analytics"
    assert auth.can_manage_settings(), "Admin should manage settings"
    
    print("✓ Administrator has full access")


def test_manager_permissions():
    """Test manager permissions"""
    print("\n=== Testing Manager Permissions ===")
    
    auth = AuthService()
    
    # Create manager user
    manager = User(id=2, username="manager", role="Руководитель", is_active=True)
    auth._current_user = manager
    auth._current_person_id = 2
    
    # Test permissions
    assert auth.has_permission("view", "estimate"), "Manager should view estimates"
    assert auth.has_permission("create", "estimate"), "Manager should create estimates"
    assert auth.has_permission("edit", "estimate", 1), "Manager should edit estimates"
    assert auth.has_permission("delete", "estimate", 1), "Manager should delete estimates"
    assert auth.has_permission("post", "estimate", 1), "Manager should post estimates"
    
    assert auth.has_permission("view", "daily_report"), "Manager should view daily reports"
    assert auth.has_permission("create", "daily_report"), "Manager should create daily reports"
    
    assert auth.can_manage_references(), "Manager should manage references"
    assert auth.can_view_analytics(), "Manager should view analytics"
    assert not auth.can_manage_settings(), "Manager should NOT manage system settings"
    
    print("✓ Manager has appropriate access")


def test_foreman_permissions():
    """Test foreman permissions"""
    print("\n=== Testing Foreman Permissions ===")
    
    auth = AuthService()
    
    # Create foreman user
    foreman = User(id=3, username="foreman", role="Бригадир", is_active=True)
    auth._current_user = foreman
    auth._current_person_id = 3
    
    # Test permissions (without resource_id to avoid DB access)
    assert auth.has_permission("view", "estimate"), "Foreman should view estimates"
    assert auth.has_permission("create", "estimate"), "Foreman should create estimates"
    # Note: Edit/delete/post require resource_id for ownership check, which requires DB
    # Without resource_id, these return False for foreman
    assert not auth.has_permission("edit", "estimate"), "Foreman edit requires resource_id check"
    assert not auth.has_permission("delete", "estimate"), "Foreman delete requires resource_id check"
    
    assert auth.has_permission("view", "daily_report"), "Foreman should view daily reports"
    assert auth.has_permission("create", "daily_report"), "Foreman should create daily reports"
    
    assert not auth.can_manage_references(), "Foreman should NOT manage references"
    assert auth.can_view_analytics(), "Foreman should view analytics"
    assert not auth.can_manage_settings(), "Foreman should NOT manage settings"
    
    print("✓ Foreman has limited access")


def test_employee_permissions():
    """Test employee permissions"""
    print("\n=== Testing Employee Permissions ===")
    
    auth = AuthService()
    
    # Create employee user
    employee = User(id=4, username="employee", role="Сотрудник", is_active=True)
    auth._current_user = employee
    auth._current_person_id = 4
    
    # Test permissions
    assert auth.has_permission("view", "estimate"), "Employee should view estimates"
    assert not auth.has_permission("create", "estimate"), "Employee should NOT create estimates"
    assert not auth.has_permission("edit", "estimate", 1), "Employee should NOT edit estimates"
    assert not auth.has_permission("delete", "estimate", 1), "Employee should NOT delete estimates"
    
    assert auth.has_permission("view", "daily_report"), "Employee should view daily reports"
    assert not auth.has_permission("create", "daily_report"), "Employee should NOT create daily reports"
    
    assert not auth.can_manage_references(), "Employee should NOT manage references"
    assert auth.can_view_analytics(), "Employee should view analytics"
    assert not auth.can_manage_settings(), "Employee should NOT manage settings"
    
    print("✓ Employee has read-only access")


def test_no_user_permissions():
    """Test permissions when no user is logged in"""
    print("\n=== Testing No User Permissions ===")
    
    auth = AuthService()
    auth._current_user = None
    auth._current_person_id = None
    
    # Test permissions
    assert not auth.has_permission("view", "estimate"), "No user should have no access"
    assert not auth.has_permission("create", "estimate"), "No user should have no access"
    assert not auth.can_manage_references(), "No user should have no access"
    assert not auth.can_view_analytics(), "No user should have no access"
    
    print("✓ No user has no access")


def test_convenience_methods():
    """Test convenience permission methods"""
    print("\n=== Testing Convenience Methods ===")
    
    auth = AuthService()
    
    # Test with admin (no resource_id to avoid DB access)
    admin = User(id=1, username="admin", role="Администратор", is_active=True)
    auth._current_user = admin
    auth._current_person_id = 1
    
    assert auth.can_create_estimate(), "Admin should create estimates"
    # Note: Methods with resource_id require DB, so we test basic permissions
    assert auth.has_permission("edit", "estimate"), "Admin should edit estimates"
    assert auth.has_permission("delete", "estimate"), "Admin should delete estimates"
    assert auth.has_permission("post", "estimate"), "Admin should post estimates"
    
    assert auth.can_create_daily_report(), "Admin should create daily reports"
    assert auth.has_permission("edit", "daily_report"), "Admin should edit daily reports"
    assert auth.has_permission("delete", "daily_report"), "Admin should delete daily reports"
    assert auth.has_permission("post", "daily_report"), "Admin should post daily reports"
    
    # Test with employee
    employee = User(id=4, username="employee", role="Сотрудник", is_active=True)
    auth._current_user = employee
    auth._current_person_id = 4
    
    assert not auth.can_create_estimate(), "Employee should NOT create estimates"
    assert not auth.has_permission("edit", "estimate"), "Employee should NOT edit estimates"
    assert not auth.can_create_daily_report(), "Employee should NOT create daily reports"
    
    print("✓ Convenience methods work correctly")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Access Rights Verification System")
    print("=" * 60)
    
    try:
        test_administrator_permissions()
        test_manager_permissions()
        test_foreman_permissions()
        test_employee_permissions()
        test_no_user_permissions()
        test_convenience_methods()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

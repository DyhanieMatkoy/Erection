#!/usr/bin/env python3
"""Test login functionality"""
from src.services.auth_service import AuthService


def test_login():
    """Test login with test users"""
    auth = AuthService()
    
    test_users = [
        ("admin", "admin", "Администратор"),
        ("manager", "manager", "Руководитель"),
        ("foreman", "foreman", "Бригадир")
    ]
    
    print("Testing login functionality...")
    print("=" * 60)
    
    for username, password, expected_role in test_users:
        user = auth.login(username, password)
        if user:
            print(f"✓ {username:10} - {user.role:20} - OK")
            auth.logout()
        else:
            print(f"✗ {username:10} - Failed to login")
    
    print("=" * 60)
    
    # Test wrong password
    user = auth.login("admin", "wrong_password")
    if not user:
        print("✓ Wrong password correctly rejected")
    else:
        print("✗ Wrong password accepted (security issue!)")
    
    # Test non-existent user
    user = auth.login("nonexistent", "password")
    if not user:
        print("✓ Non-existent user correctly rejected")
    else:
        print("✗ Non-existent user accepted (security issue!)")
    
    print("=" * 60)
    print("Login test completed!")


if __name__ == "__main__":
    from src.data.database_manager import DatabaseManager
    DatabaseManager().initialize("construction.db")
    test_login()

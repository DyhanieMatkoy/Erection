#!/usr/bin/env python3
"""
Test script to check MainWindow imports
"""
import sys
import traceback

try:
    print("Testing imports...")
    
    print("1. Testing PyQt6...")
    from PyQt6.QtWidgets import QApplication
    print("   ✓ PyQt6 imported successfully")
    
    print("2. Testing DatabaseManager...")
    from src.data.database_manager import DatabaseManager
    print("   ✓ DatabaseManager imported successfully")
    
    print("3. Testing MainWindow...")
    from src.views.main_window import MainWindow
    print("   ✓ MainWindow imported successfully")
    
    print("4. Testing AuthService...")
    from src.services.auth_service import AuthService
    print("   ✓ AuthService imported successfully")
    
    print("5. Testing User model...")
    from src.data.models.user import User
    print("   ✓ User model imported successfully")
    
    print("\nAll imports successful!")
    
    print("\n6. Testing database initialization...")
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    print("   ✓ Database initialized successfully")
    
    print("\n7. Testing auth service setup...")
    auth_service = AuthService()
    fake_admin = User()
    fake_admin.id = 4
    fake_admin.username = "admin"
    fake_admin.role = "admin"
    fake_admin.is_active = True
    auth_service._current_user = fake_admin
    auth_service._current_person_id = 1
    print("   ✓ Auth service setup successful")
    
    print("\nAll tests passed! The issue might be with GUI display.")
    
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    print(f"Error type: {type(e).__name__}")
    print("\nFull traceback:")
    traceback.print_exc()
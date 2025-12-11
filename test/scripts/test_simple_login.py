"""Test simple SHA256 login"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.auth_service import AuthService
from src.data.database_manager import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize('construction.db')

# Get session
session = db_manager.get_session()

# Test authentication
auth_service = AuthService(db=session)

print("Testing login with username='admin', password='admin'...")
user = auth_service.authenticate_user('admin', 'admin', db=session)

if user:
    print(f"✓ Login successful!")
    print(f"  User ID: {user['id']}")
    print(f"  Username: {user['username']}")
    print(f"  Role: {user['role']}")
else:
    print("✗ Login failed!")

session.close()

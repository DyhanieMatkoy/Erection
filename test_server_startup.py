#!/usr/bin/env python3
"""
Test script to check if server starts without migration errors
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_import():
    """Test if we can import API without migration errors"""
    try:
        from api.main import app
        print("✅ API imported successfully")
        return True
    except Exception as e:
        print(f"❌ API import failed: {e}")
        return False

def test_database_connection():
    """Test basic database connection"""
    try:
        import sqlite3
        conn = sqlite3.connect("construction.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        print(f"✅ Database connection OK, found {len(tables)} tables")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing server components...")
    
    api_ok = test_api_import()
    db_ok = test_database_connection()
    
    if api_ok and db_ok:
        print("✅ All tests passed! Server should start without issues.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
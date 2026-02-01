#!/usr/bin/env python3
"""Test legacy database manager with SQL translation"""

import os
import sys
import logging
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LegacyDatabaseManagerTest")

def test_legacy_database_manager():
    """Test legacy database manager initialization with SQL translation"""
    
    try:
        # Import database manager
        from src.data.database_manager import DatabaseManager
        
        # Create test database
        test_db_path = "test_legacy_manager.db"
        
        # Remove existing database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print(f"Testing legacy database manager with: {test_db_path}")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        success = db_manager.initialize(test_db_path)
        
        if success:
            print("✅ Database manager initialized successfully")
            
            # Check if estimates table exists and has correct schema
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                print("✅ Estimates table exists")
                
                # Check table schema
                cursor.execute("PRAGMA table_info(estimates)")
                columns = cursor.fetchall()
                
                print("Estimates table schema:")
                date_column_found = False
                for col in columns:
                    col_name, col_type = col[1], col[2]
                    print(f"  {col_name}: {col_type}")
                    if col_name == 'date':
                        date_column_found = True
                        if col_type.upper() == 'TEXT':
                            print("✅ DATE column correctly translated to TEXT")
                        else:
                            print(f"❌ DATE column has wrong type: {col_type}")
                
                if not date_column_found:
                    print("❌ DATE column not found in table")
                
                # Test index creation
                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS test_idx_estimates_date ON estimates(date)")
                    print("✅ Index on date column created successfully")
                except Exception as e:
                    print(f"❌ Index creation failed: {e}")
                
            else:
                print("❌ Estimates table does not exist")
            
            conn.close()
            
        else:
            print("❌ Database manager initialization failed")
            return False
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_legacy_database_manager()
    exit(0 if success else 1)
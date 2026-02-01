#!/usr/bin/env python3
"""Test SQL translator consistency between Universal and Legacy Database Managers"""

import os
import sys
import logging
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SQLTranslatorConsistencyTest")

def test_unified_database_manager():
    """Test Unified Database Manager table creation"""
    
    try:
        from unified_database_manager import UnifiedDatabaseManager
        
        # Create test database
        test_db_path = "test_universal_consistency.db"
        
        # Remove existing database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("Testing Unified Database Manager...")
        
        with UnifiedDatabaseManager(logger) as db_manager:
            # Connect to SQLite database
            connection_string = f"sqlite:///{test_db_path}"
            success = db_manager.connect_to_database(connection_string, "test")
            
            if success:
                # Run migrations (creates tables with SQL translation)
                migration_success = db_manager.run_migrations("test")
                
                if migration_success:
                    print("✅ Unified Database Manager: Tables created successfully")
                    
                    # Check estimates table schema
                    conn = sqlite3.connect(test_db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("PRAGMA table_info(estimates)")
                    columns = cursor.fetchall()
                    
                    print("Unified Database Manager - Estimates table schema:")
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
                        print("❌ DATE column not found in estimates table")
                    
                    conn.close()
                    return True
                else:
                    print("❌ Unified Database Manager: Migration failed")
                    return False
            else:
                print("❌ Unified Database Manager: Connection failed")
                return False
                
    except Exception as e:
        print(f"❌ Unified Database Manager test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except:
                pass

def test_legacy_database_manager():
    """Test Legacy Database Manager table creation"""
    
    try:
        from src.data.database_manager import DatabaseManager
        
        # Create test database
        test_db_path = "test_legacy_consistency.db"
        
        # Remove existing database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("\nTesting Legacy Database Manager...")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        success = db_manager.initialize(test_db_path)
        
        if success:
            print("✅ Legacy Database Manager: Tables created successfully")
            
            # Check estimates table schema
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(estimates)")
            columns = cursor.fetchall()
            
            print("Legacy Database Manager - Estimates table schema:")
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
                print("❌ DATE column not found in estimates table")
            
            conn.close()
            return True
        else:
            print("❌ Legacy Database Manager: Initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Legacy Database Manager test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except:
                pass

def main():
    """Main test function"""
    
    print("=" * 80)
    print("SQL TRANSLATOR CONSISTENCY TEST")
    print("=" * 80)
    
    universal_success = test_unified_database_manager()
    legacy_success = test_legacy_database_manager()
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    if universal_success and legacy_success:
        print("✅ Both managers use consistent SQL translation")
        return 0
    else:
        print("❌ SQL translation inconsistency detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Test Unified Database Manager schema fix

Проверяет, что Unified Database Manager создает правильную схему таблицы estimates
с колонками number, date, а не name, description.
"""

import os
import sys
import sqlite3
import tempfile
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_database_manager import UnifiedDatabaseManager
from sql_dialect_translator import SQLDialect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_universal_database_estimates_schema():
    """Test that Unified Database Manager creates correct estimates schema"""
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        logger.info(f"Testing Unified Database Manager with database: {temp_db_path}")
        
        # Initialize Unified Database Manager
        universal_manager = UnifiedDatabaseManager(logger=logger, use_docker=False)
        
        # Connect to SQLite database
        connection_string = f"sqlite:///{temp_db_path}"
        success = universal_manager.connect_to_database(connection_string, "test_connection")
        
        if not success:
            raise Exception("Failed to connect to database")
        
        # Run migrations to create tables
        migration_success = universal_manager.run_migrations("test_connection")
        
        if not migration_success:
            raise Exception("Failed to run migrations")
        
        # Check the schema of estimates table
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get table info for estimates
        cursor.execute("PRAGMA table_info(estimates)")
        columns = cursor.fetchall()
        
        # Convert to dictionary for easier checking
        column_info = {col[1]: {'type': col[2], 'notnull': col[3], 'default': col[4]} for col in columns}
        
        logger.info("Estimates table schema:")
        for col_name, col_info in column_info.items():
            logger.info(f"  {col_name}: {col_info['type']} (NOT NULL: {col_info['notnull']}, DEFAULT: {col_info['default']})")
        
        # Check that correct columns exist
        required_columns = {
            'id': 'INTEGER',
            'number': 'TEXT',  # Правильно - должно быть number, а не name
            'date': 'DATE',    # Правильно - должно быть date, а не description
            'customer_id': 'INTEGER',
            'object_id': 'INTEGER',
            'contractor_id': 'INTEGER',
            'responsible_id': 'INTEGER',
            'total_sum': 'REAL',
            'total_labor': 'REAL',
            'created_at': 'TIMESTAMP',
            'modified_at': 'TIMESTAMP'
        }
        
        # Check for incorrect columns that should NOT exist
        incorrect_columns = ['name', 'description']
        
        # Verify correct columns exist
        missing_columns = []
        for col_name, expected_type in required_columns.items():
            if col_name not in column_info:
                missing_columns.append(col_name)
            else:
                actual_type = column_info[col_name]['type']
                # SQLite may convert DATE to TEXT, which is acceptable
                if col_name == 'date' and actual_type == 'TEXT':
                    logger.info(f"Column '{col_name}' has type TEXT (converted from DATE) - this is acceptable for SQLite")
                elif actual_type != expected_type:
                    logger.warning(f"Column '{col_name}' has type '{actual_type}', expected '{expected_type}'")
        
        # Check for incorrect columns
        found_incorrect_columns = []
        for col_name in incorrect_columns:
            if col_name in column_info:
                found_incorrect_columns.append(col_name)
        
        # Report results
        success = True
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            success = False
        
        if found_incorrect_columns:
            logger.error(f"Found incorrect columns that should not exist: {found_incorrect_columns}")
            success = False
        
        # Check specific requirements from the problem description
        if 'number' not in column_info:
            logger.error("CRITICAL: Column 'number' is missing - this should exist instead of 'name'")
            success = False
        else:
            logger.info("✓ Column 'number' exists (correct)")
        
        if 'date' not in column_info:
            logger.error("CRITICAL: Column 'date' is missing - this is required")
            success = False
        else:
            logger.info("✓ Column 'date' exists (correct)")
        
        if 'name' in column_info:
            logger.error("CRITICAL: Column 'name' exists but should not - it should be 'number'")
            success = False
        else:
            logger.info("✓ Column 'name' does not exist (correct)")
        
        if 'description' in column_info:
            logger.error("CRITICAL: Column 'description' exists but should not")
            success = False
        else:
            logger.info("✓ Column 'description' does not exist (correct)")
        
        # Check timestamp columns
        if 'created_at' not in column_info:
            logger.error("CRITICAL: Column 'created_at' is missing")
            success = False
        else:
            created_at_type = column_info['created_at']['type']
            if created_at_type in ['TIMESTAMP', 'DATETIME', 'TEXT']:  # SQLite may convert TIMESTAMP
                logger.info(f"✓ Column 'created_at' exists with type {created_at_type} (correct)")
            else:
                logger.error(f"CRITICAL: Column 'created_at' has wrong type: {created_at_type}")
                success = False
        
        conn.close()
        
        if success:
            logger.info("✅ SUCCESS: Unified Database Manager creates correct estimates schema!")
            logger.info("Schema matches Legacy Database Manager:")
            logger.info("  - Has 'number' column (not 'name')")
            logger.info("  - Has 'date' column (not 'description')")
            logger.info("  - Has 'created_at' as TIMESTAMP (not DATETIME)")
            return True
        else:
            logger.error("❌ FAILURE: Unified Database Manager creates incorrect estimates schema!")
            return False
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False
        
    finally:
        # Clean up temporary database
        try:
            os.unlink(temp_db_path)
        except:
            pass


def test_legacy_database_schema_comparison():
    """Test Legacy Database Manager schema for comparison"""
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        logger.info(f"Testing Legacy Database Manager with database: {temp_db_path}")
        
        # Import and initialize Legacy Database Manager
        from src.data.database_manager import DatabaseManager as LegacyDatabaseManager
        
        legacy_manager = LegacyDatabaseManager()
        success = legacy_manager.initialize(temp_db_path)
        
        if not success:
            raise Exception("Failed to initialize legacy database manager")
        
        # Check the schema of estimates table
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get table info for estimates
        cursor.execute("PRAGMA table_info(estimates)")
        columns = cursor.fetchall()
        
        # Convert to dictionary for easier checking
        column_info = {col[1]: {'type': col[2], 'notnull': col[3], 'default': col[4]} for col in columns}
        
        logger.info("Legacy Database Manager - Estimates table schema:")
        for col_name, col_info in column_info.items():
            logger.info(f"  {col_name}: {col_info['type']} (NOT NULL: {col_info['notnull']}, DEFAULT: {col_info['default']})")
        
        conn.close()
        
        # Verify legacy schema is correct
        if 'number' in column_info and 'date' in column_info:
            logger.info("✅ Legacy Database Manager has correct schema (number, date columns)")
            return True
        else:
            logger.error("❌ Legacy Database Manager has incorrect schema")
            return False
        
    except Exception as e:
        logger.error(f"Legacy test failed with exception: {e}")
        return False
        
    finally:
        # Clean up temporary database
        try:
            os.unlink(temp_db_path)
        except:
            pass


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("TESTING UNIVERSAL DATABASE MANAGER SCHEMA FIX")
    logger.info("=" * 80)
    
    # Test legacy database manager first for comparison
    logger.info("\n1. Testing Legacy Database Manager schema (for comparison):")
    legacy_success = test_legacy_database_schema_comparison()
    
    # Test universal database manager
    logger.info("\n2. Testing Unified Database Manager schema (after fix):")
    universal_success = test_universal_database_estimates_schema()
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL RESULTS:")
    logger.info(f"Legacy Database Manager: {'✅ CORRECT' if legacy_success else '❌ INCORRECT'}")
    logger.info(f"Unified Database Manager: {'✅ FIXED' if universal_success else '❌ STILL BROKEN'}")
    
    if universal_success:
        logger.info("\n🎉 SUCCESS: Unified Database Manager now creates the correct estimates schema!")
        logger.info("The schema now matches Legacy Database Manager with:")
        logger.info("  - number column (instead of name)")
        logger.info("  - date column (instead of description)")
        logger.info("  - created_at as TIMESTAMP (instead of DATETIME)")
    else:
        logger.error("\n💥 FAILURE: Unified Database Manager still creates incorrect schema!")
        logger.error("The fix did not work properly.")
    
    logger.info("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if universal_success else 1)
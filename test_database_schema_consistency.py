#!/usr/bin/env python3
"""Test database schema consistency between Universal and Legacy Database Managers

Проверяет, что Unified Database Manager и Legacy Database Manager создают
одинаковые схемы таблиц, особенно для таблицы estimates.
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


def get_table_schema(db_path: str, table_name: str) -> dict:
    """Get table schema as dictionary"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Convert to dictionary: column_name -> {type, notnull, default}
    schema = {}
    for col in columns:
        schema[col[1]] = {
            'type': col[2],
            'notnull': bool(col[3]),
            'default': col[4]
        }
    
    conn.close()
    return schema


def compare_schemas(schema1: dict, schema2: dict, table_name: str) -> bool:
    """Compare two table schemas"""
    logger.info(f"\nComparing {table_name} schemas:")
    
    # Get all columns from both schemas
    all_columns = set(schema1.keys()) | set(schema2.keys())
    
    differences = []
    
    for column in sorted(all_columns):
        if column not in schema1:
            differences.append(f"Column '{column}' missing in schema1")
        elif column not in schema2:
            differences.append(f"Column '{column}' missing in schema2")
        else:
            # Compare column properties
            col1 = schema1[column]
            col2 = schema2[column]
            
            # Type comparison (allow DATE -> TEXT conversion for SQLite)
            type1 = col1['type']
            type2 = col2['type']
            if type1 != type2:
                if (type1 == 'DATE' and type2 == 'TEXT') or (type1 == 'TEXT' and type2 == 'DATE'):
                    logger.info(f"  {column}: {type1} vs {type2} (acceptable DATE/TEXT conversion)")
                else:
                    differences.append(f"Column '{column}' type mismatch: {type1} vs {type2}")
            
            # NOT NULL comparison
            if col1['notnull'] != col2['notnull']:
                differences.append(f"Column '{column}' NOT NULL mismatch: {col1['notnull']} vs {col2['notnull']}")
            
            # Default value comparison (more lenient)
            if col1['default'] != col2['default']:
                # Some defaults might be equivalent
                if not (col1['default'] is None and col2['default'] is None):
                    logger.info(f"  {column}: default {col1['default']} vs {col2['default']} (may be equivalent)")
    
    if differences:
        logger.error(f"Schema differences found for {table_name}:")
        for diff in differences:
            logger.error(f"  - {diff}")
        return False
    else:
        logger.info(f"✅ {table_name} schemas are consistent")
        return True


def test_schema_consistency():
    """Test schema consistency between Universal and Legacy Database Managers"""
    
    # Create temporary database files
    with tempfile.NamedTemporaryFile(suffix='_universal.db', delete=False) as temp_universal:
        universal_db_path = temp_universal.name
    
    with tempfile.NamedTemporaryFile(suffix='_legacy.db', delete=False) as temp_legacy:
        legacy_db_path = temp_legacy.name
    
    try:
        logger.info("Testing schema consistency between Universal and Legacy Database Managers")
        
        # Initialize Unified Database Manager
        logger.info("\n1. Creating database with Unified Database Manager...")
        universal_manager = UnifiedDatabaseManager(logger=logger, use_docker=False)
        connection_string = f"sqlite:///{universal_db_path}"
        success = universal_manager.connect_to_database(connection_string, "test_connection")
        
        if not success:
            raise Exception("Failed to connect to Universal database")
        
        migration_success = universal_manager.run_migrations("test_connection")
        if not migration_success:
            raise Exception("Failed to run Universal migrations")
        
        # Initialize Legacy Database Manager
        logger.info("\n2. Creating database with Legacy Database Manager...")
        from src.data.database_manager import DatabaseManager as LegacyDatabaseManager
        
        legacy_manager = LegacyDatabaseManager()
        success = legacy_manager.initialize(legacy_db_path)
        
        if not success:
            raise Exception("Failed to initialize legacy database manager")
        
        # Compare schemas for key tables
        tables_to_compare = [
            'estimates',
            'persons',
            'organizations',
            'counterparties',
            'objects',
            'works',
            'daily_reports',
            'timesheets'
        ]
        
        logger.info("\n3. Comparing table schemas...")
        
        all_consistent = True
        
        for table_name in tables_to_compare:
            try:
                universal_schema = get_table_schema(universal_db_path, table_name)
                legacy_schema = get_table_schema(legacy_db_path, table_name)
                
                is_consistent = compare_schemas(universal_schema, legacy_schema, table_name)
                if not is_consistent:
                    all_consistent = False
                    
            except Exception as e:
                logger.error(f"Failed to compare {table_name}: {e}")
                all_consistent = False
        
        # Special focus on estimates table
        logger.info("\n4. Detailed estimates table comparison:")
        
        universal_estimates = get_table_schema(universal_db_path, 'estimates')
        legacy_estimates = get_table_schema(legacy_db_path, 'estimates')
        
        logger.info("Unified Database Manager estimates columns:")
        for col, info in sorted(universal_estimates.items()):
            logger.info(f"  {col}: {info['type']}")
        
        logger.info("Legacy Database Manager estimates columns:")
        for col, info in sorted(legacy_estimates.items()):
            logger.info(f"  {col}: {info['type']}")
        
        # Check critical columns
        critical_columns = ['id', 'number', 'date', 'customer_id', 'created_at']
        estimates_ok = True
        
        for col in critical_columns:
            if col not in universal_estimates:
                logger.error(f"❌ Universal DB missing critical column: {col}")
                estimates_ok = False
            if col not in legacy_estimates:
                logger.error(f"❌ Legacy DB missing critical column: {col}")
                estimates_ok = False
        
        # Check that wrong columns don't exist
        wrong_columns = ['name', 'description']
        for col in wrong_columns:
            if col in universal_estimates:
                logger.error(f"❌ Universal DB has incorrect column: {col}")
                estimates_ok = False
            if col in legacy_estimates:
                logger.error(f"❌ Legacy DB has incorrect column: {col}")
                estimates_ok = False
        
        if estimates_ok:
            logger.info("✅ Estimates table has correct structure in both managers")
        
        return all_consistent and estimates_ok
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False
        
    finally:
        # Clean up temporary databases
        try:
            os.unlink(universal_db_path)
            os.unlink(legacy_db_path)
        except:
            pass


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("DATABASE SCHEMA CONSISTENCY TEST")
    logger.info("=" * 80)
    
    success = test_schema_consistency()
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("🎉 SUCCESS: Database schemas are consistent!")
        logger.info("Unified Database Manager creates the same schema as Legacy Database Manager")
    else:
        logger.error("💥 FAILURE: Database schemas are inconsistent!")
        logger.error("Unified Database Manager creates different schema than Legacy Database Manager")
    
    logger.info("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
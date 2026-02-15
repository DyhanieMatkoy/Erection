#!/usr/bin/env python3
"""
Test Schema Validation

Simple test to validate database schema consistency.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def count_tables_in_database(db_path: str) -> int:
    """Count tables in SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Number of tables
    """
    try:
        if not os.path.exists(db_path):
            logger.warning(f"Database not found: {db_path}")
            return 0
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables (excluding sqlite_* system tables)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        conn.close()
        
        logger.info(f"Database {db_path} has {len(table_names)} tables:")
        for table_name in table_names:
            logger.info(f"  - {table_name}")
        
        return len(table_names)
        
    except Exception as e:
        logger.error(f"Failed to count tables in {db_path}: {e}")
        return 0


def main():
    """Main validation function"""
    logger.info("Starting schema validation")
    
    # Check main database
    main_db_count = count_tables_in_database("construction.db")
    logger.info(f"Main database (construction.db): {main_db_count} tables")
    
    # Check test databases
    test_db_dir = Path("test_databases")
    if test_db_dir.exists():
        for db_file in test_db_dir.glob("*.db"):
            count = count_tables_in_database(str(db_file))
            logger.info(f"Test database ({db_file.name}): {count} tables")
    
    logger.info("Schema validation completed")


if __name__ == "__main__":
    main()
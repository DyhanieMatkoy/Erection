#!/usr/bin/env python3
"""
Cleanup Test Migrations Script

This script cleans up test migration files and resets the Alembic version
to the main branch head to prevent conflicts.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_test_migration_files() -> List[Path]:
    """Find all test migration files in the alembic/versions directory
    
    Returns:
        List of test migration file paths
    """
    migrations_dir = Path("alembic/versions")
    test_migration_files = []
    
    if migrations_dir.exists():
        for file_path in migrations_dir.glob("*.py"):
            # Test migrations typically start with timestamp like 202601xx
            if file_path.stem.startswith("202601"):
                test_migration_files.append(file_path)
    
    return test_migration_files


def cleanup_migration_files(test_files: List[Path]) -> int:
    """Remove test migration files
    
    Args:
        test_files: List of test migration file paths
        
    Returns:
        Number of files cleaned up
    """
    cleaned_count = 0
    
    for file_path in test_files:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted test migration file: {file_path}")
                cleaned_count += 1
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
    
    return cleaned_count


def reset_alembic_version(db_path: str, target_version: str = "e281607a0287") -> bool:
    """Reset alembic_version table to target version
    
    Args:
        db_path: Path to SQLite database
        target_version: Target migration version
        
    Returns:
        True if successful
    """
    try:
        if not os.path.exists(db_path):
            logger.warning(f"Database not found: {db_path}")
            return True  # Not an error if DB doesn't exist
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if alembic_version table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if not cursor.fetchone():
            logger.info(f"alembic_version table not found in {db_path}")
            conn.close()
            return True
        
        # Get current version
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()
        
        if current_version:
            current_version = current_version[0]
            logger.info(f"Current version in {db_path}: {current_version}")
            
            # Only update if it's a test migration (starts with 202601)
            if current_version.startswith("202601"):
                cursor.execute("UPDATE alembic_version SET version_num = ?", (target_version,))
                conn.commit()
                logger.info(f"Reset alembic version in {db_path} to {target_version}")
            else:
                logger.info(f"Version {current_version} is not a test migration, leaving unchanged")
        else:
            # Insert target version if no version exists
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (target_version,))
            conn.commit()
            logger.info(f"Inserted alembic version {target_version} in {db_path}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset alembic version in {db_path}: {e}")
        return False


def cleanup_all_test_databases() -> None:
    """Clean up alembic versions in all test databases"""
    
    # Main database
    reset_alembic_version("construction.db")
    
    # Test databases (common patterns)
    test_db_patterns = [
        "test_*.db",
        "client_*.db", 
        "server_*.db",
        "test_databases/*.db"
    ]
    
    for pattern in test_db_patterns:
        for db_path in Path(".").glob(pattern):
            if db_path.is_file():
                reset_alembic_version(str(db_path))


def main():
    """Main cleanup function"""
    logger.info("Starting test migration cleanup")
    
    try:
        # Find test migration files
        test_files = find_test_migration_files()
        logger.info(f"Found {len(test_files)} test migration files")
        
        # Clean up migration files
        cleaned_count = cleanup_migration_files(test_files)
        logger.info(f"Cleaned up {cleaned_count} test migration files")
        
        # Reset alembic versions in databases
        cleanup_all_test_databases()
        
        logger.info("Test migration cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Test migration cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
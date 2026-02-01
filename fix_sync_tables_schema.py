#!/usr/bin/env python3
"""Fix Sync Tables Schema

This script fixes the sync tables schema to ensure compatibility between
Universal Database Manager and the main sync system.
"""

import sqlite3
import logging
import sys
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_sync_tables_schema(db_path: str) -> bool:
    """Fix sync tables schema in the database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        True if successful
    """
    try:
        logger.info(f"Fixing sync tables schema in: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sync tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sync_%'")
        sync_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found sync tables: {sync_tables}")
        
        # Drop existing sync tables if they have wrong schema
        for table in sync_tables:
            logger.info(f"Dropping existing sync table: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Create correct sync tables schema
        logger.info("Creating correct sync tables schema")
        
        # Sync Nodes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_nodes (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_sync_in TIMESTAMP,
                last_sync_out TIMESTAMP,
                received_packet_no INTEGER,
                sent_packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sync Changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                entity_type TEXT NOT NULL,
                entity_uuid TEXT NOT NULL,
                operation TEXT NOT NULL,
                packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT
            )
        """)
        
        # Object Version History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS object_version_history (
                id TEXT PRIMARY KEY,
                entity_uuid TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source_node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                serialized_data TEXT NOT NULL,
                conflict_resolution TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_node_operation ON sync_changes(node_id, operation)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_version_conflict ON object_version_history(entity_type, entity_uuid, resolved_at)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Sync tables schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix sync tables schema: {e}")
        return False


def fix_persons_table_schema(db_path: str) -> bool:
    """Fix persons table schema to use full_name instead of name
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        True if successful
    """
    try:
        logger.info(f"Fixing persons table schema in: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current persons table schema
        cursor.execute("PRAGMA table_info(persons)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'full_name' in columns:
            logger.info("✅ Persons table already has full_name column")
            conn.close()
            return True
        
        if 'name' not in columns:
            logger.warning("⚠️ Persons table has neither 'name' nor 'full_name' column")
            conn.close()
            return False
        
        # Rename name column to full_name
        logger.info("Renaming 'name' column to 'full_name' in persons table")
        cursor.execute("ALTER TABLE persons RENAME COLUMN name TO full_name")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Persons table schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix persons table schema: {e}")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python fix_sync_tables_schema.py <database_path>")
        print("   or: python fix_sync_tables_schema.py --fix-all-test-databases")
        sys.exit(1)
    
    if sys.argv[1] == "--fix-all-test-databases":
        # Fix all test databases
        test_db_dir = Path("test_databases")
        if not test_db_dir.exists():
            logger.error("test_databases directory not found")
            sys.exit(1)
        
        success_count = 0
        total_count = 0
        
        for db_file in test_db_dir.glob("*.db"):
            total_count += 1
            logger.info(f"Processing: {db_file}")
            
            sync_success = fix_sync_tables_schema(str(db_file))
            persons_success = fix_persons_table_schema(str(db_file))
            
            if sync_success and persons_success:
                success_count += 1
                logger.info(f"✅ Successfully fixed: {db_file}")
            else:
                logger.error(f"❌ Failed to fix: {db_file}")
        
        logger.info(f"Fixed {success_count}/{total_count} databases")
        sys.exit(0 if success_count == total_count else 1)
    
    else:
        # Fix single database
        db_path = sys.argv[1]
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            sys.exit(1)
        
        sync_success = fix_sync_tables_schema(db_path)
        persons_success = fix_persons_table_schema(db_path)
        
        if sync_success and persons_success:
            logger.info("✅ Database schema fixed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Failed to fix database schema")
            sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Fix Legacy Database Sync Tables

This script fixes existing databases created by Legacy Database Manager
to include the correct sync tables schema that matches Universal Database Manager.
"""

import sqlite3
import logging
import sys
import os
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_legacy_database_sync_tables(db_path: str) -> bool:
    """Fix sync tables in legacy database to match Universal Database Manager schema
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        True if successful
    """
    try:
        logger.info(f"Fixing legacy database sync tables: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sync tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sync_%'")
        existing_sync_tables = [row[0] for row in cursor.fetchall()]
        
        if existing_sync_tables:
            logger.info(f"Found existing sync tables: {existing_sync_tables}")
            
            # Drop existing sync tables (they have wrong schema)
            for table in existing_sync_tables:
                logger.info(f"Dropping existing sync table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Check if object_version_history exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='object_version_history'")
        if cursor.fetchone():
            logger.info("Dropping existing object_version_history table")
            cursor.execute("DROP TABLE IF EXISTS object_version_history")
        
        # Create correct sync tables schema (matching Universal Database Manager)
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
        
        # Create sync table indexes
        logger.info("Creating sync table indexes")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_changes_node_operation ON sync_changes(node_id, operation)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_version_conflict ON object_version_history(entity_type, entity_uuid, resolved_at)")
        
        # Fix persons table if needed (name -> full_name)
        cursor.execute("PRAGMA table_info(persons)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'name' in columns and 'full_name' not in columns:
            logger.info("Fixing persons table: renaming 'name' to 'full_name'")
            cursor.execute("ALTER TABLE persons RENAME COLUMN name TO full_name")
        elif 'name' in columns and 'full_name' in columns:
            logger.info("Both 'name' and 'full_name' columns exist in persons table, removing 'name'")
            # Copy data from name to full_name if full_name is empty
            cursor.execute("UPDATE persons SET full_name = name WHERE full_name IS NULL OR full_name = ''")
            # Drop name column (SQLite doesn't support DROP COLUMN directly, need to recreate table)
            cursor.execute("PRAGMA table_info(persons)")
            all_columns = cursor.fetchall()
            
            # Get all columns except 'name'
            new_columns = [col for col in all_columns if col[1] != 'name']
            column_defs = []
            for col in new_columns:
                col_def = f"{col[1]} {col[2]}"
                if col[3]:  # NOT NULL
                    col_def += " NOT NULL"
                if col[4] is not None:  # DEFAULT
                    col_def += f" DEFAULT {col[4]}"
                if col[5]:  # PRIMARY KEY
                    col_def += " PRIMARY KEY"
                column_defs.append(col_def)
            
            # Recreate persons table without 'name' column
            cursor.execute("ALTER TABLE persons RENAME TO persons_old")
            cursor.execute(f"CREATE TABLE persons ({', '.join(column_defs)})")
            
            # Copy data
            column_names = [col[1] for col in new_columns]
            cursor.execute(f"INSERT INTO persons ({', '.join(column_names)}) SELECT {', '.join(column_names)} FROM persons_old")
            
            # Drop old table
            cursor.execute("DROP TABLE persons_old")
            
            logger.info("Removed duplicate 'name' column from persons table")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Legacy database sync tables fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix legacy database sync tables: {e}")
        return False


def find_all_databases() -> List[str]:
    """Find all SQLite database files in the project
    
    Returns:
        List of database file paths
    """
    db_files = []
    
    # Common database locations
    search_paths = [
        ".",
        "test_databases",
        "src",
        "test",
        "temp_test"
    ]
    
    for search_path in search_paths:
        path = Path(search_path)
        if path.exists():
            # Find .db files
            for db_file in path.glob("*.db"):
                db_files.append(str(db_file))
            
            # Find .sqlite files
            for db_file in path.glob("*.sqlite"):
                db_files.append(str(db_file))
    
    return db_files


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--fix-all":
            # Fix all found databases
            db_files = find_all_databases()
            logger.info(f"Found {len(db_files)} database files")
            
            success_count = 0
            total_count = len(db_files)
            
            for db_file in db_files:
                logger.info(f"Processing: {db_file}")
                
                if fix_legacy_database_sync_tables(db_file):
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
            
            if fix_legacy_database_sync_tables(db_path):
                logger.info("✅ Database sync tables fixed successfully")
                sys.exit(0)
            else:
                logger.error("❌ Failed to fix database sync tables")
                sys.exit(1)
    
    else:
        print("Usage:")
        print("  python fix_legacy_database_sync_tables.py <database_path>")
        print("  python fix_legacy_database_sync_tables.py --fix-all")
        sys.exit(1)


if __name__ == "__main__":
    main()
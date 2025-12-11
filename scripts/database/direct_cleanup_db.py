#!/usr/bin/env python3
"""
Direct script to check and clean up the database before migration.
This script will directly connect to the SQLite database and check for the existence 
of cost_items, materials, and cost_item_materials tables and drop them if they exist.
"""

import sqlite3
import os
from pathlib import Path

def check_and_cleanup_database():
    """Check for and drop tables that might interfere with migration"""
    # Path to the database
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Current tables in database: {tables}")
        
        # Tables to check and potentially drop
        tables_to_check = ['cost_items', 'materials', 'cost_item_materials']
        
        # Check for tables that need to be dropped
        tables_to_drop = [table for table in tables_to_check if table in tables]
        
        if tables_to_drop:
            print(f"Found tables that need to be dropped: {tables_to_drop}")
            
            # Drop tables in correct order (respecting foreign key constraints)
            # cost_item_materials depends on cost_items and materials
            if 'cost_item_materials' in tables_to_drop:
                cursor.execute("DROP TABLE IF EXISTS cost_item_materials")
                print("Dropped cost_item_materials table")
            
            if 'materials' in tables_to_drop:
                cursor.execute("DROP TABLE IF EXISTS materials")
                print("Dropped materials table")
            
            if 'cost_items' in tables_to_drop:
                cursor.execute("DROP TABLE IF EXISTS cost_items")
                print("Dropped cost_items table")
            
            # Check for columns in existing tables that might have been added
            if 'estimate_lines' in tables:
                cursor.execute("PRAGMA table_info(estimate_lines)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Check for material-related columns
                material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
                columns_found = [col for col in material_columns if col in columns]
                
                if columns_found:
                    print(f"Found columns in estimate_lines that may interfere: {columns_found}")
                    print("Note: SQLite doesn't support DROP COLUMN directly. Migration will handle this.")
            
            if 'daily_report_lines' in tables:
                cursor.execute("PRAGMA table_info(daily_report_lines)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Check for material-related columns
                material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
                columns_found = [col for col in material_columns if col in columns]
                
                if columns_found:
                    print(f"Found columns in daily_report_lines that may interfere: {columns_found}")
                    print("Note: SQLite doesn't support DROP COLUMN directly. Migration will handle this.")
            
            # Check alembic version
            try:
                cursor.execute("SELECT version_num FROM alembic_version")
                current_version = cursor.fetchone()[0]
                print(f"Current Alembic version: {current_version}")
            except sqlite3.OperationalError:
                print("Could not check Alembic version (table may not exist)")
            
            conn.commit()
            print("Database cleanup completed successfully")
        else:
            print("No tables to drop. Database is ready for migration.")
            
            # Check alembic version
            try:
                cursor.execute("SELECT version_num FROM alembic_version")
                current_version = cursor.fetchone()[0]
                print(f"Current Alembic version: {current_version}")
            except sqlite3.OperationalError:
                print("Could not check Alembic version (table may not exist)")
        
        conn.close()
        return True
                
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        return False

if __name__ == "__main__":
    success = check_and_cleanup_database()
    exit(0 if success else 1)
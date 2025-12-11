#!/usr/bin/env python3
"""
Script to check and clean up the database before migration.
This script will check for the existence of cost_items, materials, and cost_item_materials tables
and drop them if they were created by a partial migration.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.database_manager import DatabaseManager
from sqlalchemy import inspect, text

def check_and_cleanup_database():
    """Check for and drop tables that might interfere with migration"""
    db_manager = DatabaseManager()
    
    # Initialize the database manager
    if not db_manager.initialize():
        print("Failed to initialize database manager")
        return False
    
    # Tables to check and potentially drop
    tables_to_check = ['cost_items', 'materials', 'cost_item_materials']
    
    try:
        with db_manager.get_engine().connect() as conn:
            inspector = inspect(conn)
            existing_tables = inspector.get_table_names()
            
            print(f"Current tables in database: {existing_tables}")
            
            # Check for tables that need to be dropped
            tables_to_drop = [table for table in tables_to_check if table in existing_tables]
            
            if tables_to_drop:
                print(f"Found tables that need to be dropped: {tables_to_drop}")
                
                # Drop tables in correct order (respecting foreign key constraints)
                # cost_item_materials depends on cost_items and materials
                if 'cost_item_materials' in tables_to_drop:
                    conn.execute(text("DROP TABLE IF EXISTS cost_item_materials"))
                    print("Dropped cost_item_materials table")
                
                if 'materials' in tables_to_drop:
                    conn.execute(text("DROP TABLE IF EXISTS materials"))
                    print("Dropped materials table")
                
                if 'cost_items' in tables_to_drop:
                    conn.execute(text("DROP TABLE IF EXISTS cost_items"))
                    print("Dropped cost_items table")
                
                # Also drop any columns that might have been added to existing tables
                if 'estimate_lines' in existing_tables:
                    columns = inspector.get_columns('estimate_lines')
                    column_names = [col['name'] for col in columns]
                    
                    # Check for material-related columns
                    material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
                    columns_to_drop = [col for col in material_columns if col in column_names]
                    
                    if columns_to_drop:
                        print(f"Found columns in estimate_lines that need to be dropped: {columns_to_drop}")
                        
                        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                        # For now, we'll just note this and let the migration handle it
                        print("Note: SQLite doesn't support DROP COLUMN directly. Migration will handle this.")
                
                if 'daily_report_lines' in existing_tables:
                    columns = inspector.get_columns('daily_report_lines')
                    column_names = [col['name'] for col in columns]
                    
                    # Check for material-related columns
                    material_columns = ['material_id', 'material_quantity', 'material_price', 'material_sum']
                    columns_to_drop = [col for col in material_columns if col in column_names]
                    
                    if columns_to_drop:
                        print(f"Found columns in daily_report_lines that need to be dropped: {columns_to_drop}")
                        print("Note: SQLite doesn't support DROP COLUMN directly. Migration will handle this.")
                
                conn.commit()
                print("Database cleanup completed successfully")
            else:
                print("No tables to drop. Database is ready for migration.")
                
            # Check alembic version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.fetchone()[0]
                print(f"Current Alembic version: {current_version}")
            except Exception as e:
                print(f"Could not check Alembic version: {e}")
                
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_and_cleanup_database()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Script to clean up backup tables created during migration attempts.
"""

import sqlite3
import os

def cleanup_backup_tables():
    """Drop backup tables created during migration attempts."""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check for backup tables
        backup_tables = [table for table in tables if table.endswith('_backup')]
        
        if backup_tables:
            print(f"Found backup tables: {backup_tables}")
            
            # Drop each backup table
            for table in backup_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"Dropped {table} table")
        else:
            print("No backup tables found")
        
        # Commit the changes
        conn.commit()
        print("Backup tables cleanup completed successfully")
        
    except Exception as e:
        print(f"Error cleaning up backup tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_backup_tables()
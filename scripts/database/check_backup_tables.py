#!/usr/bin/env python3
"""
Script to check if estimate_lines table exists in the backup database.
"""

import sqlite3
import os

def check_backup_tables():
    """Check if estimate_lines table exists in the backup database."""
    
    # Get the backup database path
    backup_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction_backup_20251208_001233.db')
    
    # Connect to the backup database
    conn = sqlite3.connect(backup_db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Backup database path: {backup_db_path}")
        print(f"Number of tables: {len(tables)}")
        print("All tables in the backup database:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Check if estimate_lines exists
        if 'estimate_lines' in tables:
            print("\nestimate_lines table found in backup!")
            # Get the structure of the table
            cursor.execute("PRAGMA table_info(estimate_lines)")
            columns = cursor.fetchall()
            print("\nStructure of estimate_lines table:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\nestimate_lines table NOT found in backup!")
        
    except Exception as e:
        print(f"Error checking backup tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_backup_tables()
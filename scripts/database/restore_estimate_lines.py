#!/usr/bin/env python3
"""
Script to restore the estimate_lines table from the backup database.
"""

import sqlite3
import os

def restore_estimate_lines():
    """Restore the estimate_lines table from the backup database."""
    
    # Get the database paths
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction.db')
    backup_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction_backup_20251208_001233.db')
    
    # Connect to both databases
    conn = sqlite3.connect(db_path)
    backup_conn = sqlite3.connect(backup_db_path)
    
    try:
        # Get the structure of the estimate_lines table from backup
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='estimate_lines'")
        create_sql = backup_cursor.fetchone()[0]
        
        print(f"Creating estimate_lines table in main database...")
        
        # Create the table in the main database
        cursor = conn.cursor()
        cursor.execute(create_sql)
        
        # Get data from backup
        backup_cursor.execute("SELECT * FROM estimate_lines")
        rows = backup_cursor.fetchall()
        
        # Get column names
        backup_cursor.execute("PRAGMA table_info(estimate_lines)")
        columns = [col[1] for col in backup_cursor.fetchall()]
        
        # Insert data into main database
        placeholders = ', '.join(['?'] * len(columns))
        insert_sql = f"INSERT INTO estimate_lines ({', '.join(columns)}) VALUES ({placeholders})"
        
        cursor.executemany(insert_sql, rows)
        
        # Commit the changes
        conn.commit()
        
        print(f"Successfully restored estimate_lines table with {len(rows)} rows")
        
    except Exception as e:
        print(f"Error restoring estimate_lines table: {e}")
        conn.rollback()
    finally:
        conn.close()
        backup_conn.close()

if __name__ == "__main__":
    restore_estimate_lines()
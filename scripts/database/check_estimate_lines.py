#!/usr/bin/env python3
"""
Script to check the current state of estimate_lines table.
"""

import sqlite3
import os
from pathlib import Path

def check_estimate_lines():
    """Check the current state of estimate_lines table"""
    # Path to the database
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get the current table structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='estimate_lines'")
        create_sql = cursor.fetchone()[0]
        print(f"Current CREATE SQL for estimate_lines:\n{create_sql}\n")
        
        # Get column information
        cursor.execute("PRAGMA table_info(estimate_lines)")
        columns = cursor.fetchall()
        print("Columns in estimate_lines:")
        for col in columns:
            print(f"  {col[1]} - {col[2]} (nullable: {not col[3]}, default: {col[4]})")
        
        conn.close()
        return True
                
    except Exception as e:
        print(f"Error checking estimate_lines: {e}")
        return False

if __name__ == "__main__":
    success = check_estimate_lines()
    exit(0 if success else 1)
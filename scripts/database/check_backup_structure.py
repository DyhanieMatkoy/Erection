#!/usr/bin/env python3
"""
Check the structure of backup tables to understand column differences
"""
import sqlite3
from pathlib import Path

def check_table_structure(db_path, table_name):
    """Check the structure of a specific table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\nStructure of {table_name}:")
        print("-" * 50)
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        
        if rows:
            print(f"\nSample data from {table_name}:")
            print("-" * 50)
            for row in rows:
                print(row)
        
    except sqlite3.Error as e:
        print(f"Error checking {table_name}: {e}")
    finally:
        conn.close()

def main():
    # Get the database path
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    print(f"Checking database: {db_path}")
    
    # Check both tables
    check_table_structure(db_path, "daily_report_lines")
    check_table_structure(db_path, "daily_report_lines_backup")

if __name__ == "__main__":
    main()
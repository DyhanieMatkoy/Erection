#!/usr/bin/env python3
"""
Check the current state of the database
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
        
    except sqlite3.Error as e:
        print(f"Error checking {table_name}: {e}")
    finally:
        conn.close()

def list_tables(db_path):
    """List all tables in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\nTables in database:")
        print("-" * 50)
        for table in tables:
            print(table[0])
    except sqlite3.Error as e:
        print(f"Error listing tables: {e}")
    finally:
        conn.close()

def main():
    # Get the database path
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    print(f"Checking database: {db_path}")
    
    # List all tables
    list_tables(db_path)
    
    # Check daily_report_lines structure
    check_table_structure(db_path, "daily_report_lines")
    
    # Check if daily_report_lines_backup exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_report_lines_backup'")
    backup_exists = cursor.fetchone()
    conn.close()
    
    if backup_exists:
        print("\nBackup table exists")
        check_table_structure(db_path, "daily_report_lines_backup")
    else:
        print("\nNo backup table found")

if __name__ == "__main__":
    main()
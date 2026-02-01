#!/usr/bin/env python3
"""Debug Alembic table creation"""

import sqlite3
import os

def check_database_schema(db_path):
    """Check database schema after Alembic migrations"""
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist")
        return
    
    print(f"Checking database schema: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if estimates table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        print("✅ Estimates table exists")
        
        # Check table schema
        cursor.execute("PRAGMA table_info(estimates)")
        columns = cursor.fetchall()
        
        print("Estimates table schema:")
        date_column_found = False
        for col in columns:
            col_name, col_type = col[1], col[2]
            print(f"  {col_name}: {col_type}")
            if col_name.lower() == 'date':
                date_column_found = True
                print(f"✅ Date column found: {col_name} ({col_type})")
        
        if not date_column_found:
            print("❌ Date column not found")
            # Check for similar column names
            date_like_columns = [col for col in columns if 'date' in col[1].lower()]
            if date_like_columns:
                print("Found date-like columns:")
                for col in date_like_columns:
                    print(f"  {col[1]}: {col[2]}")
            
    else:
        print("❌ Estimates table does not exist")
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nAll tables in database ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check for any table with date column
    print(f"\nSearching for 'date' columns in all tables:")
    for table in tables:
        table_name = table[0]
        if table_name.startswith('sqlite_'):
            continue
        
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            date_columns = [col for col in columns if 'date' in col[1].lower()]
            if date_columns:
                print(f"  Table {table_name}:")
                for col in date_columns:
                    print(f"    {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error checking table {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    # Check the server database that was created during the test
    db_path = "test_databases/server_sqlite_only.db"
    check_database_schema(db_path)
    
    # Also check if there are any other test databases
    if os.path.exists("test_databases"):
        print(f"\n" + "="*50)
        print("Checking all test databases:")
        for file in os.listdir("test_databases"):
            if file.endswith(".db"):
                print(f"\n--- {file} ---")
                check_database_schema(f"test_databases/{file}")
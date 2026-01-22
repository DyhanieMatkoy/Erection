#!/usr/bin/env python3
"""Check client database tables"""

import sqlite3
import os

def check_client_db():
    db_path = 'test_databases/client_1_test.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Tables in {db_path}:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if estimates table exists
        if ('estimates',) in tables:
            cursor.execute("PRAGMA table_info(estimates)")
            columns = cursor.fetchall()
            print("\nEstimates table columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\n❌ estimates table not found!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_client_db()
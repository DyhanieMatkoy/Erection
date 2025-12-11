#!/usr/bin/env python3
"""
Script to list all tables in the database.
"""

import sqlite3
import os

def list_tables():
    """List all tables in the database."""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Database path: {db_path}")
        print(f"Number of tables: {len(tables)}")
        print("All tables in the database:")
        for table in sorted(tables):
            print(f"  - {table}")
        
    except Exception as e:
        print(f"Error listing tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_tables()
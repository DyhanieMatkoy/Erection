#!/usr/bin/env python3
"""
Check the current Alembic version
"""
import sqlite3
from pathlib import Path

def main():
    # Get the database path
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        
        if version:
            print(f"Current Alembic version: {version[0]}")
        else:
            print("No Alembic version found in database")
    except sqlite3.Error as e:
        print(f"Error checking Alembic version: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
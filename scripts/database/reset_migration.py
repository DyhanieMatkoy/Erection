#!/usr/bin/env python3
"""
Reset the migration state and clean up partially applied migration
"""
import sqlite3
from pathlib import Path

def main():
    # Get the database path
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop the new tables that were created
        cursor.execute("DROP TABLE IF EXISTS cost_items")
        cursor.execute("DROP TABLE IF EXISTS materials")
        cursor.execute("DROP TABLE IF EXISTS cost_item_materials")
        
        # Reset the Alembic version to the previous version
        cursor.execute("UPDATE alembic_version SET version_num = '201f5ef24462'")
        
        conn.commit()
        print("Migration state reset successfully")
    except sqlite3.Error as e:
        print(f"Error resetting migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
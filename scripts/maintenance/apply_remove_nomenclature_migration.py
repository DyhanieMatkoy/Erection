#!/usr/bin/env python3
"""
Apply migration to remove nomenclatures table
"""
import sqlite3
from pathlib import Path

def main():
    # Get the database path
    db_path = Path(__file__).parent / "construction.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Remove nomenclature_id column from works table
        cursor.execute("ALTER TABLE works DROP COLUMN nomenclature_id")
        
        # Drop nomenclatures table
        cursor.execute("DROP TABLE IF EXISTS nomenclatures")
        
        # Update alembic version
        cursor.execute("UPDATE alembic_version SET version_num = '20251208_140000'")
        
        conn.commit()
        print("Migration to remove nomenclatures table applied successfully!")
    except sqlite3.Error as e:
        print(f"Error applying migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
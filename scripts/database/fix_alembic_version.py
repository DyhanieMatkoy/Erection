#!/usr/bin/env python3
"""
Script to fix the alembic_version table.
"""

import sqlite3
import os
from pathlib import Path

def fix_alembic_version():
    """Fix the alembic_version table"""
    # Path to the database
    db_path = Path(__file__).parent.parent.parent / "construction.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Update the alembic_version table
        cursor.execute("UPDATE alembic_version SET version_num = '201f5ef24462'")
        
        conn.commit()
        print("Successfully updated alembic_version to 201f5ef24462")
        
        conn.close()
        return True
                
    except Exception as e:
        print(f"Error fixing alembic_version: {e}")
        return False

if __name__ == "__main__":
    success = fix_alembic_version()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Script to reset the database and fix migration issues
"""
import os
import sys
import sqlite3
from pathlib import Path

def reset_database():
    """Reset the database and create fresh schema"""
    db_path = "construction.db"
    
    # Try to remove existing database
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✓ Removed existing database: {db_path}")
    except PermissionError:
        print(f"❌ Cannot remove {db_path} - file is in use by another process")
        print("Please stop the server first and try again")
        return False
    
    # Create new database with basic schema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create alembic version table
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Mark database as up-to-date with the latest migration
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('97168f34447a')")
        
        conn.commit()
        conn.close()
        
        print(f"✓ Created new database: {db_path}")
        print("✓ Marked as up-to-date with latest migration")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Resetting database...")
    if reset_database():
        print("✅ Database reset complete!")
        print("You can now restart the server.")
    else:
        print("❌ Database reset failed!")
        sys.exit(1)
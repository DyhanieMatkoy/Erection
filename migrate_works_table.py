"""Migration script to add missing fields to works table"""
import sqlite3

def migrate():
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    # Check current structure
    cursor.execute("PRAGMA table_info(works)")
    columns = {row[1]: row for row in cursor.fetchall()}
    print("Current columns:", list(columns.keys()))
    
    # Add missing columns
    if 'code' not in columns:
        print("Adding 'code' column...")
        cursor.execute("ALTER TABLE works ADD COLUMN code TEXT")
    
    if 'parent_id' not in columns:
        print("Adding 'parent_id' column...")
        cursor.execute("ALTER TABLE works ADD COLUMN parent_id INTEGER")
    
    if 'is_group' not in columns:
        print("Adding 'is_group' column...")
        cursor.execute("ALTER TABLE works ADD COLUMN is_group INTEGER DEFAULT 0")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(works)")
    columns = {row[1]: row for row in cursor.fetchall()}
    print("\nUpdated columns:", list(columns.keys()))
    
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()

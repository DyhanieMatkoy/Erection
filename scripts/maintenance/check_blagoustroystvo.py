#!/usr/bin/env python3
"""
Check БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ location
"""

import sys
import os

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager

def check_blagoustroystvo():
    """Check where БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ is located"""
    print("=== Checking БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ ===")
    
    db_manager = DatabaseManager()
    db_manager.initialize()
    db = db_manager.get_connection()
    cursor = db.cursor()
    
    # Find БЛАГОУСТРОЙСТВО И МАЛЫЕ ФОРМЫ by ID (from previous analysis)
    cursor.execute("""
        SELECT id, name, parent_id, is_group 
        FROM works 
        WHERE id = 1958
    """)
    
    print("Searching by ID 1958:")
    works = cursor.fetchall()
    if not works:
        print("Not found by ID, searching by name pattern...")
        # Try different patterns
        patterns = ['%БЛАГО%', '%благо%', '%Благо%', '%МАЛЫЕ%', '%малые%']
        for pattern in patterns:
            cursor.execute("""
                SELECT id, name, parent_id, is_group 
                FROM works 
                WHERE name LIKE ? 
                AND marked_for_deletion = 0
                LIMIT 5
            """, (pattern,))
            results = cursor.fetchall()
            if results:
                print(f"Found with pattern '{pattern}':")
                for work in results:
                    print(f"  ID: {work['id']}, Name: {work['name']}")
                works = results
                break
    
    works = cursor.fetchall()
    for work in works:
        print(f"ID: {work['id']}, Name: {work['name']}")
        print(f"parent_id: {work['parent_id']}, is_group: {work['is_group']}")
        
        if work['parent_id']:
            # Find parent
            cursor.execute("""
                SELECT id, name FROM works WHERE id = ?
            """, (work['parent_id'],))
            parent = cursor.fetchone()
            if parent:
                print(f"Parent: ID {parent['id']}, Name: {parent['name']}")
        else:
            print("Parent: None (root level)")
        
        # Check children count
        cursor.execute("""
            SELECT COUNT(*) as count FROM works 
            WHERE parent_id = ? AND marked_for_deletion = 0
        """, (work['id'],))
        children_count = cursor.fetchone()['count']
        print(f"Children count: {children_count}")

if __name__ == "__main__":
    check_blagoustroystvo()
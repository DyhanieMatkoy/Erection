#!/usr/bin/env python3
"""
Test script to verify unit fixes
"""
import sqlite3

def test_desktop_app():
    """Test desktop app logic"""
    conn = sqlite3.connect('construction.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test the query used in desktop app
    cursor.execute("""
        SELECT w.code, w.price, w.labor_rate, w.unit_id, u.name as unit_name
        FROM works w
        LEFT JOIN units u ON w.unit_id = u.id
        WHERE w.id = ?
    """, (1736,))
    
    work_row = cursor.fetchone()
    print("Desktop app query result:")
    print(f"  unit_name: {work_row['unit_name']}")
    print(f"  unit_id: {work_row['unit_id']}")
    
    conn.close()

def test_api_query():
    """Test API query"""
    conn = sqlite3.connect('construction.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test the query used in API
    cursor.execute("""
        SELECT w.id, w.name, w.code, COALESCE(u.name, w.unit) as unit, w.unit_id, u.name as unit_name, w.price, w.labor_rate, w.is_group, w.parent_id, w.marked_for_deletion
        FROM works w
        LEFT JOIN units u ON w.unit_id = u.id
        WHERE w.id = ?
    """, (1736,))
    
    work_row = cursor.fetchone()
    print("\nAPI query result:")
    print(f"  unit: {work_row['unit']}")
    print(f"  unit_name: {work_row['unit_name']}")
    print(f"  unit_id: {work_row['unit_id']}")
    
    conn.close()

if __name__ == "__main__":
    test_desktop_app()
    test_api_query()
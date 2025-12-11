#!/usr/bin/env python
"""
Fix daily report error by checking and potentially recreating the table
"""

import sqlite3
import sys

def check_and_fix_daily_report_schema():
    """Check and fix daily report schema"""
    try:
        conn = sqlite3.connect('construction.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("=== Checking daily_report_lines table ===")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_report_lines'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("ERROR: daily_report_lines table does not exist!")
            return False
        
        print("✓ Table exists")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(daily_report_lines)")
        columns = cursor.fetchall()
        
        print("Current columns:")
        column_names = []
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
            column_names.append(col['name'])
        
        # Check if daily_report_id column exists (the correct column name)
        if 'daily_report_id' not in column_names:
            print("ERROR: daily_report_id column is missing!")
            print("Available columns:", column_names)
            return False
        
        print("✓ daily_report_id column exists")
        
        # Test the corrected query
        print("\n=== Testing the corrected query ===")
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM daily_report_lines WHERE daily_report_id = ?
            """, (1,))
            result = cursor.fetchone()
            print(f"✓ Query works, count: {result[0]}")
        except Exception as e:
            print(f"ERROR in query: {e}")
            return False
        
        # Check if there are any daily_reports
        cursor.execute("SELECT COUNT(*) FROM daily_reports")
        report_count = cursor.fetchone()[0]
        print(f"Total daily reports: {report_count}")
        
        # Check if there are any daily_report_lines
        cursor.execute("SELECT COUNT(*) FROM daily_report_lines")
        line_count = cursor.fetchone()[0]
        print(f"Total daily report lines: {line_count}")
        
        print("\n✓ Database schema appears to be correct")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_daily_report_list_query():
    """Test the exact query from daily_report_list_form.py"""
    try:
        conn = sqlite3.connect('construction.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== Testing corrected query from daily_report_list_form.py ===")
        
        # This is the corrected query with daily_report_id instead of report_id
        query = """
            SELECT dr.id, dr.date, 
                   e.number as estimate_number,
                   p.full_name as foreman_name,
                   (SELECT COUNT(*) FROM daily_report_lines WHERE daily_report_id = dr.id) as line_count,
                   dr.is_posted
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            LEFT JOIN persons p ON dr.foreman_id = p.id
            WHERE (dr.marked_for_deletion = 0 OR dr.marked_for_deletion IS NULL)
            ORDER BY dr.date DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"✓ Query executed successfully, returned {len(rows)} rows")
        
        if rows:
            print("Sample row:")
            row = rows[0]
            for key in row.keys():
                print(f"  {key}: {row[key]}")
        
        return True
        
    except Exception as e:
        print(f"ERROR in query: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Checking daily report database schema...")
    
    schema_ok = check_and_fix_daily_report_schema()
    if schema_ok:
        query_ok = test_daily_report_list_query()
        if query_ok:
            print("\n✅ All checks passed - the database schema is correct")
            print("The error might be caused by a different issue.")
        else:
            print("\n❌ Query test failed")
    else:
        print("\n❌ Schema check failed")
#!/usr/bin/env python
"""
Check daily report schema
"""

import sqlite3

def check_daily_report_schema():
    """Check daily report related tables"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    # Check daily_reports table
    print("=== DAILY_REPORTS TABLE ===")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_reports'")
    daily_reports_schema = cursor.fetchone()
    if daily_reports_schema:
        print("Schema:")
        print(daily_reports_schema[0])
    else:
        print("Table not found")
    
    print("\nColumns:")
    try:
        cursor.execute("PRAGMA table_info(daily_reports)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check daily_report_lines table
    print("\n=== DAILY_REPORT_LINES TABLE ===")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_report_lines'")
    daily_report_lines_schema = cursor.fetchone()
    if daily_report_lines_schema:
        print("Schema:")
        print(daily_report_lines_schema[0])
    else:
        print("Table not found")
    
    print("\nColumns:")
    try:
        cursor.execute("PRAGMA table_info(daily_report_lines)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check if there are any daily report related tables
    print("\n=== ALL DAILY REPORT RELATED TABLES ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%daily%'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    check_daily_report_schema()
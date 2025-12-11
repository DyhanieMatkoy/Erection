#!/usr/bin/env python3
"""
Script to check the structure of the daily_report_lines table in the backup database.
"""

import sqlite3
import os

def check_daily_report_lines():
    """Check the structure of the daily_report_lines table in the backup database."""
    
    # Get the backup database path
    backup_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'construction_backup_20251208_001233.db')
    
    # Connect to the backup database
    conn = sqlite3.connect(backup_db_path)
    cursor = conn.cursor()
    
    try:
        # Get the structure of the daily_report_lines table
        cursor.execute("PRAGMA table_info(daily_report_lines)")
        columns = cursor.fetchall()
        
        print(f"Structure of daily_report_lines table in backup:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get some sample data
        cursor.execute("SELECT * FROM daily_report_lines LIMIT 5")
        rows = cursor.fetchall()
        
        print("\nSample data from daily_report_lines:")
        for row in rows:
            print(f"  {row}")
        
    except Exception as e:
        print(f"Error checking daily_report_lines table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_daily_report_lines()
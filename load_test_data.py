#!/usr/bin/env python3
"""Load test data into database"""
import sqlite3


def load_test_data():
    """Load test data from SQL file"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    try:
        # Clear existing test data
        print("Clearing existing test data...")
        cursor.execute("DELETE FROM daily_report_executors")
        cursor.execute("DELETE FROM daily_report_lines")
        cursor.execute("DELETE FROM daily_reports")
        cursor.execute("DELETE FROM estimate_lines")
        cursor.execute("DELETE FROM estimates")
        cursor.execute("DELETE FROM works")
        cursor.execute("DELETE FROM objects")
        cursor.execute("DELETE FROM counterparties")
        cursor.execute("DELETE FROM organizations")
        cursor.execute("DELETE FROM persons")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM constants")
        conn.commit()
        
        # Load new test data
        print("Loading test data...")
        with open('test_data.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor.executescript(sql_script)
        conn.commit()
        print("✓ Test data loaded successfully!")
        print("\nTest users:")
        print("  admin / admin (Администратор)")
        print("  manager / manager (Руководитель)")
        print("  foreman / foreman (Бригадир)")
    except Exception as e:
        print(f"✗ Failed to load test data: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    load_test_data()

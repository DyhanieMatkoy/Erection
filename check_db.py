#!/usr/bin/env python
"""
Проверка импортированных данных
"""

import sqlite3

def check_imported_data():
    """Проверяет импортированные данные"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, code, unit FROM works LIMIT 5")
    rows = cursor.fetchall()
    
    print("Импортированные записи:")
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}, Code: {row[2]}, Unit: {row[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_imported_data()
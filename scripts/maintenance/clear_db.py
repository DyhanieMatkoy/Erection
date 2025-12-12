#!/usr/bin/env python
"""
Очистка таблицы works
"""

import sqlite3

def clear_works_table():
    """Очищает таблицу works"""
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM works")
    conn.commit()
    
    print("Таблица works очищена")
    
    conn.close()

if __name__ == "__main__":
    clear_works_table()
#!/usr/bin/env python3
"""Check project status"""
import sqlite3
import os


def check_status():
    """Check project status"""
    print("=" * 60)
    print("Система управления рабочим временем - Статус проекта")
    print("=" * 60)
    print()
    
    # Check Python
    import sys
    print(f"✓ Python: {sys.version.split()[0]}")
    
    # Check PyQt6
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✓ PyQt6: {QT_VERSION_STR}")
    except ImportError:
        print("✗ PyQt6: не установлен")
        return
    
    # Check database
    if os.path.exists('construction.db'):
        print("✓ База данных: construction.db")
        
        # Check tables
        conn = sqlite3.connect('construction.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  Таблиц: {len(tables)}")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Пользователей: {user_count}")
        
        if user_count > 0:
            cursor.execute("SELECT username, role FROM users")
            print("\n  Тестовые пользователи:")
            for username, role in cursor.fetchall():
                print(f"    - {username} ({role})")
        
        # Check works
        cursor.execute("SELECT COUNT(*) FROM works")
        work_count = cursor.fetchone()[0]
        print(f"\n  Работ в справочнике: {work_count}")
        
        conn.close()
    else:
        print("✗ База данных: не найдена")
        print("  Запустите приложение для создания БД")
    
    print()
    print("=" * 60)
    print("Для запуска приложения:")
    print("  run.bat")
    print("или")
    print("  .\\venv\\Scripts\\python.exe main.py")
    print("=" * 60)


if __name__ == "__main__":
    check_status()

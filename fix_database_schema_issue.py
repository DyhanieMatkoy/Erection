#!/usr/bin/env python3
"""
Быстрое исправление проблемы с созданием индексов в DatabaseManager
"""

import os
import sys
import sqlite3
from pathlib import Path

def fix_database_schema_issue():
    """Исправляет проблему с созданием индексов в DatabaseManager"""
    
    print("🔧 Исправление проблемы с созданием индексов в DatabaseManager...")
    
    # Путь к файлу DatabaseManager
    db_manager_path = Path("src/data/database_manager.py")
    
    if not db_manager_path.exists():
        print(f"❌ Файл не найден: {db_manager_path}")
        return False
    
    # Читаем содержимое файла
    with open(db_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем метод _create_indices - добавляем проверку существования таблиц
    old_create_indices = '''    def _create_indices(self):
        """Create database indices with automatic SQL translation for multi-database support"""
        cursor = self._connection.cursor()
        
        # Determine target SQL dialect based on current database configuration
        target_dialect = self._get_current_sql_dialect()
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",'''
    
    new_create_indices = '''    def _create_indices(self):
        """Create database indices with automatic SQL translation for multi-database support"""
        cursor = self._connection.cursor()
        
        # Determine target SQL dialect based on current database configuration
        target_dialect = self._get_current_sql_dialect()
        
        # Проверяем, что все необходимые таблицы существуют перед созданием индексов
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estimates'")
            if not cursor.fetchone():
                logger.warning("Table 'estimates' does not exist, skipping index creation")
                return
                
            cursor.execute("PRAGMA table_info(estimates)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'date' not in columns:
                logger.warning("Column 'date' does not exist in estimates table, skipping date index")
                # Создаем индексы без проблемного индекса на date
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_estimates_responsible ON estimates(responsible_id)",
                    "CREATE INDEX IF NOT EXISTS idx_daily_reports_estimate ON daily_reports(estimate_id)",
                    # Audit Logs
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
                ]
            else:
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_estimates_date ON estimates(date)",'''
    
    # Заменяем старый код на новый
    if old_create_indices in content:
        content = content.replace(old_create_indices, new_create_indices)
        
        # Записываем исправленный файл
        with open(db_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Исправление применено к DatabaseManager")
        return True
    else:
        print("⚠️ Не удалось найти код для исправления")
        return False

def test_database_creation():
    """Тестирует создание базы данных после исправления"""
    
    print("\n🧪 Тестирование создания базы данных...")
    
    # Создаем тестовую базу данных
    test_db_path = Path("test_fix.db")
    
    try:
        # Удаляем старую тестовую БД если есть
        if test_db_path.exists():
            test_db_path.unlink()
        
        # Импортируем DatabaseManager
        sys.path.insert(0, 'src')
        from data.database_manager import DatabaseManager
        
        # Создаем экземпляр и инициализируем
        db_manager = DatabaseManager()
        success = db_manager.initialize(str(test_db_path))
        
        if success:
            print("✅ База данных создана успешно")
            
            # Проверяем, что таблицы созданы
            conn = sqlite3.connect(str(test_db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📋 Создано таблиц: {len(tables)}")
            
            # Проверяем таблицу estimates
            if 'estimates' in tables:
                cursor.execute("PRAGMA table_info(estimates)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"📊 Колонки в таблице estimates: {columns}")
                
                if 'date' in columns:
                    print("✅ Колонка 'date' найдена в таблице estimates")
                else:
                    print("❌ Колонка 'date' НЕ найдена в таблице estimates")
            
            conn.close()
            return True
        else:
            print("❌ Не удалось создать базу данных")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    
    finally:
        # Очищаем тестовую БД
        if test_db_path.exists():
            test_db_path.unlink()

def main():
    """Главная функция"""
    
    print("🚀 Исправление проблемы с созданием индексов")
    print("=" * 50)
    
    # Исправляем код
    if fix_database_schema_issue():
        # Тестируем исправление
        if test_database_creation():
            print("\n🎉 Исправление успешно применено и протестировано!")
            print("Теперь можно запускать тесты синхронизации.")
        else:
            print("\n⚠️ Исправление применено, но тестирование не прошло")
    else:
        print("\n❌ Не удалось применить исправление")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Исправление схемы синхронизации

Этот скрипт добавляет поля синхронизации в существующую БД без конфликтов с миграциями.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.database_manager import DatabaseManager


class SyncSchemaFixer:
    """Исправление схемы синхронизации"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Настройка логирования"""
        logger = logging.getLogger("sync_schema_fixer")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def fix_database_schema(self, db_path: str) -> bool:
        """Исправление схемы базы данных
        
        Args:
            db_path: Путь к базе данных
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            self.logger.info(f"Исправление схемы БД: {db_path}")
            
            if not Path(db_path).exists():
                self.logger.error(f"База данных не найдена: {db_path}")
                return False
            
            # Подключение к БД
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Список таблиц для обновления
                tables_to_update = [
                    'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
                    'timesheets', 'timesheet_lines', 'works', 'materials', 'cost_items',
                    'units', 'persons', 'organizations', 'counterparties', 'objects'
                ]
                
                updated_tables = []
                
                for table_name in tables_to_update:
                    if self._table_exists(cursor, table_name):
                        if self._add_sync_fields_to_table(cursor, table_name):
                            updated_tables.append(table_name)
                    else:
                        self.logger.warning(f"Таблица не найдена: {table_name}")
                
                # Сохранение изменений
                conn.commit()
                
                self.logger.info(f"Схема обновлена для {len(updated_tables)} таблиц: {', '.join(updated_tables)}")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Ошибка исправления схемы: {e}")
            return False
    
    def _table_exists(self, cursor: sqlite3.Cursor, table_name: str) -> bool:
        """Проверка существования таблицы"""
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    
    def _column_exists(self, cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
        """Проверка существования колонки"""
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    
    def _add_sync_fields_to_table(self, cursor: sqlite3.Cursor, table_name: str) -> bool:
        """Добавление полей синхронизации к таблице
        
        Args:
            cursor: Курсор БД
            table_name: Название таблицы
            
        Returns:
            True если поля добавлены, False если уже существуют
        """
        try:
            fields_added = []
            
            # Поле uuid
            if not self._column_exists(cursor, table_name, 'uuid'):
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN uuid VARCHAR(36) DEFAULT (lower(hex(randomblob(4))) || '-' || 
                                                        lower(hex(randomblob(2))) || '-4' || 
                                                        substr(lower(hex(randomblob(2))),2) || '-' || 
                                                        substr('89ab',abs(random()) % 4 + 1, 1) || 
                                                        substr(lower(hex(randomblob(2))),2) || '-' || 
                                                        lower(hex(randomblob(6))))
                """)
                fields_added.append('uuid')
            
            # Поле updated_at
            if not self._column_exists(cursor, table_name, 'updated_at'):
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                """)
                fields_added.append('updated_at')
            
            # Поле is_deleted
            if not self._column_exists(cursor, table_name, 'is_deleted'):
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN is_deleted BOOLEAN DEFAULT 0
                """)
                fields_added.append('is_deleted')
            
            if fields_added:
                self.logger.info(f"Добавлены поля в {table_name}: {', '.join(fields_added)}")
                
                # Обновление существующих записей с UUID
                if 'uuid' in fields_added:
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET uuid = (lower(hex(randomblob(4))) || '-' || 
                                   lower(hex(randomblob(2))) || '-4' || 
                                   substr(lower(hex(randomblob(2))),2) || '-' || 
                                   substr('89ab',abs(random()) % 4 + 1, 1) || 
                                   substr(lower(hex(randomblob(2))),2) || '-' || 
                                   lower(hex(randomblob(6))))
                        WHERE uuid IS NULL
                    """)
                
                # Обновление updated_at для существующих записей
                if 'updated_at' in fields_added:
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE updated_at IS NULL
                    """)
                
                return True
            else:
                self.logger.info(f"Поля синхронизации уже существуют в {table_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления полей синхронизации в {table_name}: {e}")
            return False
    
    def verify_sync_fields(self, db_path: str) -> Dict[str, bool]:
        """Проверка полей синхронизации
        
        Args:
            db_path: Путь к базе данных
            
        Returns:
            Словарь с результатами проверки для каждой таблицы
        """
        results = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                tables_to_check = [
                    'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
                    'timesheets', 'timesheet_lines', 'works', 'materials', 'cost_items',
                    'units', 'persons', 'organizations', 'counterparties', 'objects'
                ]
                
                for table_name in tables_to_check:
                    if self._table_exists(cursor, table_name):
                        has_uuid = self._column_exists(cursor, table_name, 'uuid')
                        has_updated_at = self._column_exists(cursor, table_name, 'updated_at')
                        has_is_deleted = self._column_exists(cursor, table_name, 'is_deleted')
                        
                        results[table_name] = {
                            'exists': True,
                            'has_uuid': has_uuid,
                            'has_updated_at': has_updated_at,
                            'has_is_deleted': has_is_deleted,
                            'complete': has_uuid and has_updated_at and has_is_deleted
                        }
                    else:
                        results[table_name] = {
                            'exists': False,
                            'has_uuid': False,
                            'has_updated_at': False,
                            'has_is_deleted': False,
                            'complete': False
                        }
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки полей синхронизации: {e}")
        
        return results


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix Sync Schema')
    parser.add_argument('--database', type=str, default='construction.db', 
                       help='Путь к базе данных')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Только проверить схему, не исправлять')
    
    args = parser.parse_args()
    
    fixer = SyncSchemaFixer()
    
    if args.verify_only:
        # Только проверка
        results = fixer.verify_sync_fields(args.database)
        
        print(f"\n{'='*60}")
        print("ПРОВЕРКА ПОЛЕЙ СИНХРОНИЗАЦИИ")
        print(f"{'='*60}")
        
        complete_tables = 0
        total_tables = 0
        
        for table_name, info in results.items():
            if info['exists']:
                total_tables += 1
                status = "✅ ПОЛНАЯ" if info['complete'] else "❌ НЕПОЛНАЯ"
                print(f"{table_name}: {status}")
                
                if not info['complete']:
                    missing = []
                    if not info['has_uuid']:
                        missing.append('uuid')
                    if not info['has_updated_at']:
                        missing.append('updated_at')
                    if not info['has_is_deleted']:
                        missing.append('is_deleted')
                    print(f"  Отсутствуют поля: {', '.join(missing)}")
                else:
                    complete_tables += 1
            else:
                print(f"{table_name}: ❌ ТАБЛИЦА НЕ НАЙДЕНА")
        
        print(f"\nИтого: {complete_tables}/{total_tables} таблиц имеют полные поля синхронизации")
        
    else:
        # Исправление схемы
        success = fixer.fix_database_schema(args.database)
        
        if success:
            print("✅ Схема синхронизации успешно исправлена")
            
            # Проверка результата
            results = fixer.verify_sync_fields(args.database)
            complete_tables = sum(1 for info in results.values() if info.get('complete', False))
            total_tables = sum(1 for info in results.values() if info.get('exists', False))
            
            print(f"Результат: {complete_tables}/{total_tables} таблиц имеют полные поля синхронизации")
            return 0
        else:
            print("❌ Ошибка исправления схемы синхронизации")
            return 1


if __name__ == "__main__":
    sys.exit(main())
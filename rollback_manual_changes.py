#!/usr/bin/env python3
"""
Откат ручных изменений схемы

Этот скрипт удаляет поля синхронизации, добавленные вручную,
чтобы миграция Alembic могла их добавить правильно.
"""

import sqlite3
import logging
from typing import List

def rollback_sync_fields(db_path: str = 'construction.db') -> bool:
    """Откат полей синхронизации из всех таблиц"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Список таблиц для отката
        tables_to_rollback = [
            'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
            'timesheets', 'timesheet_lines', 'works', 'organizations', 
            'counterparties', 'objects', 'persons'
        ]
        
        success_count = 0
        
        for table_name in tables_to_rollback:
            try:
                logger.info(f"Откат полей синхронизации из таблицы {table_name}")
                
                if _rollback_table_sync_fields(cursor, table_name):
                    success_count += 1
                    logger.info(f"✅ Откат {table_name} выполнен")
                else:
                    logger.info(f"ℹ️ Таблица {table_name} не требует отката")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка отката {table_name}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Откат завершен для {success_count} таблиц")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отката: {e}")
        return False


def _rollback_table_sync_fields(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Откат полей синхронизации для конкретной таблицы"""
    
    # Проверяем, есть ли поля синхронизации
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    sync_fields = ['uuid', 'updated_at', 'is_deleted']
    has_sync_fields = any(field in columns for field in sync_fields)
    
    if not has_sync_fields:
        return False  # Нет полей для отката
    
    # Получаем все колонки кроме полей синхронизации
    original_columns = [col for col in columns if col not in sync_fields]
    
    if not original_columns:
        return False  # Нет оригинальных колонок
    
    # Создаем временную таблицу без полей синхронизации
    cursor.execute(f"CREATE TABLE {table_name}_temp AS SELECT {', '.join(original_columns)} FROM {table_name}")
    
    # Удаляем оригинальную таблицу
    cursor.execute(f"DROP TABLE {table_name}")
    
    # Переименовываем временную таблицу
    cursor.execute(f"ALTER TABLE {table_name}_temp RENAME TO {table_name}")
    
    return True


if __name__ == "__main__":
    success = rollback_sync_fields()
    exit(0 if success else 1)
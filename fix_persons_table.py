#!/usr/bin/env python3
"""
Исправление таблицы persons

SQLite не позволяет добавлять колонки с не-константными значениями по умолчанию,
поэтому нужно пересоздать таблицу.
"""

import sqlite3
import logging

def fix_persons_table(db_path: str = 'construction.db'):
    """Исправление таблицы persons"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже поля синхронизации
        cursor.execute("PRAGMA table_info(persons)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'uuid' in columns:
            logger.info("Поля синхронизации уже существуют в таблице persons")
            return True
        
        logger.info("Исправление таблицы persons...")
        
        # Начинаем транзакцию
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Создаем временную таблицу с новой структурой
            cursor.execute("""
                CREATE TABLE persons_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    position TEXT,
                    phone TEXT,
                    user_id INTEGER REFERENCES users(id),
                    parent_id INTEGER REFERENCES persons(id),
                    marked_for_deletion INTEGER DEFAULT 0,
                    is_group INTEGER DEFAULT 0,
                    hourly_rate REAL DEFAULT 0,
                    uuid VARCHAR(36) NOT NULL DEFAULT '',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            
            # Копируем данные из старой таблицы
            cursor.execute("""
                INSERT INTO persons_new (
                    id, full_name, position, phone, user_id, parent_id, 
                    marked_for_deletion, is_group, hourly_rate
                )
                SELECT 
                    id, full_name, position, phone, user_id, parent_id,
                    marked_for_deletion, is_group, hourly_rate
                FROM persons
            """)
            
            # Генерируем UUID для существующих записей
            cursor.execute("""
                UPDATE persons_new 
                SET uuid = (
                    lower(hex(randomblob(4))) || '-' || 
                    lower(hex(randomblob(2))) || '-4' || 
                    substr(lower(hex(randomblob(2))),2) || '-' || 
                    substr('89ab',abs(random()) % 4 + 1, 1) || 
                    substr(lower(hex(randomblob(2))),2) || '-' || 
                    lower(hex(randomblob(6)))
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE uuid = ''
            """)
            
            # Удаляем старую таблицу
            cursor.execute("DROP TABLE persons")
            
            # Переименовываем новую таблицу
            cursor.execute("ALTER TABLE persons_new RENAME TO persons")
            
            # Создаем индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_uuid ON persons(uuid)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_updated_at ON persons(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_is_deleted ON persons(is_deleted)")
            
            # Подтверждаем транзакцию
            cursor.execute("COMMIT")
            
            logger.info("✅ Таблица persons успешно исправлена")
            return True
            
        except Exception as e:
            # Откатываем транзакцию при ошибке
            cursor.execute("ROLLBACK")
            logger.error(f"❌ Ошибка исправления таблицы persons: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = fix_persons_table()
    exit(0 if success else 1)
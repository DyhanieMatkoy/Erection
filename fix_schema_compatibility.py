#!/usr/bin/env python3
"""
Комплексное исправление совместимости схем между Unified Database Manager и основным кодом
"""

import os
import sys
import re
from pathlib import Path

def fix_unified_database_manager_schemas():
    """Исправляет схемы в Unified Database Manager для совместимости с основным кодом"""
    
    print("🔧 Исправление схем в Unified Database Manager...")
    
    udm_path = Path("unified_database_manager.py")
    
    if not udm_path.exists():
        print(f"❌ Файл не найден: {udm_path}")
        return False
    
    # Читаем содержимое файла
    with open(udm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Исправляем таблицу persons: name -> full_name
    old_persons = '''            # Persons
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                marked_for_deletion INTEGER DEFAULT 0
            )""",'''
    
    new_persons = '''            # Persons
            """CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                hourly_rate REAL DEFAULT 0.0,
                user_id INTEGER REFERENCES users(id),
                parent_id INTEGER REFERENCES persons(id),
                is_group INTEGER DEFAULT 0,
                marked_for_deletion INTEGER DEFAULT 0,
                uuid TEXT UNIQUE NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",'''
    
    if old_persons in content:
        content = content.replace(old_persons, new_persons)
        print("✅ Исправлена таблица persons (name -> full_name)")
    
    # 2. Добавляем правильную таблицу sync_nodes
    sync_nodes_sql = '''            # Sync Nodes
            """CREATE TABLE IF NOT EXISTS sync_nodes (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_sync_in TIMESTAMP,
                last_sync_out TIMESTAMP,
                received_packet_no INTEGER,
                sent_packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            '''
    
    # 3. Исправляем таблицу sync_changes - добавляем node_id и другие поля
    old_sync_changes = '''            # Sync Changes
            """CREATE TABLE IF NOT EXISTS sync_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_uuid TEXT,
                operation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",'''
    
    new_sync_changes = '''            # Sync Changes
            """CREATE TABLE IF NOT EXISTS sync_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT REFERENCES sync_nodes(id),
                entity_type TEXT NOT NULL,
                entity_uuid TEXT NOT NULL,
                operation TEXT NOT NULL,
                packet_no INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT
            )""",'''
    
    if old_sync_changes in content:
        content = content.replace(old_sync_changes, new_sync_changes)
        print("✅ Исправлена таблица sync_changes (добавлен node_id)")
    
    # 4. Исправляем таблицу object_version_history
    old_version_history = '''            # Object Version History
            """CREATE TABLE IF NOT EXISTS object_version_history (
                id TEXT PRIMARY KEY,
                entity_uuid TEXT,
                entity_type TEXT,
                source_node_id TEXT,
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                serialized_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",'''
    
    new_version_history = '''            # Object Version History
            """CREATE TABLE IF NOT EXISTS object_version_history (
                id TEXT PRIMARY KEY,
                entity_uuid TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source_node_id TEXT REFERENCES sync_nodes(id),
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                serialized_data TEXT NOT NULL,
                conflict_resolution TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",'''
    
    if old_version_history in content:
        content = content.replace(old_version_history, new_version_history)
        print("✅ Исправлена таблица object_version_history")
    
    # 5. Добавляем sync_nodes в список таблиц, если его нет
    if "sync_nodes" not in content:
        # Ищем место для вставки sync_nodes (перед sync_changes)
        sync_changes_pos = content.find("# Sync Changes")
        if sync_changes_pos > 0:
            content = content[:sync_changes_pos] + sync_nodes_sql + content[sync_changes_pos:]
            print("✅ Добавлена таблица sync_nodes")
    
    # 6. Исправляем таблицу timesheets - добавляем недостающие колонки
    old_timesheets = '''            # Timesheets
            """CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                month_year TEXT NOT NULL,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",'''
    
    new_timesheets = '''            # Timesheets
            """CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date DATE NOT NULL,
                object_id INTEGER REFERENCES objects(id),
                estimate_id INTEGER REFERENCES estimates(id),
                foreman_id INTEGER REFERENCES persons(id),
                month_year TEXT NOT NULL,
                is_posted INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                marked_for_deletion INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",'''
    
    if old_timesheets in content:
        content = content.replace(old_timesheets, new_timesheets)
        print("✅ Исправлена таблица timesheets (добавлены date, object_id, estimate_id, foreman_id)")
    
    # Записываем исправленный файл
    with open(udm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Unified Database Manager обновлен")
    return True

def fix_initial_data_compatibility():
    """Исправляет initial_data для работы с правильной схемой persons"""
    
    print("🔧 Исправление initial_data для совместимости...")
    
    initial_data_path = Path("src/data/initial_data.py")
    
    if not initial_data_path.exists():
        print(f"❌ Файл не найден: {initial_data_path}")
        return False
    
    # Читаем содержимое файла
    with open(initial_data_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем запросы, которые используют name вместо full_name
    replacements = [
        ("INSERT INTO persons (name,", "INSERT INTO persons (full_name,"),
        ("SELECT id FROM persons WHERE name =", "SELECT id FROM persons WHERE full_name ="),
        ("UPDATE persons SET name =", "UPDATE persons SET full_name ="),
        ("name = ?", "full_name = ?"),
        ("name=?", "full_name=?"),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Исправлено: {old} -> {new}")
    
    # Записываем исправленный файл
    with open(initial_data_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ initial_data.py обновлен")
    return True

def create_sync_tables_sql():
    """Создает SQL для правильного создания sync таблиц"""
    
    print("🔧 Создание SQL для sync таблиц...")
    
    sync_sql = '''-- Правильные SQL схемы для sync таблиц

-- Sync Nodes
CREATE TABLE IF NOT EXISTS sync_nodes (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    last_sync_in TIMESTAMP,
    last_sync_out TIMESTAMP,
    received_packet_no INTEGER,
    sent_packet_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_nodes_code ON sync_nodes(code);

-- Sync Changes
CREATE TABLE IF NOT EXISTS sync_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT REFERENCES sync_nodes(id),
    entity_type TEXT NOT NULL,
    entity_uuid TEXT NOT NULL,
    operation TEXT NOT NULL,
    packet_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id);
CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no);
CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid);
CREATE INDEX IF NOT EXISTS idx_sync_changes_node_operation ON sync_changes(node_id, operation);

-- Object Version History
CREATE TABLE IF NOT EXISTS object_version_history (
    id TEXT PRIMARY KEY,
    entity_uuid TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    source_node_id TEXT REFERENCES sync_nodes(id),
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    serialized_data TEXT NOT NULL,
    conflict_resolution TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_object_version_source_node ON object_version_history(source_node_id);
CREATE INDEX IF NOT EXISTS idx_object_version_arrival_time ON object_version_history(arrival_time);
CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid);
CREATE INDEX IF NOT EXISTS idx_object_version_conflict ON object_version_history(entity_type, entity_uuid, resolved_at);
'''
    
    # Сохраняем SQL в файл для справки
    with open("sync_tables_schema.sql", 'w', encoding='utf-8') as f:
        f.write(sync_sql)
    
    print("✅ SQL схемы сохранены в sync_tables_schema.sql")
    return True

def test_schema_compatibility():
    """Тестирует совместимость схем после исправлений"""
    
    print("🧪 Тестирование совместимости схем...")
    
    try:
        # Импортируем модули для проверки
        sys.path.insert(0, 'src')
        
        # Проверяем, что модели синхронизации импортируются
        from data.models.sync_models import SyncNode, SyncChange, ObjectVersionHistory
        print("✅ Модели синхронизации импортируются успешно")
        
        # Проверяем, что модели SQLAlchemy импортируются
        from data.models.sqlalchemy_models import Person
        print("✅ Модель Person импортируется успешно")
        
        # Проверяем поля модели Person
        person_columns = [column.name for column in Person.__table__.columns]
        if 'full_name' in person_columns:
            print("✅ Модель Person содержит поле full_name")
        else:
            print("❌ Модель Person НЕ содержит поле full_name")
        
        # Проверяем поля модели SyncChange
        sync_change_columns = [column.name for column in SyncChange.__table__.columns]
        if 'node_id' in sync_change_columns:
            print("✅ Модель SyncChange содержит поле node_id")
        else:
            print("❌ Модель SyncChange НЕ содержит поле node_id")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def main():
    """Главная функция"""
    
    print("🚀 Комплексное исправление совместимости схем")
    print("=" * 60)
    
    success = True
    
    # 1. Исправляем Unified Database Manager
    if not fix_unified_database_manager_schemas():
        success = False
    
    # 2. Исправляем initial_data
    if not fix_initial_data_compatibility():
        success = False
    
    # 3. Создаем правильные SQL схемы
    if not create_sync_tables_sql():
        success = False
    
    # 4. Тестируем совместимость
    if not test_schema_compatibility():
        success = False
    
    if success:
        print("\n🎉 Все исправления успешно применены!")
        print("Теперь можно запускать тесты синхронизации.")
    else:
        print("\n⚠️ Некоторые исправления не удались")
    
    return success

if __name__ == "__main__":
    main()
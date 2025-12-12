#!/usr/bin/env python3
"""
Тестовый скрипт для проверки иерархии работ
"""

import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.data.repositories.work_repository import WorkRepository

def test_work_hierarchy():
    """Тест иерархии работ"""
    print("=== Тест иерархии работ ===")
    
    db_manager = DatabaseManager()
    db_manager.initialize()  # Инициализируем базу данных
    work_repo = WorkRepository(db_manager)
    
    # Получаем все работы
    print("\n1. Все работы:")
    all_works = work_repo.find_all()
    for work in all_works[:10]:  # Показываем первые 10
        group_marker = "📁" if work.get('is_group', False) else "  "
        print(f"  {group_marker} ID: {work['id']}, Name: {work['name']}, is_group: {work.get('is_group', 'NOT_SET')}, parent_id: {work.get('parent_id', 'None')}")
    
    print(f"\nВсего работ: {len(all_works)}")
    
    # Получаем корневые работы (parent_id = None)
    print("\n2. Корневые работы (parent_id = None):")
    root_works = work_repo.find_children(None)
    for work in root_works:
        group_marker = "📁" if work.get('is_group', False) else "  "
        print(f"  {group_marker} ID: {work['id']}, Name: {work['name']}, is_group: {work.get('is_group', 'NOT_SET')}")
    
    print(f"\nВсего корневых работ: {len(root_works)}")
    
    # Получаем только группы
    print("\n3. Только группы работ:")
    groups = work_repo.find_groups()
    for work in groups:
        print(f"  📁 ID: {work['id']}, Name: {work['name']}, parent_id: {work.get('parent_id', 'None')}")
    
    print(f"\nВсего групп: {len(groups)}")
    
    # Если есть группы, покажем их детей
    if groups:
        first_group = groups[0]
        print(f"\n4. Дети первой группы (ID: {first_group['id']}, Name: {first_group['name']}):")
        children = work_repo.find_children(first_group['id'])
        for work in children:
            group_marker = "📁" if work.get('is_group', False) else "  "
            print(f"  {group_marker} ID: {work['id']}, Name: {work['name']}, is_group: {work.get('is_group', 'NOT_SET')}")
        
        print(f"\nВсего детей: {len(children)}")

if __name__ == "__main__":
    test_work_hierarchy()
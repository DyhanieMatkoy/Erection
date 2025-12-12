#!/usr/bin/env python3
"""
Скрипт для создания тестовых групп работ
"""

import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.data.repositories.work_repository import WorkRepository
from src.data.models.sqlalchemy_models import Work

def create_test_groups():
    """Создание тестовых групп работ"""
    print("=== Создание тестовых групп работ ===")
    
    db_manager = DatabaseManager()
    db_manager.initialize()
    work_repo = WorkRepository(db_manager)
    
    # Создаем корневые группы
    groups_to_create = [
        {
            'name': 'СТРОИТЕЛЬНЫЕ РАБОТЫ',
            'code': 'СТРОЙ',
            'is_group': True,
            'parent_id': None
        },
        {
            'name': 'ОТДЕЛОЧНЫЕ РАБОТЫ', 
            'code': 'ОТДЕЛ',
            'is_group': True,
            'parent_id': None
        },
        {
            'name': 'ИНЖЕНЕРНЫЕ РАБОТЫ',
            'code': 'ИНЖЕН',
            'is_group': True,
            'parent_id': None
        }
    ]
    
    created_groups = []
    
    for group_data in groups_to_create:
        print(f"\nСоздаем группу: {group_data['name']}")
        
        work = Work()
        work.name = group_data['name']
        work.code = group_data['code']
        work.is_group = group_data['is_group']
        work.parent_id = group_data['parent_id']
        work.price = 0.0
        work.labor_rate = 0.0
        work.marked_for_deletion = False
        
        group_id = work_repo.save(work)
        if group_id:
            print(f"  ✅ Создана группа ID: {group_id}")
            created_groups.append((group_id, group_data['name']))
        else:
            print(f"  ❌ Ошибка создания группы")
    
    # Создаем подгруппы для первой группы
    if created_groups:
        parent_group_id = created_groups[0][0]  # ID первой группы
        parent_group_name = created_groups[0][1]
        
        print(f"\nСоздаем подгруппы для '{parent_group_name}' (ID: {parent_group_id}):")
        
        subgroups = [
            {
                'name': 'Земляные работы',
                'code': 'ЗЕМЛ',
                'is_group': True,
                'parent_id': parent_group_id
            },
            {
                'name': 'Бетонные работы',
                'code': 'БЕТОН',
                'is_group': True,
                'parent_id': parent_group_id
            }
        ]
        
        for subgroup_data in subgroups:
            print(f"  Создаем подгруппу: {subgroup_data['name']}")
            
            work = Work()
            work.name = subgroup_data['name']
            work.code = subgroup_data['code']
            work.is_group = subgroup_data['is_group']
            work.parent_id = subgroup_data['parent_id']
            work.price = 0.0
            work.labor_rate = 0.0
            work.marked_for_deletion = False
            
            subgroup_id = work_repo.save(work)
            if subgroup_id:
                print(f"    ✅ Создана подгруппа ID: {subgroup_id}")
            else:
                print(f"    ❌ Ошибка создания подгруппы")
    
    print("\n=== Проверяем созданные группы ===")
    
    # Проверяем корневые группы
    root_works = work_repo.find_children(None)
    print(f"\nКорневые работы (всего: {len(root_works)}):")
    for work in root_works[:10]:  # Показываем первые 10
        group_marker = "📁" if work.get('is_group', False) else "  "
        print(f"  {group_marker} ID: {work['id']}, Name: {work['name']}")
    
    # Проверяем группы
    groups = work_repo.find_groups()
    print(f"\nВсе группы (всего: {len(groups)}):")
    for work in groups:
        print(f"  📁 ID: {work['id']}, Name: {work['name']}, parent_id: {work.get('parent_id', 'None')}")

if __name__ == "__main__":
    create_test_groups()
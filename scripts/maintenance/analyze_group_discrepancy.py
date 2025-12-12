#!/usr/bin/env python3
"""
Скрипт для анализа расхождений между списком работ и диалогом выбора родителя
"""

import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager

def analyze_group_discrepancy():
    """Анализ расхождений в определении групп"""
    print("=== Анализ расхождений в определении групп ===")
    
    db_manager = DatabaseManager()
    db_manager.initialize()
    cursor = db_manager.get_connection().cursor()
    
    # Найдем работы, которые являются родителями (имеют детей), но не помечены как группы
    print("\n1. Работы, которые являются родителями, но is_group = False:")
    cursor.execute("""
        SELECT DISTINCT p.id, p.name, p.is_group, COUNT(c.id) as children_count
        FROM works p
        INNER JOIN works c ON c.parent_id = p.id
        WHERE p.marked_for_deletion = 0 
        AND c.marked_for_deletion = 0
        AND p.is_group = 0
        GROUP BY p.id, p.name, p.is_group
        ORDER BY children_count DESC, p.name
    """)
    
    parent_not_groups = cursor.fetchall()
    for work in parent_not_groups:
        print(f"  📁❌ ID: {work['id']}, Name: {work['name']}, Children: {work['children_count']}")
    
    print(f"\nВсего таких работ: {len(parent_not_groups)}")
    
    # Найдем работы, которые помечены как группы, но не имеют детей
    print("\n2. Работы, которые помечены как группы (is_group = True), но не имеют детей:")
    cursor.execute("""
        SELECT w.id, w.name, w.is_group
        FROM works w
        LEFT JOIN works c ON c.parent_id = w.id AND c.marked_for_deletion = 0
        WHERE w.marked_for_deletion = 0 
        AND w.is_group = 1
        AND c.id IS NULL
        ORDER BY w.name
    """)
    
    groups_no_children = cursor.fetchall()
    for work in groups_no_children:
        print(f"  📁⚠️  ID: {work['id']}, Name: {work['name']}")
    
    print(f"\nВсего таких работ: {len(groups_no_children)}")
    
    # Найдем конкретно "Благоустройство и малые формы"
    print("\n3. Анализ 'Благоустройство и малые формы':")
    cursor.execute("""
        SELECT id, name, is_group, parent_id
        FROM works 
        WHERE name LIKE '%Благоустройство%' 
        AND marked_for_deletion = 0
    """)
    
    target_works = cursor.fetchall()
    for work in target_works:
        print(f"  ID: {work['id']}, Name: {work['name']}, is_group: {work['is_group']}, parent_id: {work['parent_id']}")
        
        # Проверим детей
        cursor.execute("""
            SELECT COUNT(*) as children_count
            FROM works 
            WHERE parent_id = ? AND marked_for_deletion = 0
        """, (work['id'],))
        children_count = cursor.fetchone()['children_count']
        print(f"    Детей: {children_count}")
        
        if children_count > 0:
            cursor.execute("""
                SELECT id, name 
                FROM works 
                WHERE parent_id = ? AND marked_for_deletion = 0
                LIMIT 5
            """, (work['id'],))
            children = cursor.fetchall()
            print(f"    Примеры детей:")
            for child in children:
                print(f"      - ID: {child['id']}, Name: {child['name']}")
    
    # Статистика
    print(f"\n=== Статистика ===")
    
    cursor.execute("SELECT COUNT(*) as total FROM works WHERE marked_for_deletion = 0")
    total_works = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as groups FROM works WHERE marked_for_deletion = 0 AND is_group = 1")
    marked_groups = cursor.fetchone()['groups']
    
    cursor.execute("""
        SELECT COUNT(DISTINCT parent_id) as actual_groups 
        FROM works 
        WHERE parent_id IS NOT NULL 
        AND parent_id != 0 
        AND marked_for_deletion = 0
    """)
    actual_groups = cursor.fetchone()['actual_groups']
    
    print(f"Всего работ: {total_works}")
    print(f"Помечено как группы (is_group=1): {marked_groups}")
    print(f"Фактически являются родителями: {actual_groups}")
    print(f"Расхождение: {actual_groups - marked_groups}")

if __name__ == "__main__":
    analyze_group_discrepancy()
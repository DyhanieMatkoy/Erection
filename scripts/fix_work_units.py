#!/usr/bin/env python3
"""
Script to fix missing unit_id in works table
"""
import sqlite3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    # Connect to database
    conn = sqlite3.connect('construction.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get available units
    cursor.execute("SELECT id, name FROM units WHERE marked_for_deletion = 0")
    units = {row['name']: row['id'] for row in cursor.fetchall()}
    
    print(f"Available units: {list(units.keys())}")
    
    # Find works without unit_id
    cursor.execute("""
        SELECT id, name, unit, unit_id 
        FROM works 
        WHERE (unit_id IS NULL OR unit_id = 0) 
        AND marked_for_deletion = 0 
        AND is_group = 0
        LIMIT 100
    """)
    
    works_without_units = cursor.fetchall()
    print(f"Found {len(works_without_units)} works without unit_id")
    
    # Unit mapping rules based on work name patterns
    unit_rules = [
        # Exact matches first
        ('шт', ['шт']),
        ('м', ['м']),
        ('м2', ['м2', 'кв.м', 'кв м']),
        ('м3', ['м3', 'куб.м', 'куб м']),
        ('кг', ['кг']),
        ('т', ['т', 'тн']),
        
        # Pattern matches
        ('шт', ['врезка', 'установка', 'монтаж', 'демонтаж', 'замена', 'ремонт']),
        ('м', ['прокладка труб', 'труб', 'трубопровод', 'кабель', 'провод']),
        ('м2', ['покрытие', 'облицовка', 'штукатурка', 'окраска', 'площадь']),
        ('м3', ['бетон', 'раствор', 'засыпка', 'выемка', 'объем']),
    ]
    
    updated_count = 0
    
    for work in works_without_units:
        work_name = work['name'].lower()
        unit_id = None
        
        # Try to find matching unit
        for unit_name, patterns in unit_rules:
            if unit_name in units:
                for pattern in patterns:
                    if pattern in work_name:
                        unit_id = units[unit_name]
                        break
                if unit_id:
                    break
        
        # Default to 'шт' if no specific unit found
        if not unit_id and 'шт' in units:
            unit_id = units['шт']
        
        if unit_id:
            cursor.execute(
                "UPDATE works SET unit_id = ? WHERE id = ?",
                (unit_id, work['id'])
            )
            updated_count += 1
            print(f"Updated work {work['id']}: '{work['name'][:50]}...' -> {[k for k, v in units.items() if v == unit_id][0]}")
    
    conn.commit()
    print(f"\nUpdated {updated_count} works with unit_id")
    
    # Show statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_works,
            COUNT(unit_id) as works_with_unit_id,
            COUNT(*) - COUNT(unit_id) as works_without_unit_id
        FROM works 
        WHERE marked_for_deletion = 0 AND is_group = 0
    """)
    
    stats = cursor.fetchone()
    print(f"\nStatistics:")
    print(f"Total works: {stats['total_works']}")
    print(f"Works with unit_id: {stats['works_with_unit_id']}")
    print(f"Works without unit_id: {stats['works_without_unit_id']}")
    
    conn.close()

if __name__ == "__main__":
    main()
"""Просмотр импортированных работ"""
import sqlite3
import sys


def view_works(db_path: str = 'construction.db', group_name: str = None):
    """Просмотр работ из базы данных"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if group_name:
        # Показываем работы конкретной группы
        cursor.execute(
            """SELECT w.id, w.name, w.unit, w.price
               FROM works w
               JOIN works g ON w.parent_id = g.id
               WHERE g.name = ? AND w.marked_for_deletion = 0
               ORDER BY w.name""",
            (group_name,)
        )
        works = cursor.fetchall()
        
        if not works:
            print(f"\nГруппа '{group_name}' не найдена или пуста")
            conn.close()
            return
        
        print(f"\n{'='*80}")
        print(f"Группа: {group_name}")
        print(f"{'='*80}")
        print(f"{'ID':<6} {'Наименование':<45} {'Цена':<12} {'Ед.изм.':<10}")
        print(f"{'-'*80}")
        
        for work in works:
            price_str = f"{work['price']:.2f}" if work['price'] else "0.00"
            unit_str = work['unit'] or ""
            print(f"{work['id']:<6} {work['name']:<45} {price_str:<12} {unit_str:<10}")
        
        print(f"{'='*80}")
        print(f"Всего работ: {len(works)}\n")
    
    else:
        # Показываем все группы
        cursor.execute(
            """SELECT id, name, 
                      (SELECT COUNT(*) FROM works w WHERE w.parent_id = g.id) as work_count
               FROM works g
               WHERE parent_id IS NULL AND marked_for_deletion = 0
               ORDER BY name"""
        )
        groups = cursor.fetchall()
        
        if not groups:
            print("\nГруппы работ не найдены")
            conn.close()
            return
        
        print(f"\n{'='*80}")
        print(f"Группы работ")
        print(f"{'='*80}")
        print(f"{'ID':<6} {'Название группы':<50} {'Кол-во работ':<15}")
        print(f"{'-'*80}")
        
        total_works = 0
        for group in groups:
            print(f"{group['id']:<6} {group['name']:<50} {group['work_count']:<15}")
            total_works += group['work_count']
        
        print(f"{'='*80}")
        print(f"Всего групп: {len(groups)}, работ: {total_works}\n")
    
    conn.close()


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Просмотр импортированных работ')
    parser.add_argument('--group', '-g', help='Название группы для просмотра работ')
    parser.add_argument('--db', default='construction.db', help='Путь к базе данных')
    
    args = parser.parse_args()
    
    view_works(args.db, args.group)


if __name__ == '__main__':
    main()

"""Очистка дубликатов работ"""
import sqlite3


def clean_duplicates(db_path: str = 'construction.db', dry_run: bool = True):
    """
    Удаляет дубликаты работ, оставляя самую раннюю запись
    
    Args:
        db_path: Путь к базе данных
        dry_run: Если True, только показывает дубликаты без удаления
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Находим дубликаты
    cursor.execute("""
        SELECT name, parent_id, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM works
        WHERE marked_for_deletion = 0
        GROUP BY name, parent_id
        HAVING count > 1
        ORDER BY name
    """)
    
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("\nДубликаты не найдены!")
        conn.close()
        return
    
    print(f"\n{'='*80}")
    print(f"Найдено групп дубликатов: {len(duplicates)}")
    print(f"{'='*80}\n")
    
    total_to_delete = 0
    
    for name, parent_id, count, ids in duplicates:
        id_list = [int(x) for x in ids.split(',')]
        to_delete = id_list[1:]  # Удаляем все кроме первого
        total_to_delete += len(to_delete)
        
        parent_name = "Без группы"
        if parent_id:
            cursor.execute("SELECT name FROM works WHERE id = ?", (parent_id,))
            result = cursor.fetchone()
            if result:
                parent_name = result[0]
        
        print(f"Работа: {name}")
        print(f"  Группа: {parent_name}")
        print(f"  Дубликатов: {count}")
        print(f"  ID для удаления: {to_delete}")
        print()
        
        if not dry_run:
            # Удаляем дубликаты
            placeholders = ','.join('?' * len(to_delete))
            cursor.execute(
                f"DELETE FROM works WHERE id IN ({placeholders})",
                to_delete
            )
    
    if dry_run:
        print(f"{'='*80}")
        print(f"РЕЖИМ ПРОСМОТРА: Будет удалено {total_to_delete} записей")
        print(f"Для реального удаления запустите с флагом --delete")
        print(f"{'='*80}\n")
    else:
        conn.commit()
        print(f"{'='*80}")
        print(f"Удалено {total_to_delete} дубликатов")
        print(f"{'='*80}\n")
    
    conn.close()


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Очистка дубликатов работ')
    parser.add_argument('--delete', action='store_true', 
                       help='Реально удалить дубликаты (по умолчанию только просмотр)')
    parser.add_argument('--db', default='construction.db', 
                       help='Путь к базе данных')
    
    args = parser.parse_args()
    
    if args.delete:
        confirm = input("Вы уверены, что хотите удалить дубликаты? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Отменено")
            return
    
    clean_duplicates(args.db, dry_run=not args.delete)


if __name__ == '__main__':
    main()

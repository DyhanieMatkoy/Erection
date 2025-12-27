"""Инструмент импорта работ из CSV файла"""
import csv
import sqlite3
from typing import Dict, List, Tuple


class WorksImporter:
    """Импортер работ из CSV"""
    
    def __init__(self, db_path: str = 'construction.db'):
        self.db_path = db_path
        self.work_groups: Dict[str, int] = {}  # Кэш групп работ
        self.unit_cache: Dict[str, int] = {}   # Кэш единиц измерения
    
    def parse_price(self, price_str: str) -> float:
        """Парсит цену из строки, удаляя текст"""
        try:
            # Убираем все нецифровые символы кроме точки и запятой
            clean_price = ''.join(c for c in price_str if c.isdigit() or c in '.,')
            if not clean_price:
                return 0.0
            # Заменяем запятую на точку
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, AttributeError):
            return 0.0
    
    def parse_unit(self, unit_str: str) -> str:
        """Парсит единицу измерения, убирая лишний текст"""
        if not unit_str:
            return ""
        
        # Если есть "руб./", берем то, что после слэша
        if 'руб./' in unit_str:
            unit = unit_str.split('руб./')[1].strip()
        elif 'руб/' in unit_str:
            unit = unit_str.split('руб/')[1].strip()
        else:
            # Убираем "руб." если это просто "руб."
            unit = unit_str.replace('руб.', '').strip()
        
        # Удаляем все пробелы и лишние слэши
        unit = unit.replace(' ', '').lstrip('/')
        
        # Если осталось пусто или "бесплатно", возвращаем пустую строку
        if not unit or unit.lower() == 'бесплатно':
            return ""
        
        return unit
    
    def parse_hierarchy_path(self, hierarchy_str: str, separator: str = ' > ') -> List[str]:
        """Парсит путь иерархии из строки"""
        if not hierarchy_str:
            return []
        
        # Пробуем разные разделители
        parts = hierarchy_str.split(separator)
        if len(parts) <= 1:
            # Пробуем альтернативные разделители
            alt_separators = [' | ', ' / ', '->', '|', '/', '|']
            for alt_sep in alt_separators:
                parts = hierarchy_str.split(alt_sep)
                if len(parts) > 1:
                    break
        
        # Очищаем части и удаляем пустые строки
        return [part.strip() for part in parts if part.strip()]
    
    def get_or_create_hierarchy(self, conn: sqlite3.Connection, hierarchy_parts: List[str], 
                               root_parent_id: int = None) -> int:
        """Создает или получает уровни иерархии и возвращает финальный parent_id"""
        current_parent_id = root_parent_id
        cursor = conn.cursor()
        
        for part in hierarchy_parts:
            # Проверяем кэш
            cache_key = f"{current_parent_id}:{part}"
            if cache_key in self.work_groups:
                current_parent_id = self.work_groups[cache_key]
                continue
            
            # Проверяем существование уровня
            cursor.execute(
                "SELECT id FROM works WHERE name = ? AND parent_id IS ? AND marked_for_deletion = 0",
                (part, current_parent_id)
            )
            result = cursor.fetchone()
            
            if result:
                current_parent_id = result[0]
            else:
                # Создаем новый уровень (группу)
                cursor.execute(
                    """INSERT INTO works (name, parent_id, marked_for_deletion, is_group)
                       VALUES (?, ?, 0, 1)""",
                    (part, current_parent_id)
                )
                current_parent_id = cursor.lastrowid
                conn.commit()
            
            # Кэшируем результат
            self.work_groups[cache_key] = current_parent_id
        
        return current_parent_id
    
    def get_or_create_unit(self, cursor, conn: sqlite3.Connection, unit_str: str) -> int:
        """Получает или создает единицу измерения"""
        if not unit_str:
            return None
        
        if unit_str in self.unit_cache:
            return self.unit_cache[unit_str]
        
        cursor.execute(
            "SELECT id FROM units WHERE name = ? AND marked_for_deletion = 0",
            (unit_str,)
        )
        result = cursor.fetchone()
        
        if result:
            unit_id = result[0]
        else:
            # Создаем новую единицу
            cursor.execute(
                "INSERT INTO units (name, description, marked_for_deletion) VALUES (?, ?, 0)",
                (unit_str, f"Автоматически создана при импорте из CSV")
            )
            unit_id = cursor.lastrowid
            conn.commit()
        
        self.unit_cache[unit_str] = unit_id
        return unit_id
    
    def get_or_create_work_group(self, group_name: str, conn: sqlite3.Connection) -> int:
        """Получает или создает группу работ"""
        if group_name in self.work_groups:
            return self.work_groups[group_name]
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли группа
        cursor.execute(
            "SELECT id FROM works WHERE name = ? AND parent_id IS NULL",
            (group_name,)
        )
        result = cursor.fetchone()
        
        if result:
            group_id = result[0]
        else:
            # Создаем новую группу
            cursor.execute(
                """INSERT INTO works (name, unit, price, labor_rate, parent_id, marked_for_deletion)
                   VALUES (?, '', 0, 0, NULL, 0)""",
                (group_name,)
            )
            group_id = cursor.lastrowid
            conn.commit()
        
        self.work_groups[group_name] = group_id
        return group_id
    
    def work_exists(self, name: str, parent_id: int, conn: sqlite3.Connection) -> bool:
        """Проверяет, существует ли работа с таким именем в группе"""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM works WHERE name = ? AND parent_id = ?",
            (name, parent_id)
        )
        return cursor.fetchone() is not None
    
    def import_from_csv(self, csv_path: str, skip_existing: bool = True) -> Tuple[int, int, List[str]]:
        """
        Импортирует работы из CSV файла с поддержкой иерархии и справочника единиц
        
        Args:
            csv_path: Путь к CSV файлу
            skip_existing: Пропускать существующие работы (True) или обновлять (False)
        
        Returns:
            Tuple[added_count, skipped_count, errors]
        """
        added = 0
        skipped = 0
        errors = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, т.к. 1 - заголовок
                    try:
                        work_type = (row.get('Тип работ') or '').strip()
                        work_name = (row.get('Наименование работы') or '').strip()
                        price_str = (row.get('Цена') or '0').strip()
                        unit_str = (row.get('Единица измерения') or '').strip()
                        hierarchy_str = (row.get('Иерархия') or '').strip()
                        
                        if not work_name:
                            errors.append(f"Строка {row_num}: Пустое наименование работы")
                            continue
                        
                        # Определяем parent_id с поддержкой иерархии
                        parent_id = None
                        
                        # Приоритет: Иерархия > Тип работ
                        if hierarchy_str:
                            # Парсим и создаем путь иерархии
                            hierarchy_parts = self.parse_hierarchy_path(hierarchy_str)
                            if hierarchy_parts:
                                parent_id = self.get_or_create_hierarchy(conn, hierarchy_parts)
                        elif work_type:
                            # Legacy поддержка: создаем группу одного уровня
                            parent_id = self.get_or_create_work_group(work_type, conn)
                        
                        # Проверяем существование
                        if skip_existing and self.work_exists(work_name, parent_id, conn):
                            skipped += 1
                            continue
                        
                        # Парсим данные
                        price = self.parse_price(price_str)
                        unit_id = self.get_or_create_unit(cursor, conn, unit_str)
                        
                        # Добавляем работу
                        if skip_existing:
                            cursor.execute(
                                """INSERT INTO works (name, unit_id, price, labor_rate, parent_id, marked_for_deletion)
                                   VALUES (?, ?, ?, 0, ?, 0)""",
                                (work_name, unit_id, price, parent_id)
                            )
                        else:
                            # Обновляем если существует
                            cursor.execute(
                                """INSERT OR REPLACE INTO works (name, unit_id, price, labor_rate, parent_id, marked_for_deletion)
                                   VALUES (?, ?, ?, 0, ?, 0)""",
                                (work_name, unit_id, price, parent_id)
                            )
                        
                        conn.commit()
                        added += 1
                    
                    except Exception as e:
                        errors.append(f"Строка {row_num}: {str(e)}")
                        continue
        
        except FileNotFoundError:
            errors.append(f"Файл не найден: {csv_path}")
        except Exception as e:
            errors.append(f"Ошибка чтения файла: {str(e)}")
        finally:
            conn.close()
        
        return added, skipped, errors


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Импорт работ из CSV файла')
    parser.add_argument('csv_file', help='Путь к CSV файлу')
    parser.add_argument('--update', action='store_true', 
                       help='Обновлять существующие работы вместо пропуска')
    
    args = parser.parse_args()
    
    print(f"Импорт работ из файла: {args.csv_file}")
    print("-" * 60)
    
    importer = WorksImporter()
    added, skipped, errors = importer.import_from_csv(
        args.csv_file, 
        skip_existing=not args.update
    )
    
    print(f"\nРезультаты импорта:")
    print(f"  Добавлено работ: {added}")
    print(f"  Пропущено работ: {skipped}")
    
    if errors:
        print(f"\nОшибки ({len(errors)}):")
        for error in errors[:10]:  # Показываем первые 10 ошибок
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... и еще {len(errors) - 10} ошибок")
    else:
        print("\nИмпорт завершен успешно!")


if __name__ == '__main__':
    main()

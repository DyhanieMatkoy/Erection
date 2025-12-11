"""Инструмент импорта работ из CSV файла"""
import csv
import sqlite3
from typing import Dict, List, Tuple


class WorksImporter:
    """Импортер работ из CSV"""
    
    def __init__(self, db_path: str = 'construction.db'):
        self.db_path = db_path
        self.work_groups: Dict[str, int] = {}  # Кэш групп работ
    
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
        Импортирует работы из CSV файла
        
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
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, т.к. 1 - заголовок
                    try:
                        work_type = (row.get('Тип работ') or '').strip()
                        work_name = (row.get('Наименование работы') or '').strip()
                        price_str = (row.get('Цена') or '0').strip()
                        unit_str = (row.get('Единица измерения') or '').strip()
                        
                        if not work_name:
                            errors.append(f"Строка {row_num}: Пустое наименование работы")
                            continue
                        
                        # Получаем или создаем группу
                        parent_id = self.get_or_create_work_group(work_type, conn) if work_type else None
                        
                        # Проверяем существование
                        if skip_existing and self.work_exists(work_name, parent_id, conn):
                            skipped += 1
                            continue
                        
                        # Парсим данные
                        price = self.parse_price(price_str)
                        unit = self.parse_unit(unit_str)
                        
                        # Добавляем работу
                        cursor = conn.cursor()
                        
                        if skip_existing:
                            cursor.execute(
                                """INSERT INTO works (name, unit, price, labor_rate, parent_id, marked_for_deletion)
                                   VALUES (?, ?, ?, 0, ?, 0)""",
                                (work_name, unit, price, parent_id)
                            )
                        else:
                            # Обновляем если существует
                            cursor.execute(
                                """INSERT OR REPLACE INTO works (name, unit, price, labor_rate, parent_id, marked_for_deletion)
                                   VALUES (?, ?, ?, 0, ?, 0)""",
                                (work_name, unit, price, parent_id)
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

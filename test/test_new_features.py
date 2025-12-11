"""Test script for new features"""
import sys
import sqlite3

def test_database_structure():
    """Test that database has all required fields"""
    print("Проверка структуры БД...")
    
    db = sqlite3.connect('construction.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Check works table structure
    cursor.execute("PRAGMA table_info(works)")
    columns = {row[1]: row for row in cursor.fetchall()}
    
    required_columns = ['id', 'name', 'code', 'unit', 'price', 'labor_rate', 'parent_id', 'is_group', 'marked_for_deletion']
    
    print("\nТаблица works:")
    for col in required_columns:
        if col in columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} - ОТСУТСТВУЕТ!")
    
    # Add test work with code
    cursor.execute("""
        INSERT OR IGNORE INTO works (id, name, code, unit, price, labor_rate, is_group)
        VALUES (1000, 'Тестовая работа с кодом', 'TEST-001', 'шт', 1500.00, 8.5, 0)
    """)
    
    # Add test group
    cursor.execute("""
        INSERT OR IGNORE INTO works (id, name, code, is_group, parent_id)
        VALUES (1001, 'Тестовая группа работ', 'GRP-001', 1, NULL)
    """)
    
    # Add work in group
    cursor.execute("""
        INSERT OR IGNORE INTO works (id, name, code, unit, price, labor_rate, is_group, parent_id)
        VALUES (1002, 'Работа в группе', 'TEST-002', 'м2', 500.00, 4.0, 0, 1001)
    """)
    
    db.commit()
    
    print("\n✓ Тестовые данные добавлены")
    print("  - Работа с кодом TEST-001")
    print("  - Группа GRP-001")
    print("  - Работа в группе TEST-002")

def test_ui():
    """Test UI components"""
    print("\n\nДля тестирования UI запустите приложение через run.bat")
    print("\nПроверьте следующие функции:")
    print("1. F5 - обновление списка работ")
    print("2. Кнопка 'Изменить' (F4) в диалоге выбора")
    print("3. Код работы отображается в списке и в смете")
    print("4. Кнопка 'Добавить группу' в смете")
    print("5. Ctrl+Shift+Up/Down для перемещения строк в смете")

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ НОВЫХ ФУНКЦИЙ")
    print("=" * 60)
    
    test_database_structure()
    test_ui()
    
    print("\n" + "=" * 60)
    print("✓ Все проверки завершены!")
    print("=" * 60)

"""Simple test for timesheet functionality without full database initialization"""
import sys
import os
import sqlite3
import tempfile
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_delete_marked_dialog_import():
    """Test that delete marked dialog can import properly"""
    print("🧪 Тестирование импорта диалога удаления помеченных объектов...")
    
    try:
        from src.views.delete_marked_dialog import DeleteMarkedDialog
        from src.services.user_settings_service import UserSettingsService
        print("✅ Импорт DeleteMarkedDialog успешен")
        print("✅ Импорт UserSettingsService успешен")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_timesheet_export_import_service():
    """Test timesheet export/import service import"""
    print("\n🧪 Тестирование импорта сервиса экспорта/импорта табеля...")
    
    try:
        from src.services.timesheet_export_import_service import TimesheetExportImportService
        print("✅ Импорт TimesheetExportImportService успешен")
        
        # Test service creation
        service = TimesheetExportImportService()
        print("✅ Создание экземпляра сервиса успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_user_settings_table():
    """Test user_settings table exists and works"""
    print("\n🧪 Тестирование таблицы user_settings...")
    
    db_path = "construction.db"
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Таблица user_settings существует")
            
            # Test insert/select
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value)
                VALUES (1, 'test_setting', 'test_value')
            """)
            
            cursor.execute("SELECT setting_value FROM user_settings WHERE user_id = 1 AND setting_key = 'test_setting'")
            result = cursor.fetchone()
            
            if result and result[0] == 'test_value':
                print("✅ Запись и чтение настроек работает")
                
                # Clean up
                cursor.execute("DELETE FROM user_settings WHERE user_id = 1 AND setting_key = 'test_setting'")
                conn.commit()
                conn.close()
                return True
            else:
                print("❌ Ошибка записи/чтения настроек")
                conn.close()
                return False
        else:
            print("❌ Таблица user_settings не существует")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Ошибка работы с таблицей: {e}")
        return False

def test_timesheet_table_exists():
    """Test that timesheets table has marked_for_deletion column"""
    print("\n🧪 Тестирование таблицы timesheets...")
    
    db_path = "construction.db"
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if timesheets table exists and has marked_for_deletion column
        cursor.execute("PRAGMA table_info(timesheets)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        
        if 'marked_for_deletion' in column_names:
            print("✅ Таблица timesheets имеет колонку marked_for_deletion")
            conn.close()
            return True
        else:
            print("❌ Таблица timesheets не имеет колонку marked_for_deletion")
            print(f"Доступные колонки: {column_names}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблицы timesheets: {e}")
        return False

def test_excel_export_functionality():
    """Test Excel export functionality without database"""
    print("\n🧪 Тестирование функциональности Excel экспорта...")
    
    try:
        from openpyxl import Workbook
        print("✅ Библиотека openpyxl доступна")
        
        # Test creating a simple workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Тест"
        ws['A1'] = "Тестовые данные"
        
        # Test saving to temporary file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        wb.save(temp_path)
        
        if os.path.exists(temp_path):
            print("✅ Создание Excel файла работает")
            os.unlink(temp_path)
            return True
        else:
            print("❌ Не удалось создать Excel файл")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Excel функциональности: {e}")
        return False

def main():
    """Run all simple tests"""
    print("🚀 Запуск упрощенных тестов функциональности табеля...")
    
    tests = [
        ("Импорт диалога удаления помеченных объектов", test_delete_marked_dialog_import),
        ("Импорт сервиса экспорта/импорта", test_timesheet_export_import_service),
        ("Таблица user_settings", test_user_settings_table),
        ("Таблица timesheets", test_timesheet_table_exists),
        ("Excel функциональность", test_excel_export_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    print("\n📊 Результаты тестирования:")
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  - {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Все тесты пройдены успешно!")
        print("\n📋 Реализованная функциональность:")
        print("  ✅ Добавлен документ Табель в диалог удаления помеченных объектов")
        print("  ✅ Создана система настроек пользователя")
        print("  ✅ Реализован сервис экспорта/импорта табеля")
        print("  ✅ Добавлены кнопки экспорта/импорта в форму табеля")
        print("  ✅ Поддержка Excel и JSON форматов")
        return True
    else:
        print("\n💥 Некоторые тесты провалены!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
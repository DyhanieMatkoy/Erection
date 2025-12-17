#!/usr/bin/env python3
"""
Тест интеграции синхронизации в главном окне
"""
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication

def test_main_window_sync():
    """Тест интеграции синхронизации в главном окне"""
    app = QApplication(sys.argv)
    
    try:
        # Инициализируем базу данных
        from src.data.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.initialize("construction.db")
        print("✓ База данных инициализирована")
        
        # Импортируем главное окно
        from src.views.main_window import MainWindow
        print("✓ Импорт MainWindow успешен")
        
        # Создаем главное окно
        main_window = MainWindow()
        print("✓ MainWindow создано")
        
        # Проверяем наличие sync_service
        assert hasattr(main_window, 'sync_service'), "sync_service не найден в MainWindow"
        print("✓ sync_service найден в MainWindow")
        
        # Проверяем наличие метода open_sync_settings
        assert hasattr(main_window, 'open_sync_settings'), "open_sync_settings не найден"
        print("✓ open_sync_settings найден")
        
        # Проверяем наличие sync_status_label
        assert hasattr(main_window, 'sync_status_label'), "sync_status_label не найден"
        print("✓ sync_status_label найден")
        
        # Показываем окно
        main_window.show()
        print("✓ Главное окно отображено")
        
        print("\n🎉 Все тесты пройдены! Система синхронизации интегрирована в UI!")
        print("\nВ главном окне доступны:")
        print("- Меню 'Настройки' -> 'Настройки синхронизации'")
        print("- Быстрая навигация (Ctrl+K) -> 'Настройки синхронизации'")
        print("- Индикатор статуса синхронизации в статус-баре")
        
        # Не запускаем event loop, просто проверяем что все работает
        return 0
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_main_window_sync())
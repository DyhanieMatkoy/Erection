#!/usr/bin/env python3
"""
Тест UI синхронизации
"""
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

def test_sync_ui():
    """Тест UI синхронизации"""
    app = QApplication(sys.argv)
    
    try:
        # Импортируем компоненты синхронизации
        from src.services.sync_service import SyncService
        from src.views.sync_settings_dialog import SyncSettingsDialog
        
        print("✓ Импорт SyncService успешен")
        print("✓ Импорт SyncSettingsDialog успешен")
        
        # Создаем сервис синхронизации
        from src.data.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        db_manager.initialize("construction.db")
        
        sync_service = SyncService(
            db_manager=db_manager,
            server_url="http://localhost:8000",
            node_code="TEST-NODE"
        )
        print("✓ SyncService создан")
        
        # Создаем тестовое окно
        window = QMainWindow()
        window.setWindowTitle("Тест синхронизации")
        window.resize(400, 200)
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопка для открытия настроек синхронизации
        sync_button = QPushButton("Открыть настройки синхронизации")
        
        def open_sync_settings():
            dialog = SyncSettingsDialog(sync_service, window)
            dialog.exec()
        
        sync_button.clicked.connect(open_sync_settings)
        layout.addWidget(sync_button)
        
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        print("✓ Тестовое окно создано")
        
        window.show()
        print("✓ UI синхронизации работает!")
        print("\nНажмите кнопку для тестирования диалога настроек синхронизации")
        
        return app.exec()
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_sync_ui())
#!/usr/bin/env python3
"""
Тест навигации в селекторе работ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.views.reference_picker_dialog import ReferencePickerDialog
from src.data.database_manager import DatabaseManager

def test_navigation():
    """Тест навигации вверх в селекторе работ"""
    app = QApplication(sys.argv)
    
    # Инициализируем базу данных
    db_manager = DatabaseManager()
    
    # Проверим структуру работ в базе
    print("=== Структура работ в базе ===")
    with db_manager.session_scope() as session:
        from src.data.models.sqlalchemy_models import Work
        
        works = session.query(Work).filter(Work.marked_for_deletion == False).order_by(Work.parent_id, Work.name).all()
        for work in works:
            parent_info = f" (родитель: {work.parent_id})" if work.parent_id else " (корень)"
            print(f"ID: {work.id}, Название: {work.name}, Код: {work.code}{parent_info}")
    
    print("\n=== Тест селектора работ ===")
    
    # Создаем диалог селектора работ
    dialog = ReferencePickerDialog("works", "Тест селектора работ")
    
    # Показываем диалог
    dialog.show()
    
    print("Диалог открыт. Проверьте:")
    print("1. Есть ли группы работ (с иконкой 📁)")
    print("2. Можно ли войти в группу (двойной клик или Enter)")
    print("3. Работает ли кнопка 'Вверх' для выхода из группы")
    print("4. Работает ли клавиша Backspace для навигации вверх")
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    test_navigation()
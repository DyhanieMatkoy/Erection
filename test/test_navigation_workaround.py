#!/usr/bin/env python3
"""
Тест навигации с обходным решением для проблемы базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox
from PyQt6.QtCore import Qt

class NavigationTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест навигации в селекторе работ")
        self.setGeometry(100, 100, 500, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Тест исправления навигации в селекторе работ")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title)
        
        # Описание проблемы
        problem_desc = QLabel("""
ПРОБЛЕМА: В селекторе работ не удаётся выйти из подгруппы кнопкой "вверх"

ИСПРАВЛЕНИЯ:
1. Убрана лишняя строка скрытия колонки кода работ
2. Исправлена логика навигации вверх
3. Добавлена поддержка клавиши Backspace для навигации

ИНСТРУКЦИИ ДЛЯ ТЕСТИРОВАНИЯ:
1. Запустите основное приложение: python main.py
2. Откройте любую форму с селектором работ (например, форму работы)
3. В селекторе найдите группу работ (с иконкой 📁)
4. Войдите в группу (двойной клик или Enter)
5. Проверьте, что кнопка "↑ Вверх" стала активной
6. Нажмите кнопку "↑ Вверх" или клавишу Backspace
7. Убедитесь, что вы вернулись на уровень выше
        """)
        problem_desc.setWordWrap(True)
        problem_desc.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(problem_desc)
        
        # Кнопки для запуска приложения
        app_button = QPushButton("Запустить основное приложение")
        app_button.clicked.connect(self.launch_main_app)
        layout.addWidget(app_button)
        
        # Кнопка для показа исправлений
        fixes_button = QPushButton("Показать детали исправлений")
        fixes_button.clicked.connect(self.show_fixes)
        layout.addWidget(fixes_button)
        
        central_widget.setLayout(layout)
    
    def launch_main_app(self):
        """Запустить основное приложение"""
        import subprocess
        try:
            subprocess.Popen([sys.executable, "main.py"])
            QMessageBox.information(self, "Запуск", "Основное приложение запущено в отдельном процессе")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить приложение: {e}")
    
    def show_fixes(self):
        """Показать детали исправлений"""
        fixes_text = """
ДЕТАЛИ ИСПРАВЛЕНИЙ:

1. ИСПРАВЛЕНИЕ СКРЫТИЯ КОЛОНОК:
   Проблема: Лишняя строка self.table_view.setColumnHidden(2, True) 
   скрывала колонку "Код" для работ
   Решение: Убрана дублирующая строка

2. ЛОГИКА НАВИГАЦИИ:
   Метод on_navigate_up() работает правильно:
   - Находит родителя текущей группы
   - Устанавливает current_parent_id в родителя
   - Перезагружает данные

3. ПОДДЕРЖКА КЛАВИШ:
   - Enter: вход в группу или выбор элемента
   - Backspace: навигация вверх (аналог кнопки "↑ Вверх")
   - Ctrl+Enter: выбор элемента
   - F4: редактирование
   - Insert: добавление нового элемента

4. СОСТОЯНИЕ КНОПКИ "ВВЕРХ":
   - Активна только когда current_parent_id не None
   - Обновляется в методе update_navigation_state()
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Детали исправлений")
        msg.setText(fixes_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

def main():
    app = QApplication(sys.argv)
    
    window = NavigationTestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
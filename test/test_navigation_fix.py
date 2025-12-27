#!/usr/bin/env python3
"""
Тест исправления навигации в селекторе работ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from src.views.reference_picker_dialog import ReferencePickerDialog

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест селектора работ - Исправление навигации")
        self.setGeometry(100, 100, 400, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Инструкции
        instructions = QLabel("""
Тест исправления навигации в селекторе работ:

1. Нажмите кнопку ниже для открытия селектора
2. Найдите группу работ (с иконкой 📁)
3. Войдите в группу (двойной клик или Enter)
4. Проверьте, что кнопка "↑ Вверх" активна
5. Нажмите кнопку "↑ Вверх" или клавишу Backspace
6. Убедитесь, что вы вернулись на уровень выше
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Кнопка для открытия селектора
        self.open_button = QPushButton("Открыть селектор работ")
        self.open_button.clicked.connect(self.open_selector)
        layout.addWidget(self.open_button)
        
        # Результат
        self.result_label = QLabel("Результат: Ожидание теста...")
        layout.addWidget(self.result_label)
        
        central_widget.setLayout(layout)
    
    def open_selector(self):
        """Открыть селектор работ"""
        try:
            dialog = ReferencePickerDialog("works", "Тест навигации - Селектор работ", self)
            result = dialog.exec()
            
            if result:
                selected_id, selected_value = dialog.get_selected()
                self.result_label.setText(f"Выбрано: ID={selected_id}, Название={selected_value}")
            else:
                self.result_label.setText("Результат: Отменено пользователем")
                
        except Exception as e:
            self.result_label.setText(f"Ошибка: {str(e)}")
            print(f"Ошибка при открытии селектора: {e}")

def main():
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
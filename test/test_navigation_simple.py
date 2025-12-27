#!/usr/bin/env python3
"""
Простой тест навигации в селекторе работ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from src.views.reference_picker_dialog import ReferencePickerDialog

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест селектора работ")
        self.setGeometry(100, 100, 300, 100)
        
        layout = QVBoxLayout()
        
        button = QPushButton("Открыть селектор работ")
        button.clicked.connect(self.open_selector)
        layout.addWidget(button)
        
        self.setLayout(layout)
    
    def open_selector(self):
        """Открыть селектор работ"""
        try:
            dialog = ReferencePickerDialog("works", "Тест селектора работ", self)
            dialog.exec()
        except Exception as e:
            print(f"Ошибка при открытии селектора: {e}")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("Нажмите кнопку для открытия селектора работ")
    print("В селекторе проверьте:")
    print("1. Есть ли группы работ (с иконкой 📁)")
    print("2. Можно ли войти в группу (двойной клик или Enter)")
    print("3. Работает ли кнопка 'Вверх' для выхода из группы")
    print("4. Работает ли клавиша Backspace для навигации вверх")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
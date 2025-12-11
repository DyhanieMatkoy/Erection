"""Test date input from keyboard"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QDateEdit, QLabel
from PyQt6.QtCore import QDate

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Тест ввода даты")
layout = QVBoxLayout()

label = QLabel("Попробуйте ввести дату с клавиатуры (формат: ДД.ММ.ГГГГ):")
layout.addWidget(label)

date_edit = QDateEdit()
date_edit.setCalendarPopup(True)
date_edit.setDisplayFormat("dd.MM.yyyy")
date_edit.setDate(QDate.currentDate())
layout.addWidget(date_edit)

info_label = QLabel("Можно:\n- Вводить дату с клавиатуры\n- Использовать стрелки вверх/вниз для изменения\n- Открыть календарь кнопкой справа")
layout.addWidget(info_label)

window.setLayout(layout)
window.resize(400, 150)
window.show()

sys.exit(app.exec())

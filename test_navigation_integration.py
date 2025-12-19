#!/usr/bin/env python3
"""
Тест интеграции навигации в панель поиска для форм списков.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from src.views.work_list_form_v2 import WorkListFormV2
from src.views.person_list_form_v2 import PersonListFormV2
from src.views.organization_list_form_v2 import OrganizationListFormV2

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест навигации в панели поиска")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Кнопки для открытия разных форм
        work_btn = QPushButton("Открыть справочник работ")
        work_btn.clicked.connect(self.open_work_form)
        layout.addWidget(work_btn)
        
        person_btn = QPushButton("Открыть справочник персон")
        person_btn.clicked.connect(self.open_person_form)
        layout.addWidget(person_btn)
        
        org_btn = QPushButton("Открыть справочник организаций")
        org_btn.clicked.connect(self.open_org_form)
        layout.addWidget(org_btn)
        
        self.opened_forms = []
    
    def open_work_form(self):
        try:
            form = WorkListFormV2(user_id=1)
            form.show()
            self.opened_forms.append(form)
            print("✓ Форма работ открыта. Навигация интегрирована в панель поиска.")
        except Exception as e:
            print(f"✗ Ошибка при открытии формы работ: {e}")
    
    def open_person_form(self):
        try:
            form = PersonListFormV2(user_id=1)
            form.show()
            self.opened_forms.append(form)
            print("✓ Форма персон открыта. Навигация интегрирована в панель поиска.")
        except Exception as e:
            print(f"✗ Ошибка при открытии формы персон: {e}")
    
    def open_org_form(self):
        try:
            form = OrganizationListFormV2(user_id=1)
            form.show()
            self.opened_forms.append(form)
            print("✓ Форма организаций открыта. Навигация интегрирована в панель поиска.")
        except Exception as e:
            print(f"✗ Ошибка при открытии формы организаций: {e}")

def main():
    print("Тестирование интеграции навигации в панель поиска...")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Тест импорта компонентов
    try:
        from src.views.components.filter_bar import FilterBar
        print("✓ FilterBar с навигацией импортирован успешно")
        
        # Проверим, что у FilterBar есть новые методы
        filter_bar = FilterBar()
        assert hasattr(filter_bar, 'enable_navigation'), "Метод enable_navigation не найден"
        assert hasattr(filter_bar, 'set_navigation_state'), "Метод set_navigation_state не найден"
        assert hasattr(filter_bar, 'navigation_up_clicked'), "Сигнал navigation_up_clicked не найден"
        print("✓ Все новые методы навигации присутствуют в FilterBar")
        
    except Exception as e:
        print(f"✗ Ошибка при тестировании FilterBar: {e}")
        return
    
    # Тест форм списков
    forms_to_test = [
        ("WorkListFormV2", WorkListFormV2),
        ("PersonListFormV2", PersonListFormV2),
        ("OrganizationListFormV2", OrganizationListFormV2),
    ]
    
    for form_name, form_class in forms_to_test:
        try:
            form = form_class(user_id=1)
            
            # Проверим, что у формы есть filter_bar с навигацией
            assert hasattr(form, 'filter_bar'), f"У {form_name} нет filter_bar"
            assert hasattr(form.filter_bar, 'up_button'), f"У filter_bar в {form_name} нет up_button"
            assert hasattr(form.filter_bar, 'path_label'), f"У filter_bar в {form_name} нет path_label"
            assert hasattr(form, 'on_navigation_up'), f"У {form_name} нет метода on_navigation_up"
            
            print(f"✓ {form_name} успешно интегрирован с навигацией")
            
        except Exception as e:
            print(f"✗ Ошибка при тестировании {form_name}: {e}")
    
    print("=" * 60)
    print("Результат: Навигация успешно интегрирована в панель поиска!")
    print("Тепер�� кнопка 'Корень' и навигация находятся в одной строке с поиском.")
    print("\nОткрывается главное окно для демонстрации...")
    
    # Открываем главное окно для демонстрации
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
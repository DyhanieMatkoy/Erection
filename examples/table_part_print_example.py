"""
Table Part Print Functionality Example

This example demonstrates how to use the table part print functionality,
including print dialog, preview, and multi-page printing capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

from src.views.dialogs.table_part_print_dialog import create_table_part_print_dialog
from src.services.table_part_print_service import create_print_service


class PrintExampleWindow(QMainWindow):
    """Example window demonstrating table part print functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Part Print Example")
        self.setGeometry(100, 100, 600, 400)
        
        # Create sample data
        self.create_sample_data()
        
        # Setup UI
        self.setup_ui()
    
    def create_sample_data(self):
        """Create sample table data for demonstration"""
        # Small dataset
        self.small_data = [
            {"Код": "001", "Наименование": "Земляные работы", "Ед.изм.": "м³", "Количество": 100, "Цена": 150.0, "Сумма": 15000.0},
            {"Код": "002", "Наименование": "Бетонные работы", "Ед.изм.": "м³", "Количество": 50, "Цена": 3500.0, "Сумма": 175000.0},
            {"Код": "003", "Наименование": "Арматурные работы", "Ед.изм.": "т", "Количество": 5, "Цена": 45000.0, "Сумма": 225000.0},
            {"Код": "004", "Наименование": "Кирпичная кладка", "Ед.изм.": "м³", "Количество": 25, "Цена": 2800.0, "Сумма": 70000.0},
            {"Код": "005", "Наименование": "Штукатурные работы", "Ед.изм.": "м²", "Количество": 200, "Цена": 350.0, "Сумма": 70000.0},
        ]
        
        # Large dataset for multi-page testing
        self.large_data = []
        work_types = [
            "Земляные работы", "Бетонные работы", "Арматурные работы", 
            "Кирпичная кладка", "Штукатурные работы", "Малярные работы",
            "Электромонтажные работы", "Сантехнические работы", "Кровельные работы",
            "Отделочные работы", "Изоляционные работы", "Монтажные работы"
        ]
        
        units = ["м³", "м²", "м", "шт", "т", "кг"]
        
        for i in range(1, 76):  # 75 rows for multi-page demonstration
            work_type = work_types[i % len(work_types)]
            unit = units[i % len(units)]
            quantity = (i * 2.5) + (i % 10)
            price = 100.0 + (i * 15) + (i % 100)
            
            self.large_data.append({
                "№": i,
                "Код": f"W{i:03d}",
                "Наименование работы": f"{work_type} (позиция {i})",
                "Единица измерения": unit,
                "Количество": round(quantity, 2),
                "Цена за единицу": round(price, 2),
                "Сумма": round(quantity * price, 2)
            })
    
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Демонстрация функций печати табличных частей")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Этот пример демонстрирует возможности печати табличных частей:\n"
            "• Диалог настройки печати с предварительным просмотром\n"
            "• Настройка ориентации страницы, полей и масштаба\n"
            "• Автоматическое разбиение на страницы для больших таблиц\n"
            "• Повторение заголовков на каждой странице\n"
            "• Печать на принтер или сохранение в PDF"
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(description)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        # Small table print button
        small_print_btn = QPushButton("Печать небольшой таблицы (5 строк)")
        small_print_btn.clicked.connect(self.print_small_table)
        small_print_btn.setStyleSheet("padding: 10px; font-size: 12pt;")
        button_layout.addWidget(small_print_btn)
        
        # Large table print button
        large_print_btn = QPushButton("Печать большой таблицы (75 строк, многостраничная)")
        large_print_btn.clicked.connect(self.print_large_table)
        large_print_btn.setStyleSheet("padding: 10px; font-size: 12pt;")
        button_layout.addWidget(large_print_btn)
        
        # Test print service button
        test_service_btn = QPushButton("Тестировать сервис печати")
        test_service_btn.clicked.connect(self.test_print_service)
        test_service_btn.setStyleSheet("padding: 10px; font-size: 12pt;")
        button_layout.addWidget(test_service_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e8; border-radius: 3px;")
        layout.addWidget(self.status_label)
    
    def print_small_table(self):
        """Print small table example"""
        self.status_label.setText("Открытие диалога печати для небольшой таблицы...")
        
        dialog = create_table_part_print_dialog(
            self.small_data,
            "Смета строительных работ (краткая)",
            self
        )
        
        dialog.printRequested.connect(self.on_print_completed)
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            self.status_label.setText("Печать небольшой таблицы завершена")
        else:
            self.status_label.setText("Печать отменена пользователем")
    
    def print_large_table(self):
        """Print large table example"""
        self.status_label.setText("Открытие диалога печати для большой таблицы...")
        
        dialog = create_table_part_print_dialog(
            self.large_data,
            "Полная смета строительных работ",
            self
        )
        
        dialog.printRequested.connect(self.on_print_completed)
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            self.status_label.setText("Печать большой таблицы завершена")
        else:
            self.status_label.setText("Печать отменена пользователем")
    
    def test_print_service(self):
        """Test print service functionality"""
        self.status_label.setText("Тестирование сервиса печати...")
        
        try:
            service = create_print_service()
            
            # Test data validation
            is_valid, error_msg = service.validate_print_data(self.small_data)
            if not is_valid:
                self.status_label.setText(f"Ошибка валидации: {error_msg}")
                return
            
            # Test page count calculation
            from src.services.table_part_print_service import PrintConfiguration
            config = PrintConfiguration(max_rows_per_page=20)
            
            small_pages = service.get_page_count(self.small_data, config)
            large_pages = service.get_page_count(self.large_data, config)
            
            self.status_label.setText(
                f"Тест завершен: небольшая таблица - {small_pages} стр., "
                f"большая таблица - {large_pages} стр."
            )
            
        except Exception as e:
            self.status_label.setText(f"Ошибка тестирования: {str(e)}")
    
    def on_print_completed(self, config_dict):
        """Handle print completion"""
        format_type = config_dict.get('format', 'unknown')
        orientation = config_dict.get('orientation', 'unknown')
        
        self.status_label.setText(
            f"Печать завершена: формат {format_type}, ориентация {orientation}"
        )


def main():
    """Run the print example"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Table Part Print Example")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = PrintExampleWindow()
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
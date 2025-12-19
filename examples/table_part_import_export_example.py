"""
Example demonstrating table part import/export functionality.

This example shows how to use the import and export services
with a sample table part implementation.
"""

import sys
import os
from typing import Dict, List, Any
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.table_part_import_service import ImportColumn, TablePartImportService
from services.table_part_export_service import ExportColumn, TablePartExportService, ExportOptions
from views.dialogs.table_part_import_dialog import TablePartImportDialog
from views.dialogs.table_part_export_dialog import TablePartExportDialog


class TablePartImportExportExample(QMainWindow):
    """Example window demonstrating import/export functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Part Import/Export Example")
        self.setGeometry(100, 100, 600, 400)
        
        # Sample data
        self.sample_data = [
            {
                'code': '001',
                'name': 'Работа 1',
                'quantity': 10.5,
                'price': 1500.00,
                'sum': 15750.00,
                'unit': 'м²',
                'date': '2024-01-15'
            },
            {
                'code': '002',
                'name': 'Работа 2',
                'quantity': 25.0,
                'price': 800.00,
                'sum': 20000.00,
                'unit': 'м³',
                'date': '2024-01-16'
            },
            {
                'code': '003',
                'name': 'Работа 3',
                'quantity': 5.0,
                'price': 2500.00,
                'sum': 12500.00,
                'unit': 'шт',
                'date': '2024-01-17'
            }
        ]
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Import button
        import_button = QPushButton("Тест импорта данных")
        import_button.clicked.connect(self._test_import)
        layout.addWidget(import_button)
        
        # Export button
        export_button = QPushButton("Тест экспорта данных")
        export_button.clicked.connect(self._test_export)
        layout.addWidget(export_button)
        
        # Service test buttons
        import_service_button = QPushButton("Тест сервиса импорта")
        import_service_button.clicked.connect(self._test_import_service)
        layout.addWidget(import_service_button)
        
        export_service_button = QPushButton("Тест сервиса экспорта")
        export_service_button.clicked.connect(self._test_export_service)
        layout.addWidget(export_service_button)
    
    def _get_import_columns(self) -> List[ImportColumn]:
        """Get import column definitions"""
        return [
            ImportColumn(
                source_name="код",
                target_field="code",
                data_type="str",
                required=True
            ),
            ImportColumn(
                source_name="наименование",
                target_field="name",
                data_type="str",
                required=True
            ),
            ImportColumn(
                source_name="количество",
                target_field="quantity",
                data_type="float",
                required=True,
                validation_rules={"min_value": 0}
            ),
            ImportColumn(
                source_name="цена",
                target_field="price",
                data_type="float",
                required=True,
                validation_rules={"min_value": 0}
            ),
            ImportColumn(
                source_name="сумма",
                target_field="sum",
                data_type="float",
                required=False,
                default_value=0.0
            ),
            ImportColumn(
                source_name="единица",
                target_field="unit",
                data_type="str",
                required=False,
                default_value="шт"
            ),
            ImportColumn(
                source_name="дата",
                target_field="date",
                data_type="date",
                required=False
            )
        ]
    
    def _get_export_columns(self) -> List[ExportColumn]:
        """Get export column definitions"""
        return [
            ExportColumn(
                field_name="code",
                display_name="Код",
                data_type="str",
                width=10
            ),
            ExportColumn(
                field_name="name",
                display_name="Наименование работы",
                data_type="str",
                width=40
            ),
            ExportColumn(
                field_name="quantity",
                display_name="Количество",
                data_type="float",
                width=12,
                format_string="0.00"
            ),
            ExportColumn(
                field_name="price",
                display_name="Цена",
                data_type="float",
                width=15,
                format_string="#,##0.00"
            ),
            ExportColumn(
                field_name="sum",
                display_name="Сумма",
                data_type="float",
                width=15,
                format_string="#,##0.00"
            ),
            ExportColumn(
                field_name="unit",
                display_name="Ед. изм.",
                data_type="str",
                width=10
            ),
            ExportColumn(
                field_name="date",
                display_name="Дата",
                data_type="date",
                width=12
            )
        ]
    
    def _test_import(self):
        """Test import dialog"""
        target_columns = self._get_import_columns()
        
        dialog = TablePartImportDialog(target_columns, self)
        dialog.importCompleted.connect(self._on_import_completed)
        dialog.exec()
    
    def _test_export(self):
        """Test export dialog"""
        export_columns = self._get_export_columns()
        
        dialog = TablePartExportDialog(self.sample_data, export_columns, "work_items", self)
        dialog.exportCompleted.connect(self._on_export_completed)
        dialog.exec()
    
    def _test_import_service(self):
        """Test import service directly"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл для тестирования импорта",
                "",
                "Excel файлы (*.xlsx *.xls);;CSV файлы (*.csv);;Все файлы (*.*)"
            )
            
            if not file_path:
                return
            
            service = TablePartImportService()
            target_columns = self._get_import_columns()
            
            # Create preview
            preview = service.create_preview(file_path, target_columns)
            
            # Show preview info
            info_text = f"""Предварительный просмотр:
Формат: {preview.detected_format.value}
Строк: {preview.total_rows}
Колонок: {len(preview.headers)}
Заголовки: {', '.join(preview.headers[:5])}{'...' if len(preview.headers) > 5 else ''}

Предлагаемые сопоставления:
{chr(10).join([f'{k} -> {v}' for k, v in preview.suggested_mappings.items()])}
"""
            
            QMessageBox.information(self, "Предварительный просмотр", info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка тестирования импорта: {str(e)}")
    
    def _test_export_service(self):
        """Test export service directly"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить тестовый экспорт",
                "test_export.xlsx",
                "Excel файлы (*.xlsx);;CSV файлы (*.csv);;Все файлы (*.*)"
            )
            
            if not file_path:
                return
            
            service = TablePartExportService()
            export_columns = self._get_export_columns()
            options = ExportOptions(
                include_headers=True,
                apply_formatting=True,
                auto_fit_columns=True
            )
            
            # Export data
            result = service.export_data(self.sample_data, file_path, export_columns, options)
            
            # Show result
            if result.success:
                info_text = f"""Экспорт успешно завершен:
Файл: {result.file_path}
Экспортировано строк: {result.exported_rows}

Предупреждения: {len(result.warnings)}
Ошибки: {len(result.errors)}
"""
                if result.warnings:
                    info_text += f"\nПредупреждения:\n" + "\n".join(result.warnings[:3])
                if result.errors:
                    info_text += f"\nОшибки:\n" + "\n".join(result.errors[:3])
                
                QMessageBox.information(self, "Экспорт завершен", info_text)
            else:
                error_text = f"Экспорт не удался:\n" + "\n".join(result.errors)
                QMessageBox.critical(self, "Ошибка экспорта", error_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка тестирования экспорта: {str(e)}")
    
    def _on_import_completed(self, data: List[Dict[str, Any]]):
        """Handle import completion"""
        info_text = f"""Импорт завершен успешно!
Импортировано записей: {len(data)}

Первые 3 записи:
"""
        for i, record in enumerate(data[:3], 1):
            info_text += f"\n{i}. {record.get('code', '')} - {record.get('name', '')}"
        
        QMessageBox.information(self, "Импорт завершен", info_text)
    
    def _on_export_completed(self, file_path: str):
        """Handle export completion"""
        QMessageBox.information(
            self,
            "Экспорт завершен",
            f"Данные успешно экспортированы в файл:\n{file_path}"
        )


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    window = TablePartImportExportExample()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
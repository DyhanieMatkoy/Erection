"""
Table part export dialog for selecting format and configuring export options.

This dialog provides a user interface for exporting table part data
with format selection, column configuration, and export options.
"""

import os
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox, QScrollArea,
    QFrame, QSplitter, QHeaderView, QAbstractItemView, QLineEdit,
    QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon

from ...services.table_part_export_service import (
    TablePartExportService, ExportColumn, ExportOptions, ExportResult,
    ExportFormat, ExportValidationError
)


class ExportWorkerThread(QThread):
    """Worker thread for performing export operations"""
    
    progressUpdated = pyqtSignal(int)
    exportCompleted = pyqtSignal(object)  # ExportResult
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, export_service: TablePartExportService, data: List[Dict[str, Any]], 
                 file_path: str, columns: List[ExportColumn], options: ExportOptions):
        super().__init__()
        self.export_service = export_service
        self.data = data
        self.file_path = file_path
        self.columns = columns
        self.options = options
    
    def run(self):
        """Run export operation in background thread"""
        try:
            self.progressUpdated.emit(10)
            
            result = self.export_service.export_data(
                self.data,
                self.file_path,
                self.columns,
                self.options
            )
            
            self.progressUpdated.emit(100)
            self.exportCompleted.emit(result)
            
        except Exception as e:
            self.errorOccurred.emit(str(e))


class TablePartExportDialog(QDialog):
    """Dialog for exporting table part data"""
    
    exportCompleted = pyqtSignal(str)  # File path of exported file
    
    def __init__(self, data: List[Dict[str, Any]], columns: List[ExportColumn], 
                 table_name: str = "table_part", parent=None):
        super().__init__(parent)
        self.data = data
        self.available_columns = columns
        self.table_name = table_name
        self.export_service = TablePartExportService()
        self.worker_thread: Optional[ExportWorkerThread] = None
        
        self.setWindowTitle("Экспорт данных табличной части")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._connect_signals()
        self._update_preview()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Format selection section
        format_group = QGroupBox("Формат экспорта")
        format_layout = QHBoxLayout(format_group)
        
        self.format_group = QButtonGroup()
        
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.excel_radio.setChecked(True)
        self.format_group.addButton(self.excel_radio, 0)
        format_layout.addWidget(self.excel_radio)
        
        self.csv_radio = QRadioButton("CSV (.csv)")
        self.format_group.addButton(self.csv_radio, 1)
        format_layout.addWidget(self.csv_radio)
        
        format_layout.addStretch()
        layout.addWidget(format_group)
        
        # File selection section
        file_group = QGroupBox("Файл для сохранения")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Выберите файл для сохранения...")
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(file_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Column selection section
        columns_group = QGroupBox("Выбор колонок")
        columns_layout = QVBoxLayout(columns_group)
        
        # Column selection controls
        column_controls = QHBoxLayout()
        
        self.select_all_button = QPushButton("Выбрать все")
        self.select_all_button.clicked.connect(self._select_all_columns)
        column_controls.addWidget(self.select_all_button)
        
        self.select_none_button = QPushButton("Снять все")
        self.select_none_button.clicked.connect(self._select_no_columns)
        column_controls.addWidget(self.select_none_button)
        
        column_controls.addStretch()
        columns_layout.addLayout(column_controls)
        
        # Column table
        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(4)
        self.columns_table.setHorizontalHeaderLabels([
            "Экспорт", "Поле", "Заголовок", "Тип данных"
        ])
        self.columns_table.horizontalHeader().setStretchLastSection(True)
        self.columns_table.setAlternatingRowColors(True)
        columns_layout.addWidget(self.columns_table)
        
        splitter.addWidget(columns_group)
        
        # Options section
        options_group = QGroupBox("Параметры экспорта")
        options_layout = QVBoxLayout(options_group)
        
        # General options
        self.include_headers_cb = QCheckBox("Включить заголовки колонок")
        self.include_headers_cb.setChecked(True)
        options_layout.addWidget(self.include_headers_cb)
        
        # Excel-specific options
        self.excel_options_group = QGroupBox("Параметры Excel")
        excel_options_layout = QVBoxLayout(self.excel_options_group)
        
        self.apply_formatting_cb = QCheckBox("Применить форматирование")
        self.apply_formatting_cb.setChecked(True)
        excel_options_layout.addWidget(self.apply_formatting_cb)
        
        self.auto_fit_columns_cb = QCheckBox("Автоподбор ширины колонок")
        self.auto_fit_columns_cb.setChecked(True)
        excel_options_layout.addWidget(self.auto_fit_columns_cb)
        
        # Number format
        number_format_layout = QHBoxLayout()
        number_format_layout.addWidget(QLabel("Формат чисел:"))
        self.number_format_edit = QLineEdit("0.00")
        number_format_layout.addWidget(self.number_format_edit)
        excel_options_layout.addLayout(number_format_layout)
        
        # Date format
        date_format_layout = QHBoxLayout()
        date_format_layout.addWidget(QLabel("Формат дат:"))
        self.date_format_edit = QLineEdit("dd.mm.yyyy")
        date_format_layout.addWidget(self.date_format_edit)
        excel_options_layout.addLayout(date_format_layout)
        
        options_layout.addWidget(self.excel_options_group)
        
        # CSV-specific options
        self.csv_options_group = QGroupBox("Параметры CSV")
        csv_options_layout = QVBoxLayout(self.csv_options_group)
        
        # Encoding
        encoding_layout = QHBoxLayout()
        encoding_layout.addWidget(QLabel("Кодировка:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "cp1251", "windows-1251", "iso-8859-1"])
        encoding_layout.addWidget(self.encoding_combo)
        csv_options_layout.addLayout(encoding_layout)
        
        # Delimiter
        delimiter_layout = QHBoxLayout()
        delimiter_layout.addWidget(QLabel("Разделитель:"))
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems([",", ";", "\t"])
        delimiter_layout.addWidget(self.delimiter_combo)
        csv_options_layout.addLayout(delimiter_layout)
        
        options_layout.addWidget(self.csv_options_group)
        
        # Initially hide CSV options
        self.csv_options_group.hide()
        
        splitter.addWidget(options_group)
        layout.addWidget(splitter)
        
        # Preview section
        preview_group = QGroupBox("Предварительный просмотр")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_info_label = QLabel()
        preview_layout.addWidget(self.preview_info_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(150)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        preview_layout.addWidget(self.preview_table)
        
        layout.addWidget(preview_group)
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Прогресс экспорта")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Готов к экспорту")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(self.progress_group)
        self.progress_group.hide()
        
        # Results section (initially hidden)
        self.results_group = QGroupBox("Результаты экспорта")
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(self.results_group)
        self.results_group.hide()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Экспортировать")
        self.export_button.clicked.connect(self._start_export)
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        
        self.open_file_button = QPushButton("Открыть файл")
        self.open_file_button.clicked.connect(self._open_exported_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.format_group.buttonToggled.connect(self._on_format_changed)
        self.columns_table.itemChanged.connect(self._on_column_selection_changed)
        self.include_headers_cb.toggled.connect(self._update_preview)
        
        # Update file path when format changes
        self.excel_radio.toggled.connect(self._update_suggested_filename)
        self.csv_radio.toggled.connect(self._update_suggested_filename)
    
    def _browse_file(self):
        """Open file browser dialog"""
        if self.excel_radio.isChecked():
            file_filter = "Excel файлы (*.xlsx);;Все файлы (*.*)"
            default_ext = ".xlsx"
        else:
            file_filter = "CSV файлы (*.csv);;Все файлы (*.*)"
            default_ext = ".csv"
        
        suggested_name = self.export_service.get_suggested_filename(
            self.table_name,
            ExportFormat.EXCEL if self.excel_radio.isChecked() else ExportFormat.CSV
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить экспорт как",
            suggested_name,
            file_filter
        )
        
        if file_path:
            # Ensure correct extension
            if not file_path.lower().endswith(default_ext):
                file_path += default_ext
            
            self.file_path_edit.setText(file_path)
    
    def _update_suggested_filename(self):
        """Update suggested filename when format changes"""
        if not self.file_path_edit.text():
            format_type = ExportFormat.EXCEL if self.excel_radio.isChecked() else ExportFormat.CSV
            suggested_name = self.export_service.get_suggested_filename(self.table_name, format_type)
            self.file_path_edit.setText(suggested_name)
    
    def _on_format_changed(self, button, checked):
        """Handle format selection changes"""
        if checked:
            if button == self.excel_radio:
                self.excel_options_group.show()
                self.csv_options_group.hide()
            else:
                self.excel_options_group.hide()
                self.csv_options_group.show()
            
            self._update_preview()
    
    def _populate_columns_table(self):
        """Populate columns selection table"""
        self.columns_table.setRowCount(len(self.available_columns))
        
        for row_idx, column in enumerate(self.available_columns):
            # Export checkbox
            export_cb = QCheckBox()
            export_cb.setChecked(column.include_in_export)
            export_cb.toggled.connect(self._on_column_selection_changed)
            self.columns_table.setCellWidget(row_idx, 0, export_cb)
            
            # Field name
            field_item = QTableWidgetItem(column.field_name)
            field_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.columns_table.setItem(row_idx, 1, field_item)
            
            # Display name (editable)
            display_item = QTableWidgetItem(column.display_name)
            self.columns_table.setItem(row_idx, 2, display_item)
            
            # Data type
            type_item = QTableWidgetItem(column.data_type)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.columns_table.setItem(row_idx, 3, type_item)
        
        self.columns_table.resizeColumnsToContents()
    
    def _select_all_columns(self):
        """Select all columns for export"""
        for row in range(self.columns_table.rowCount()):
            cb = self.columns_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(True)
    
    def _select_no_columns(self):
        """Deselect all columns"""
        for row in range(self.columns_table.rowCount()):
            cb = self.columns_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(False)
    
    def _on_column_selection_changed(self):
        """Handle column selection changes"""
        self._update_preview()
    
    def _get_selected_columns(self) -> List[ExportColumn]:
        """Get list of selected columns for export"""
        selected_columns = []
        
        for row in range(self.columns_table.rowCount()):
            cb = self.columns_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox) and cb.isChecked():
                # Get updated column info
                field_name = self.columns_table.item(row, 1).text()
                display_name = self.columns_table.item(row, 2).text()
                data_type = self.columns_table.item(row, 3).text()
                
                # Find original column for other properties
                original_column = None
                for col in self.available_columns:
                    if col.field_name == field_name:
                        original_column = col
                        break
                
                if original_column:
                    # Create updated column
                    export_column = ExportColumn(
                        field_name=field_name,
                        display_name=display_name,
                        data_type=data_type,
                        width=original_column.width,
                        format_string=original_column.format_string,
                        include_in_export=True
                    )
                    selected_columns.append(export_column)
        
        return selected_columns
    
    def _get_export_options(self) -> ExportOptions:
        """Get current export options"""
        return ExportOptions(
            include_headers=self.include_headers_cb.isChecked(),
            date_format=self.date_format_edit.text(),
            number_format=self.number_format_edit.text(),
            encoding=self.encoding_combo.currentText(),
            delimiter=self.delimiter_combo.currentText(),
            apply_formatting=self.apply_formatting_cb.isChecked(),
            auto_fit_columns=self.auto_fit_columns_cb.isChecked()
        )
    
    def _update_preview(self):
        """Update preview table"""
        selected_columns = self._get_selected_columns()
        
        if not selected_columns:
            self.preview_info_label.setText("Не выбрано ни одной колонки")
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return
        
        # Update info
        info_text = f"Колонок: {len(selected_columns)}, Строк данных: {len(self.data)}"
        self.preview_info_label.setText(info_text)
        
        # Setup preview table
        options = self._get_export_options()
        
        if options.include_headers:
            self.preview_table.setRowCount(min(6, len(self.data) + 1))  # +1 for header
            self.preview_table.setColumnCount(len(selected_columns))
            
            # Set headers
            headers = [col.display_name for col in selected_columns]
            self.preview_table.setHorizontalHeaderLabels([f"Col {i+1}" for i in range(len(selected_columns))])
            
            # Add header row
            for col_idx, header in enumerate(headers):
                item = QTableWidgetItem(header)
                item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.preview_table.setItem(0, col_idx, item)
            
            # Add data rows
            for row_idx, row_data in enumerate(self.data[:5], start=1):
                for col_idx, column in enumerate(selected_columns):
                    value = row_data.get(column.field_name, "")
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.preview_table.setItem(row_idx, col_idx, item)
        else:
            self.preview_table.setRowCount(min(5, len(self.data)))
            self.preview_table.setColumnCount(len(selected_columns))
            
            # Set headers
            headers = [col.display_name for col in selected_columns]
            self.preview_table.setHorizontalHeaderLabels(headers)
            
            # Add data rows
            for row_idx, row_data in enumerate(self.data[:5]):
                for col_idx, column in enumerate(selected_columns):
                    value = row_data.get(column.field_name, "")
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.preview_table.setItem(row_idx, col_idx, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def _start_export(self):
        """Start the export process"""
        # Validate inputs
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Ошибка", "Укажите файл для сохранения")
            return
        
        selected_columns = self._get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну колонку для экспорта")
            return
        
        # Validate file path
        if not self.export_service.validate_file_path(file_path):
            QMessageBox.warning(self, "Ошибка", "Невозможно записать в указанный файл")
            return
        
        # Show progress
        self.progress_group.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Начинаем экспорт...")
        
        # Disable controls
        self.export_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Get export options
        options = self._get_export_options()
        
        # Start worker thread
        self.worker_thread = ExportWorkerThread(
            self.export_service,
            self.data,
            file_path,
            selected_columns,
            options
        )
        
        self.worker_thread.progressUpdated.connect(self._on_progress_updated)
        self.worker_thread.exportCompleted.connect(self._on_export_completed)
        self.worker_thread.errorOccurred.connect(self._on_export_error)
        
        self.worker_thread.start()
    
    def _on_progress_updated(self, value: int):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        if value < 100:
            self.progress_label.setText(f"Экспорт данных... {value}%")
    
    def _on_export_completed(self, result: ExportResult):
        """Handle export completion"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("Экспорт завершен")
        
        # Show results
        self.results_group.show()
        
        results_text = []
        if result.success:
            results_text.append(f"✓ Успешно экспортировано строк: {result.exported_rows}")
            results_text.append(f"Файл сохранен: {result.file_path}")
            
            if result.warnings:
                results_text.append("\nПредупреждения:")
                for warning in result.warnings:
                    results_text.append(f"• {warning}")
            
            if result.errors:
                results_text.append("\nОшибки:")
                for error in result.errors[:5]:  # Show first 5 errors
                    results_text.append(f"• {error}")
                if len(result.errors) > 5:
                    results_text.append(f"... и еще {len(result.errors) - 5} ошибок")
            
            # Enable file operations
            self.open_file_button.setEnabled(True)
            self.exported_file_path = result.file_path
            
        else:
            results_text.append("✗ Экспорт не удался")
            if result.errors:
                results_text.append("\nОшибки:")
                for error in result.errors:
                    results_text.append(f"• {error}")
        
        self.results_text.setPlainText("\n".join(results_text))
        
        # Re-enable controls
        self.export_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        # Emit completion signal
        if result.success:
            self.exportCompleted.emit(result.file_path)
    
    def _on_export_error(self, error_message: str):
        """Handle export errors"""
        self.progress_label.setText("Ошибка экспорта")
        
        # Show error
        QMessageBox.critical(self, "Ошибка экспорта", f"Произошла ошибка при экспорте:\n{error_message}")
        
        # Re-enable controls
        self.export_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        # Hide progress
        self.progress_group.hide()
    
    def _open_exported_file(self):
        """Open the exported file"""
        if hasattr(self, 'exported_file_path'):
            try:
                import subprocess
                import sys
                
                if sys.platform.startswith('win'):
                    os.startfile(self.exported_file_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', self.exported_file_path])
                else:
                    subprocess.call(['xdg-open', self.exported_file_path])
                    
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def showEvent(self, event):
        """Handle dialog show event"""
        super().showEvent(event)
        self._populate_columns_table()
        self._update_suggested_filename()
        self._update_preview()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Прервать экспорт?",
                "Экспорт данных еще не завершен. Прервать операцию?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.terminate()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
"""
Table part import dialog for selecting files and configuring column mappings.

This dialog provides a user interface for importing data into table parts
with file selection, preview, and column mapping configuration.
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox, QScrollArea,
    QFrame, QSplitter, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon

from ...services.table_part_import_service import (
    TablePartImportService, ImportColumn, ImportPreview, ImportResult,
    ImportFormat, ImportValidationError
)


class ImportWorkerThread(QThread):
    """Worker thread for performing import operations"""
    
    progressUpdated = pyqtSignal(int)
    importCompleted = pyqtSignal(object)  # ImportResult
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, import_service: TablePartImportService, file_path: str, 
                 column_mappings: Dict[str, str], target_columns: List[ImportColumn]):
        super().__init__()
        self.import_service = import_service
        self.file_path = file_path
        self.column_mappings = column_mappings
        self.target_columns = target_columns
    
    def run(self):
        """Run import operation in background thread"""
        try:
            self.progressUpdated.emit(10)
            
            result = self.import_service.import_data(
                self.file_path,
                self.column_mappings,
                self.target_columns,
                skip_header=True
            )
            
            self.progressUpdated.emit(100)
            self.importCompleted.emit(result)
            
        except Exception as e:
            self.errorOccurred.emit(str(e))


class TablePartImportDialog(QDialog):
    """Dialog for importing data into table parts"""
    
    importCompleted = pyqtSignal(list)  # List of imported data dictionaries
    
    def __init__(self, target_columns: List[ImportColumn], parent=None):
        super().__init__(parent)
        self.target_columns = target_columns
        self.import_service = TablePartImportService()
        self.preview_data: Optional[ImportPreview] = None
        self.column_mappings: Dict[str, str] = {}
        self.worker_thread: Optional[ImportWorkerThread] = None
        
        self.setWindowTitle("Импорт данных в табличную часть")
        self.setModal(True)
        self.resize(900, 700)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # File selection section
        file_group = QGroupBox("Выбор файла")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("Файл не выбран")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        file_layout.addWidget(self.file_path_label)
        
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(file_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Preview section
        preview_group = QGroupBox("Предварительный просмотр данных")
        preview_layout = QVBoxLayout(preview_group)
        
        # Preview info
        self.preview_info_label = QLabel("Выберите файл для предварительного просмотра")
        self.preview_info_label.setStyleSheet("color: gray; font-style: italic;")
        preview_layout.addWidget(self.preview_info_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        preview_layout.addWidget(self.preview_table)
        
        splitter.addWidget(preview_group)
        
        # Column mapping section
        mapping_group = QGroupBox("Сопоставление колонок")
        mapping_layout = QVBoxLayout(mapping_group)
        
        # Mapping instructions
        mapping_info = QLabel(
            "Укажите соответствие между колонками файла и полями табличной части:"
        )
        mapping_layout.addWidget(mapping_info)
        
        # Mapping table
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels([
            "Колонка в файле", "Поле табличной части", "Обязательное"
        ])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setAlternatingRowColors(True)
        mapping_layout.addWidget(self.mapping_table)
        
        # Auto-mapping button
        auto_map_layout = QHBoxLayout()
        self.auto_map_button = QPushButton("Автоматическое сопоставление")
        self.auto_map_button.clicked.connect(self._auto_map_columns)
        self.auto_map_button.setEnabled(False)
        auto_map_layout.addWidget(self.auto_map_button)
        auto_map_layout.addStretch()
        mapping_layout.addLayout(auto_map_layout)
        
        splitter.addWidget(mapping_group)
        layout.addWidget(splitter)
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Прогресс импорта")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Готов к импорту")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(self.progress_group)
        self.progress_group.hide()
        
        # Results section (initially hidden)
        self.results_group = QGroupBox("Результаты импорта")
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(self.results_group)
        self.results_group.hide()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Импортировать")
        self.import_button.clicked.connect(self._start_import)
        self.import_button.setEnabled(False)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("Готово")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass
    
    def _browse_file(self):
        """Open file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для импорта",
            "",
            "Excel файлы (*.xlsx *.xls);;CSV файлы (*.csv);;Все файлы (*.*)"
        )
        
        if file_path:
            self._load_file_preview(file_path)
    
    def _load_file_preview(self, file_path: str):
        """Load and display file preview"""
        try:
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("color: black;")
            
            # Create preview
            self.preview_data = self.import_service.create_preview(file_path, self.target_columns)
            
            # Update preview info
            format_name = "Excel" if self.preview_data.detected_format == ImportFormat.EXCEL else "CSV"
            info_text = f"Формат: {format_name}, Строк: {self.preview_data.total_rows}, Колонок: {len(self.preview_data.headers)}"
            self.preview_info_label.setText(info_text)
            self.preview_info_label.setStyleSheet("color: black;")
            
            # Populate preview table
            self._populate_preview_table()
            
            # Populate mapping table
            self._populate_mapping_table()
            
            # Enable controls
            self.auto_map_button.setEnabled(True)
            self._update_import_button_state()
            
        except ImportValidationError as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки файла: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неожиданная ошибка: {str(e)}")
    
    def _populate_preview_table(self):
        """Populate preview table with sample data"""
        if not self.preview_data:
            return
        
        # Set up table
        self.preview_table.setRowCount(len(self.preview_data.sample_rows))
        self.preview_table.setColumnCount(len(self.preview_data.headers))
        self.preview_table.setHorizontalHeaderLabels(self.preview_data.headers)
        
        # Populate data
        for row_idx, row_data in enumerate(self.preview_data.sample_rows):
            for col_idx, cell_value in enumerate(row_data):
                if col_idx < len(self.preview_data.headers):
                    item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.preview_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.preview_table.resizeColumnsToContents()
    
    def _populate_mapping_table(self):
        """Populate column mapping table"""
        if not self.preview_data:
            return
        
        # Set up table
        self.mapping_table.setRowCount(len(self.preview_data.headers))
        
        # Populate mapping rows
        for row_idx, header in enumerate(self.preview_data.headers):
            # Source column name (read-only)
            source_item = QTableWidgetItem(header)
            source_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.mapping_table.setItem(row_idx, 0, source_item)
            
            # Target field combo box
            target_combo = QComboBox()
            target_combo.addItem("-- Не сопоставлено --", "")
            
            for target_col in self.target_columns:
                target_combo.addItem(
                    f"{target_col.target_field} ({target_col.data_type})",
                    target_col.target_field
                )
            
            # Set suggested mapping if available
            if header in self.preview_data.suggested_mappings:
                suggested_field = self.preview_data.suggested_mappings[header]
                for i in range(target_combo.count()):
                    if target_combo.itemData(i) == suggested_field:
                        target_combo.setCurrentIndex(i)
                        break
            
            target_combo.currentTextChanged.connect(self._on_mapping_changed)
            self.mapping_table.setCellWidget(row_idx, 1, target_combo)
            
            # Required field indicator
            target_field = target_combo.currentData()
            is_required = False
            if target_field:
                for target_col in self.target_columns:
                    if target_col.target_field == target_field:
                        is_required = target_col.required
                        break
            
            required_item = QTableWidgetItem("Да" if is_required else "Нет")
            required_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            if is_required:
                font = required_item.font()
                font.setBold(True)
                required_item.setFont(font)
            self.mapping_table.setItem(row_idx, 2, required_item)
        
        # Resize columns
        self.mapping_table.resizeColumnsToContents()
    
    def _auto_map_columns(self):
        """Apply automatic column mapping"""
        if not self.preview_data:
            return
        
        # Apply suggested mappings
        for row_idx in range(self.mapping_table.rowCount()):
            header = self.preview_data.headers[row_idx]
            if header in self.preview_data.suggested_mappings:
                suggested_field = self.preview_data.suggested_mappings[header]
                
                combo = self.mapping_table.cellWidget(row_idx, 1)
                if isinstance(combo, QComboBox):
                    for i in range(combo.count()):
                        if combo.itemData(i) == suggested_field:
                            combo.setCurrentIndex(i)
                            break
        
        self._update_import_button_state()
    
    def _on_mapping_changed(self):
        """Handle mapping changes"""
        self._update_required_indicators()
        self._update_import_button_state()
    
    def _update_required_indicators(self):
        """Update required field indicators"""
        for row_idx in range(self.mapping_table.rowCount()):
            combo = self.mapping_table.cellWidget(row_idx, 1)
            if isinstance(combo, QComboBox):
                target_field = combo.currentData()
                is_required = False
                
                if target_field:
                    for target_col in self.target_columns:
                        if target_col.target_field == target_field:
                            is_required = target_col.required
                            break
                
                required_item = self.mapping_table.item(row_idx, 2)
                if required_item:
                    required_item.setText("Да" if is_required else "Нет")
                    font = required_item.font()
                    font.setBold(is_required)
                    required_item.setFont(font)
    
    def _update_import_button_state(self):
        """Update import button enabled state"""
        if not self.preview_data:
            self.import_button.setEnabled(False)
            return
        
        # Check if all required fields are mapped
        mapped_fields = set()
        for row_idx in range(self.mapping_table.rowCount()):
            combo = self.mapping_table.cellWidget(row_idx, 1)
            if isinstance(combo, QComboBox):
                target_field = combo.currentData()
                if target_field:
                    mapped_fields.add(target_field)
        
        # Check required fields
        required_fields = {col.target_field for col in self.target_columns if col.required}
        missing_required = required_fields - mapped_fields
        
        self.import_button.setEnabled(len(missing_required) == 0)
        
        if missing_required:
            self.import_button.setToolTip(
                f"Не сопоставлены обязательные поля: {', '.join(missing_required)}"
            )
        else:
            self.import_button.setToolTip("Начать импорт данных")
    
    def _get_column_mappings(self) -> Dict[str, str]:
        """Get current column mappings"""
        mappings = {}
        
        for row_idx in range(self.mapping_table.rowCount()):
            source_item = self.mapping_table.item(row_idx, 0)
            combo = self.mapping_table.cellWidget(row_idx, 1)
            
            if source_item and isinstance(combo, QComboBox):
                source_column = source_item.text()
                target_field = combo.currentData()
                
                if target_field:
                    mappings[source_column] = target_field
        
        return mappings
    
    def _start_import(self):
        """Start the import process"""
        if not self.preview_data:
            return
        
        # Get column mappings
        self.column_mappings = self._get_column_mappings()
        
        if not self.column_mappings:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного сопоставления колонок")
            return
        
        # Show progress
        self.progress_group.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Начинаем импорт...")
        
        # Disable controls
        self.import_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.auto_map_button.setEnabled(False)
        
        # Start worker thread
        self.worker_thread = ImportWorkerThread(
            self.import_service,
            self.file_path_label.text(),
            self.column_mappings,
            self.target_columns
        )
        
        self.worker_thread.progressUpdated.connect(self._on_progress_updated)
        self.worker_thread.importCompleted.connect(self._on_import_completed)
        self.worker_thread.errorOccurred.connect(self._on_import_error)
        
        self.worker_thread.start()
    
    def _on_progress_updated(self, value: int):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        if value < 100:
            self.progress_label.setText(f"Импорт данных... {value}%")
    
    def _on_import_completed(self, result: ImportResult):
        """Handle import completion"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("Импорт завершен")
        
        # Show results
        self.results_group.show()
        
        results_text = []
        if result.success:
            results_text.append(f"✓ Успешно импортировано строк: {result.imported_rows}")
            
            if result.failed_rows > 0:
                results_text.append(f"⚠ Пропущено строк с ошибками: {result.failed_rows}")
            
            if result.warnings:
                results_text.append("\nПредупреждения:")
                for warning in result.warnings:
                    results_text.append(f"• {warning}")
            
            if result.errors:
                results_text.append("\nОшибки:")
                for error in result.errors[:10]:  # Show first 10 errors
                    results_text.append(f"• {error}")
                if len(result.errors) > 10:
                    results_text.append(f"... и еще {len(result.errors) - 10} ошибок")
            
            # Enable OK button
            self.ok_button.setEnabled(True)
            
            # Store imported data for return
            self.imported_data = result.data
            
        else:
            results_text.append("✗ Импорт не удался")
            if result.errors:
                results_text.append("\nОшибки:")
                for error in result.errors:
                    results_text.append(f"• {error}")
        
        self.results_text.setPlainText("\n".join(results_text))
        
        # Re-enable controls
        self.browse_button.setEnabled(True)
        self.auto_map_button.setEnabled(True)
        if not result.success:
            self.import_button.setEnabled(True)
    
    def _on_import_error(self, error_message: str):
        """Handle import errors"""
        self.progress_label.setText("Ошибка импорта")
        
        # Show error
        QMessageBox.critical(self, "Ошибка импорта", f"Произошла ошибка при импорте:\n{error_message}")
        
        # Re-enable controls
        self.import_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.auto_map_button.setEnabled(True)
        
        # Hide progress
        self.progress_group.hide()
    
    def accept(self):
        """Accept dialog and return imported data"""
        if hasattr(self, 'imported_data'):
            self.importCompleted.emit(self.imported_data)
        super().accept()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Прервать импорт?",
                "Импорт данных еще не завершен. Прервать операцию?",
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
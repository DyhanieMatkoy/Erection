"""
Диалог импорта данных из DBF файлов
"""

import logging
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QCheckBox, QProgressBar, QTextEdit, QDialogButtonBox,
    QMessageBox, QSplitter, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.importer import DBFImporter

logger = logging.getLogger(__name__)


class ValidationThread(QThread):
    """Поток для валидации DBF файлов"""
    
    validation_finished = pyqtSignal(dict)  # результаты валидации
    error_occurred = pyqtSignal(str)  # сообщение об ошибке
    
    def __init__(self, dbf_path: str, entity_types: List[str]):
        super().__init__()
        self.dbf_path = dbf_path
        self.entity_types = entity_types
        self.importer = DBFImporter()
    
    def run(self):
        """Выполняет валидацию в отдельном потоке"""
        try:
            results = {}
            
            for entity_type in self.entity_types:
                result = self.importer.validate_dbf_structure(self.dbf_path, entity_type)
                results[entity_type] = result
            
            self.validation_finished.emit(results)
            
        except Exception as e:
            logger.error(f"Ошибка в потоке валидации: {e}")
            self.error_occurred.emit(str(e))


class ImportDialog(QDialog):
    """Диалог импорта данных"""
    
    def __init__(self, dbf_path: str, entity_types: List[str], allow_import: bool = True, parent=None):
        super().__init__(parent)
        self.dbf_path = dbf_path
        self.entity_types = entity_types
        self.allow_import = allow_import
        self.validation_thread: ValidationThread = None
        self.import_thread = None
        self.validation_results = {}
        
        self.init_ui()
        self.start_validation()
    
    def init_ui(self):
        """Инициализирует пользовательский интерфейс"""
        self.setWindowTitle("Импорт данных из DBF")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Создание разделителя
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Верхняя панель с результатами валидации
        top_panel = self.create_validation_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с логом
        bottom_panel = self.create_log_panel()
        splitter.addWidget(bottom_panel)
        
        # Установка пропорций разделителя
        splitter.setSizes([400, 200])
        
        # Кнопки диалога
        if self.allow_import:
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.start_import)
            buttons.rejected.connect(self.reject)
            
            # Изначально блокируем кнопку OK
            self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
            self.ok_button.setEnabled(False)
            
            layout.addWidget(buttons)
        else:
            # Режим только валидации
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
    
    def create_validation_panel(self) -> QWidget:
        """Создает панель с результатами валидации"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Результаты проверки структуры DBF файла:"))
        header_layout.addWidget(QLabel(f"Файл: {self.dbf_path}"))
        layout.addLayout(header_layout)
        
        # Таблица с результатами
        self.validation_table = QTableWidget()
        self.validation_table.setColumnCount(4)
        self.validation_table.setHorizontalHeaderLabels([
            "Сущность", "Статус", "Количество записей", "Детали"
        ])
        
        # Настройка таблицы
        header = self.validation_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.validation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.validation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.validation_table)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def create_log_panel(self) -> QWidget:
        """Создает панель с логом"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Лог операций:"))
        
        self.clear_log_button = QPushButton("Очистить")
        self.clear_log_button.clicked.connect(self.clear_log)
        header_layout.addWidget(self.clear_log_button)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Текстовое поле для лога
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        return panel
    
    def start_validation(self):
        """Начинает валидацию DBF файла"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Индeterminate progress
        self.log_message("Начало проверки структуры DBF файла...")
        
        # Создание и запуск потока валидации
        self.validation_thread = ValidationThread(self.dbf_path, self.entity_types)
        self.validation_thread.validation_finished.connect(self.validation_finished)
        self.validation_thread.error_occurred.connect(self.validation_error)
        self.validation_thread.start()
    
    def validation_finished(self, results: Dict[str, Dict[str, Any]]):
        """Обрабатывает завершение валидации"""
        self.progress_bar.setVisible(False)
        self.validation_results = results
        
        # Заполнение таблицы результатами
        self.validation_table.setRowCount(len(results))
        
        all_valid = True
        row = 0
        
        for entity_type, result in results.items():
            # Сущность
            self.validation_table.setItem(row, 0, QTableWidgetItem(entity_type))
            
            # Статус
            status = "Корректна" if result["valid"] else "Ошибка"
            status_item = QTableWidgetItem(status)
            if result["valid"]:
                status_item.setBackground(Qt.GlobalColor.green)
            else:
                status_item.setBackground(Qt.GlobalColor.red)
                all_valid = False
            self.validation_table.setItem(row, 1, status_item)
            
            # Количество записей
            record_count = str(result.get("record_count", 0))
            self.validation_table.setItem(row, 2, QTableWidgetItem(record_count))
            
            # Детали
            details = result.get("message", "")
            if not result["valid"] and "missing_fields" in result:
                missing = ", ".join(result["missing_fields"])
                details += f"\nОтсутствуют поля: {missing}"
            
            if "extra_fields" in result and result["extra_fields"]:
                extra = ", ".join(result["extra_fields"])
                details += f"\nЛишние поля: {extra}"
            
            self.validation_table.setItem(row, 3, QTableWidgetItem(details))
            
            self.log_message(f"{entity_type}: {status}")
            if not result["valid"]:
                self.log_message(f"  {details}")
            
            row += 1
        
        # Разрешаем импорт, если все структуры корректны
        if self.allow_import and all_valid:
            self.ok_button.setEnabled(True)
            self.log_message("Структура всех файлов корректна. Импорт разрешен.")
        elif self.allow_import:
            self.log_message("Обнаружены ошибки в структуре файлов. Импорт не рекомендуется.")
    
    def validation_error(self, error_message: str):
        """Обрабатывает ошибку валидации"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Ошибка при проверке структуры:\n{error_message}")
        self.log_message(f"Ошибка: {error_message}")
    
    def start_import(self):
        """Начинает импорт данных"""
        if not self.validation_results:
            QMessageBox.warning(self, "Предупреждение", "Сначала выполните проверку структуры")
            return
        
        # Проверка, что все структуры корректны
        all_valid = all(result["valid"] for result in self.validation_results.values())
        
        if not all_valid:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Обнаружены ошибки в структуре файлов. Продолжить импорт может привести к ошибкам. Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Подтверждение импорта
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите импортировать данные из DBF файла?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Блокировка UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.ok_button.setEnabled(False)
        
        # Создание и запуск потока импорта
        from ui.main_window import ImportThread
        self.import_thread = ImportThread(self.dbf_path, self.entity_types, False)
        self.import_thread.progress_updated.connect(self.update_progress)
        self.import_thread.import_finished.connect(self.import_finished)
        self.import_thread.error_occurred.connect(self.import_error)
        self.import_thread.start()
        
        self.log_message("Начало импорта данных...")
    
    def update_progress(self, message: str, progress: int):
        """Обновляет прогресс-бар и лог"""
        self.progress_bar.setValue(progress)
        self.log_message(message)
    
    def import_finished(self, results: dict):
        """Обрабатывает завершение импорта"""
        self.progress_bar.setVisible(False)
        
        # Формирование сообщения о результатах
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        message = f"Импорт завершен. Успешно: {success_count}/{total_count}"
        
        if success_count == total_count:
            QMessageBox.information(self, "Успех", message)
            self.log_message(message)
            self.accept()
        else:
            details = []
            for entity, success in results.items():
                status = "Успешно" if success else "Ошибка"
                details.append(f"{entity}: {status}")
            
            QMessageBox.warning(
                self,
                "Предупреждение",
                message + "\n\n" + "\n".join(details)
            )
            self.log_message(message + "\n" + "\n".join(details))
    
    def import_error(self, error_message: str):
        """Обрабатывает ошибку импорта"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте данных:\n{error_message}")
        self.log_message(f"Ошибка: {error_message}")
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_text.append(message)
        # Прокрутка к последнему сообщению
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Очищает лог"""
        self.log_text.clear()
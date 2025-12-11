"""
Главное окно приложения DBF Importer
"""

import os
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QCheckBox,
    QProgressBar, QTextEdit, QSplitter, QFrame, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from core.importer import DBFImporter
from ui.import_dialog import ImportDialog

logger = logging.getLogger(__name__)


class ImportThread(QThread):
    """Поток для выполнения импорта данных"""
    
    progress_updated = pyqtSignal(str, int)  # сообщение, прогресс
    import_finished = pyqtSignal(dict)  # результаты импорта
    error_occurred = pyqtSignal(str)  # сообщение об ошибке
    
    def __init__(self, dbf_path: str, entity_types: list, clear_existing: bool = False, limit: int = None):
        super().__init__()
        self.dbf_path = dbf_path
        self.entity_types = entity_types
        self.clear_existing = clear_existing
        self.limit = limit
        self.importer = DBFImporter(progress_callback=self.progress_callback)
    
    def progress_callback(self, message: str, progress: int):
        """Callback для обновления прогресса"""
        self.progress_updated.emit(message, progress)
    
    def run(self):
        """Выполняет импорт в отдельном потоке"""
        try:
            results = {}
            
            for entity_type in self.entity_types:
                self.progress_updated.emit(f"Импорт {entity_type}...", 0)
                success = self.importer.import_entity(self.dbf_path, entity_type, self.clear_existing, self.limit)
                results[entity_type] = success
                
                if not success:
                    self.error_occurred.emit(f"Ошибка при импорте {entity_type}")
                    return
            
            self.import_finished.emit(results)
            
        except Exception as e:
            logger.error(f"Ошибка в потоке импорта: {e}")
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.import_thread: Optional[ImportThread] = None
        from config.settings import DBF_DEFAULT_PATH
        self.dbf_path = DBF_DEFAULT_PATH
        self.init_ui()
    
    def init_ui(self):
        """Инициализирует пользовательский интерфейс"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Создание разделителя
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Верхняя панель с настройками
        top_panel = self.create_top_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с логом
        bottom_panel = self.create_bottom_panel()
        splitter.addWidget(bottom_panel)
        
        # Установка пропорций разделителя
        splitter.setSizes([400, 200])
        
        # Изначально блокируем кнопку импорта, если путь не задан
        from config.settings import DBF_DEFAULT_PATH
        self.import_button.setEnabled(bool(DBF_DEFAULT_PATH))
    
    def create_top_panel(self) -> QWidget:
        """Создает верхнюю панель с настройками"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Группа выбора файла
        file_group = QGroupBox("Выбор DBF файла или директории")
        file_layout = QHBoxLayout(file_group)
        
        from config.settings import DBF_DEFAULT_PATH
        self.path_label = QLabel(f"Путь: {DBF_DEFAULT_PATH}")
        self.path_label.setWordWrap(True)
        file_layout.addWidget(self.path_label)
        
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self.browse_dbf_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(file_group)
        
        # Группа настроек импорта
        settings_group = QGroupBox("Настройки импорта")
        settings_layout = QVBoxLayout(settings_group)
        
        # Чекбоксы для выбора сущностей
        self.units_check = QCheckBox("Единицы измерения")
        self.units_check.setChecked(True)
        settings_layout.addWidget(self.units_check)

        self.nomenclature_check = QCheckBox("Номенклатура (Работы)")
        self.nomenclature_check.setChecked(True)
        settings_layout.addWidget(self.nomenclature_check)
        
        self.materials_check = QCheckBox("Материалы")
        self.materials_check.setChecked(True)
        settings_layout.addWidget(self.materials_check)
        
        self.composition_check = QCheckBox("Состав работ (Затраты)")
        self.composition_check.setChecked(True)
        settings_layout.addWidget(self.composition_check)
        
        # Чекбокс очистки данных
        self.clear_data_check = QCheckBox("Очистить существующие данные перед импортом")
        settings_layout.addWidget(self.clear_data_check)
        
        # Опция ограничения количества записей
        limit_layout = QHBoxLayout()
        self.limit_check = QCheckBox("Ограничить количество записей")
        self.limit_check.toggled.connect(self.on_limit_check_toggled)
        limit_layout.addWidget(self.limit_check)
        
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setMinimum(1)
        self.limit_spinbox.setMaximum(10000)
        self.limit_spinbox.setValue(100)
        self.limit_spinbox.setEnabled(False)
        limit_layout.addWidget(self.limit_spinbox)
        limit_layout.addWidget(QLabel("записей"))
        limit_layout.addStretch()
        
        settings_layout.addLayout(limit_layout)
        
        layout.addWidget(settings_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Импорт")
        self.import_button.clicked.connect(self.start_import)
        self.import_button.setEnabled(False)
        buttons_layout.addWidget(self.import_button)
        
        self.validate_button = QPushButton("Проверить структуру")
        self.validate_button.clicked.connect(self.validate_structure)
        self.validate_button.setEnabled(False)
        buttons_layout.addWidget(self.validate_button)
        
        layout.addLayout(buttons_layout)
        
        return panel
    
    def create_bottom_panel(self) -> QWidget:
        """Создает нижнюю панель с логом"""
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
    
    def browse_dbf_file(self):
        """Открывает диалог выбора DBF файла или директории"""
        # Сначала пробуем выбрать директорию
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию с DBF файлами",
            ""
        )
        
        if dir_path:
            self.dbf_path = dir_path
            self.path_label.setText(f"Выбрана директория: {dir_path}")
            self.import_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.log_message(f"Выбрана директория: {dir_path}")
            return
        
        # Если директория не выбрана, пробуем выбрать файл
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите DBF файл",
            "",
            "DBF файлы (*.dbf);;Все файлы (*)"
        )
        
        if file_path:
            self.dbf_path = file_path
            self.path_label.setText(f"Выбран файл: {file_path}")
            self.import_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.log_message(f"Выбран файл: {file_path}")
    
    def start_import(self):
        """Начинает импорт данных"""
        if not self.dbf_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите DBF файл или директорию для импорта")
            return
        
        # Получение выбранных сущностей
        entity_types = []
        if self.units_check.isChecked():
            entity_types.append("units")
        if self.materials_check.isChecked():
            entity_types.append("materials")
        if self.nomenclature_check.isChecked():
            entity_types.append("nomenclature")
        if self.composition_check.isChecked():
            entity_types.append("composition")
        
        if not entity_types:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну сущность для импорта")
            return
        
        # Подтверждение очистки данных
        if self.clear_data_check.isChecked():
            reply = QMessageBox.question(
                self, 
                "Подтверждение", 
                "Вы уверены, что хотите очистить существующие данные перед импортом?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Получение ограничения на количество записей
        limit = None
        if self.limit_check.isChecked():
            limit = self.limit_spinbox.value()
        
        # Блокировка UI
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Создание и запуск потока импорта
        self.import_thread = ImportThread(
            self.dbf_path, 
            entity_types, 
            self.clear_data_check.isChecked(),
            limit
        )
        self.import_thread.progress_updated.connect(self.update_progress)
        self.import_thread.import_finished.connect(self.import_finished)
        self.import_thread.error_occurred.connect(self.import_error)
        self.import_thread.start()
        
        self.log_message("Начало импорта данных...")
    
    def on_limit_check_toggled(self, checked: bool):
        """Обрабатывает изменение состояния чекбокса ограничения записей"""
        self.limit_spinbox.setEnabled(checked)
    
    def validate_structure(self):
        """Проверяет структуру DBF файла"""
        if not self.dbf_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите DBF файл или директорию для проверки")
            return
        
        # Если выбрана директория, проверяем все типы сущностей
        if Path(self.dbf_path).is_dir():
            entity_types = ["units", "materials", "nomenclature", "composition"]
            dialog = ImportDialog(self.dbf_path, entity_types, False)
            dialog.exec()
            return
        
        # Определение типа сущности на основе имени файла
        file_name = Path(self.dbf_path).stem.lower()
        
        entity_type = None
        if "sc46" in file_name or "unit" in file_name:
            entity_type = "units"
        elif "sc25" in file_name or "material" in file_name:
            entity_type = "materials"
        elif "sc12" in file_name or "nomenclature" in file_name or "номенклатура" in file_name:
            entity_type = "nomenclature"
        elif "sc20" in file_name or "composition" in file_name or "затрат" in file_name:
            entity_type = "composition"
        
        if not entity_type:
            QMessageBox.warning(
                self, 
                "Предупреждение", 
                "Не удалось определить тип сущности по имени файла. "
                "Используйте диалог импорта для выбора типа сущности."
            )
            return
        
        # Открытие диалога импорта для проверки структуры
        dialog = ImportDialog(self.dbf_path, [entity_type], False)
        dialog.exec()
    
    def update_progress(self, message: str, progress: int):
        """Обновляет прогресс-бар и лог"""
        self.progress_bar.setValue(progress)
        self.log_message(message)
    
    def import_finished(self, results: dict):
        """Обрабатывает завершение импорта"""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        # Формирование сообщения о результатах
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        message = f"Импорт завершен. Успешно: {success_count}/{total_count}"
        
        if success_count == total_count:
            QMessageBox.information(self, "Успех", message)
            self.log_message(message)
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
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте данных:\n{error_message}")
        self.log_message(f"Ошибка: {error_message}")
    
    def set_ui_enabled(self, enabled: bool):
        """Включает или выключает элементы UI"""
        self.browse_button.setEnabled(enabled)
        self.import_button.setEnabled(enabled and bool(self.dbf_path))
        self.validate_button.setEnabled(enabled and bool(self.dbf_path))
        self.units_check.setEnabled(enabled)
        self.nomenclature_check.setEnabled(enabled)
        self.materials_check.setEnabled(enabled)
        self.composition_check.setEnabled(enabled)
        self.clear_data_check.setEnabled(enabled)
        self.limit_check.setEnabled(enabled)
        if enabled:
            self.limit_spinbox.setEnabled(self.limit_check.isChecked())
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_text.append(message)
        # Прокрутка к последнему сообщению
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Очищает лог"""
        self.log_text.clear()
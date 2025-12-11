"""Print settings dialog"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QPushButton, QGroupBox, QMessageBox,
                             QButtonGroup, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt
from ..services.print_form_service import PrintFormService


class PrintSettingsDialog(QDialog):
    """Dialog for configuring print form settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = PrintFormService()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Настройки печатных форм")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Format selection group
        format_group = QGroupBox("Формат печатных форм")
        format_layout = QVBoxLayout()
        
        self.format_button_group = QButtonGroup(self)
        
        self.pdf_radio = QRadioButton("PDF")
        self.excel_radio = QRadioButton("Excel")
        
        self.format_button_group.addButton(self.pdf_radio, 1)
        self.format_button_group.addButton(self.excel_radio, 2)
        
        format_layout.addWidget(self.pdf_radio)
        format_layout.addWidget(self.excel_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Templates path group
        templates_group = QGroupBox("Путь к шаблонам Excel")
        templates_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.templates_path_edit = QLineEdit()
        self.templates_path_edit.setReadOnly(True)
        path_layout.addWidget(QLabel("Папка:"))
        path_layout.addWidget(self.templates_path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_templates_path)
        path_layout.addWidget(browse_btn)
        
        templates_layout.addLayout(path_layout)
        
        # Create templates button
        create_templates_btn = QPushButton("Создать шаблоны печатных форм")
        create_templates_btn.clicked.connect(self.create_templates)
        templates_layout.addWidget(create_templates_btn)
        
        info_label = QLabel(
            "При выборе формата Excel программа будет использовать шаблоны из указанной папки.\n"
            "Если шаблоны не найдены, документы будут создаваться автоматически."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        templates_layout.addWidget(info_label)
        
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings"""
        # Load format
        format_type = self.service.get_print_format()
        if format_type == 'EXCEL':
            self.excel_radio.setChecked(True)
        else:
            self.pdf_radio.setChecked(True)
        
        # Load templates path
        templates_path = self.service.get_templates_path()
        self.templates_path_edit.setText(templates_path)
    
    def browse_templates_path(self):
        """Browse for templates directory"""
        current_path = self.templates_path_edit.text()
        path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для шаблонов",
            current_path
        )
        if path:
            self.templates_path_edit.setText(path)
    
    def save_settings(self):
        """Save settings"""
        try:
            # Save format
            if self.excel_radio.isChecked():
                format_type = 'EXCEL'
            else:
                format_type = 'PDF'
            
            success = self.service.set_print_format(format_type)
            
            if success:
                QMessageBox.information(
                    self,
                    "Успех",
                    "Настройки сохранены успешно"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось сохранить настройки"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка при сохранении настроек: {str(e)}"
            )
    
    def create_templates(self):
        """Create default templates"""
        reply = QMessageBox.question(
            self,
            "Создание шаблонов",
            "Создать шаблоны печатных форм?\n\n"
            "Будут созданы файлы:\n"
            "- estimate_template.xlsx (шаблон сметы)\n"
            "- daily_report_template.xlsx (шаблон ежедневного отчета)\n\n"
            "Вы сможете отредактировать их в Excel для настройки внешнего вида.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.service.create_templates()
            
            if success:
                QMessageBox.information(
                    self,
                    "Успех",
                    message
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    message
                )

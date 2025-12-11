"""Settings dialog for env.ini configuration"""
import os
import configparser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QLineEdit, QPushButton,
                             QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
                             QFileDialog, QLabel)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Dialog for editing env.ini settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config_file = 'env.ini'
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Настройки программы")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Auth tab
        auth_tab = self.create_auth_tab()
        self.tabs.addTab(auth_tab, "Авторизация")
        
        # Print forms tab
        print_tab = self.create_print_forms_tab()
        self.tabs.addTab(print_tab, "Печатные формы")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_auth_tab(self):
        """Create authentication settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Auth group
        auth_group = QGroupBox("Автоматический вход")
        auth_layout = QFormLayout()
        
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин для автоматического входа")
        auth_layout.addRow("Логин:", self.login_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Пароль для автоматического входа")
        auth_layout.addRow("Пароль:", self.password_edit)
        
        info_label = QLabel(
            "Эти данные используются для автоматического входа при запуске программы.\n"
            "Оставьте пустыми, чтобы отключить автоматический вход."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt; margin-top: 10px;")
        auth_layout.addRow(info_label)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_print_forms_tab(self):
        """Create print forms settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Format group
        format_group = QGroupBox("Формат печатных форм")
        format_layout = QVBoxLayout()
        
        self.format_button_group = QButtonGroup(self)
        
        self.pdf_radio = QRadioButton("PDF - для печати и просмотра")
        self.excel_radio = QRadioButton("Excel - для редактирования и обработки")
        
        self.format_button_group.addButton(self.pdf_radio, 1)
        self.format_button_group.addButton(self.excel_radio, 2)
        
        format_layout.addWidget(self.pdf_radio)
        format_layout.addWidget(self.excel_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Templates path group
        templates_group = QGroupBox("Шаблоны Excel")
        templates_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Папка с шаблонами:"))
        
        self.templates_path_edit = QLineEdit()
        self.templates_path_edit.setPlaceholderText("PrnForms")
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
            "Если шаблоны не найдены, документы будут создаваться автоматически.\n\n"
            "Нажмите 'Создать шаблоны', чтобы создать стандартные шаблоны,\n"
            "которые затем можно отредактировать в Excel."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt; margin-top: 10px;")
        templates_layout.addWidget(info_label)
        
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def load_settings(self):
        """Load settings from env.ini"""
        if not os.path.exists(self.config_file):
            return
        
        try:
            self.config.read(self.config_file, encoding='utf-8')
            
            # Load auth settings
            if self.config.has_section('Auth'):
                if self.config.has_option('Auth', 'login'):
                    self.login_edit.setText(self.config.get('Auth', 'login'))
                if self.config.has_option('Auth', 'password'):
                    self.password_edit.setText(self.config.get('Auth', 'password'))
            else:
                # Try to read old format (without sections)
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#') and not line.startswith('['):
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if key == 'login':
                                    self.login_edit.setText(value)
                                elif key == 'password':
                                    self.password_edit.setText(value)
                except:
                    pass
            
            # Load print forms settings
            if self.config.has_section('PrintForms'):
                if self.config.has_option('PrintForms', 'format'):
                    format_type = self.config.get('PrintForms', 'format').upper()
                    if format_type == 'EXCEL':
                        self.excel_radio.setChecked(True)
                    else:
                        self.pdf_radio.setChecked(True)
                else:
                    self.pdf_radio.setChecked(True)
                
                if self.config.has_option('PrintForms', 'templates_path'):
                    self.templates_path_edit.setText(self.config.get('PrintForms', 'templates_path'))
                else:
                    self.templates_path_edit.setText('PrnForms')
            else:
                self.pdf_radio.setChecked(True)
                self.templates_path_edit.setText('PrnForms')
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось загрузить настройки: {str(e)}"
            )
    
    def save_settings(self):
        """Save settings and close dialog"""
        if self.apply_settings():
            self.accept()
    
    def apply_settings(self):
        """Apply settings to env.ini"""
        try:
            # Ensure sections exist
            if not self.config.has_section('Auth'):
                self.config.add_section('Auth')
            if not self.config.has_section('PrintForms'):
                self.config.add_section('PrintForms')
            
            # Save auth settings
            self.config.set('Auth', 'login', self.login_edit.text())
            self.config.set('Auth', 'password', self.password_edit.text())
            
            # Save print forms settings
            if self.excel_radio.isChecked():
                self.config.set('PrintForms', 'format', 'EXCEL')
            else:
                self.config.set('PrintForms', 'format', 'PDF')
            
            templates_path = self.templates_path_edit.text().strip()
            if not templates_path:
                templates_path = 'PrnForms'
            self.config.set('PrintForms', 'templates_path', templates_path)
            
            # Write to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            QMessageBox.information(
                self,
                "Успех",
                "Настройки успешно сохранены"
            )
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить настройки: {str(e)}"
            )
            return False
    
    def browse_templates_path(self):
        """Browse for templates directory"""
        current_path = self.templates_path_edit.text()
        if not current_path:
            current_path = 'PrnForms'
        
        path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для шаблонов",
            current_path
        )
        if path:
            self.templates_path_edit.setText(path)
    
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
            try:
                from ..services.print_form_service import PrintFormService
                
                service = PrintFormService()
                success, message = service.create_templates()
                
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
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось создать шаблоны: {str(e)}"
                )

"""Settings dialog for env.ini configuration"""
import os
import configparser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QLineEdit, QPushButton,
                             QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
                             QFileDialog, QLabel)
from PyQt6.QtCore import Qt, QTimer


class SettingsDialog(QDialog):
    """Dialog for editing env.ini settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config_file = 'env.ini'
        self.init_ui()
        # load_settings() будет вызван после создания всех вкладок
        QTimer.singleShot(0, self.load_settings)
    
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
        
        # Interface tab
        interface_tab = self.create_interface_tab()
        self.tabs.addTab(interface_tab, "Интерфейс")
        
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
    
    def create_interface_tab(self):
        """Create interface settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Button appearance group
        button_group = QGroupBox("Внешний вид кнопок")
        button_layout = QVBoxLayout()
        
        # Font icons checkbox
        self.use_font_icons_checkbox = QRadioButton("Использовать иконки шрифтов для кнопок")
        self.use_text_icons_checkbox = QRadioButton("Использовать текстовые подписи для кнопок")
        self.use_both_icons_checkbox = QRadioButton("Использовать иконки и текст")
        
        self.icon_button_group = QButtonGroup(self)
        self.icon_button_group.addButton(self.use_font_icons_checkbox, 0)
        self.icon_button_group.addButton(self.use_text_icons_checkbox, 1)
        self.icon_button_group.addButton(self.use_both_icons_checkbox, 2)
        
        button_layout.addWidget(self.use_font_icons_checkbox)
        button_layout.addWidget(self.use_text_icons_checkbox)
        button_layout.addWidget(self.use_both_icons_checkbox)
        
        # Icon mappings info
        icons_info = QLabel(
            "Иконки шрифтов будут использоваться для стандартных команд:\n"
            "➕ Создать (Insert)\n"
            "📋 Копировать (F9)\n"
            "✏️ Изменить (F2)\n"
            "🗑️ Удалить (Delete)\n"
            "🔄 Обновить (F5)\n"
            "🖨️ Печать (F8)\n\n"
            "При выборе 'только иконки' всплывающие подсказки покажут назначение кнопок."
        )
        icons_info.setWordWrap(True)
        icons_info.setStyleSheet("color: gray; font-size: 9pt; margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;")
        button_layout.addWidget(icons_info)
        
        button_group.setLayout(button_layout)
        
        # Button position group
        position_group = QGroupBox("Расположение кнопок в документах")
        position_layout = QVBoxLayout()
        
        self.top_radio = QRadioButton("Кнопки вверху формы")
        self.bottom_radio = QRadioButton("Кнопки внизу формы (стандарт)")
        self.both_radio = QRadioButton("Кнопки и вверху, и внизу")
        
        self.position_button_group = QButtonGroup(self)
        self.position_button_group.addButton(self.top_radio, 0)
        self.position_button_group.addButton(self.bottom_radio, 1)
        self.position_button_group.addButton(self.both_radio, 2)
        
        position_layout.addWidget(self.top_radio)
        position_layout.addWidget(self.bottom_radio)
        position_layout.addWidget(self.both_radio)
        
        # Button order info
        position_info = QLabel(
            "Настройка определяет расположение кнопок действий:\n"
            "• Сохранить, Сохранить и закрыть, Провести, Отменить проведение, Печать, Закрыть\n"
            "• 'Кнопки вверху' - удобство при работе с формами\n"
            "• 'Кнопки и вверху, и внизу' - максимальная гибкость"
        )
        position_info.setWordWrap(True)
        position_info.setStyleSheet("color: gray; font-size: 9pt; margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;")
        position_layout.addWidget(position_info)
        
        position_group.setLayout(position_layout)
        layout.addWidget(position_group)
        
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
            
            # Load interface settings
            try:
                if self.config.has_section('Interface'):
                    if self.config.has_option('Interface', 'button_style'):
                        button_style = self.config.get('Interface', 'button_style')
                        if button_style == 'text':
                            if hasattr(self, 'use_text_icons_checkbox'):
                                self.use_text_icons_checkbox.setChecked(True)
                        elif button_style == 'both':
                            if hasattr(self, 'use_both_icons_checkbox'):
                                self.use_both_icons_checkbox.setChecked(True)
                        else:
                            if hasattr(self, 'use_font_icons_checkbox'):
                                self.use_font_icons_checkbox.setChecked(True)
                    else:
                        if hasattr(self, 'use_text_icons_checkbox'):
                            self.use_text_icons_checkbox.setChecked(True)  # Default
                        
                    # Load button position setting
                    if self.config.has_option('Interface', 'button_position'):
                        button_position = self.config.get('Interface', 'button_position')
                        if button_position == 'top':
                            if hasattr(self, 'top_radio'):
                                self.top_radio.setChecked(True)
                        elif button_position == 'both':
                            if hasattr(self, 'both_radio'):
                                self.both_radio.setChecked(True)
                        else:
                            if hasattr(self, 'bottom_radio'):
                                self.bottom_radio.setChecked(True)  # Default
                    else:
                        if hasattr(self, 'bottom_radio'):
                            self.bottom_radio.setChecked(True)  # Default
                else:
                    if hasattr(self, 'use_text_icons_checkbox'):
                        self.use_text_icons_checkbox.setChecked(True)  # Default
                    if hasattr(self, 'bottom_radio'):
                        self.bottom_radio.setChecked(True)  # Default
            except Exception as e:
                print(f"Warning: Could not load interface settings: {e}")
                # Set safe defaults
                if hasattr(self, 'use_text_icons_checkbox'):
                    self.use_text_icons_checkbox.setChecked(True)
                if hasattr(self, 'bottom_radio'):
                    self.bottom_radio.setChecked(True)
                
                # Ensure button_position option exists
                if not self.config.has_option('Interface', 'button_position'):
                    self.config.set('Interface', 'button_position', 'bottom')
                
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
            if not self.config.has_section('Interface'):
                self.config.add_section('Interface')
            
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
            
            # Save interface settings
            if self.use_font_icons_checkbox.isChecked():
                button_style = 'icons'
            elif self.use_both_icons_checkbox.isChecked():
                button_style = 'both'
            else:
                button_style = 'text'
            self.config.set('Interface', 'button_style', button_style)
            
            # Save button position setting
            if self.top_radio.isChecked():
                button_position = 'top'
            elif self.both_radio.isChecked():
                button_position = 'both'
            else:
                button_position = 'bottom'
            self.config.set('Interface', 'button_position', button_position)
            
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

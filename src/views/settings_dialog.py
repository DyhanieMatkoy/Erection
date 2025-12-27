"""Settings dialog for env.ini configuration"""
import os
import configparser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QLineEdit, QPushButton,
                             QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
                             QFileDialog, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QTimer


class SettingsDialog(QDialog):
    """Dialog for editing env.ini settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config_file = 'env.ini'
        
        # Initialize UI component references to prevent access errors
        self.use_font_icons_checkbox = None
        self.use_text_icons_checkbox = None
        self.use_both_icons_checkbox = None
        self.icon_button_group = None
        self.position_combo = None
        self.pdf_radio = None
        self.excel_radio = None
        self.format_button_group = None
        
        # Flag to track initialization state
        self._ui_initialized = False
        self._settings_loaded = False
        
        self.init_ui()
        
        # Use much longer delay and multiple validation steps
        QTimer.singleShot(500, self.validate_and_load_settings)
    
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
        
        # Sync tab
        sync_tab = self.create_sync_tab()
        self.tabs.addTab(sync_tab, "Синхронизация")
        
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
        
        # Mark UI as initialized
        self._ui_initialized = True
    
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
        
        # Create radio buttons with explicit parent
        self.pdf_radio = QRadioButton("PDF - для печати и просмотра", format_group)
        self.excel_radio = QRadioButton("Excel - для редактирования и обработки", format_group)
        
        # Create button group AFTER creating radio buttons
        self.format_button_group = QButtonGroup(format_group)
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
        
        # Create button style radio buttons with explicit parent
        self.use_font_icons_checkbox = QRadioButton("Использовать иконки шрифтов для кнопок", button_group)
        self.use_text_icons_checkbox = QRadioButton("Использовать текстовые подписи для кнопок", button_group)
        self.use_both_icons_checkbox = QRadioButton("Использовать иконки и текст", button_group)
        
        # Create button group AFTER creating radio buttons and set parent explicitly
        self.icon_button_group = QButtonGroup(button_group)
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
        layout.addWidget(button_group)
        
        # Button position group
        position_group = QGroupBox("Расположение кнопок в документах")
        position_layout = QVBoxLayout()
        
        # Create dropdown for button position
        position_label = QLabel("Выберите расположение кнопок:")
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "Кнопки вверху формы",
            "Кнопки внизу формы (стандарт)", 
            "Кнопки и вверху, и внизу"
        ])
        self.position_combo.setCurrentIndex(1)  # Default to bottom
        
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_combo)
        
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
    
    def create_sync_tab(self):
        """Create synchronization settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        
        
        # Alternative methods group
        alt_group = QGroupBox("Альтернативные способы отключения")
        alt_layout = QVBoxLayout()
        
        alt_info = QLabel(
            "Для временного отключения синхронизации также можно:\n"
            "1. Использовать файл disable_sync.bat (устанавливает переменную окружения)\n"
            "2. Использовать файл start_app_no_sync.bat (запуск с отключенной синхронизацией)\n"
            "3. Установить переменную окружения DISABLE_SYNC=true перед запуском"
        )
        alt_info.setWordWrap(True)
        alt_info.setStyleSheet("color: #6c757d; font-size: 9pt; margin-top: 10px; padding: 10px; background: #e9ecef; border-radius: 4px;")
        alt_layout.addWidget(alt_info)
        
        alt_group.setLayout(alt_layout)
        layout.addWidget(alt_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def validate_and_load_settings(self):
        """Validate UI components are ready and load settings with multiple retry attempts"""
        try:
            if not self._ui_initialized:
                print("UI not yet initialized, retrying in 200ms...")
                QTimer.singleShot(200, self.validate_and_load_settings)
                return
            
            # Validate all critical UI components exist and are accessible
            validation_passed = self.validate_ui_components()
            
            if not validation_passed:
                print("UI validation failed, retrying in 200ms...")
                QTimer.singleShot(200, self.validate_and_load_settings)
                return
            
            # All validations passed, proceed with loading
            self.safe_load_settings()
            
        except Exception as e:
            print(f"Error in validate_and_load_settings: {e}")
            # Final fallback - set safe defaults
            QTimer.singleShot(100, self.set_safe_defaults)
    
    def validate_ui_components(self):
        """Validate that all UI components are properly initialized and accessible"""
        try:
            # Test radio buttons by attempting to access their properties
            radio_buttons = [
                ('use_font_icons_checkbox', self.use_font_icons_checkbox),
                ('use_text_icons_checkbox', self.use_text_icons_checkbox),
                ('use_both_icons_checkbox', self.use_both_icons_checkbox),
                ('pdf_radio', self.pdf_radio),
                ('excel_radio', self.excel_radio)
            ]
            
            for name, button in radio_buttons:
                if button is None:
                    print(f"Validation failed: {name} is None")
                    return False
                
                # Test if we can access the button's properties without error
                try:
                    _ = button.isChecked()  # This will fail if button is deleted
                    _ = button.text()       # Additional validation
                except RuntimeError as e:
                    print(f"Validation failed: {name} is deleted or inaccessible: {e}")
                    return False
            
            # Test other components
            other_components = [
                ('position_combo', self.position_combo),
                ('icon_button_group', self.icon_button_group),
                ('format_button_group', self.format_button_group)
            ]
            
            for name, component in other_components:
                if component is None:
                    print(f"Validation failed: {name} is None")
                    return False
                
                try:
                    if hasattr(component, 'currentIndex'):
                        _ = component.currentIndex()
                    elif hasattr(component, 'checkedId'):
                        _ = component.checkedId()
                except RuntimeError as e:
                    print(f"Validation failed: {name} is deleted or inaccessible: {e}")
                    return False
            
            print("UI component validation passed")
            return True
            
        except Exception as e:
            print(f"Exception during UI validation: {e}")
            return False
    
    def safe_load_settings(self):
        """Safely load settings with comprehensive error handling"""
        try:
            if self._settings_loaded:
                print("Settings already loaded, skipping...")
                return
            
            # Double-check that all UI components exist and are properly initialized
            required_components = [
                ('use_font_icons_checkbox', 'Font icons radio button'),
                ('use_text_icons_checkbox', 'Text icons radio button'),
                ('use_both_icons_checkbox', 'Both icons radio button'),
                ('position_combo', 'Position dropdown'),
                ('pdf_radio', 'PDF radio button'),
                ('excel_radio', 'Excel radio button'),
                ('format_button_group', 'Format button group')
            ]
            
            missing_components = []
            for attr_name, description in required_components:
                if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
                    missing_components.append(f"{description} ({attr_name})")
            
            if missing_components:
                print(f"Warning: Missing UI components during load_settings: {missing_components}")
                self.set_safe_defaults()
                return
            
            # Add sync checkbox to required components
            required_components.extend([
                ('enable_sync_checkbox', 'Enable sync checkbox')
            ])
            
            missing_components = []
            for attr_name, description in required_components:
                if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
                    missing_components.append(f"{description} ({attr_name})")
            
            if missing_components:
                print(f"Warning: Missing UI components during load_settings: {missing_components}")
                self.set_safe_defaults()
                return
            
            # All components exist, proceed with loading settings
            self.load_settings()
            self._settings_loaded = True
            print("Settings loaded successfully")
            
        except Exception as e:
            print(f"Error in safe_load_settings: {e}")
            # Set safe defaults as fallback
            self.set_safe_defaults()
    
    def set_safe_defaults(self):
        """Set safe default values without accessing potentially problematic components"""
        try:
            # Set radio button defaults safely using the new safe method
            self.safe_set_radio_button(self.use_text_icons_checkbox, 'use_text_icons_checkbox')
            
            if hasattr(self, 'position_combo') and self.position_combo is not None:
                try:
                    self.position_combo.setCurrentIndex(1)  # Default to bottom
                except Exception as e:
                    print(f"Error setting position combo default: {e}")
            
            # Set print format radio button defaults safely
            self.safe_set_radio_button(self.pdf_radio, 'pdf_radio')
                
            print("Safe defaults applied successfully")
                
        except Exception as e:
            print(f"Warning: Could not set safe defaults: {e}")
    
    def load_settings(self):
        """Load settings from env.ini with improved error handling"""
        if not os.path.exists(self.config_file):
            print("Config file not found, using defaults")
            self.set_safe_defaults()
            return
        
        try:
            self.config.read(self.config_file, encoding='utf-8')
            
            # Load auth settings
            self.load_auth_settings()
            
            # Load print forms settings
            self.load_print_forms_settings()
            
            # Load interface settings
            self.load_interface_settings()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось загрузить настройки: {str(e)}\nИспользуются значения по умолчанию."
            )
            self.set_safe_defaults()
    
    def load_auth_settings(self):
        """Load authentication settings"""
        try:
            if self.login_edit is None or self.password_edit is None:
                print("Warning: Auth UI components not initialized")
                return
                
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
                except Exception as e:
                    print(f"Warning: Could not read old format auth settings: {e}")
        except Exception as e:
            print(f"Warning: Could not load auth settings: {e}")
    
    def load_print_forms_settings(self):
        """Load print forms settings"""
        try:
            if self.templates_path_edit is None:
                print("Warning: Templates path edit not initialized")
                return
                
            if self.config.has_section('PrintForms'):
                if self.config.has_option('PrintForms', 'format'):
                    format_type = self.config.get('PrintForms', 'format').upper()
                    if format_type == 'EXCEL' and hasattr(self, 'excel_radio') and self.excel_radio:
                        self.excel_radio.setChecked(True)
                    elif hasattr(self, 'pdf_radio') and self.pdf_radio:
                        self.pdf_radio.setChecked(True)
                elif hasattr(self, 'pdf_radio') and self.pdf_radio:
                    self.pdf_radio.setChecked(True)
                
                if self.config.has_option('PrintForms', 'templates_path'):
                    self.templates_path_edit.setText(self.config.get('PrintForms', 'templates_path'))
                else:
                    self.templates_path_edit.setText('PrnForms')
            else:
                if hasattr(self, 'pdf_radio') and self.pdf_radio:
                    self.pdf_radio.setChecked(True)
                self.templates_path_edit.setText('PrnForms')
        except Exception as e:
            print(f"Warning: Could not load print forms settings: {e}")
            # Set safe defaults
            if hasattr(self, 'pdf_radio') and self.pdf_radio:
                self.pdf_radio.setChecked(True)
            self.templates_path_edit.setText('PrnForms')
    
    def load_interface_settings(self):
        """Load interface settings with enhanced error handling"""
        try:
            if self.config.has_section('Interface'):
                # Load button style setting with individual radio button validation
                if self.config.has_option('Interface', 'button_style'):
                    button_style = self.config.get('Interface', 'button_style')
                    
                    # Validate each radio button before setting
                    if button_style == 'text':
                        if self.safe_set_radio_button(self.use_text_icons_checkbox, 'use_text_icons_checkbox'):
                            pass  # Successfully set
                        else:
                            print("Failed to set text icons radio button")
                    elif button_style == 'both':
                        if self.safe_set_radio_button(self.use_both_icons_checkbox, 'use_both_icons_checkbox'):
                            pass  # Successfully set
                        else:
                            print("Failed to set both icons radio button")
                    else:  # 'icons'
                        if self.safe_set_radio_button(self.use_font_icons_checkbox, 'use_font_icons_checkbox'):
                            pass  # Successfully set
                        else:
                            print("Failed to set font icons radio button")
                else:
                    # Default to text icons
                    self.safe_set_radio_button(self.use_text_icons_checkbox, 'use_text_icons_checkbox')
                    
                # Load button position setting
                if self.config.has_option('Interface', 'button_position'):
                    button_position = self.config.get('Interface', 'button_position')
                    if hasattr(self, 'position_combo') and self.position_combo:
                        try:
                            if button_position == 'top':
                                self.position_combo.setCurrentIndex(0)
                            elif button_position == 'both':
                                self.position_combo.setCurrentIndex(2)
                            else:
                                self.position_combo.setCurrentIndex(1)  # Default (bottom)
                        except Exception as e:
                            print(f"Error setting position combo: {e}")
                            self.position_combo.setCurrentIndex(1)  # Safe default
                elif hasattr(self, 'position_combo') and self.position_combo:
                    self.position_combo.setCurrentIndex(1)  # Default (bottom)
            else:
                # Set defaults for missing Interface section
                self.safe_set_radio_button(self.use_text_icons_checkbox, 'use_text_icons_checkbox')
                if hasattr(self, 'position_combo') and self.position_combo:
                    self.position_combo.setCurrentIndex(1)  # Default (bottom)
                    
        except Exception as e:
            print(f"Warning: Could not load interface settings: {e}")
            # Set safe defaults
            self.safe_set_radio_button(self.use_text_icons_checkbox, 'use_text_icons_checkbox')
            if hasattr(self, 'position_combo') and self.position_combo:
                try:
                    self.position_combo.setCurrentIndex(1)  # Default (bottom)
                except Exception as combo_e:
                    print(f"Error setting combo default: {combo_e}")
            
            # Ensure button_position option exists
            try:
                if not self.config.has_section('Interface'):
                    self.config.add_section('Interface')
                if not self.config.has_option('Interface', 'button_position'):
                    self.config.set('Interface', 'button_position', 'bottom')
            except Exception as config_e:
                print(f"Warning: Could not update config: {config_e}")
    
    
    
    def safe_set_radio_button(self, radio_button, button_name):
        """Safely set a radio button with comprehensive error handling"""
        try:
            if radio_button is None:
                print(f"Warning: {button_name} is None")
                return False
            
            # Test if button is accessible
            try:
                _ = radio_button.isChecked()  # This will fail if button is deleted
            except RuntimeError as e:
                print(f"Warning: {button_name} is deleted or inaccessible: {e}")
                return False
            
            # Set the button
            radio_button.setChecked(True)
            print(f"Successfully set {button_name}")
            return True
            
        except Exception as e:
            print(f"Error setting {button_name}: {e}")
            return False
    
    def save_settings(self):
        """Save settings and close dialog"""
        if self.apply_settings():
            self.accept()
    
    def apply_settings(self):
        """Apply settings to env.ini with improved error handling"""
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
            
            # Save print forms settings with safe radio button access
            try:
                if hasattr(self, 'excel_radio') and self.excel_radio and self.excel_radio.isChecked():
                    self.config.set('PrintForms', 'format', 'EXCEL')
                else:
                    self.config.set('PrintForms', 'format', 'PDF')
            except Exception as e:
                print(f"Warning: Could not read print format, defaulting to PDF: {e}")
                self.config.set('PrintForms', 'format', 'PDF')
            
            templates_path = self.templates_path_edit.text().strip()
            if not templates_path:
                templates_path = 'PrnForms'
            self.config.set('PrintForms', 'templates_path', templates_path)
            
            # Save interface settings with safe radio button access
            try:
                if hasattr(self, 'use_font_icons_checkbox') and self.use_font_icons_checkbox and self.use_font_icons_checkbox.isChecked():
                    button_style = 'icons'
                elif hasattr(self, 'use_both_icons_checkbox') and self.use_both_icons_checkbox and self.use_both_icons_checkbox.isChecked():
                    button_style = 'both'
                else:
                    button_style = 'text'  # Default or use_text_icons_checkbox is checked
                self.config.set('Interface', 'button_style', button_style)
            except Exception as e:
                print(f"Warning: Could not read button style, defaulting to text: {e}")
                self.config.set('Interface', 'button_style', 'text')
            
            # Save button position setting with safe combo box access
            try:
                if hasattr(self, 'position_combo') and self.position_combo:
                    position_index = self.position_combo.currentIndex()
                    if position_index == 0:
                        button_position = 'top'
                    elif position_index == 2:
                        button_position = 'both'
                    else:
                        button_position = 'bottom'
                else:
                    button_position = 'bottom'  # Safe default
                self.config.set('Interface', 'button_position', button_position)
            except Exception as e:
                print(f"Warning: Could not read button position, defaulting to bottom: {e}")
                self.config.set('Interface', 'button_position', 'bottom')
            
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

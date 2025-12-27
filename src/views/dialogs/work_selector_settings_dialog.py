"""Work selector settings dialog for desktop version"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QPushButton, QRadioButton, QCheckBox, QGroupBox,
                              QButtonGroup, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from ...services.user_settings_service import UserSettingsService


class WorkSelectorSettingsDialog(QDialog):
    """Dialog for configuring work selector behavior"""
    
    def __init__(self, parent=None, user_id=4):
        super().__init__(parent)
        self.user_id = user_id
        self.settings_service = UserSettingsService()
        self.current_settings = {}
        
        self.setup_ui()
        self.load_settings()
        self.setWindowTitle("Настройки селектора работ")
        self.setModal(True)
        self.resize(450, 350)
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        
        # Opening mode group
        mode_group = QGroupBox("Режим открытия селектора работ")
        mode_layout = QVBoxLayout()
        
        self.mode_button_group = QButtonGroup()
        
        self.modal_radio = QRadioButton("Модальное окно (блокирует основную форму)")
        self.modal_radio.setChecked(True)  # Default
        self.mode_button_group.addButton(self.modal_radio, 0)
        mode_layout.addWidget(self.modal_radio)
        
        self.non_modal_radio = QRadioButton("Немодальное окно (не блокирует основную форму)")
        self.mode_button_group.addButton(self.non_modal_radio, 1)
        mode_layout.addWidget(self.non_modal_radio)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Hierarchy display group
        hierarchy_group = QGroupBox("Отображение иерархии")
        hierarchy_layout = QVBoxLayout()
        
        self.hierarchy_button_group = QButtonGroup()
        
        self.flat_radio = QRadioButton("Плоский список (все работы в одном списке)")
        self.hierarchy_button_group.addButton(self.flat_radio, 0)
        hierarchy_layout.addWidget(self.flat_radio)
        
        self.tree_radio = QRadioButton("Иерархическое дерево (навигация по группам)")
        self.tree_radio.setChecked(True)  # Default
        self.hierarchy_button_group.addButton(self.tree_radio, 1)
        hierarchy_layout.addWidget(self.tree_radio)
        
        self.breadcrumb_radio = QRadioButton("С отображением путей (показывать полный путь)")
        self.hierarchy_button_group.addButton(self.breadcrumb_radio, 2)
        hierarchy_layout.addWidget(self.breadcrumb_radio)
        
        hierarchy_group.setLayout(hierarchy_layout)
        layout.addWidget(hierarchy_group)
        
        # Additional options group
        options_group = QGroupBox("Дополнительные настройки")
        options_layout = QVBoxLayout()
        
        self.show_hierarchy_controls_check = QCheckBox("Показывать элементы управления иерархией")
        self.show_hierarchy_controls_check.setChecked(True)  # Default
        self.show_hierarchy_controls_check.setToolTip("Показывать кнопки навигации и переключения режимов")
        options_layout.addWidget(self.show_hierarchy_controls_check)
        
        self.auto_expand_groups_check = QCheckBox("Автоматически разворачивать группы при открытии")
        self.auto_expand_groups_check.setChecked(True)  # Default
        self.auto_expand_groups_check.setToolTip("Показывать содержимое групп работ сразу при открытии селектора")
        options_layout.addWidget(self.auto_expand_groups_check)
        
        self.remember_last_position_check = QCheckBox("Запоминать последнюю позицию в списке")
        self.remember_last_position_check.setChecked(True)  # Default
        self.remember_last_position_check.setToolTip("Возвращаться к последней выбранной работе при повторном открытии")
        options_layout.addWidget(self.remember_last_position_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.on_save)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.clicked.connect(self.on_reset)
        self.reset_button.setToolTip("Сбросить все настройки к значениям по умолчанию")
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings from service"""
        try:
            self.current_settings = self.settings_service.get_work_selector_settings(self.user_id)
            
            # Apply settings to UI
            if self.current_settings.get('open_modal', True):
                self.modal_radio.setChecked(True)
            else:
                self.non_modal_radio.setChecked(True)
            
            hierarchy_mode = self.current_settings.get('default_hierarchy_mode', 'tree')
            if hierarchy_mode == 'flat':
                self.flat_radio.setChecked(True)
            elif hierarchy_mode == 'breadcrumb':
                self.breadcrumb_radio.setChecked(True)
            else:  # 'tree' or default
                self.tree_radio.setChecked(True)
            
            self.show_hierarchy_controls_check.setChecked(
                self.current_settings.get('show_hierarchy_controls', True)
            )
            
            self.auto_expand_groups_check.setChecked(
                self.current_settings.get('auto_expand_groups', True)
            )
            
            self.remember_last_position_check.setChecked(
                self.current_settings.get('remember_last_position', True)
            )
            
        except Exception as e:
            print(f"Error loading work selector settings: {e}")
            # Use defaults if loading fails
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.modal_radio.setChecked(True)
        self.tree_radio.setChecked(True)
        self.show_hierarchy_controls_check.setChecked(True)
        self.auto_expand_groups_check.setChecked(True)
        self.remember_last_position_check.setChecked(True)
    
    def on_reset(self):
        """Handle reset button"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Сбросить все настройки к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_to_defaults()
    
    def on_save(self):
        """Save settings and close dialog"""
        try:
            # Collect settings from UI
            settings = {
                'open_modal': self.modal_radio.isChecked(),
                'default_hierarchy_mode': self.get_selected_hierarchy_mode(),
                'show_hierarchy_controls': self.show_hierarchy_controls_check.isChecked(),
                'auto_expand_groups': self.auto_expand_groups_check.isChecked(),
                'remember_last_position': self.remember_last_position_check.isChecked()
            }
            
            # Save to service
            success = self.settings_service.set_work_selector_settings(self.user_id, settings)
            
            if success:
                self.current_settings = settings
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Ошибка",
                    "Не удалось сохранить настройки. Попробуйте еще раз."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Ошибка при сохранении настроек: {str(e)}"
            )
    
    def get_selected_hierarchy_mode(self):
        """Get selected hierarchy mode"""
        if self.flat_radio.isChecked():
            return 'flat'
        elif self.breadcrumb_radio.isChecked():
            return 'breadcrumb'
        else:
            return 'tree'
    
    def get_settings(self):
        """Get current settings"""
        return self.current_settings.copy()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.on_save()
        else:
            super().keyPressEvent(event)
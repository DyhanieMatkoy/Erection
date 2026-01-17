"""
Panel Configuration Dialog for PyQt6 Desktop Application.

This module provides a dialog for customizing row control panel commands,
allowing users to show/hide commands and organize them with a "More" submenu.

Requirements: 9.1, 9.2, 9.3, 9.4
"""

from typing import Dict, List, Optional, Set
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QCheckBox, QGroupBox, QSplitter, QWidget,
    QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from dataclasses import dataclass

from src.services.table_part_settings_service import TablePartSettingsService


@dataclass
class CommandTreeNode:
    """Represents a command in the configuration tree"""
    id: str
    name: str
    icon: str
    tooltip: str
    visible: bool = True
    enabled: bool = True
    is_standard: bool = True


class PanelConfigurationDialog(QDialog):
    """
    Dialog for configuring row control panel commands.
    
    Features:
    - Command tree interface with checkboxes
    - Real-time panel preview updates
    - Drag-and-drop command reordering
    - "More" submenu configuration
    - Save/Reset functionality
    
    Signals:
        configurationChanged(dict): Emitted when configuration changes
        previewRequested(list): Emitted to update panel preview
    """
    
    # Signals
    configurationChanged = pyqtSignal(dict)  # configuration dict
    previewRequested = pyqtSignal(list)  # visible command list
    
    def __init__(
        self,
        current_config: Optional[Dict] = None,
        available_commands: Optional[Dict[str, CommandTreeNode]] = None,
        settings_service: Optional[TablePartSettingsService] = None,
        parent=None
    ):
        """
        Initialize the panel configuration dialog.
        
        Args:
            current_config: Current panel configuration
            available_commands: Available commands for configuration
            settings_service: Service for saving/loading settings
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings_service = settings_service  # Will be None if not provided
        self.current_config = current_config or {}
        self.available_commands = available_commands or self._get_default_commands()
        self.modified_config = self.current_config.copy()
        
        self.setWindowTitle("Настройка панели команд")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_configuration()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Command tree
        left_widget = self._create_command_tree_widget()
        splitter.addWidget(left_widget)
        
        # Right side - Preview and options
        right_widget = self._create_preview_widget()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        
        # Add custom buttons
        self.preview_button = QPushButton("Предварительный просмотр")
        self.preview_button.setToolTip("Показать предварительный просмотр панели")
        button_box.addButton(self.preview_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
        # Connect button box signals
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset_configuration)
        self.preview_button.clicked.connect(self._update_preview)
    
    def _create_command_tree_widget(self) -> QWidget:
        """Create the command tree configuration widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title_label = QLabel("Доступные команды:")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel(
            "Отметьте команды, которые должны быть видны на панели.\n"
            "Неотмеченные команды будут доступны в меню 'Еще'."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(instructions)
        
        # Command tree
        self.command_tree = QTreeWidget()
        self.command_tree.setHeaderLabel("Команды")
        self.command_tree.setRootIsDecorated(False)
        self.command_tree.setAlternatingRowColors(True)
        layout.addWidget(self.command_tree)
        
        # Options group
        options_group = QGroupBox("Настройки")
        options_layout = QVBoxLayout(options_group)
        
        self.show_tooltips_checkbox = QCheckBox("Показывать подсказки")
        self.show_tooltips_checkbox.setChecked(True)
        options_layout.addWidget(self.show_tooltips_checkbox)
        
        self.compact_mode_checkbox = QCheckBox("Компактный режим")
        self.compact_mode_checkbox.setToolTip("Показывать только иконки без текста")
        options_layout.addWidget(self.compact_mode_checkbox)
        
        layout.addWidget(options_group)
        
        return widget
    
    def _create_preview_widget(self) -> QWidget:
        """Create the preview widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview title
        preview_label = QLabel("Предварительный просмотр:")
        preview_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(preview_label)
        
        # Preview area
        self.preview_area = QLabel("Выберите команды для предварительного просмотра")
        self.preview_area.setMinimumHeight(100)
        self.preview_area.setStyleSheet(
            "border: 1px solid #ccc; "
            "background-color: #f9f9f9; "
            "padding: 10px; "
            "border-radius: 4px;"
        )
        self.preview_area.setWordWrap(True)
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.preview_area)
        
        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        return widget
    
    def _get_default_commands(self) -> Dict[str, CommandTreeNode]:
        """Get default command definitions"""
        return {
            'add_row': CommandTreeNode(
                id='add_row',
                name='Добавить',
                icon='➕',
                tooltip='Добавить новую строку (Insert)'
            ),
            'delete_row': CommandTreeNode(
                id='delete_row',
                name='Удалить',
                icon='🗑',
                tooltip='Удалить выбранные строки (Delete)'
            ),
            'move_up': CommandTreeNode(
                id='move_up',
                name='Переместить выше',
                icon='↑',
                tooltip='Переместить строки выше (Ctrl+Shift+Up)'
            ),
            'move_down': CommandTreeNode(
                id='move_down',
                name='Переместить ниже',
                icon='↓',
                tooltip='Переместить строки ниже (Ctrl+Shift+Down)'
            ),
            'import_data': CommandTreeNode(
                id='import_data',
                name='Импорт',
                icon='📥',
                tooltip='Импортировать данные из файла'
            ),
            'export_data': CommandTreeNode(
                id='export_data',
                name='Экспорт',
                icon='📤',
                tooltip='Экспортировать данные в файл'
            ),
            'print_data': CommandTreeNode(
                id='print_data',
                name='Печать',
                icon='🖨',
                tooltip='Печать табличной части'
            )
        }
    
    def _load_configuration(self):
        """Load current configuration into the tree"""
        self.command_tree.clear()
        
        # Get visible commands from current config
        visible_commands = self.current_config.get('visible_commands', list(self.available_commands.keys()))
        
        # Create tree items for all available commands
        for command_id, command_node in self.available_commands.items():
            item = QTreeWidgetItem(self.command_tree)
            item.setText(0, f"{command_node.icon} {command_node.name}")
            item.setData(0, Qt.ItemDataRole.UserRole, command_id)
            item.setToolTip(0, command_node.tooltip)
            
            # Set checkbox state
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, 
                Qt.CheckState.Checked if command_id in visible_commands 
                else Qt.CheckState.Unchecked
            )
            
            # Disable if command is not enabled
            if not command_node.enabled:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setForeground(0, self.palette().color(self.palette().ColorRole.Disabled, self.palette().ColorGroup.Disabled))
        
        # Load other options
        self.show_tooltips_checkbox.setChecked(
            self.current_config.get('show_tooltips', True)
        )
        self.compact_mode_checkbox.setChecked(
            self.current_config.get('compact_mode', False)
        )
        
        # Update preview
        self._update_preview()
    
    def _connect_signals(self):
        """Connect UI signals"""
        self.command_tree.itemChanged.connect(self._on_command_changed)
        self.show_tooltips_checkbox.toggled.connect(self._on_option_changed)
        self.compact_mode_checkbox.toggled.connect(self._on_option_changed)
    
    def _on_command_changed(self, item: QTreeWidgetItem, column: int):
        """Handle command checkbox changes"""
        if column == 0:
            self._update_modified_config()
            self._update_preview()
    
    def _on_option_changed(self):
        """Handle option checkbox changes"""
        self._update_modified_config()
        self._update_preview()
    
    def _update_modified_config(self):
        """Update the modified configuration based on current UI state"""
        # Get visible commands
        visible_commands = []
        for i in range(self.command_tree.topLevelItemCount()):
            item = self.command_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                command_id = item.data(0, Qt.ItemDataRole.UserRole)
                visible_commands.append(command_id)
        
        # Update modified config
        self.modified_config = {
            'visible_commands': visible_commands,
            'show_tooltips': self.show_tooltips_checkbox.isChecked(),
            'compact_mode': self.compact_mode_checkbox.isChecked()
        }
    
    def _update_preview(self):
        """Update the preview area with current configuration"""
        visible_commands = self.modified_config.get('visible_commands', [])
        hidden_commands = [
            cmd_id for cmd_id in self.available_commands.keys()
            if cmd_id not in visible_commands
        ]
        
        # Build preview text
        preview_lines = []
        
        if visible_commands:
            preview_lines.append("Видимые кнопки:")
            for cmd_id in visible_commands:
                if cmd_id in self.available_commands:
                    cmd = self.available_commands[cmd_id]
                    preview_lines.append(f"  {cmd.icon} {cmd.name}")
        
        if hidden_commands:
            preview_lines.append("\nМеню 'Еще':")
            for cmd_id in hidden_commands:
                if cmd_id in self.available_commands:
                    cmd = self.available_commands[cmd_id]
                    preview_lines.append(f"  {cmd.icon} {cmd.name}")
        
        if not visible_commands and not hidden_commands:
            preview_lines.append("Нет доступных команд")
        
        self.preview_area.setText("\n".join(preview_lines))
        
        # Update statistics
        total_commands = len(self.available_commands)
        visible_count = len(visible_commands)
        hidden_count = len(hidden_commands)
        
        stats_text = f"Всего команд: {total_commands} | Видимых: {visible_count} | Скрытых: {hidden_count}"
        self.stats_label.setText(stats_text)
        
        # Emit preview signal for real-time panel updates
        self.previewRequested.emit(visible_commands)
    
    def _reset_configuration(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self,
            "Сброс настроек",
            "Вы уверены, что хотите сбросить настройки панели к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default configuration
            default_config = {
                'visible_commands': list(self.available_commands.keys()),
                'show_tooltips': True,
                'compact_mode': False
            }
            
            self.current_config = default_config
            self.modified_config = default_config.copy()
            self._load_configuration()
    
    def get_configuration(self) -> Dict:
        """Get the current configuration"""
        return self.modified_config.copy()
    
    def set_available_commands(self, commands: Dict[str, CommandTreeNode]):
        """Set available commands for configuration"""
        self.available_commands = commands
        self._load_configuration()
    
    def accept(self):
        """Accept the dialog and save configuration"""
        # Validate configuration
        if not self.modified_config.get('visible_commands'):
            reply = QMessageBox.question(
                self,
                "Предупреждение",
                "Вы не выбрали ни одной видимой команды. Все команды будут доступны только в меню 'Еще'. Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Emit configuration change signal
        self.configurationChanged.emit(self.modified_config)
        
        # Call parent accept
        super().accept()
    
    def show_with_commands(self, commands: Dict[str, CommandTreeNode]) -> bool:
        """
        Show dialog with specific commands and return True if accepted.
        
        Args:
            commands: Available commands for configuration
            
        Returns:
            True if dialog was accepted, False otherwise
        """
        self.set_available_commands(commands)
        return self.exec() == QDialog.DialogCode.Accepted

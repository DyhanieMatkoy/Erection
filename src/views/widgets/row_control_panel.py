"""
Row Control Panel Component for PyQt6 Desktop Application.

This module provides a reusable row control panel component that displays
standard buttons for managing table rows with proper state management and
tooltip support.

Requirements: 1.1, 1.2, 1.3
"""

from typing import Dict, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolBar, QPushButton, QMenu, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from dataclasses import dataclass

from src.services.table_part_command_manager import (
    TablePartCommandManager, CommandContext, FormCommand
)
from src.views.dialogs.panel_configuration_dialog import PanelConfigurationDialog
from src.data.models.table_part_models import TablePartCommand, PanelSettings
from src.views.dialogs.panel_configuration_dialog import (
    PanelConfigurationDialog, CommandTreeNode
)


@dataclass
class PanelButton:
    """Configuration for a panel button"""
    id: str
    name: str
    icon: str
    tooltip: str
    enabled: bool = True
    visible: bool = True
    requires_selection: bool = False


class RowControlPanel(QWidget):
    """
    Reusable row control panel component.
    
    Displays standard buttons for row management:
    - Add (Добавить)
    - Delete (Удалить)
    - Move Up (Переместить выше)
    - Move Down (Переместить ниже)
    - Import (Импорт)
    - Export (Экспорт)
    - Print (Печать)
    
    Features:
    - Button state management based on row selection
    - Tooltip support for all buttons
    - Customizable button visibility
    - "More" menu for hidden commands
    - Customization dialog support
    
    Signals:
        commandTriggered(str): Emitted when a button is clicked with command ID
        customizeRequested(): Emitted when customization is requested
    """
    
    # Signals
    commandTriggered = pyqtSignal(str)  # command_id
    customizeRequested = pyqtSignal()
    
    def __init__(
        self,
        visible_commands: Optional[List[str]] = None,
        command_manager: Optional[TablePartCommandManager] = None,
        parent=None
    ):
        """
        Initialize the row control panel.
        
        Args:
            visible_commands: List of command IDs to display. If None, shows default commands.
            command_manager: Command manager for form integration. If None, creates a new one.
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Default visible commands if not specified
        if visible_commands is None:
            visible_commands = [
                'add_row',
                'delete_row',
                'move_up',
                'move_down',
                'import_data',
                'export_data',
                'print_data'
            ]
        
        self.visible_commands = visible_commands
        self.buttons: Dict[str, QAction] = {}
        self.has_selection = False
        self.has_rows = False
        self.is_first_row_selected = False
        self.is_last_row_selected = False
        
        # Command manager for form integration
        self.command_manager = command_manager or TablePartCommandManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Create toolbar for buttons
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(self.toolbar.iconSize() * 0.8)  # Slightly smaller icons
        
        # Define all standard buttons
        self.standard_buttons = self._create_standard_buttons()
        
        # Add visible buttons to toolbar
        for command_id in self.visible_commands:
            if command_id in self.standard_buttons:
                button_config = self.standard_buttons[command_id]
                action = self._create_action(button_config)
                self.buttons[command_id] = action
                self.toolbar.addAction(action)
        
        # Add "More" menu for hidden commands
        hidden_commands = [
            cmd_id for cmd_id in self.standard_buttons.keys()
            if cmd_id not in self.visible_commands
        ]
        
        if hidden_commands:
            self.toolbar.addSeparator()
            more_button = self._create_more_menu(hidden_commands)
            self.toolbar.addWidget(more_button)
        
        # Add customization button
        self.toolbar.addSeparator()
        customize_action = QAction("⚙️", self)
        customize_action.setToolTip("Настроить панель")
        customize_action.triggered.connect(self._show_configuration_dialog)
        self.toolbar.addAction(customize_action)
        
        layout.addWidget(self.toolbar)
        layout.addStretch()
    
    def _create_standard_buttons(self) -> Dict[str, PanelButton]:
        """Create standard button configurations"""
        return {
            'add_row': PanelButton(
                id='add_row',
                name='Добавить',
                icon='➕',
                tooltip='Добавить новую строку (Insert)',
                requires_selection=False
            ),
            'delete_row': PanelButton(
                id='delete_row',
                name='Удалить',
                icon='🗑',
                tooltip='Удалить выбранные строки (Delete)',
                requires_selection=True
            ),
            'move_up': PanelButton(
                id='move_up',
                name='Выше',
                icon='↑',
                tooltip='Переместить строки выше (Ctrl+Shift+Up)',
                requires_selection=True
            ),
            'move_down': PanelButton(
                id='move_down',
                name='Ниже',
                icon='↓',
                tooltip='Переместить строки ниже (Ctrl+Shift+Down)',
                requires_selection=True
            ),
            'import_data': PanelButton(
                id='import_data',
                name='Импорт',
                icon='📥',
                tooltip='Импортировать данные из файла',
                requires_selection=False
            ),
            'export_data': PanelButton(
                id='export_data',
                name='Экспорт',
                icon='📤',
                tooltip='Экспортировать данные в файл',
                requires_selection=False
            ),
            'print_data': PanelButton(
                id='print_data',
                name='Печать',
                icon='🖨',
                tooltip='Печать табличной части',
                requires_selection=False
            )
        }
    
    def _create_action(self, button_config: PanelButton) -> QAction:
        """Create a QAction from button configuration"""
        action = QAction(f"{button_config.icon} {button_config.name}", self)
        action.setToolTip(button_config.tooltip)
        action.setData(button_config.id)
        action.setEnabled(button_config.enabled)
        action.triggered.connect(
            lambda checked, cmd_id=button_config.id: self._execute_command_with_manager(cmd_id)
        )
        return action
    
    def _create_more_menu(self, hidden_command_ids: List[str]) -> QToolButton:
        """Create 'More' menu button for hidden commands"""
        more_button = QToolButton()
        more_button.setText("Еще")
        more_button.setToolTip("Дополнительные команды")
        more_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        more_menu = QMenu(more_button)
        
        for command_id in hidden_command_ids:
            if command_id in self.standard_buttons:
                button_config = self.standard_buttons[command_id]
                action = QAction(
                    f"{button_config.icon} {button_config.name}",
                    more_menu
                )
                action.setToolTip(button_config.tooltip)
                action.setData(button_config.id)
                action.triggered.connect(
                    lambda checked, cmd_id=button_config.id: self._execute_command_with_manager(cmd_id)
                )
                more_menu.addAction(action)
                self.buttons[command_id] = action
        
        more_button.setMenu(more_menu)
        return more_button
    
    def update_button_states(
        self,
        has_selection: bool,
        has_rows: bool,
        is_first_row_selected: bool = False,
        is_last_row_selected: bool = False
    ):
        """
        Update button enabled states based on current selection.
        
        Args:
            has_selection: Whether any rows are selected
            has_rows: Whether the table has any rows
            is_first_row_selected: Whether the first row is selected
            is_last_row_selected: Whether the last row is selected
        
        Requirements: 1.4, 1.5, 1.6
        """
        self.has_selection = has_selection
        self.has_rows = has_rows
        self.is_first_row_selected = is_first_row_selected
        self.is_last_row_selected = is_last_row_selected
        
        # Update button states
        for command_id, action in self.buttons.items():
            button_config = self.standard_buttons.get(command_id)
            if not button_config:
                continue
            
            # Determine if button should be enabled
            enabled = True
            
            if command_id == 'delete_row':
                # Delete requires selection
                enabled = has_selection
            
            elif command_id == 'move_up':
                # Move up requires selection and not first row
                enabled = has_selection and not is_first_row_selected
            
            elif command_id == 'move_down':
                # Move down requires selection and not last row
                enabled = has_selection and not is_last_row_selected
            
            elif command_id == 'export_data':
                # Export requires rows
                enabled = has_rows
            
            action.setEnabled(enabled)
    
    def set_visible_commands(self, command_ids: List[str]):
        """
        Update which commands are visible on the panel.
        
        Args:
            command_ids: List of command IDs to display
        """
        self.visible_commands = command_ids
        
        # Rebuild the UI with new configuration
        # Clear existing toolbar
        self.toolbar.clear()
        self.buttons.clear()
        
        # Recreate toolbar with new visible commands
        for command_id in self.visible_commands:
            if command_id in self.standard_buttons:
                button_config = self.standard_buttons[command_id]
                action = self._create_action(button_config)
                self.buttons[command_id] = action
                self.toolbar.addAction(action)
        
        # Recreate "More" menu
        hidden_commands = [
            cmd_id for cmd_id in self.standard_buttons.keys()
            if cmd_id not in self.visible_commands
        ]
        
        if hidden_commands:
            self.toolbar.addSeparator()
            more_button = self._create_more_menu(hidden_commands)
            self.toolbar.addWidget(more_button)
        
        # Re-add customization button
        self.toolbar.addSeparator()
        customize_action = QAction("⚙️", self)
        customize_action.setToolTip("Настроить панель")
        customize_action.triggered.connect(self._show_configuration_dialog)
        self.toolbar.addAction(customize_action)
        
        # Update button states
        self.update_button_states(
            self.has_selection,
            self.has_rows,
            self.is_first_row_selected,
            self.is_last_row_selected
        )
    
    def _show_configuration_dialog(self):
        """
        Show the panel configuration dialog.
        
        Requirements: 9.1, 9.2, 9.3, 9.4
        """
        # Convert standard buttons to TablePartCommand objects
        available_commands = []
        for cmd_id, button_config in self.standard_buttons.items():
            command = TablePartCommand(
                id=cmd_id,
                name=button_config.name,
                icon=button_config.icon,
                tooltip=button_config.tooltip,
                enabled=button_config.enabled,
                visible=cmd_id in self.visible_commands,
                position=list(self.standard_buttons.keys()).index(cmd_id) + 1,
                requires_selection=button_config.requires_selection
            )
            available_commands.append(command)
        
        # Create panel settings
        panel_settings = PanelSettings(
            visible_commands=self.visible_commands.copy(),
            button_size="medium",
            show_tooltips=True,
            compact_mode=False
        )
        
        # Show configuration dialog
        dialog = PanelConfigurationDialog(
            available_commands=available_commands,
            current_visible_commands=self.visible_commands,
            panel_settings=panel_settings,
            parent=self
        )
        
        # Connect real-time updates
        dialog.configurationChanged.connect(self._on_configuration_changed)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply final configuration
            commands, new_panel_settings = dialog.get_configuration()
            self._apply_configuration(commands, new_panel_settings)
            
            # Emit signal for external handling (e.g., saving to settings)
            self.customizeRequested.emit()
    
    def _on_configuration_changed(self, commands: List[TablePartCommand], visible_command_ids: List[str]):
        """
        Handle real-time configuration changes from dialog.
        
        Requirements: 9.2
        """
        # Apply configuration immediately for real-time preview
        self.set_visible_commands(visible_command_ids)
    
    def _apply_configuration(self, commands: List[TablePartCommand], panel_settings: PanelSettings):
        """
        Apply the final configuration from the dialog.
        
        Requirements: 9.4
        """
        # Update visible commands
        self.set_visible_commands(panel_settings.visible_commands)
        
        # Store panel settings for future use
        self.panel_settings = panel_settings
        
        # Update command configurations
        for command in commands:
            if command.id in self.standard_buttons:
                button_config = self.standard_buttons[command.id]
                button_config.enabled = command.enabled
                button_config.visible = command.visible
    
    def get_visible_commands(self) -> List[str]:
        """Get list of currently visible command IDs"""
        return self.visible_commands.copy()
    
    def enable_command(self, command_id: str, enabled: bool = True):
        """
        Enable or disable a specific command.
        
        Args:
            command_id: ID of the command to enable/disable
            enabled: Whether to enable (True) or disable (False) the command
        """
        if command_id in self.buttons:
            self.buttons[command_id].setEnabled(enabled)
    
    def set_command_visible(self, command_id: str, visible: bool = True):
        """
        Show or hide a specific command.
        
        Args:
            command_id: ID of the command to show/hide
            visible: Whether to show (True) or hide (False) the command
        """
        if command_id in self.buttons:
            self.buttons[command_id].setVisible(visible)
    
    def register_form_instance(self, form_instance):
        """
        Register a form instance for command discovery and integration.
        
        Args:
            form_instance: Form instance to discover commands from
            
        Requirements: 2.1, 2.2
        """
        discovered_commands = self.command_manager.discover_and_register_commands(form_instance)
        
        # Update button states based on discovered commands
        self._update_form_command_integration()
        
        return discovered_commands
    
    def _execute_command_with_manager(self, command_id: str):
        """
        Execute command through command manager if available, otherwise emit signal.
        
        Requirements: 2.3, 2.4
        """
        # Create command context
        context = CommandContext(
            selected_rows=self._get_selected_rows(),
            table_data=self._get_table_data(),
            additional_data={}
        )
        
        # Try to execute through command manager first
        if self.command_manager.registered_commands:
            result = self.command_manager.execute_command(command_id, context)
            if result.success:
                # Emit signal with result
                self.commandTriggered.emit(command_id)
                return
        
        # Fall back to emitting signal for standard handling
        self.commandTriggered.emit(command_id)
    
    def _update_form_command_integration(self):
        """
        Update button states based on registered form commands.
        
        Requirements: 2.5
        """
        # Create current context
        context = CommandContext(
            selected_rows=self._get_selected_rows(),
            table_data=self._get_table_data(),
            additional_data={}
        )
        
        # Update command states through manager
        command_states = self.command_manager.update_command_states(context)
        
        # Apply states to buttons
        for command_id, enabled in command_states.items():
            if command_id in self.buttons:
                self.buttons[command_id].setEnabled(enabled)
    
    def _get_selected_rows(self) -> List[int]:
        """Get currently selected row indices (to be overridden by subclasses)"""
        return []
    
    def _get_table_data(self) -> List[Dict]:
        """Get current table data (to be overridden by subclasses)"""
        return []
    
    def update_context_and_states(
        self,
        selected_rows: List[int],
        table_data: List[Dict],
        additional_data: Optional[Dict] = None
    ):
        """
        Update command context and refresh button states.
        
        Args:
            selected_rows: List of selected row indices
            table_data: Current table data
            additional_data: Additional context data
            
        Requirements: 2.5
        """
        context = CommandContext(
            selected_rows=selected_rows,
            table_data=table_data,
            additional_data=additional_data or {}
        )
        
        # Update states through command manager
        command_states = self.command_manager.update_command_states(context)
        
        # Apply to buttons
        for command_id, enabled in command_states.items():
            if command_id in self.buttons:
                self.buttons[command_id].setEnabled(enabled)
        
        # Also update standard button states
        self.update_button_states(
            has_selection=len(selected_rows) > 0,
            has_rows=len(table_data) > 0,
            is_first_row_selected=0 in selected_rows if selected_rows else False,
            is_last_row_selected=(len(table_data) - 1) in selected_rows if selected_rows and table_data else False
        )
    def _show_configuration_dialog(self):
        """
        Show the panel configuration dialog.
        
        Requirements: 9.1, 9.2, 9.3, 9.4
        """
        # Convert standard buttons to CommandTreeNode format
        available_commands = {}
        for cmd_id, button_config in self.standard_buttons.items():
            available_commands[cmd_id] = CommandTreeNode(
                id=cmd_id,
                name=button_config.name,
                icon=button_config.icon,
                tooltip=button_config.tooltip,
                visible=cmd_id in self.visible_commands,
                enabled=button_config.enabled,
                is_standard=True
            )
        
        # Create current configuration
        current_config = {
            'visible_commands': self.visible_commands.copy(),
            'show_tooltips': True,  # TODO: Get from settings
            'compact_mode': False   # TODO: Get from settings
        }
        
        # Create and show dialog
        dialog = PanelConfigurationDialog(
            current_config=current_config,
            available_commands=available_commands,
            parent=self
        )
        
        # Connect signals for real-time preview
        dialog.previewRequested.connect(self._apply_preview_configuration)
        
        # Show dialog and handle result
        if dialog.exec() == PanelConfigurationDialog.DialogCode.Accepted:
            new_config = dialog.get_configuration()
            self._apply_configuration(new_config)
            
            # Emit configuration change signal
            self.customizeRequested.emit()
    
    def _apply_preview_configuration(self, visible_commands: List[str]):
        """
        Apply configuration for preview (temporary).
        
        Args:
            visible_commands: List of command IDs to show
        """
        # Temporarily update visible commands for preview
        # This could be enhanced to show actual preview without changing the panel
        pass
    
    def _apply_configuration(self, config: Dict):
        """
        Apply the new panel configuration.
        
        Args:
            config: Configuration dictionary with visible_commands, show_tooltips, compact_mode
            
        Requirements: 9.2, 9.3
        """
        # Update visible commands
        new_visible_commands = config.get('visible_commands', [])
        self.set_visible_commands(new_visible_commands)
        
        # TODO: Apply other settings like show_tooltips and compact_mode
        # This would require extending the panel to support these options
        
        # Save configuration to settings service if available
        # TODO: Implement settings persistence
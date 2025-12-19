"""
Base table part component for PyQt6 desktop application.

This module provides the foundation for all document table parts,
implementing common functionality for row management, keyboard shortcuts,
and integration with form commands.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QToolBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QIcon
from dataclasses import dataclass
from enum import Enum
import logging

from ...services.table_part_keyboard_handler import (
    TablePartKeyboardHandler, ShortcutAction, ShortcutContext,
    create_keyboard_handler, create_table_context
)
from ...services.table_part_calculation_engine import (
    TablePartCalculationEngine, CalculationResult, PerformanceMetrics,
    create_calculation_engine
)
from .calculation_performance_monitor import (
    CalculationPerformanceMonitor, PerformanceStatus, create_performance_monitor
)
from ...services.table_part_settings_service import TablePartSettingsService
from ...data.models.table_part_models import TablePartSettingsData

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of table part commands"""
    ADD_ROW = "add_row"
    DELETE_ROW = "delete_row"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    IMPORT_DATA = "import_data"
    EXPORT_DATA = "export_data"
    PRINT_DATA = "print_data"
    COPY_ROWS = "copy_rows"
    PASTE_ROWS = "paste_rows"


@dataclass
class TablePartCommand:
    """Configuration for a table part command"""
    id: str
    name: str
    icon: str
    tooltip: str
    shortcut: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    form_method: Optional[str] = None
    position: int = 0


@dataclass
class TablePartConfiguration:
    """Configuration for table part behavior and appearance"""
    table_id: str
    document_type: str
    available_commands: List[TablePartCommand]
    visible_commands: List[str]
    keyboard_shortcuts_enabled: bool = True
    auto_calculation_enabled: bool = True
    drag_drop_enabled: bool = True
    calculation_timeout_ms: int = 100
    total_calculation_timeout_ms: int = 200


class BaseTablePart(QWidget):
    """
    Base class for all document table parts.
    
    Provides common functionality for:
    - Row control panel with standard buttons
    - Keyboard shortcuts integration
    - Command management and form integration
    - User settings persistence
    - Automatic calculations
    """
    
    # Signals
    rowSelectionChanged = pyqtSignal(list)  # List of selected row indices
    dataChanged = pyqtSignal(int, str, object)  # row, column, new_value
    commandExecuted = pyqtSignal(str, dict)  # command_id, context
    calculationRequested = pyqtSignal(int, str)  # row, column
    totalCalculationRequested = pyqtSignal()
    
    def __init__(self, config: TablePartConfiguration, parent=None, db_session=None, user_id: Optional[int] = None):
        super().__init__(parent)
        self.config = config
        self.form_commands: Dict[str, Callable] = {}
        self.db_session = db_session
        self.user_id = user_id
        self.settings_service = None
        self.user_settings: Optional[TablePartSettingsData] = None
        
        # Initialize settings service if database session is provided
        if self.db_session:
            self.settings_service = TablePartSettingsService(self.db_session)
        
        self.calculation_timer = QTimer()
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self._perform_calculations)
        
        self.total_calculation_timer = QTimer()
        self.total_calculation_timer.setSingleShot(True)
        self.total_calculation_timer.timeout.connect(self._perform_total_calculations)
        
        # Initialize calculation engine
        self.calculation_engine = create_calculation_engine()
        self.calculation_engine.set_performance_thresholds(
            config.calculation_timeout_ms,
            config.total_calculation_timeout_ms
        )
        
        # Initialize performance monitor
        self.performance_monitor = create_performance_monitor()
        self.performance_monitor.hide()  # Hidden by default
        
        self._connect_calculation_signals()
        
        # Initialize keyboard handler
        self.keyboard_handler = create_keyboard_handler(self)
        self._setup_keyboard_handlers()
        
        # Load user settings
        self._load_user_settings()
        
        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create row control panel
        self.control_panel = self._create_control_panel()
        layout.addWidget(self.control_panel)
        
        # Create table widget
        self.table = self._create_table_widget()
        layout.addWidget(self.table)
        
        # Add performance monitor (initially hidden)
        layout.addWidget(self.performance_monitor)
    
    def _create_control_panel(self) -> QToolBar:
        """Create the row control panel with command buttons"""
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # Standard commands with icons and tooltips
        standard_commands = {
            CommandType.ADD_ROW.value: TablePartCommand(
                id=CommandType.ADD_ROW.value,
                name="Добавить",
                icon="➕",
                tooltip="Добавить новую строку (Insert)",
                shortcut="Insert"
            ),
            CommandType.DELETE_ROW.value: TablePartCommand(
                id=CommandType.DELETE_ROW.value,
                name="Удалить",
                icon="🗑",
                tooltip="Удалить выбранные строки (Delete)",
                shortcut="Delete"
            ),
            CommandType.MOVE_UP.value: TablePartCommand(
                id=CommandType.MOVE_UP.value,
                name="Выше",
                icon="↑",
                tooltip="Переместить строки выше (Ctrl+Shift+Up)",
                shortcut="Ctrl+Shift+Up"
            ),
            CommandType.MOVE_DOWN.value: TablePartCommand(
                id=CommandType.MOVE_DOWN.value,
                name="Ниже",
                icon="↓",
                tooltip="Переместить строки ниже (Ctrl+Shift+Down)",
                shortcut="Ctrl+Shift+Down"
            ),
            CommandType.IMPORT_DATA.value: TablePartCommand(
                id=CommandType.IMPORT_DATA.value,
                name="Импорт",
                icon="📥",
                tooltip="Импортировать данные из файла"
            ),
            CommandType.EXPORT_DATA.value: TablePartCommand(
                id=CommandType.EXPORT_DATA.value,
                name="Экспорт",
                icon="📤",
                tooltip="Экспортировать данные в файл"
            ),
            CommandType.PRINT_DATA.value: TablePartCommand(
                id=CommandType.PRINT_DATA.value,
                name="Печать",
                icon="🖨",
                tooltip="Печать табличной части"
            )
        }
        
        # Add visible commands to toolbar
        for command_id in self.config.visible_commands:
            if command_id in standard_commands:
                cmd = standard_commands[command_id]
                action = QAction(cmd.name, self)
                action.setToolTip(cmd.tooltip)
                action.setData(cmd.id)
                action.triggered.connect(lambda checked, cmd_id=cmd.id: self._execute_command(cmd_id))
                toolbar.addAction(action)
        
        # Add "More" menu for hidden commands
        hidden_commands = [cmd for cmd_id, cmd in standard_commands.items() 
                          if cmd_id not in self.config.visible_commands]
        if hidden_commands:
            more_action = QAction("Еще", self)
            more_menu = QMenu()
            for cmd in hidden_commands:
                menu_action = QAction(cmd.name, self)
                menu_action.setToolTip(cmd.tooltip)
                menu_action.setData(cmd.id)
                menu_action.triggered.connect(lambda checked, cmd_id=cmd.id: self._execute_command(cmd_id))
                more_menu.addAction(menu_action)
            more_action.setMenu(more_menu)
            toolbar.addAction(more_action)
        
        # Add customization option
        toolbar.addSeparator()
        customize_action = QAction("Настроить панель", self)
        customize_action.triggered.connect(self._customize_panel)
        toolbar.addAction(customize_action)
        
        return toolbar
    
    def _setup_keyboard_handlers(self):
        """Setup keyboard shortcut handlers"""
        # Register action handlers for standard shortcuts
        self.keyboard_handler.register_action_handler(
            ShortcutAction.ADD_ROW, 
            lambda ctx: self._execute_command(CommandType.ADD_ROW.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.DELETE_ROW, 
            lambda ctx: self._execute_command(CommandType.DELETE_ROW.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.COPY_ROWS, 
            lambda ctx: self._execute_command(CommandType.COPY_ROWS.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.PASTE_ROWS, 
            lambda ctx: self._execute_command(CommandType.PASTE_ROWS.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.MOVE_ROW_UP, 
            lambda ctx: self._execute_command(CommandType.MOVE_UP.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.MOVE_ROW_DOWN, 
            lambda ctx: self._execute_command(CommandType.MOVE_DOWN.value)
        )
        self.keyboard_handler.register_action_handler(
            ShortcutAction.OPEN_REFERENCE_SELECTOR, 
            lambda ctx: self._execute_command("open_reference_selector")
        )
        
        # Connect keyboard handler signals
        self.keyboard_handler.shortcutTriggered.connect(self._on_shortcut_triggered)
        self.keyboard_handler.shortcutBlocked.connect(self._on_shortcut_blocked)
    
    def _create_table_widget(self) -> QTableWidget:
        """Create and configure the table widget"""
        table = QTableWidget()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        
        # Enable drag and drop if configured
        if self.config.drag_drop_enabled:
            table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            table.setDefaultDropAction(Qt.DropAction.MoveAction)
            table.setDragEnabled(True)
            table.setAcceptDrops(True)
            table.setDropIndicatorShown(True)
            
            # Connect drag and drop signals
            table.model().rowsMoved.connect(self._on_rows_moved)
        
        return table
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for table operations"""
        if not self.config.keyboard_shortcuts_enabled:
            self.keyboard_handler.set_enabled(False)
            return
        
        # The keyboard handler is already set up in _setup_keyboard_handlers()
        # This method is kept for compatibility but shortcuts are now handled
        # by the dedicated keyboard handler
        pass
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)
    
    def _on_rows_moved(self, parent, start, end, destination, row):
        """Handle rows moved via drag and drop"""
        logger.debug(f"Rows moved: {start}-{end} to {row}")
        
        # Trigger recalculation if enabled
        if self.config.auto_calculation_enabled:
            self.total_calculation_timer.stop()
            self.total_calculation_timer.start(self.config.total_calculation_timeout_ms)
    
    def _on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = list(set(item.row() for item in self.table.selectedItems()))
        self.rowSelectionChanged.emit(selected_rows)
        self._update_command_states(selected_rows)
        self._update_keyboard_context(selected_rows)
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle table item changes"""
        row = item.row()
        column = self.table.horizontalHeaderItem(item.column()).text()
        value = item.text()
        
        self.dataChanged.emit(row, column, value)
        
        # Trigger calculations if enabled
        if self.config.auto_calculation_enabled:
            self._schedule_calculation(row, column)
    
    def _schedule_calculation(self, row: int, column: str):
        """Schedule automatic calculation with debouncing"""
        self.calculation_timer.stop()
        self.calculation_timer.start(self.config.calculation_timeout_ms)
        self._pending_calculation = (row, column)
    
    def _perform_calculations(self):
        """Perform pending calculations"""
        if hasattr(self, '_pending_calculation'):
            row, column = self._pending_calculation
            
            # Get current row data
            row_data = self._get_row_data(row)
            if row_data:
                # Perform calculation using the engine
                result = self.calculation_engine.calculate_field(row_data, column, self._get_table_data())
                
                if result.success and result.value is not None:
                    # Update the table with calculated value
                    self._update_calculated_field(row, result.rule_id or column, result.value)
                
                self.calculationRequested.emit(row, column)
            
            # Schedule total calculation
            self.total_calculation_timer.stop()
            self.total_calculation_timer.start(self.config.total_calculation_timeout_ms)
    
    def _perform_total_calculations(self):
        """Perform total calculations"""
        all_data = self._get_table_data()
        totals = self.calculation_engine.calculate_totals(all_data)
        
        # Update UI with totals
        self._update_document_totals(totals)
        
        self.totalCalculationRequested.emit()
    
    def _update_keyboard_context(self, selected_rows: List[int]):
        """Update keyboard handler context"""
        current_item = self.table.currentItem()
        current_row = current_item.row() if current_item else None
        current_column = None
        if current_item:
            header_item = self.table.horizontalHeaderItem(current_item.column())
            current_column = header_item.text() if header_item else None
        
        # Check if currently editing
        is_editing = self.table.state() == QAbstractItemView.State.EditingState
        
        context = create_table_context(
            widget=self,
            selected_rows=selected_rows,
            current_row=current_row,
            is_hierarchical=False,  # Override in subclasses for hierarchical tables
            is_editing=is_editing
        )
        context.current_column = current_column
        
        self.keyboard_handler.update_context(context)
    
    def _on_shortcut_triggered(self, action: ShortcutAction, context: ShortcutContext):
        """Handle keyboard shortcut triggered"""
        # This is already handled by the action handlers registered in _setup_keyboard_handlers
        # But can be overridden in subclasses for custom behavior
        pass
    
    def _on_shortcut_blocked(self, action: ShortcutAction, reason: str):
        """Handle keyboard shortcut blocked"""
        # Log or show user feedback about blocked shortcut
        logger.debug(f"Shortcut {action.value} blocked: {reason}")
    
    def _update_command_states(self, selected_rows: List[int]):
        """Update command button states based on selection"""
        has_selection = len(selected_rows) > 0
        has_rows = self.table.rowCount() > 0
        
        # Update toolbar actions
        for action in self.control_panel.actions():
            command_id = action.data()
            if command_id == CommandType.DELETE_ROW.value:
                action.setEnabled(has_selection)
            elif command_id in [CommandType.MOVE_UP.value, CommandType.MOVE_DOWN.value]:
                action.setEnabled(has_selection and has_rows)
            elif command_id == CommandType.EXPORT_DATA.value:
                action.setEnabled(has_rows)
    
    def _execute_command(self, command_id: str):
        """Execute a table part command"""
        context = {
            'selected_rows': [item.row() for item in self.table.selectedItems()],
            'table_data': self._get_table_data(),
            'command_id': command_id
        }
        
        # Try to execute form command first
        if command_id in self.form_commands:
            try:
                self.form_commands[command_id]()
                self.commandExecuted.emit(command_id, context)
                return
            except Exception as e:
                QMessageBox.warning(self, "Ошибка команды", f"Ошибка выполнения команды: {str(e)}")
                return
        
        # Execute built-in command
        if command_id == CommandType.ADD_ROW.value:
            self._add_row()
        elif command_id == CommandType.DELETE_ROW.value:
            self._delete_selected_rows()
        elif command_id == CommandType.MOVE_UP.value:
            self._move_rows_up()
        elif command_id == CommandType.MOVE_DOWN.value:
            self._move_rows_down()
        elif command_id == CommandType.IMPORT_DATA.value:
            self._import_data()
        elif command_id == CommandType.EXPORT_DATA.value:
            self._export_data()
        elif command_id == CommandType.PRINT_DATA.value:
            self._print_data()
        elif command_id == "open_reference_selector":
            self._open_reference_selector()
        
        self.commandExecuted.emit(command_id, context)
    
    def _customize_panel(self):
        """Open panel customization dialog"""
        try:
            from ..dialogs.panel_configuration_dialog import PanelConfigurationDialog
            
            # Get current panel settings
            current_settings = self.user_settings.panel_settings if self.user_settings else None
            
            # Create and show dialog
            dialog = PanelConfigurationDialog(
                document_type=self.config.document_type,
                table_part_id=self.config.table_id,
                current_settings=current_settings,
                parent=self
            )
            
            # Connect dialog signals
            dialog.settingsChanged.connect(self.update_panel_settings)
            dialog.resetRequested.connect(self.reset_settings_to_defaults)
            
            dialog.exec()
            
        except ImportError:
            # Fallback if dialog is not available
            QMessageBox.information(
                self, 
                "Настройка панели", 
                "Диалог настройки панели временно недоступен"
            )
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    def _get_table_data(self) -> List[Dict[str, Any]]:
        """Get current table data as list of dictionaries"""
        pass
    
    @abstractmethod
    def _add_row(self):
        """Add a new row to the table"""
        pass
    
    @abstractmethod
    def _delete_selected_rows(self):
        """Delete selected rows from the table"""
        pass
    
    def _move_rows_up(self):
        """Move selected rows up"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return
        
        # Sort selected rows to maintain order
        selected_rows.sort()
        
        # Check if we can move up (first selected row must not be at index 0)
        if selected_rows[0] <= 0:
            return
        
        # Move rows by swapping each with the row above it
        # Process from top to bottom to avoid conflicts
        for row_index in selected_rows:
            self._swap_rows(row_index, row_index - 1)
        
        # Update selection to follow moved rows
        new_selection = [row - 1 for row in selected_rows]
        self._update_selection(new_selection)
        
        # Trigger recalculation if enabled
        if self.config.auto_calculation_enabled:
            self.total_calculation_timer.stop()
            self.total_calculation_timer.start(self.config.total_calculation_timeout_ms)
    
    def _move_rows_down(self):
        """Move selected rows down"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return
        
        # Sort selected rows in reverse order to maintain order when moving down
        selected_rows.sort(reverse=True)
        
        # Check if we can move down (last selected row must not be at last index)
        if selected_rows[0] >= self.table.rowCount() - 1:
            return
        
        # Move rows by swapping each with the row below it
        # Process from bottom to top to avoid conflicts
        for row_index in selected_rows:
            self._swap_rows(row_index, row_index + 1)
        
        # Update selection to follow moved rows
        new_selection = [row + 1 for row in sorted(selected_rows)]
        self._update_selection(new_selection)
        
        # Trigger recalculation if enabled
        if self.config.auto_calculation_enabled:
            self.total_calculation_timer.stop()
            self.total_calculation_timer.start(self.config.total_calculation_timeout_ms)
    
    @abstractmethod
    def _swap_rows(self, row1: int, row2: int):
        """Swap two rows in the table - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _update_selection(self, row_indices: List[int]):
        """Update row selection - must be implemented by subclasses"""
        pass
    
    def _import_data(self):
        """Import data from external file"""
        from ..dialogs.table_part_import_dialog import TablePartImportDialog
        from ...services.table_part_import_service import ImportColumn
        
        # Define target columns for this table part
        target_columns = self._get_import_columns()
        
        if not target_columns:
            QMessageBox.information(
                self, 
                "Импорт недоступен", 
                "Импорт данных не настроен для данной табличной части"
            )
            return
        
        # Open import dialog
        dialog = TablePartImportDialog(target_columns, self)
        dialog.importCompleted.connect(self._on_data_imported)
        dialog.exec()
    
    @abstractmethod
    def _get_import_columns(self) -> List:
        """Get import column definitions for this table part"""
        pass
    
    @abstractmethod
    def _on_data_imported(self, data: List[Dict[str, Any]]):
        """Handle imported data"""
        pass
    
    def _export_data(self):
        """Export table data to file"""
        from ..dialogs.table_part_export_dialog import TablePartExportDialog
        from ...services.table_part_export_service import ExportColumn
        
        # Get current table data
        table_data = self._get_table_data()
        
        if not table_data:
            QMessageBox.information(
                self, 
                "Нет данных", 
                "Нет данных для экспорта"
            )
            return
        
        # Define export columns for this table part
        export_columns = self._get_export_columns()
        
        if not export_columns:
            QMessageBox.information(
                self, 
                "Экспорт недоступен", 
                "Экспорт данных не настроен для данной табличной части"
            )
            return
        
        # Open export dialog
        dialog = TablePartExportDialog(table_data, export_columns, self.config.table_id, self)
        dialog.exportCompleted.connect(self._on_data_exported)
        dialog.exec()
    
    @abstractmethod
    def _get_export_columns(self) -> List:
        """Get export column definitions for this table part"""
        pass
    
    def _on_data_exported(self, file_path: str):
        """Handle successful data export"""
        QMessageBox.information(
            self,
            "Экспорт завершен",
            f"Данные успешно экспортированы в файл:\n{file_path}"
        )
    
    def _print_data(self):
        """Print table data"""
        from ..dialogs.table_part_print_dialog import create_table_part_print_dialog
        
        # Get current table data
        table_data = self._get_table_data()
        
        if not table_data:
            QMessageBox.information(
                self, 
                "Нет данных", 
                "Нет данных для печати"
            )
            return
        
        # Open print dialog
        dialog = create_table_part_print_dialog(
            table_data, 
            self.config.table_id, 
            self
        )
        dialog.printRequested.connect(self._on_print_requested)
        dialog.exec()
    
    def _on_print_requested(self, print_config: dict):
        """Handle print request completion"""
        # This can be overridden in subclasses for custom handling
        pass
    
    @abstractmethod
    def _open_reference_selector(self):
        """Open reference selector for current cell"""
        pass
    
    # Public interface methods
    def register_form_command(self, command_id: str, method: Callable):
        """Register a form command method"""
        self.form_commands[command_id] = method
    
    def update_configuration(self, config: TablePartConfiguration):
        """Update table part configuration"""
        self.config = config
        # Rebuild UI with new configuration
        # This would require recreating the control panel
    
    def get_selected_rows(self) -> List[int]:
        """Get list of selected row indices"""
        return list(set(item.row() for item in self.table.selectedItems()))
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set table data"""
        # This should be implemented by subclasses based on their data structure
        pass
    
    def get_data(self) -> List[Dict[str, Any]]:
        """Get table data"""
        return self._get_table_data()
    
    def set_keyboard_shortcuts_enabled(self, enabled: bool):
        """Enable or disable keyboard shortcuts"""
        self.keyboard_handler.set_enabled(enabled)
        self.config.keyboard_shortcuts_enabled = enabled
    
    def get_keyboard_handler(self) -> TablePartKeyboardHandler:
        """Get the keyboard handler instance"""
        return self.keyboard_handler
    
    def _connect_calculation_signals(self):
        """Connect calculation engine signals"""
        self.calculation_engine.calculationCompleted.connect(self._on_calculation_completed)
        self.calculation_engine.totalCalculationCompleted.connect(self._on_total_calculation_completed)
        self.calculation_engine.calculationError.connect(self._on_calculation_error)
        self.calculation_engine.performanceAlert.connect(self._on_performance_alert)
        
        # Connect performance monitor signals
        self.performance_monitor.performanceStatusChanged.connect(self._on_performance_status_changed)
        self.performance_monitor.thresholdExceeded.connect(self._on_threshold_exceeded)
    
    def _on_calculation_completed(self, row: int, column: str, result: CalculationResult):
        """Handle calculation completion"""
        logger.debug(f"Calculation completed for row {row}, column {column}: {result.value}")
        
        # Update performance monitor
        self.performance_monitor.add_calculation_result(result)
        metrics = self.calculation_engine.get_performance_metrics()
        self.performance_monitor.update_metrics(metrics)
        
        # Show calculation activity indicator
        self.performance_monitor.show_calculation_indicator()
    
    def _on_total_calculation_completed(self, totals: Dict[str, Any]):
        """Handle total calculation completion"""
        logger.debug(f"Total calculations completed: {totals}")
        
        # Update performance metrics
        metrics = self.calculation_engine.get_performance_metrics()
        self.performance_monitor.update_metrics(metrics)
    
    def _on_calculation_error(self, error_type: str, message: str):
        """Handle calculation errors"""
        logger.error(f"Calculation error ({error_type}): {message}")
        
        # Show error indicator
        self.performance_monitor.show_error_indicator()
        
        # Show user-friendly error message
        QMessageBox.warning(self, "Ошибка расчета", f"Ошибка при выполнении расчетов: {message}")
    
    def _on_performance_alert(self, metric_name: str, value: float):
        """Handle performance alerts"""
        logger.warning(f"Performance alert - {metric_name}: {value:.2f}")
        
        # Show performance monitor if not visible
        if not self.performance_monitor.isVisible():
            self.performance_monitor.show()
    
    def _on_performance_status_changed(self, status: PerformanceStatus):
        """Handle performance status changes"""
        logger.info(f"Performance status changed to: {status.value}")
        
        # Show performance monitor for warning/critical status
        if status in [PerformanceStatus.WARNING, PerformanceStatus.CRITICAL]:
            if not self.performance_monitor.isVisible():
                self.performance_monitor.show()
    
    def _on_threshold_exceeded(self, metric_name: str, value: float):
        """Handle threshold exceeded events"""
        logger.warning(f"Performance threshold exceeded - {metric_name}: {value:.2f}")
        
        # Show performance monitor
        if not self.performance_monitor.isVisible():
            self.performance_monitor.show()
    
    @abstractmethod
    def _get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific row"""
        pass
    
    @abstractmethod
    def _update_calculated_field(self, row: int, column: str, value: Any):
        """Update a calculated field in the table"""
        pass
    
    @abstractmethod
    def _update_document_totals(self, totals: Dict[str, Any]):
        """Update document totals display"""
        pass
    
    def get_calculation_engine(self) -> TablePartCalculationEngine:
        """Get the calculation engine instance"""
        return self.calculation_engine
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return self.calculation_engine.get_performance_metrics()
    
    def get_performance_monitor(self) -> CalculationPerformanceMonitor:
        """Get the performance monitor instance"""
        return self.performance_monitor
    
    def show_performance_monitor(self):
        """Show the performance monitor"""
        self.performance_monitor.show()
    
    def hide_performance_monitor(self):
        """Hide the performance monitor"""
        self.performance_monitor.hide()
    
    def toggle_performance_monitor(self):
        """Toggle performance monitor visibility"""
        if self.performance_monitor.isVisible():
            self.performance_monitor.hide()
        else:
            self.performance_monitor.show()
    
    def _load_user_settings(self):
        """Load user settings for this table part"""
        if not self.settings_service or not self.user_id:
            # Use default settings if no service or user
            self.user_settings = self._get_default_settings()
            return
        
        try:
            # Load user settings from database
            settings = self.settings_service.get_user_settings(
                self.user_id,
                self.config.document_type,
                self.config.table_id
            )
            
            if settings:
                self.user_settings = settings
                logger.info(f"Loaded user settings for table {self.config.table_id}")
            else:
                # Create default settings for new user
                self.user_settings = self._get_default_settings()
                self._save_user_settings()  # Save defaults for future use
                logger.info(f"Created default settings for table {self.config.table_id}")
            
            # Apply settings to configuration
            self._apply_settings_to_config()
            
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
            self.user_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> TablePartSettingsData:
        """Get default settings for this table part"""
        if self.settings_service:
            return self.settings_service.get_default_settings(
                self.config.document_type,
                self.config.table_id
            )
        else:
            # Fallback default settings
            from ...data.models.table_part_models import PanelSettings, ShortcutSettings
            return TablePartSettingsData(
                panel_settings=PanelSettings(
                    visible_commands=self.config.visible_commands,
                    button_size="medium",
                    show_tooltips=True
                ),
                shortcuts=ShortcutSettings(enabled=True)
            )
    
    def _apply_settings_to_config(self):
        """Apply user settings to table configuration"""
        if not self.user_settings:
            return
        
        # Update visible commands from settings
        if self.user_settings.panel_settings.visible_commands:
            self.config.visible_commands = self.user_settings.panel_settings.visible_commands
        
        # Update keyboard shortcuts setting
        self.config.keyboard_shortcuts_enabled = self.user_settings.shortcuts.enabled
    
    def _save_user_settings(self):
        """Save current user settings to database"""
        if not self.settings_service or not self.user_id or not self.user_settings:
            return
        
        try:
            success = self.settings_service.save_user_settings(
                self.user_id,
                self.config.document_type,
                self.config.table_id,
                self.user_settings
            )
            
            if success:
                logger.info(f"Saved user settings for table {self.config.table_id}")
            else:
                logger.error(f"Failed to save user settings for table {self.config.table_id}")
                
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")
    
    def update_panel_settings(self, panel_settings):
        """Update panel settings and save to database"""
        if not self.user_settings:
            self.user_settings = self._get_default_settings()
        
        self.user_settings.panel_settings = panel_settings
        
        # Apply settings to current configuration
        self._apply_settings_to_config()
        
        # Rebuild control panel with new settings
        self._rebuild_control_panel()
        
        # Save to database
        self._save_user_settings()
    
    def update_shortcut_settings(self, shortcut_settings):
        """Update shortcut settings and save to database"""
        if not self.user_settings:
            self.user_settings = self._get_default_settings()
        
        self.user_settings.shortcuts = shortcut_settings
        
        # Apply settings
        self.config.keyboard_shortcuts_enabled = shortcut_settings.enabled
        self.keyboard_handler.set_enabled(shortcut_settings.enabled)
        
        # Apply custom mappings if any
        if shortcut_settings.custom_mappings:
            self.keyboard_handler.update_custom_mappings(shortcut_settings.custom_mappings)
        
        # Save to database
        self._save_user_settings()
    
    def update_column_settings(self, column_widths: Dict[str, int] = None, 
                             column_order: List[str] = None, 
                             hidden_columns: List[str] = None):
        """Update column settings and save to database"""
        if not self.user_settings:
            self.user_settings = self._get_default_settings()
        
        if column_widths is not None:
            self.user_settings.column_widths = column_widths
        
        if column_order is not None:
            self.user_settings.column_order = column_order
        
        if hidden_columns is not None:
            self.user_settings.hidden_columns = hidden_columns
        
        # Apply column settings to table
        self._apply_column_settings()
        
        # Save to database
        self._save_user_settings()
    
    def _apply_column_settings(self):
        """Apply column settings to the table widget"""
        if not self.user_settings:
            return
        
        # Apply column widths
        for column_name, width in self.user_settings.column_widths.items():
            # Find column index by name
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                if header_item and header_item.text() == column_name:
                    self.table.setColumnWidth(col, width)
                    break
        
        # Hide columns if specified
        for column_name in self.user_settings.hidden_columns:
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                if header_item and header_item.text() == column_name:
                    self.table.setColumnHidden(col, True)
                    break
    
    def _rebuild_control_panel(self):
        """Rebuild the control panel with current settings"""
        # Remove old control panel
        old_panel = self.control_panel
        self.layout().removeWidget(old_panel)
        old_panel.deleteLater()
        
        # Create new control panel with updated settings
        self.control_panel = self._create_control_panel()
        self.layout().insertWidget(0, self.control_panel)
    
    def reset_settings_to_defaults(self):
        """Reset user settings to defaults"""
        if not self.settings_service or not self.user_id:
            return
        
        try:
            # Reset in database
            success = self.settings_service.reset_user_settings(
                self.user_id,
                self.config.document_type,
                self.config.table_id
            )
            
            if success:
                # Reload settings
                self._load_user_settings()
                
                # Rebuild UI with default settings
                self._rebuild_control_panel()
                self._apply_column_settings()
                
                logger.info(f"Reset settings to defaults for table {self.config.table_id}")
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Настройки сброшены",
                    "Настройки табличной части сброшены к значениям по умолчанию"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось сбросить настройки"
                )
                
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Ошибка при сбросе настроек: {str(e)}"
            )
    
    def get_user_settings(self) -> Optional[TablePartSettingsData]:
        """Get current user settings"""
        return self.user_settings
    
    def cleanup(self):
        """Cleanup resources"""
        # Save current settings before cleanup
        if hasattr(self, 'user_settings') and self.user_settings:
            self._save_user_settings()
        
        if hasattr(self, 'keyboard_handler'):
            self.keyboard_handler.cleanup()
        
        # Stop timers
        if hasattr(self, 'calculation_timer'):
            self.calculation_timer.stop()
        if hasattr(self, 'total_calculation_timer'):
            self.total_calculation_timer.stop()
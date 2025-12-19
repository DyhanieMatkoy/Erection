"""
Table Part Keyboard Shortcut Handler.

This module provides comprehensive keyboard shortcut handling for table parts,
implementing standard table shortcuts and ensuring consistent behavior across
all table part instances.

Requirements: 3.1, 3.2, 7.3, 7.4
"""

from typing import Dict, Callable, Optional, Any, List
from dataclasses import dataclass, field
from enum import Enum
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QKeyEvent
from PyQt6.QtWidgets import QWidget
import logging

logger = logging.getLogger(__name__)


class ShortcutAction(Enum):
    """Standard table part shortcut actions"""
    # Row management
    ADD_ROW = "add_row"
    DELETE_ROW = "delete_row"
    COPY_ROWS = "copy_rows"
    PASTE_ROWS = "paste_rows"
    
    # Row movement
    MOVE_ROW_UP = "move_row_up"
    MOVE_ROW_DOWN = "move_row_down"
    
    # Reference field
    OPEN_REFERENCE_SELECTOR = "open_reference_selector"
    
    # Navigation (for hierarchical lists)
    EXPAND_NODE = "expand_node"
    COLLAPSE_NODE = "collapse_node"
    EXPAND_ALL_CHILDREN = "expand_all_children"
    COLLAPSE_ALL_CHILDREN = "collapse_all_children"
    GO_TO_FIRST = "go_to_first"
    GO_TO_LAST = "go_to_last"
    GO_TO_ROOT = "go_to_root"
    GO_TO_LAST_IN_HIERARCHY = "go_to_last_in_hierarchy"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"


@dataclass
class ShortcutMapping:
    """Configuration for a keyboard shortcut"""
    key_sequence: str
    action: ShortcutAction
    description: str
    enabled: bool = True
    context: str = "table"  # "table", "hierarchical", "all"
    requires_selection: bool = False
    custom_handler: Optional[Callable] = None


@dataclass
class ShortcutContext:
    """Context information for shortcut execution"""
    widget: QWidget
    selected_rows: List[int] = field(default_factory=list)
    current_row: Optional[int] = None
    current_column: Optional[str] = None
    is_hierarchical: bool = False
    is_editing: bool = False
    additional_data: Dict[str, Any] = field(default_factory=dict)


class TablePartKeyboardHandler(QObject):
    """
    Keyboard shortcut handler for table parts.
    
    Provides comprehensive keyboard shortcut handling including:
    - Standard table shortcuts (Insert, Delete, F4, Ctrl+C/V, Ctrl+±)
    - Row movement shortcuts (Ctrl+Shift+Up/Down)
    - Hierarchical navigation shortcuts (Ctrl+→/←, Home/End, etc.)
    - Consistent behavior across all table parts
    
    Requirements: 3.1, 3.2, 7.3, 7.4
    """
    
    # Signals
    shortcutTriggered = pyqtSignal(ShortcutAction, ShortcutContext)
    shortcutBlocked = pyqtSignal(ShortcutAction, str)  # action, reason
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize keyboard handler.
        
        Args:
            parent: Parent widget to attach shortcuts to
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.shortcuts: Dict[str, QShortcut] = {}
        self.action_handlers: Dict[ShortcutAction, Callable] = {}
        self.enabled = True
        self.current_context: Optional[ShortcutContext] = None
        
        # Initialize standard shortcut mappings
        self.standard_mappings = self._create_standard_mappings()
        
        # Setup shortcuts if parent widget provided
        if parent:
            self._setup_shortcuts()
    
    def _create_standard_mappings(self) -> List[ShortcutMapping]:
        """
        Create standard keyboard shortcut mappings.
        
        Requirements: 3.1, 3.2, 7.3, 7.4
        """
        return [
            # Row management shortcuts
            ShortcutMapping(
                key_sequence="Insert",
                action=ShortcutAction.ADD_ROW,
                description="Добавить новую строку",
                context="all"
            ),
            ShortcutMapping(
                key_sequence="Delete",
                action=ShortcutAction.DELETE_ROW,
                description="Удалить выбранные строки",
                context="all",
                requires_selection=True
            ),
            ShortcutMapping(
                key_sequence="Ctrl+C",
                action=ShortcutAction.COPY_ROWS,
                description="Копировать выбранные строки",
                context="all",
                requires_selection=True
            ),
            ShortcutMapping(
                key_sequence="Ctrl+V",
                action=ShortcutAction.PASTE_ROWS,
                description="Вставить скопированные строки",
                context="all"
            ),
            ShortcutMapping(
                key_sequence="Ctrl++",
                action=ShortcutAction.ADD_ROW,
                description="Добавить новую строку (альтернатива)",
                context="all"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+-",
                action=ShortcutAction.DELETE_ROW,
                description="Удалить выбранные строки (альтернатива)",
                context="all",
                requires_selection=True
            ),
            
            # Row movement shortcuts
            ShortcutMapping(
                key_sequence="Ctrl+Shift+Up",
                action=ShortcutAction.MOVE_ROW_UP,
                description="Переместить строки вверх",
                context="all",
                requires_selection=True
            ),
            ShortcutMapping(
                key_sequence="Ctrl+Shift+Down",
                action=ShortcutAction.MOVE_ROW_DOWN,
                description="Переместить строки вниз",
                context="all",
                requires_selection=True
            ),
            
            # Reference field shortcut
            ShortcutMapping(
                key_sequence="F4",
                action=ShortcutAction.OPEN_REFERENCE_SELECTOR,
                description="Открыть форму выбора для поля справочника",
                context="all"
            ),
            
            # Hierarchical navigation shortcuts
            ShortcutMapping(
                key_sequence="Ctrl+Right",
                action=ShortcutAction.EXPAND_NODE,
                description="Развернуть узел",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+Left",
                action=ShortcutAction.COLLAPSE_NODE,
                description="Свернуть узел",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+Shift+Right",
                action=ShortcutAction.EXPAND_ALL_CHILDREN,
                description="Развернуть все дочерние узлы",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+Shift+Left",
                action=ShortcutAction.COLLAPSE_ALL_CHILDREN,
                description="Свернуть все дочерние узлы",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Home",
                action=ShortcutAction.GO_TO_FIRST,
                description="Перейти к первому элементу",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="End",
                action=ShortcutAction.GO_TO_LAST,
                description="Перейти к последнему элементу",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+Home",
                action=ShortcutAction.GO_TO_ROOT,
                description="Перейти к корневому элементу",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="Ctrl+End",
                action=ShortcutAction.GO_TO_LAST_IN_HIERARCHY,
                description="Перейти к последнему элементу в иерархии",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="PgUp",
                action=ShortcutAction.PAGE_UP,
                description="Прокрутить на страницу вверх",
                context="hierarchical"
            ),
            ShortcutMapping(
                key_sequence="PgDown",
                action=ShortcutAction.PAGE_DOWN,
                description="Прокрутить на страницу вниз",
                context="hierarchical"
            ),
        ]
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts on parent widget"""
        if not self.parent_widget:
            logger.warning("Cannot setup shortcuts: no parent widget")
            return
        
        for mapping in self.standard_mappings:
            self._register_shortcut(mapping)
        
        logger.info(f"Registered {len(self.shortcuts)} keyboard shortcuts")
    
    def _register_shortcut(self, mapping: ShortcutMapping):
        """Register a single keyboard shortcut"""
        try:
            shortcut = QShortcut(QKeySequence(mapping.key_sequence), self.parent_widget)
            shortcut.setEnabled(mapping.enabled)
            shortcut.activated.connect(
                lambda m=mapping: self._handle_shortcut_activation(m)
            )
            
            # Store shortcut with unique key
            key = f"{mapping.key_sequence}_{mapping.action.value}"
            self.shortcuts[key] = shortcut
            
            logger.debug(f"Registered shortcut: {mapping.key_sequence} -> {mapping.action.value}")
        except Exception as e:
            logger.error(f"Failed to register shortcut {mapping.key_sequence}: {e}")
    
    def _handle_shortcut_activation(self, mapping: ShortcutMapping):
        """Handle shortcut activation"""
        if not self.enabled:
            logger.debug(f"Shortcut {mapping.action.value} blocked: handler disabled")
            return
        
        # Get current context
        context = self.current_context or ShortcutContext(widget=self.parent_widget)
        
        # Check if shortcut is applicable in current context
        if not self._is_shortcut_applicable(mapping, context):
            reason = self._get_block_reason(mapping, context)
            logger.debug(f"Shortcut {mapping.action.value} blocked: {reason}")
            self.shortcutBlocked.emit(mapping.action, reason)
            return
        
        # Check if custom handler exists
        if mapping.custom_handler:
            try:
                mapping.custom_handler(context)
                return
            except Exception as e:
                logger.error(f"Custom handler failed for {mapping.action.value}: {e}")
        
        # Check if action handler is registered
        if mapping.action in self.action_handlers:
            try:
                self.action_handlers[mapping.action](context)
            except Exception as e:
                logger.error(f"Action handler failed for {mapping.action.value}: {e}")
        
        # Emit signal for external handling
        self.shortcutTriggered.emit(mapping.action, context)
        logger.debug(f"Shortcut triggered: {mapping.action.value}")
    
    def _is_shortcut_applicable(self, mapping: ShortcutMapping, context: ShortcutContext) -> bool:
        """Check if shortcut is applicable in current context"""
        # Check if editing (some shortcuts should be disabled while editing)
        if context.is_editing and mapping.action in [
            ShortcutAction.DELETE_ROW,
            ShortcutAction.MOVE_ROW_UP,
            ShortcutAction.MOVE_ROW_DOWN
        ]:
            return False
        
        # Check context type
        if mapping.context == "hierarchical" and not context.is_hierarchical:
            return False
        
        # Check selection requirement
        if mapping.requires_selection and len(context.selected_rows) == 0:
            return False
        
        return True
    
    def _get_block_reason(self, mapping: ShortcutMapping, context: ShortcutContext) -> str:
        """Get reason why shortcut was blocked"""
        if context.is_editing:
            return "editing in progress"
        if mapping.context == "hierarchical" and not context.is_hierarchical:
            return "not in hierarchical context"
        if mapping.requires_selection and len(context.selected_rows) == 0:
            return "no rows selected"
        return "unknown reason"
    
    # Public interface methods
    
    def register_action_handler(self, action: ShortcutAction, handler: Callable):
        """
        Register a handler for a specific shortcut action.
        
        Args:
            action: Shortcut action to handle
            handler: Callable that takes ShortcutContext as argument
        """
        self.action_handlers[action] = handler
        logger.debug(f"Registered action handler for {action.value}")
    
    def unregister_action_handler(self, action: ShortcutAction):
        """Unregister a handler for a specific shortcut action"""
        if action in self.action_handlers:
            del self.action_handlers[action]
            logger.debug(f"Unregistered action handler for {action.value}")
    
    def update_context(self, context: ShortcutContext):
        """
        Update current shortcut context.
        
        Args:
            context: New context information
        """
        self.current_context = context
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable all keyboard shortcuts.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(enabled)
        logger.info(f"Keyboard shortcuts {'enabled' if enabled else 'disabled'}")
    
    def enable_shortcut(self, action: ShortcutAction, enabled: bool = True):
        """
        Enable or disable a specific shortcut.
        
        Args:
            action: Shortcut action to enable/disable
            enabled: True to enable, False to disable
        """
        for key, shortcut in self.shortcuts.items():
            if action.value in key:
                shortcut.setEnabled(enabled)
                logger.debug(f"Shortcut {action.value} {'enabled' if enabled else 'disabled'}")
    
    def add_custom_shortcut(
        self,
        key_sequence: str,
        action: ShortcutAction,
        description: str,
        handler: Optional[Callable] = None,
        **kwargs
    ):
        """
        Add a custom keyboard shortcut.
        
        Args:
            key_sequence: Key sequence (e.g., "Ctrl+K")
            action: Shortcut action
            description: Human-readable description
            handler: Optional custom handler
            **kwargs: Additional ShortcutMapping parameters
        """
        mapping = ShortcutMapping(
            key_sequence=key_sequence,
            action=action,
            description=description,
            custom_handler=handler,
            **kwargs
        )
        
        # Add to standard mappings list
        self.standard_mappings.append(mapping)
        
        # Register the shortcut if parent widget is available
        if self.parent_widget:
            self._register_shortcut(mapping)
        
        logger.info(f"Added custom shortcut: {key_sequence} -> {action.value}")
    
    def remove_shortcut(self, key_sequence: str, action: ShortcutAction):
        """
        Remove a keyboard shortcut.
        
        Args:
            key_sequence: Key sequence to remove
            action: Action associated with the shortcut
        """
        key = f"{key_sequence}_{action.value}"
        if key in self.shortcuts:
            shortcut = self.shortcuts[key]
            shortcut.setEnabled(False)
            shortcut.deleteLater()
            del self.shortcuts[key]
            logger.info(f"Removed shortcut: {key_sequence} -> {action.value}")
    
    def get_shortcut_mappings(self, context_filter: Optional[str] = None) -> List[ShortcutMapping]:
        """
        Get list of shortcut mappings, optionally filtered by context.
        
        Args:
            context_filter: Optional context to filter by ("table", "hierarchical", "all")
            
        Returns:
            List of shortcut mappings
        """
        if context_filter:
            return [m for m in self.standard_mappings 
                   if m.context == context_filter or m.context == "all"]
        return self.standard_mappings.copy()
    
    def get_shortcut_help_text(self) -> str:
        """
        Get formatted help text for all shortcuts.
        
        Returns:
            Multi-line string with shortcut descriptions
        """
        lines = ["Горячие клавиши табличной части:", ""]
        
        # Group by category
        categories = {
            "Управление строками": [
                ShortcutAction.ADD_ROW,
                ShortcutAction.DELETE_ROW,
                ShortcutAction.COPY_ROWS,
                ShortcutAction.PASTE_ROWS
            ],
            "Перемещение строк": [
                ShortcutAction.MOVE_ROW_UP,
                ShortcutAction.MOVE_ROW_DOWN
            ],
            "Справочники": [
                ShortcutAction.OPEN_REFERENCE_SELECTOR
            ],
            "Навигация по иерархии": [
                ShortcutAction.EXPAND_NODE,
                ShortcutAction.COLLAPSE_NODE,
                ShortcutAction.EXPAND_ALL_CHILDREN,
                ShortcutAction.COLLAPSE_ALL_CHILDREN,
                ShortcutAction.GO_TO_FIRST,
                ShortcutAction.GO_TO_LAST,
                ShortcutAction.GO_TO_ROOT,
                ShortcutAction.GO_TO_LAST_IN_HIERARCHY,
                ShortcutAction.PAGE_UP,
                ShortcutAction.PAGE_DOWN
            ]
        }
        
        for category, actions in categories.items():
            lines.append(f"{category}:")
            for mapping in self.standard_mappings:
                if mapping.action in actions:
                    lines.append(f"  {mapping.key_sequence:20} - {mapping.description}")
            lines.append("")
        
        return "\n".join(lines)
    
    def cleanup(self):
        """Cleanup resources"""
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self.shortcuts.clear()
        self.action_handlers.clear()
        logger.info("Keyboard handler cleaned up")


# Utility functions

def create_keyboard_handler(parent: QWidget) -> TablePartKeyboardHandler:
    """
    Create a keyboard handler for a table part widget.
    
    Args:
        parent: Parent widget to attach shortcuts to
        
    Returns:
        Configured keyboard handler
    """
    return TablePartKeyboardHandler(parent)


def create_table_context(
    widget: QWidget,
    selected_rows: List[int] = None,
    current_row: Optional[int] = None,
    is_hierarchical: bool = False,
    is_editing: bool = False
) -> ShortcutContext:
    """
    Create a shortcut context for table operations.
    
    Args:
        widget: Widget context
        selected_rows: List of selected row indices
        current_row: Current row index
        is_hierarchical: Whether context is hierarchical
        is_editing: Whether currently editing
        
    Returns:
        Shortcut context
    """
    return ShortcutContext(
        widget=widget,
        selected_rows=selected_rows or [],
        current_row=current_row,
        is_hierarchical=is_hierarchical,
        is_editing=is_editing
    )

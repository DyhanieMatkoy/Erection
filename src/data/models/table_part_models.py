"""
Data models for document table parts configuration and management.

This module provides Python data classes and utilities for managing
table part configurations, user settings, and command definitions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import json
from datetime import datetime


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
    DUPLICATE_ROW = "duplicate_row"
    CLEAR_SELECTION = "clear_selection"


class ColumnType(Enum):
    """Types of table columns"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    REFERENCE = "reference"
    BOOLEAN = "boolean"


@dataclass
class ColumnValidation:
    """Validation rules for table columns"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    required: bool = False
    custom_validator: Optional[Callable[[Any], Union[bool, str]]] = None


@dataclass
class TableColumn:
    """Configuration for a table column"""
    id: str
    name: str
    type: ColumnType
    width: Optional[str] = None
    sortable: bool = True
    editable: bool = True
    show_total: bool = False
    reference_type: Optional[str] = None
    validation: Optional[ColumnValidation] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'width': self.width,
            'sortable': self.sortable,
            'editable': self.editable,
            'show_total': self.show_total,
            'reference_type': self.reference_type,
            'validation': {
                'min_value': self.validation.min_value,
                'max_value': self.validation.max_value,
                'pattern': self.validation.pattern,
                'required': self.validation.required
            } if self.validation else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableColumn':
        """Create from dictionary"""
        validation = None
        if data.get('validation'):
            val_data = data['validation']
            validation = ColumnValidation(
                min_value=val_data.get('min_value'),
                max_value=val_data.get('max_value'),
                pattern=val_data.get('pattern'),
                required=val_data.get('required', False)
            )
        
        return cls(
            id=data['id'],
            name=data['name'],
            type=ColumnType(data['type']),
            width=data.get('width'),
            sortable=data.get('sortable', True),
            editable=data.get('editable', True),
            show_total=data.get('show_total', False),
            reference_type=data.get('reference_type'),
            validation=validation
        )


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
    requires_selection: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'tooltip': self.tooltip,
            'shortcut': self.shortcut,
            'enabled': self.enabled,
            'visible': self.visible,
            'form_method': self.form_method,
            'position': self.position,
            'requires_selection': self.requires_selection
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TablePartCommand':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            icon=data['icon'],
            tooltip=data['tooltip'],
            shortcut=data.get('shortcut'),
            enabled=data.get('enabled', True),
            visible=data.get('visible', True),
            form_method=data.get('form_method'),
            position=data.get('position', 0),
            requires_selection=data.get('requires_selection', False)
        )


@dataclass
class PanelSettings:
    """Settings for the row control panel"""
    visible_commands: List[str] = field(default_factory=list)
    hidden_commands: List[str] = field(default_factory=list)
    button_size: str = "medium"  # small, medium, large
    show_tooltips: bool = True
    compact_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'visible_commands': self.visible_commands,
            'hidden_commands': self.hidden_commands,
            'button_size': self.button_size,
            'show_tooltips': self.show_tooltips,
            'compact_mode': self.compact_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PanelSettings':
        """Create from dictionary"""
        return cls(
            visible_commands=data.get('visible_commands', []),
            hidden_commands=data.get('hidden_commands', []),
            button_size=data.get('button_size', 'medium'),
            show_tooltips=data.get('show_tooltips', True),
            compact_mode=data.get('compact_mode', False)
        )


@dataclass
class ShortcutSettings:
    """Settings for keyboard shortcuts"""
    enabled: bool = True
    custom_mappings: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'enabled': self.enabled,
            'custom_mappings': self.custom_mappings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShortcutSettings':
        """Create from dictionary"""
        return cls(
            enabled=data.get('enabled', True),
            custom_mappings=data.get('custom_mappings', {})
        )


@dataclass
class TablePartSettingsData:
    """Complete settings data for a table part"""
    column_widths: Dict[str, int] = field(default_factory=dict)
    column_order: List[str] = field(default_factory=list)
    hidden_columns: List[str] = field(default_factory=list)
    panel_settings: PanelSettings = field(default_factory=PanelSettings)
    shortcuts: ShortcutSettings = field(default_factory=ShortcutSettings)
    sort_column: Optional[str] = None
    sort_direction: str = "asc"  # asc, desc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'column_widths': self.column_widths,
            'column_order': self.column_order,
            'hidden_columns': self.hidden_columns,
            'panel_settings': self.panel_settings.to_dict(),
            'shortcuts': self.shortcuts.to_dict(),
            'sort_column': self.sort_column,
            'sort_direction': self.sort_direction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TablePartSettingsData':
        """Create from dictionary"""
        return cls(
            column_widths=data.get('column_widths', {}),
            column_order=data.get('column_order', []),
            hidden_columns=data.get('hidden_columns', []),
            panel_settings=PanelSettings.from_dict(data.get('panel_settings', {})),
            shortcuts=ShortcutSettings.from_dict(data.get('shortcuts', {})),
            sort_column=data.get('sort_column'),
            sort_direction=data.get('sort_direction', 'asc')
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TablePartSettingsData':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class TablePartConfiguration:
    """Complete configuration for a table part"""
    table_id: str
    document_type: str
    columns: List[TableColumn] = field(default_factory=list)
    available_commands: List[TablePartCommand] = field(default_factory=list)
    visible_commands: List[str] = field(default_factory=list)
    keyboard_shortcuts_enabled: bool = True
    auto_calculation_enabled: bool = True
    drag_drop_enabled: bool = True
    calculation_timeout_ms: int = 100
    total_calculation_timeout_ms: int = 200
    show_row_numbers: bool = False
    allow_multi_select: bool = True
    show_totals: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'table_id': self.table_id,
            'document_type': self.document_type,
            'columns': [col.to_dict() for col in self.columns],
            'available_commands': [cmd.to_dict() for cmd in self.available_commands],
            'visible_commands': self.visible_commands,
            'keyboard_shortcuts_enabled': self.keyboard_shortcuts_enabled,
            'auto_calculation_enabled': self.auto_calculation_enabled,
            'drag_drop_enabled': self.drag_drop_enabled,
            'calculation_timeout_ms': self.calculation_timeout_ms,
            'total_calculation_timeout_ms': self.total_calculation_timeout_ms,
            'show_row_numbers': self.show_row_numbers,
            'allow_multi_select': self.allow_multi_select,
            'show_totals': self.show_totals
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TablePartConfiguration':
        """Create from dictionary"""
        return cls(
            table_id=data['table_id'],
            document_type=data['document_type'],
            columns=[TableColumn.from_dict(col) for col in data.get('columns', [])],
            available_commands=[TablePartCommand.from_dict(cmd) for cmd in data.get('available_commands', [])],
            visible_commands=data.get('visible_commands', []),
            keyboard_shortcuts_enabled=data.get('keyboard_shortcuts_enabled', True),
            auto_calculation_enabled=data.get('auto_calculation_enabled', True),
            drag_drop_enabled=data.get('drag_drop_enabled', True),
            calculation_timeout_ms=data.get('calculation_timeout_ms', 100),
            total_calculation_timeout_ms=data.get('total_calculation_timeout_ms', 200),
            show_row_numbers=data.get('show_row_numbers', False),
            allow_multi_select=data.get('allow_multi_select', True),
            show_totals=data.get('show_totals', False)
        )


@dataclass
class CommandContext:
    """Context information for command execution"""
    selected_rows: List[int]
    table_data: List[Dict[str, Any]]
    command_id: str
    current_row: Optional[int] = None
    current_column: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: Optional[str] = None
    data: Any = None
    affected_rows: List[int] = field(default_factory=list)


@dataclass
class ReferenceFieldConfig:
    """Configuration for reference fields"""
    reference_type: str
    current_value: Optional[Dict[str, Any]] = None
    related_fields: List[str] = field(default_factory=list)
    compact_buttons: bool = True
    allow_create: bool = False
    allow_edit: bool = True
    search_enabled: bool = True
    hierarchical: bool = False


class TablePartFactory:
    """Factory for creating table part configurations and components"""
    
    @staticmethod
    def create_standard_commands() -> List[TablePartCommand]:
        """Create standard table part commands"""
        return [
            TablePartCommand(
                id=CommandType.ADD_ROW.value,
                name="Добавить",
                icon="➕",
                tooltip="Добавить новую строку (Insert)",
                shortcut="Insert",
                position=1
            ),
            TablePartCommand(
                id=CommandType.DELETE_ROW.value,
                name="Удалить",
                icon="🗑",
                tooltip="Удалить выбранные строки (Delete)",
                shortcut="Delete",
                position=2,
                requires_selection=True
            ),
            TablePartCommand(
                id=CommandType.MOVE_UP.value,
                name="Выше",
                icon="↑",
                tooltip="Переместить строки выше (Ctrl+Shift+Up)",
                shortcut="Ctrl+Shift+Up",
                position=3,
                requires_selection=True
            ),
            TablePartCommand(
                id=CommandType.MOVE_DOWN.value,
                name="Ниже",
                icon="↓",
                tooltip="Переместить строки ниже (Ctrl+Shift+Down)",
                shortcut="Ctrl+Shift+Down",
                position=4,
                requires_selection=True
            ),
            TablePartCommand(
                id=CommandType.IMPORT_DATA.value,
                name="Импорт",
                icon="📥",
                tooltip="Импортировать данные из файла",
                position=5
            ),
            TablePartCommand(
                id=CommandType.EXPORT_DATA.value,
                name="Экспорт",
                icon="📤",
                tooltip="Экспортировать данные в файл",
                position=6
            ),
            TablePartCommand(
                id=CommandType.PRINT_DATA.value,
                name="Печать",
                icon="🖨",
                tooltip="Печать табличной части",
                position=7
            )
        ]
    
    @staticmethod
    def create_default_configuration(document_type: str, table_id: str) -> TablePartConfiguration:
        """Create default table part configuration"""
        standard_commands = TablePartFactory.create_standard_commands()
        visible_commands = [cmd.id for cmd in standard_commands[:4]]  # Show first 4 commands by default
        
        return TablePartConfiguration(
            table_id=table_id,
            document_type=document_type,
            available_commands=standard_commands,
            visible_commands=visible_commands,
            keyboard_shortcuts_enabled=True,
            auto_calculation_enabled=True,
            drag_drop_enabled=True,
            calculation_timeout_ms=100,
            total_calculation_timeout_ms=200,
            show_row_numbers=False,
            allow_multi_select=True,
            show_totals=False
        )
    
    @staticmethod
    def create_column(
        id: str,
        name: str,
        column_type: ColumnType,
        **kwargs
    ) -> TableColumn:
        """Create a table column with optional parameters"""
        return TableColumn(
            id=id,
            name=name,
            type=column_type,
            **kwargs
        )
    
    @staticmethod
    def create_reference_column(
        id: str,
        name: str,
        reference_type: str,
        **kwargs
    ) -> TableColumn:
        """Create a reference column"""
        return TableColumn(
            id=id,
            name=name,
            type=ColumnType.REFERENCE,
            reference_type=reference_type,
            **kwargs
        )
    
    @staticmethod
    def create_currency_column(
        id: str,
        name: str,
        show_total: bool = True,
        **kwargs
    ) -> TableColumn:
        """Create a currency column with totals"""
        return TableColumn(
            id=id,
            name=name,
            type=ColumnType.CURRENCY,
            show_total=show_total,
            **kwargs
        )
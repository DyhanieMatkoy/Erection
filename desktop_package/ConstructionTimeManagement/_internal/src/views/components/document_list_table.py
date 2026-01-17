from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QColor, QBrush
from typing import List, Dict, Any, Optional

class DocumentListTable(QTableWidget):
    """
    Generic table component for document lists.
    Supports column configuration, sorting, selection, and context menus.
    """
    
    # Signals
    row_double_clicked = pyqtSignal(int) # Emits ID of document
    selection_changed = pyqtSignal(list) # Emits list of selected IDs
    column_resized = pyqtSignal(str, int) # Emits column_id, new_width
    sort_requested = pyqtSignal(str) # Emits column_id
    context_menu_requested = pyqtSignal(QPoint, int) # Emits point, row_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.column_map: List[Dict] = [] # Maps visual index to column config
        self.data_map: List[Any] = [] # Maps row index to data object
        self.row_style_callback: Optional[callable] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize table settings"""
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.doubleClicked.connect(self.on_double_click)
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.horizontalHeader().sectionResized.connect(self.on_column_resized)
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.horizontalHeader().setSectionsMovable(True) # Allow reordering

    def set_row_style_callback(self, callback):
        """
        Set callback for row styling.
        Callback receives data item and returns dict with:
        - 'background': QColor
        - 'foreground': QColor
        - 'font_bold': bool
        - 'tooltip': str
        """
        self.row_style_callback = callback

    def configure_columns(self, columns: List[Dict], settings: Optional[Dict] = None):
        """
        Configure table columns.
        columns: List of dicts {'id', 'name', 'width', 'visible', 'format'}
        settings: Optional dict of user settings override
        """
        self.column_map = []
        visible_columns = []
        
        # Apply settings if provided
        for col in columns:
            col_id = col['id']
            is_visible = col.get('visible', True)
            width = col.get('width', 100)
            
            if settings and col_id in settings:
                col_settings = settings[col_id]
                if isinstance(col_settings, dict):
                    is_visible = col_settings.get('visible', is_visible)
                    width = col_settings.get('width', width)
            
            if is_visible:
                # Store full config for mapping
                col_config = col.copy()
                col_config['width'] = width
                visible_columns.append(col_config)
        
        self.column_map = visible_columns
        self.setColumnCount(len(visible_columns))
        self.setHorizontalHeaderLabels([c['name'] for c in visible_columns])
        
        # Set widths
        for i, col in enumerate(visible_columns):
            self.setColumnWidth(i, col['width'])

    def set_data(self, items: List[Any]):
        """Populate table with data"""
        self.setRowCount(len(items))
        self.data_map = items
        self.setSortingEnabled(False) # Disable auto-sort during population
        
        def get_value(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            
            # Handle dot notation for nested attributes (e.g. customer.name)
            if '.' in key:
                parts = key.split('.')
                current = obj
                for part in parts:
                    if current is None:
                        return None
                    current = getattr(current, part, None)
                return current
                
            return getattr(obj, key, None)
        
        for i, item in enumerate(items):
            for j, col in enumerate(self.column_map):
                col_id = col['id']
                val = get_value(item, col_id)
                
                # Formatting
                text = str(val) if val is not None else ""
                if 'format' in col:
                     # Implement custom formatters if needed
                     pass
                
                item_widget = QTableWidgetItem(text)
                
                # Alignment
                if isinstance(val, (int, float)):
                    item_widget.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item_widget.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.setItem(i, j, item_widget)

            # Apply row styling
            if self.row_style_callback:
                try:
                    style = self.row_style_callback(item)
                    if style:
                        if 'background' in style:
                            bg = style['background']
                            if isinstance(bg, str): bg = QColor(bg)
                            for j in range(self.columnCount()):
                                self.item(i, j).setBackground(QBrush(bg))
                        
                        if 'foreground' in style:
                            fg = style['foreground']
                            if isinstance(fg, str): fg = QColor(fg)
                            for j in range(self.columnCount()):
                                self.item(i, j).setForeground(QBrush(fg))
                                
                        if style.get('font_bold'):
                            font = self.item(i, 0).font()
                            font.setBold(True)
                            for j in range(self.columnCount()):
                                self.item(i, j).setFont(font)
                                
                        if 'tooltip' in style:
                             for j in range(self.columnCount()):
                                self.item(i, j).setToolTip(style['tooltip'])
                except Exception as e:
                    print(f"Error applying row style: {e}")
        
        # Restore selection if possible (TODO)

    def on_double_click(self, index):
        """Handle double click"""
        row = index.row()
        if 0 <= row < len(self.data_map):
            item = self.data_map[row]
            # Assume item has 'id' attribute or key
            item_id = item.get('id') if isinstance(item, dict) else getattr(item, 'id', None)
            if item_id:
                self.row_double_clicked.emit(item_id)

    def on_selection_changed(self):
        """Handle selection change"""
        selected_rows = self.selectionModel().selectedRows()
        selected_ids = []
        for index in selected_rows:
            row = index.row()
            if 0 <= row < len(self.data_map):
                item = self.data_map[row]
                item_id = item.get('id') if isinstance(item, dict) else getattr(item, 'id', None)
                if item_id:
                    selected_ids.append(item_id)
        self.selection_changed.emit(selected_ids)

    def on_column_resized(self, logical_index, old_size, new_size):
        """Handle resize"""
        if 0 <= logical_index < len(self.column_map):
            col_id = self.column_map[logical_index]['id']
            self.column_resized.emit(col_id, new_size)

    def on_header_clicked(self, logical_index):
        """Handle header click for sorting"""
        if 0 <= logical_index < len(self.column_map):
            col_id = self.column_map[logical_index]['id']
            self.sort_requested.emit(col_id)

    def on_context_menu(self, pos):
        """Handle context menu request"""
        item = self.itemAt(pos)
        if item:
            row = item.row()
            self.context_menu_requested.emit(pos, row)

from PyQt6.QtWidgets import QMenu, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from src.views.components.document_list_table import DocumentListTable
from typing import List, Dict, Any, Optional

class TablePartComponent(DocumentListTable):
    """
    Table Part Component for editable document lines.
    (Task 9)
    """
    # Signals for row management
    row_add_requested = pyqtSignal()
    row_copy_requested = pyqtSignal(int) # row_index
    row_delete_requested = pyqtSignal(int) # row_index
    row_move_up_requested = pyqtSignal(int) # row_index
    row_move_down_requested = pyqtSignal(int) # row_index
    cell_value_changed = pyqtSignal(int, str, object) # row_index, col_id, new_value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(DocumentListTable.EditTrigger.DoubleClicked | DocumentListTable.EditTrigger.AnyKeyPressed)
        self._updating = False
        self.itemChanged.connect(self.on_item_changed)
        self.column_editable_map: Dict[str, bool] = {} # col_id -> is_editable

    def configure_columns(self, columns: List[Dict], settings: Optional[Dict] = None):
        super().configure_columns(columns, settings)
        # Cache editable status
        self.column_editable_map = {c['id']: c.get('editable', False) for c in columns}

    def set_data(self, items: List[Any]):
        self._updating = True
        super().set_data(items)
        
        # Apply editable flags
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item:
                    col_id = self.column_map[j]['id']
                    is_editable = self.column_editable_map.get(col_id, False)
                    flags = item.flags()
                    if is_editable:
                        flags |= Qt.ItemFlag.ItemIsEditable
                    else:
                        flags &= ~Qt.ItemFlag.ItemIsEditable
                    item.setFlags(flags)
        
        self._updating = False

    def on_item_changed(self, item):
        if self._updating:
            return
            
        row = item.row()
        col = item.column()
        if 0 <= col < len(self.column_map):
            col_id = self.column_map[col]['id']
            val = item.text() # TODO: handle types based on column config
            self.cell_value_changed.emit(row, col_id, val)

    def on_context_menu(self, pos):
        """Override to add row management commands"""
        menu = QMenu(self)
        
        # Standard actions
        add_action = QAction("Добавить", self)
        add_action.triggered.connect(self.row_add_requested.emit)
        menu.addAction(add_action)
        
        item = self.itemAt(pos)
        if item:
            row = item.row()
            
            copy_action = QAction("Копировать", self)
            copy_action.triggered.connect(lambda: self.row_copy_requested.emit(row))
            menu.addAction(copy_action)
            
            delete_action = QAction("Удалить", self)
            delete_action.triggered.connect(lambda: self.row_delete_requested.emit(row))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            move_up = QAction("Переместить вверх", self)
            move_up.triggered.connect(lambda: self.row_move_up_requested.emit(row))
            menu.addAction(move_up)
            
            move_down = QAction("Переместить вниз", self)
            move_down.triggered.connect(lambda: self.row_move_down_requested.emit(row))
            menu.addAction(move_down)
            
        menu.exec(self.mapToGlobal(pos))
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Insert:
            self.row_add_requested.emit()
        elif event.key() == Qt.Key.Key_Delete:
            if self.currentRow() >= 0:
                self.row_delete_requested.emit(self.currentRow())
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Up:
                if self.currentRow() >= 0:
                    self.row_move_up_requested.emit(self.currentRow())
            elif event.key() == Qt.Key.Key_Down:
                if self.currentRow() >= 0:
                    self.row_move_down_requested.emit(self.currentRow())
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

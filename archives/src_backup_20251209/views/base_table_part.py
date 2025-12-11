"""Base table part"""
from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtCore import Qt


class BaseTablePart(QTableWidget):
    def __init__(self):
        super().__init__()
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key.Key_Insert:
            self.on_insert_row()
        elif event.key() == Qt.Key.Key_Delete:
            self.on_delete_row()
        elif event.key() == Qt.Key.Key_F4:
            self.on_f4_pressed()
        else:
            super().keyPressEvent(event)
    
    def on_insert_row(self):
        """Handle insert row"""
        pass
    
    def on_delete_row(self):
        """Handle delete row"""
        pass
    
    def on_f4_pressed(self):
        """Handle F4 key"""
        pass

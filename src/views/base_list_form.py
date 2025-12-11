"""Base list form"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget
from PyQt6.QtCore import Qt


class BaseListForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        self.table_view = QTableWidget()
        layout.addWidget(self.table_view)
        
        self.setLayout(layout)
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key.Key_Insert or event.key() == Qt.Key.Key_F9:
            self.on_insert_pressed()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_enter_pressed()
        elif event.key() == Qt.Key.Key_Delete:
            self.on_delete_pressed()
        elif event.key() == Qt.Key.Key_F5:
            self.on_refresh_pressed()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            self.on_search_activated()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            self.on_copy_pressed()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_A:
            self.on_select_all_pressed()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Up:
            self.go_up()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Down:
            self.go_down()
        else:
            super().keyPressEvent(event)
    
    def go_up(self):
        """Navigate up in hierarchy"""
        pass

    def go_down(self):
        """Navigate down in hierarchy"""
        self.on_enter_pressed()

    def on_insert_pressed(self):
        """Handle insert key"""
        pass
    
    def on_enter_pressed(self):
        """Handle enter key"""
        pass
    
    def on_delete_pressed(self):
        """Handle delete key"""
        pass
    
    def on_refresh_pressed(self):
        """Handle refresh"""
        if hasattr(self, 'load_data'):
            search_text = self.search_edit.text() if hasattr(self, 'search_edit') else ""
            self.load_data(search_text)
    
    def on_search_activated(self):
        """Handle search activation"""
        pass
    
    def on_copy_pressed(self):
        """Handle copy"""
        pass
    
    def on_select_all_pressed(self):
        """Handle select all (Ctrl+A)"""
        if hasattr(self, 'table_view') and self.table_view:
            self.table_view.selectAll()

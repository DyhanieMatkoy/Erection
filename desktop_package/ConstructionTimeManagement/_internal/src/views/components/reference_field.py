"""Reference field component with keyboard shortcuts"""
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional


class ReferenceField(QWidget):
    """
    Reference field component with F2/F4 keyboard shortcuts.
    
    F2: Start editing search substring
    F4: Call selector for current field
    """
    
    # Signal when reference value changes
    value_changed = pyqtSignal(int, str)  # id, name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reference_id = 0
        self.reference_name = ""
        self.reference_table = ""
        self.reference_title = "Выбор из справочника"
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Main edit field (read-only, displays selected value)
        self.edit_field = QLineEdit()
        self.edit_field.setReadOnly(True)
        self.edit_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Don't take focus by default
        layout.addWidget(self.edit_field)
        
        # Selector button
        self.selector_button = QPushButton("...")
        self.selector_button.setMaximumWidth(30)
        self.selector_button.setToolTip("Выбор из справочника (F4)")
        self.selector_button.clicked.connect(self.open_selector)
        layout.addWidget(self.selector_button)
        
        # Clear button
        self.clear_button = QPushButton("✕")
        self.clear_button.setMaximumWidth(30)
        self.clear_button.setToolTip("Очистить")
        self.clear_button.clicked.connect(self.clear_value)
        layout.addWidget(self.clear_button)
        
        self.setLayout(layout)
    
    def set_reference(self, table_name: str, title: str = None):
        """Set reference table and title"""
        self.reference_table = table_name
        self.reference_title = title or f"Выбор из справочника: {table_name}"
    
    def set_value(self, ref_id: int, name: str):
        """Set reference value"""
        self.reference_id = ref_id
        self.reference_name = name
        self.edit_field.setText(name if name else "")
        self.value_changed.emit(ref_id, name)
    
    def get_value(self) -> tuple[int, str]:
        """Get current value as (id, name) tuple"""
        return (self.reference_id, self.reference_name)
    
    def clear_value(self):
        """Clear reference value"""
        self.set_value(0, "")
    
    def open_selector(self):
        """Open reference selector dialog"""
        if not self.reference_table:
            return
        
        from ..reference_picker_dialog import ReferencePickerDialog
        dialog = ReferencePickerDialog(
            self.reference_table, 
            self.reference_title, 
            self.parentWidget(),
            current_id=self.reference_id
        )
        
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.set_value(selected_id, selected_name)
    
    def start_search_edit(self):
        """
        Start editing search substring.
        Opens selector with focus on search field.
        """
        if not self.reference_table:
            return
        
        from ..reference_picker_dialog import ReferencePickerDialog
        dialog = ReferencePickerDialog(
            self.reference_table, 
            self.reference_title, 
            self.parentWidget(),
            current_id=self.reference_id
        )
        
        # Set focus to search field
        dialog.search_edit.setFocus()
        dialog.search_edit.selectAll()
        
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.set_value(selected_id, selected_name)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F2:
            # F2: Start editing search substring
            self.start_search_edit()
        elif event.key() == Qt.Key.Key_F4:
            # F4: Call selector
            self.open_selector()
        else:
            super().keyPressEvent(event)
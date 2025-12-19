from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                             QTreeWidgetItem, QPushButton, QDialogButtonBox, QLabel)
from PyQt6.QtCore import Qt
from typing import List, Dict, Any

class FormConfigurationDialog(QDialog):
    """
    Dialog for configuring form settings (columns, commands).
    (Task 8.1)
    """
    def __init__(self, parent=None, settings_manager=None, form_id: str = "", available_columns: List[Dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Настройка формы")
        self.resize(400, 500)
        self.settings_manager = settings_manager
        self.form_id = form_id
        self.available_columns = available_columns or []
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tabs or just a tree for now? 
        # Requirement says "command tree interface", but we also need column config.
        # Let's use a tree for everything or separate sections.
        # Columns first.
        
        layout.addWidget(QLabel("Колонки:"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя", "Видимость"])
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove) # Reordering
        layout.addWidget(self.tree)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        
        # Reset button
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self.reset_to_defaults)
        btn_box.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def load_settings(self):
        """Load current settings into tree"""
        self.tree.clear()
        
        # Get saved settings
        saved_settings = {}
        if self.settings_manager:
            saved_settings = self.settings_manager.load_column_settings(1, self.form_id) or {} # Mock user_id 1 for now or pass it
        
        # Merge available columns with saved settings (order and visibility)
        # If saved settings exist, we should respect their order if possible.
        # Simple approach: Iterate available, check saved.
        # Better: Iterate saved keys for order, add missing.
        
        # For now, just list available
        for col in self.available_columns:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, col['name'])
            item.setData(0, Qt.ItemDataRole.UserRole, col['id'])
            
            # Check visibility
            is_visible = col.get('visible', True)
            if col['id'] in saved_settings:
                # If settings is dict
                s = saved_settings[col['id']]
                if isinstance(s, dict):
                    is_visible = s.get('visible', True)
            
            item.setCheckState(1, Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked)

    def get_settings(self) -> Dict:
        """Get settings from UI"""
        settings = {}
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            col_id = item.data(0, Qt.ItemDataRole.UserRole)
            is_visible = item.checkState(1) == Qt.CheckState.Checked
            settings[col_id] = {'visible': is_visible}
            # We could also save order here if we store it as a list instead of dict
        return settings

    def reset_to_defaults(self):
        """Reset UI to defaults"""
        self.tree.clear()
        for col in self.available_columns:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, col['name'])
            item.setData(0, Qt.ItemDataRole.UserRole, col['id'])
            # Default visibility
            is_visible = col.get('visible', True)
            item.setCheckState(1, Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked)

    def accept(self):
        """Save settings and close"""
        if self.settings_manager:
            settings = self.get_settings()
            try:
                # 1 is mock user_id, in real app we pass it
                # We should probably store user_id in self
                user_id = 1 
                self.settings_manager.save_column_settings(user_id, self.form_id, settings)
            except Exception as e:
                print(f"Error saving settings: {e}")
                # Maybe show error dialog
        
        super().accept()

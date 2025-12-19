from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                             QTreeWidgetItem, QPushButton, QDialogButtonBox, QLabel, QComboBox)
from PyQt6.QtCore import Qt
from typing import List, Dict
from src.controllers.admin_configuration_controller import AdminConfigurationController

class AdminConfigurationDialog(QDialog):
    """
    Dialog for Admin Configuration of form permissions (Task 11.3).
    """
    def __init__(self, form_id: str, available_columns: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Администрирование формы: {form_id}")
        self.resize(600, 500)
        self.form_id = form_id
        self.available_columns = available_columns
        self.controller = AdminConfigurationController()
        
        self.setup_ui()
        self.load_rules()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Role selector
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Роль:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(['all', 'admin', 'manager', 'foreman', 'executor'])
        self.role_combo.currentTextChanged.connect(self.load_rules)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Колонка", "Обязательная", "Скрыта (Доступ запрещен)"])
        self.tree.setColumnWidth(0, 200)
        layout.addWidget(self.tree)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)

    def load_rules(self):
        """Load rules for selected role"""
        self.tree.clear()
        role = self.role_combo.currentText()
        rules = self.controller.get_column_rules(self.form_id, role)
        
        # Map rules by column_id
        rules_map = {r['column_id']: r for r in rules}
        
        for col in self.available_columns:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, col['name'])
            item.setData(0, Qt.ItemDataRole.UserRole, col['id'])
            
            rule = rules_map.get(col['id'], {})
            is_mandatory = rule.get('is_mandatory', False)
            is_restricted = rule.get('is_restricted', False)
            
            item.setCheckState(1, Qt.CheckState.Checked if is_mandatory else Qt.CheckState.Unchecked)
            item.setCheckState(2, Qt.CheckState.Checked if is_restricted else Qt.CheckState.Unchecked)

    def save_rules(self):
        """Collect and save rules"""
        role = self.role_combo.currentText()
        rules_data = []
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            col_id = item.data(0, Qt.ItemDataRole.UserRole)
            is_mandatory = item.checkState(1) == Qt.CheckState.Checked
            is_restricted = item.checkState(2) == Qt.CheckState.Checked
            
            if is_mandatory or is_restricted:
                rules_data.append({
                    'column_id': col_id,
                    'is_mandatory': is_mandatory,
                    'is_restricted': is_restricted
                })
        
        self.controller.save_rules(self.form_id, role, rules_data)

    def accept(self):
        self.save_rules()
        self.controller.close()
        super().accept()
        
    def reject(self):
        self.controller.close()
        super().reject()

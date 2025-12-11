"""Cost Item Material form for managing materials for a cost item"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from ..data.repositories.cost_item_material_repository import CostItemMaterialRepository
from ..data.repositories.material_repository import MaterialRepository
from ..data.repositories.cost_item_repository import CostItemRepository
from .material_picker_dialog import MaterialPickerDialog


class CostItemMaterialForm(QDialog):
    def __init__(self, parent=None, cost_item_id=None):
        super().__init__(parent)
        self.cost_item_id = cost_item_id
        self.cost_item_material_repo = CostItemMaterialRepository()
        self.material_repo = MaterialRepository()
        self.cost_item_repo = CostItemRepository()
        
        self.setWindowTitle("Материалы элемента затрат")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Cost Item info
        self.cost_item_label = QLabel()
        layout.addWidget(self.cost_item_label)
        
        # Materials table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels(["Код", "Наименование", "Ед. изм.", "Кол-во на ед."])
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.materials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.materials_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить (Insert)")
        self.add_button.clicked.connect(self.on_add_material)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Изменить (Enter)")
        self.edit_button.clicked.connect(self.on_edit_material)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить (Delete)")
        self.delete_button.clicked.connect(self.on_delete_material)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_data(self):
        """Load cost item and materials data"""
        # Load cost item info
        cost_item = self.cost_item_repo.find_by_id(self.cost_item_id)
        if cost_item:
            self.cost_item_label.setText(f"Элемент затрат: {cost_item.code} - {cost_item.description}")
        
        # Load materials
        materials = self.cost_item_material_repo.get_materials_for_cost_item(self.cost_item_id)
        self.populate_materials_table(materials)
    
    def populate_materials_table(self, materials):
        """Populate materials table"""
        self.materials_table.setRowCount(len(materials))
        
        for row, (material, quantity) in enumerate(materials):
            # Code
            self.materials_table.setItem(row, 0, QTableWidgetItem(material.code or ""))
            
            # Description
            self.materials_table.setItem(row, 1, QTableWidgetItem(material.description or ""))
            
            # Unit
            self.materials_table.setItem(row, 2, QTableWidgetItem(material.unit or ""))
            
            # Quantity
            quantity_item = QTableWidgetItem(f"{quantity:.2f}")
            quantity_item.setData(Qt.ItemDataRole.UserRole, quantity)
            self.materials_table.setItem(row, 3, quantity_item)
    
    def get_selected_material_id(self):
        """Get ID of selected material"""
        row = self.materials_table.currentRow()
        if row >= 0:
            # Get material code and find by code
            code = self.materials_table.item(row, 0).text()
            material = self.material_repo.find_by_code(code)
            return material.id if material else None
        return None
    
    def get_selected_quantity(self):
        """Get quantity of selected material"""
        row = self.materials_table.currentRow()
        if row >= 0:
            item = self.materials_table.item(row, 3)
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def on_add_material(self):
        """Handle add material button"""
        # Get materials not already associated with cost item
        available_materials = self.cost_item_material_repo.find_materials_not_in_cost_item(self.cost_item_id)
        
        if not available_materials:
            QMessageBox.information(self, "Информация", "Все материалы уже добавлены")
            return
        
        # Show material picker dialog
        dialog = MaterialPickerDialog(self, available_materials)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_material:
            # Show quantity dialog
            quantity_dialog = QuantityDialog(self, dialog.selected_material)
            if quantity_dialog.exec() == QDialog.DialogCode.Accepted:
                # Add material to cost item
                if self.cost_item_material_repo.create_or_update_association(
                    self.cost_item_id, 
                    dialog.selected_material.id, 
                    quantity_dialog.quantity
                ):
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить материал")
    
    def on_edit_material(self):
        """Handle edit material button"""
        material_id = self.get_selected_material_id()
        quantity = self.get_selected_quantity()
        
        if material_id and quantity is not None:
            material = self.material_repo.find_by_id(material_id)
            if material:
                # Show quantity dialog
                quantity_dialog = QuantityDialog(self, material, quantity)
                if quantity_dialog.exec() == QDialog.DialogCode.Accepted:
                    # Update material quantity
                    if self.cost_item_material_repo.create_or_update_association(
                        self.cost_item_id, 
                        material_id, 
                        quantity_dialog.quantity
                    ):
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Не удалось обновить количество материала")
    
    def on_delete_material(self):
        """Handle delete material button"""
        material_id = self.get_selected_material_id()
        
        if material_id:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Вы уверены, что хотите удалить этот материал?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.cost_item_material_repo.remove_association(self.cost_item_id, material_id):
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить материал")


class QuantityDialog(QDialog):
    """Dialog for entering material quantity"""
    
    def __init__(self, parent=None, material=None, initial_quantity=1.0):
        super().__init__(parent)
        self.material = material
        self.quantity = initial_quantity
        
        self.setWindowTitle("Количество материала")
        self.setModal(True)
        self.resize(300, 150)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Material info
        if self.material:
            material_label = QLabel(f"Материал: {self.material.code} - {self.material.description}")
            layout.addWidget(material_label)
        
        # Quantity
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Количество на единицу:"))
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 999999.99)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setValue(self.quantity)
        quantity_layout.addWidget(self.quantity_spin)
        layout.addLayout(quantity_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    @property
    def quantity(self):
        """Get quantity from spin box"""
        return self.quantity_spin.value()
    
    @quantity.setter
    def quantity(self, value):
        """Set quantity to spin box"""
        self.quantity_spin.setValue(value)
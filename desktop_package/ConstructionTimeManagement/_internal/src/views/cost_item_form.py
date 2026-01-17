"""Cost Item form for editing individual cost items"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                              QCheckBox, QPushButton, QMessageBox, QDoubleSpinBox, QComboBox,
                              QListWidget, QListWidgetItem, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from ..data.repositories.cost_item_repository import CostItemRepository
from ..data.repositories.unit_repository import UnitRepository
from ..data.repositories.material_repository import MaterialRepository
from ..data.models.sqlalchemy_models import CostItem
from ..data.database_manager import DatabaseManager


class CostItemForm(QDialog):
    def __init__(self, parent=None, cost_item_id=None):
        super().__init__(parent)
        self.cost_item_id = cost_item_id
        self.cost_item_repo = CostItemRepository()
        self.unit_repo = UnitRepository(DatabaseManager())
        self.material_repo = MaterialRepository(DatabaseManager())
        self.cost_item = None
        
        self.setWindowTitle("Элемент затрат")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.load_units()
        self.load_materials()
        
        if cost_item_id:
            self.load_cost_item()
        elif self.parent_id or self.is_folder_init:
            self.setup_new_item()

    def setup_new_item(self):
        """Setup new item defaults"""
        if self.parent_id:
             for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break
        
        if self.is_folder_init:
            self.is_folder_check.setChecked(True)
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Code
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Код:"))
        self.code_edit = QLineEdit()
        code_layout.addWidget(self.code_edit)
        layout.addLayout(code_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Наименование:"))
        self.desc_edit = QLineEdit()
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # Is Folder
        self.is_folder_check = QCheckBox("Это группа")
        self.is_folder_check.stateChanged.connect(self.on_folder_changed)
        layout.addWidget(self.is_folder_check)
        
        # Parent
        parent_layout = QHBoxLayout()
        parent_layout.addWidget(QLabel("Родитель:"))
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("(Нет)", None)
        parent_layout.addWidget(self.parent_combo)
        layout.addLayout(parent_layout)
        
        # Price
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Цена:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" руб.")
        price_layout.addWidget(self.price_spin)
        layout.addLayout(price_layout)
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Ед. изм.:"))
        self.unit_combo = QComboBox()
        self.unit_combo.setEditable(True)  # Allow custom values for backward compatibility
        unit_layout.addWidget(self.unit_combo)
        layout.addLayout(unit_layout)
        
        # Labor Coefficient
        labor_layout = QHBoxLayout()
        labor_layout.addWidget(QLabel("Коэфф. трудозатрат:"))
        self.labor_spin = QDoubleSpinBox()
        self.labor_spin.setRange(0, 999.99)
        self.labor_spin.setDecimals(2)
        labor_layout.addWidget(self.labor_spin)
        layout.addLayout(labor_layout)
        
        # Materials section
        materials_group = QGroupBox("Материалы")
        materials_layout = QVBoxLayout()
        
        # Materials list
        self.materials_list = QListWidget()
        self.materials_list.setMaximumHeight(150)
        materials_layout.addWidget(self.materials_list)
        
        # Materials buttons
        materials_buttons_layout = QHBoxLayout()
        
        self.add_material_button = QPushButton("Добавить")
        self.add_material_button.clicked.connect(self.add_material)
        materials_buttons_layout.addWidget(self.add_material_button)
        
        self.remove_material_button = QPushButton("Удалить")
        self.remove_material_button.clicked.connect(self.remove_material)
        materials_buttons_layout.addWidget(self.remove_material_button)
        
        materials_layout.addLayout(materials_buttons_layout)
        materials_group.setLayout(materials_layout)
        layout.addWidget(materials_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Load parent items
        self.load_parent_items()
    
    def load_units(self):
        """Load units into combo box"""
        units = self.unit_repo.find_all()
        self.unit_combo.clear()
        self.unit_combo.addItem("", None)  # Empty option
        
        for unit in units:
            self.unit_combo.addItem(unit['name'], unit['id'])
    
    def load_materials(self):
        """Load all available materials"""
        self.all_materials = self.material_repo.find_all()
    
    def add_material(self):
        """Add material to the cost item"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор материала")
        dialog.setModal(True)
        dialog.resize(400, 150)
        
        layout = QVBoxLayout()
        
        # Material selection
        material_layout = QHBoxLayout()
        material_layout.addWidget(QLabel("Материал:"))
        material_combo = QComboBox()
        
        for material in self.all_materials:
            material_combo.addItem(f"{material['code']} - {material['description']}", material['id'])
        
        material_layout.addWidget(material_combo)
        layout.addLayout(material_layout)
        
        # Quantity
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Количество на единицу:"))
        quantity_spin = QDoubleSpinBox()
        quantity_spin.setRange(0, 999999.99)
        quantity_spin.setDecimals(3)
        quantity_spin.setValue(1.0)
        quantity_layout.addWidget(quantity_spin)
        layout.addLayout(quantity_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            material_id = material_combo.currentData()
            quantity = quantity_spin.value()
            
            if material_id:
                # Find material data
                material_data = None
                for material in self.all_materials:
                    if material['id'] == material_id:
                        material_data = material
                        break
                
                if material_data:
                    # Check if already in list
                    for i in range(self.materials_list.count()):
                        item = self.materials_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == material_id:
                            return  # Already added
                    
                    # Add to list
                    item = QListWidgetItem(f"{material_data['code']} - {material_data['description']} ({quantity})")
                    item.setData(Qt.ItemDataRole.UserRole, material_id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, quantity)  # Store quantity
                    self.materials_list.addItem(item)
    
    def remove_material(self):
        """Remove selected material from the cost item"""
        current_row = self.materials_list.currentRow()
        if current_row >= 0:
            self.materials_list.takeItem(current_row)
    
    def load_parent_items(self):
        """Load parent items into combo box"""
        cost_items = self.cost_item_repo.find_folders()
        for item in cost_items:
            if self.cost_item_id is None or item['id'] != self.cost_item_id:
                self.parent_combo.addItem(f"{item['code']} - {item['description']}", item['id'])
    
    def load_cost_item(self):
        """Load cost item data"""
        self.cost_item = self.cost_item_repo.find_by_id(self.cost_item_id)
        if self.cost_item:
            self.code_edit.setText(self.cost_item.code or "")
            self.desc_edit.setText(self.cost_item.description or "")
            self.is_folder_check.setChecked(self.cost_item.is_folder)
            
            # Set parent
            if self.cost_item.parent_id:
                for i in range(self.parent_combo.count()):
                    if self.parent_combo.itemData(i) == self.cost_item.parent_id:
                        self.parent_combo.setCurrentIndex(i)
                        break
            
            self.price_spin.setValue(self.cost_item.price or 0)
            
            # Set unit
            if self.cost_item.unit_id:
                # Find unit in combo box by ID
                for i in range(self.unit_combo.count()):
                    if self.unit_combo.itemData(i) == self.cost_item.unit_id:
                        self.unit_combo.setCurrentIndex(i)
                        break
            # Legacy unit column removed - only use unit_id foreign key
            
            self.labor_spin.setValue(self.cost_item.labor_coefficient or 0)
            
            # Load materials
            self.load_cost_item_materials()
            
            self.on_folder_changed()
    
    def load_cost_item_materials(self):
        """Load materials associated with the cost item"""
        if not self.cost_item_id:
            return
            
        materials = self.cost_item_repo.find_materials(self.cost_item_id)
        self.materials_list.clear()
        
        for material in materials:
            # Find material data
            material_data = None
            for m in self.all_materials:
                if m['id'] == material['material_id']:
                    material_data = m
                    break
            
            if material_data:
                # Add to list
                item = QListWidgetItem(f"{material_data['code']} - {material_data['description']} ({material['quantity_per_unit']})")
                item.setData(Qt.ItemDataRole.UserRole, material['material_id'])
                item.setData(Qt.ItemDataRole.UserRole + 1, material['quantity_per_unit'])  # Store quantity
                self.materials_list.addItem(item)
    
    def on_folder_changed(self):
        """Handle folder checkbox change"""
        is_folder = self.is_folder_check.isChecked()
        self.price_spin.setEnabled(not is_folder)
        self.unit_combo.setEnabled(not is_folder)
        self.labor_spin.setEnabled(not is_folder)
    
    def save(self):
        """Save cost item"""
        # Validate
        if not self.code_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Код не может быть пустым")
            return
        
        if not self.desc_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование не может быть пустым")
            return
        
        # Create or update cost item
        if self.cost_item is None:
            self.cost_item = CostItem()
        
        self.cost_item.code = self.code_edit.text().strip()
        self.cost_item.description = self.desc_edit.text().strip()
        self.cost_item.is_folder = self.is_folder_check.isChecked()
        self.cost_item.parent_id = self.parent_combo.currentData()
        self.cost_item.price = self.price_spin.value()
        
        # Handle unit selection
        unit_id = self.unit_combo.currentData()
        if unit_id:
            self.cost_item.unit_id = unit_id
            # Legacy unit column removed - only use unit_id foreign key
        else:
            # Custom unit - should create a new unit record instead of using legacy column
            self.cost_item.unit_id = None
        
        self.cost_item.labor_coefficient = self.labor_spin.value()
        
        # Save cost item
        result = self.cost_item_repo.save(self.cost_item)
        if not result:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить элемент затрат")
            return
        
        # Save materials
        self.save_cost_item_materials()
        
        self.accept()
    
    def save_cost_item_materials(self):
        """Save materials associated with the cost item"""
        if not self.cost_item.id:
            return
        
        # Get current materials from the list
        materials = []
        for i in range(self.materials_list.count()):
            item = self.materials_list.item(i)
            material_id = item.data(Qt.ItemDataRole.UserRole)
            quantity = item.data(Qt.ItemDataRole.UserRole + 1)
            materials.append({
                'material_id': material_id,
                'quantity_per_unit': quantity
            })
        
        # Save materials
        self.cost_item_repo.save_materials(self.cost_item.id, materials)
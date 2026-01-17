"""Material form for editing individual materials"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                              QPushButton, QMessageBox, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt
from ..data.repositories.material_repository import MaterialRepository
from ..data.repositories.unit_repository import UnitRepository
from ..data.models.sqlalchemy_models import Material
from ..data.database_manager import DatabaseManager


class MaterialForm(QDialog):
    def __init__(self, parent=None, material_id=None):
        super().__init__(parent)
        self.material_id = material_id
        self.material_repo = MaterialRepository()
        self.unit_repo = UnitRepository(DatabaseManager())
        self.material = None
        
        self.setWindowTitle("Материал")
        self.setModal(True)
        self.resize(500, 200)
        
        self.setup_ui()
        self.load_units()
        
        if material_id:
            self.load_material()
    
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
    
    def load_units(self):
        """Load units into combo box"""
        units = self.unit_repo.find_all()
        self.unit_combo.clear()
        self.unit_combo.addItem("", None)  # Empty option
        
        for unit in units:
            self.unit_combo.addItem(unit['name'], unit['id'])
    
    def load_material(self):
        """Load material data"""
        self.material = self.material_repo.find_by_id(self.material_id)
        if self.material:
            self.code_edit.setText(self.material.code or "")
            self.desc_edit.setText(self.material.description or "")
            self.price_spin.setValue(self.material.price or 0)
            
            # Set unit
            if self.material.unit_id:
                # Find unit in combo box by ID
                for i in range(self.unit_combo.count()):
                    if self.unit_combo.itemData(i) == self.material.unit_id:
                        self.unit_combo.setCurrentIndex(i)
                        break
            # Legacy unit column removed - only use unit_id foreign key
    
    def save(self):
        """Save material"""
        # Validate
        if not self.code_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Код не может быть пустым")
            return
        
        if not self.desc_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование не может быть пустым")
            return
        
        # Create or update material
        if self.material is None:
            self.material = Material()
        
        self.material.code = self.code_edit.text().strip()
        self.material.description = self.desc_edit.text().strip()
        self.material.price = self.price_spin.value()
        
        # Handle unit selection
        unit_id = self.unit_combo.currentData()
        if unit_id:
            self.material.unit_id = unit_id
            # Legacy unit column removed - only use unit_id foreign key
        else:
            # Custom unit - should create a new unit record instead of using legacy column
            self.material.unit_id = None
        
        # Save
        result = self.material_repo.save(self.material)
        if result:
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить материал")
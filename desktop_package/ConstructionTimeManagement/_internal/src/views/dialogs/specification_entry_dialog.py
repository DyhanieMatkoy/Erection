from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, 
    QDoubleSpinBox, QDialogButtonBox, QLabel, QMessageBox, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from ...data.repositories.material_repository import MaterialRepository
from .material_selector_dialog import MaterialSelectorDialog

class SpecificationEntryDialog(QDialog):
    """Dialog for adding or editing a work specification entry"""
    
    def __init__(self, parent=None, units=None, data=None):
        super().__init__(parent)
        self.units = units or [] # List of dicts or objects with id, name
        self.data = data # Existing data for edit mode
        self.material_repo = MaterialRepository()
        self.selected_material_id = None
        
        self.setup_ui()
        if self.data:
            self.load_data()
            self.setWindowTitle("Изменить компонент")
        else:
            self.setWindowTitle("Добавить компонент")
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Component Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Material', 'Labor', 'Equipment', 'Other'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Тип:", self.type_combo)
        
        # Component Name
        name_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        
        self.select_material_btn = QPushButton("...")
        self.select_material_btn.setToolTip("Выбрать из справочника материалов")
        self.select_material_btn.setMaximumWidth(30)
        self.select_material_btn.clicked.connect(self.on_select_material)
        name_layout.addWidget(self.select_material_btn)
        
        form_layout.addRow("Наименование:", name_layout)
        
        # Unit
        self.unit_combo = QComboBox()
        # Add empty item
        self.unit_combo.addItem("", None)
        for unit in self.units:
            # Assuming unit is object or dict
            if isinstance(unit, dict):
                self.unit_combo.addItem(unit.get('name', ''), unit.get('id'))
            else:
                self.unit_combo.addItem(unit.name, unit.id)
        form_layout.addRow("Ед. изм.:", self.unit_combo)
        
        # Consumption Rate
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0.0, 999999.999999)
        self.rate_spin.setDecimals(6)
        form_layout.addRow("Норма расхода:", self.rate_spin)
        
        # Unit Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 999999999.99)
        self.price_spin.setDecimals(2)
        form_layout.addRow("Цена:", self.price_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initialize button state
        self.on_type_changed(self.type_combo.currentText())
        
    def load_data(self):
        # Type
        index = self.type_combo.findText(self.data.get('component_type', ''))
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
            
        # Name
        self.name_edit.setText(self.data.get('component_name', ''))
        
        # Unit
        unit_id = self.data.get('unit_id')
        if unit_id:
            index = self.unit_combo.findData(unit_id)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
                
        # Rate
        self.rate_spin.setValue(float(self.data.get('consumption_rate', 0)))
        
        # Price
        self.price_spin.setValue(float(self.data.get('unit_price', 0)))
        
    def on_type_changed(self, text):
        """Enable/disable material selection button based on type"""
        self.select_material_btn.setVisible(text == 'Material')

    def on_select_material(self):
        """Open material selector dialog"""
        dialog = MaterialSelectorDialog(self)
        if dialog.exec():
            material_id = dialog.get_selected_material_id()
            if material_id:
                material = self.material_repo.find_by_id(material_id)
                if material:
                    # Populate fields
                    # Check if material is an object or dict
                    description = getattr(material, 'description', None) or material.get('description')
                    code = getattr(material, 'code', None) or material.get('code')
                    price = getattr(material, 'price', None) or material.get('price')
                    unit_id = getattr(material, 'unit_id', None) or material.get('unit_id')
                    
                    self.name_edit.setText(description or code or "")
                    
                    # Set Price
                    self.price_spin.setValue(float(price or 0))
                    
                    # Set Unit
                    if unit_id:
                        index = self.unit_combo.findData(unit_id)
                        if index >= 0:
                            self.unit_combo.setCurrentIndex(index)
                    
                    # Store material ID for saving
                    self.selected_material_id = material_id

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите наименование компонента")
            return
            
        self.accept()
        
    def get_data(self):
        return {
            'component_type': self.type_combo.currentText(),
            'component_name': self.name_edit.text().strip(),
            'unit_id': self.unit_combo.currentData(),
            'consumption_rate': self.rate_spin.value(),
            'unit_price': self.price_spin.value(),
            'material_id': self.selected_material_id
        }

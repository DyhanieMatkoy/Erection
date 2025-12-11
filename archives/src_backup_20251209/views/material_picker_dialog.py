"""Material picker dialog for selecting materials"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QLineEdit, QLabel)
from PyQt6.QtCore import Qt
from ..data.models.sqlalchemy_models import Material


class MaterialPickerDialog(QDialog):
    def __init__(self, parent=None, materials=None):
        super().__init__(parent)
        self.materials = materials or []
        self.selected_material = None
        
        self.setWindowTitle("Выбор материала")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        self.populate_table()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels(["Код", "Наименование", "Цена", "Ед. изм."])
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.materials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.materials_table.doubleClicked.connect(self.on_double_clicked)
        layout.addWidget(self.materials_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.on_select)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def populate_table(self, materials=None):
        """Populate table with materials"""
        materials_to_show = materials or self.materials
        self.materials_table.setRowCount(len(materials_to_show))
        
        for row, material in enumerate(materials_to_show):
            # Code
            self.materials_table.setItem(row, 0, QTableWidgetItem(material.code or ""))
            
            # Description
            self.materials_table.setItem(row, 1, QTableWidgetItem(material.description or ""))
            
            # Price
            price_text = f"{material.price:.2f}" if material.price else ""
            self.materials_table.setItem(row, 2, QTableWidgetItem(price_text))
            
            # Unit
            self.materials_table.setItem(row, 3, QTableWidgetItem(material.unit or ""))
            
            # Store material object in item data
            self.materials_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, material)
    
    def get_selected_material(self):
        """Get selected material from table"""
        row = self.materials_table.currentRow()
        if row >= 0:
            item = self.materials_table.item(row, 0)
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def on_select(self):
        """Handle select button"""
        self.selected_material = self.get_selected_material()
        if self.selected_material:
            self.accept()
    
    def on_double_clicked(self):
        """Handle double click"""
        self.on_select()
    
    def on_search_changed(self):
        """Handle search text change"""
        search_text = self.search_edit.text().strip().lower()
        
        if not search_text:
            self.populate_table()
            return
        
        # Filter materials
        filtered_materials = []
        for material in self.materials:
            if (material.code and search_text in material.code.lower()) or \
               (material.description and search_text in material.description.lower()):
                filtered_materials.append(material)
        
        self.populate_table(filtered_materials)
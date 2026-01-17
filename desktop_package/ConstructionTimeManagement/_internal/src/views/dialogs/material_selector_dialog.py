
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                             QHeaderView)
from PyQt6.QtCore import Qt
from ...data.repositories.material_repository import MaterialRepository

class MaterialSelectorDialog(QDialog):
    def __init__(self, parent=None, current_id=None):
        super().__init__(parent)
        self.repo = MaterialRepository()
        self.selected_material_id = None
        self.current_id = current_id
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Выбор материала")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Код или наименование...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Код", "Наименование", "Ед.изм", "Цена"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Выбрать")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        self.table.setRowCount(0)
        
        materials = self.repo.find_all()
        
        self.table.setRowCount(len(materials))
        for row, material in enumerate(materials):
            self.table.setItem(row, 0, QTableWidgetItem(material['code'] or ""))
            self.table.setItem(row, 1, QTableWidgetItem(material['description'] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(material['unit_name'] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"{material['price']:.2f}"))
            
            # Store ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, material['id'])
            
            # Select current if matches
            if self.current_id and material['id'] == self.current_id:
                self.table.selectRow(row)
                self.table.scrollToItem(self.table.item(row, 0))

    def on_search(self, text):
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0).text().lower()
            desc = self.table.item(row, 1).text().lower()
            
            match = not text or (text.lower() in code or text.lower() in desc)
            self.table.setRowHidden(row, not match)

    def on_item_double_clicked(self, item):
        self.accept()

    def accept(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
            
        item = self.table.item(current_row, 0)
        self.selected_material_id = item.data(Qt.ItemDataRole.UserRole)
        super().accept()

    def get_selected_material_id(self):
        return self.selected_material_id

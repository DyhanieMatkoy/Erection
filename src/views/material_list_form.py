"""Material list form for managing materials"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QDialog, QMenu)
from PyQt6.QtCore import Qt
from .base_list_form import BaseListForm
from .material_form import MaterialForm
from ..data.repositories.material_repository import MaterialRepository


class MaterialListForm(BaseListForm):
    def __init__(self):
        self.material_repo = MaterialRepository()
        super().__init__()
        self.setWindowTitle("Справочник: Материалы")
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск (Ctrl+F):"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(5)
        self.table_view.setHorizontalHeaderLabels(["ID", "Код", "Наименование", "Цена", "Ед. изм."])
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_enter_pressed)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("Создать (Insert/F9)")
        self.new_button.clicked.connect(self.on_insert_pressed)
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Изменить (Enter/F4)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить (Delete)")
        self.delete_button.clicked.connect(self.on_delete_pressed)
        button_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Обновить (F5)")
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_data(self):
        """Load materials into table"""
        materials = self.material_repo.find_all()
        self.populate_table(materials)
    
    def populate_table(self, materials):
        """Populate table with materials"""
        self.table_view.setRowCount(len(materials))
        
        for row, material in enumerate(materials):
            # ID
            self.table_view.setItem(row, 0, QTableWidgetItem(str(material['id'])))
            
            # Code
            self.table_view.setItem(row, 1, QTableWidgetItem(material['code'] or ""))
            
            # Description
            self.table_view.setItem(row, 2, QTableWidgetItem(material['description'] or ""))
            
            # Price
            price_text = f"{material['price']:.2f}" if material['price'] else ""
            self.table_view.setItem(row, 3, QTableWidgetItem(price_text))
            
            # Unit
            unit_text = material['unit_name'] or material['unit'] or ""
            self.table_view.setItem(row, 4, QTableWidgetItem(unit_text))
    
    def get_selected_id(self):
        """Get ID of selected material"""
        row = self.table_view.currentRow()
        if row >= 0:
            return int(self.table_view.item(row, 0).text())
        return None
    
    def on_insert_pressed(self):
        """Handle insert button"""
        form = MaterialForm(self)
        if form.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def on_enter_pressed(self):
        """Handle edit button"""
        material_id = self.get_selected_id()
        if material_id:
            form = MaterialForm(self, material_id)
            if form.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def on_delete_pressed(self):
        """Handle delete button"""
        material_id = self.get_selected_id()
        if material_id:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Вы уверены, что хотите удалить этот материал?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.material_repo.delete(material_id):
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить материал")
    
    def on_search_text_changed(self):
        """Handle search text change"""
        search_text = self.search_edit.text().strip().lower()
        
        if not search_text:
            self.load_data()
            return
        
        # Search materials
        materials = self.material_repo.search_by_description(search_text)
        self.populate_table(materials)
    
    def show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu(self)
        
        new_action = menu.addAction("Создать")
        new_action.triggered.connect(self.on_insert_pressed)
        
        edit_action = menu.addAction("Изменить")
        edit_action.triggered.connect(self.on_enter_pressed)
        
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self.on_delete_pressed)
        
        menu.exec(self.table_view.mapToGlobal(position))
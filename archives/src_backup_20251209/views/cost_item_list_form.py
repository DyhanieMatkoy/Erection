"""Cost Item list form for managing cost items"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu, QDialog)
from PyQt6.QtCore import Qt
from .base_list_form import BaseListForm
from .cost_item_form import CostItemForm
from .cost_item_material_form import CostItemMaterialForm
from ..data.repositories.cost_item_repository import CostItemRepository


class CostItemListForm(BaseListForm):
    def __init__(self):
        self.cost_item_repo = CostItemRepository()
        super().__init__()
        self.setWindowTitle("Справочник: Элементы затрат")
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
        self.table_view.setColumnCount(7)
        self.table_view.setHorizontalHeaderLabels(["ID", "Код", "Наименование", "Это группа", "Цена", "Ед. изм.", "Материалы"])
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
        
        self.new_group_button = QPushButton("Создать группу")
        self.new_group_button.clicked.connect(self.on_create_group)
        button_layout.addWidget(self.new_group_button)
        
        self.edit_button = QPushButton("Изменить (Enter/F4)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить (Delete)")
        self.delete_button.clicked.connect(self.on_delete_pressed)
        button_layout.addWidget(self.delete_button)
        
        self.materials_button = QPushButton("Материалы")
        self.materials_button.clicked.connect(self.on_materials)
        button_layout.addWidget(self.materials_button)
        
        self.refresh_button = QPushButton("Обновить (F5)")
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_data(self):
        """Load cost items into table"""
        cost_items = self.cost_item_repo.find_all()
        self.populate_table(cost_items)
    
    def populate_table(self, cost_items):
        """Populate table with cost items"""
        self.table_view.setRowCount(len(cost_items))
        
        for row, cost_item in enumerate(cost_items):
            # ID
            self.table_view.setItem(row, 0, QTableWidgetItem(str(cost_item['id'])))
            
            # Code
            self.table_view.setItem(row, 1, QTableWidgetItem(cost_item['code'] or ""))
            
            # Description with indentation for hierarchy
            description = cost_item['description'] or ""
            if cost_item['parent_id']:
                # Add indentation for child items
                description = "  " + description
            self.table_view.setItem(row, 2, QTableWidgetItem(description))
            
            # Is Folder
            is_folder_text = "Да" if cost_item['is_folder'] else "Нет"
            self.table_view.setItem(row, 3, QTableWidgetItem(is_folder_text))
            
            # Price
            price_text = f"{cost_item['price']:.2f}" if cost_item['price'] else ""
            self.table_view.setItem(row, 4, QTableWidgetItem(price_text))
            
            # Unit
            unit_text = cost_item['unit_name'] or cost_item['unit'] or ""
            self.table_view.setItem(row, 5, QTableWidgetItem(unit_text))
            
            # Materials count
            materials_count = len(self.cost_item_repo.find_materials(cost_item['id']))
            materials_text = f"{materials_count} шт." if materials_count > 0 else ""
            self.table_view.setItem(row, 6, QTableWidgetItem(materials_text))
    
    def get_selected_id(self):
        """Get ID of selected cost item"""
        row = self.table_view.currentRow()
        if row >= 0:
            return int(self.table_view.item(row, 0).text())
        return None
    
    def on_insert_pressed(self):
        """Handle insert button"""
        form = CostItemForm(self)
        if form.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def on_create_group(self):
        """Handle create group button"""
        form = CostItemForm(self)
        form.is_folder_check.setChecked(True)
        form.on_folder_changed()
        if form.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def on_enter_pressed(self):
        """Handle edit button"""
        cost_item_id = self.get_selected_id()
        if cost_item_id:
            form = CostItemForm(self, cost_item_id)
            if form.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def on_delete_pressed(self):
        """Handle delete button"""
        cost_item_id = self.get_selected_id()
        if cost_item_id:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Вы уверены, что хотите удалить этот элемент затрат?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.cost_item_repo.delete(cost_item_id):
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить элемент затрат")
    
    def on_materials(self):
        """Handle materials button"""
        cost_item_id = self.get_selected_id()
        if cost_item_id:
            cost_item = self.cost_item_repo.find_by_id(cost_item_id)
            if cost_item and not cost_item.is_folder:
                form = CostItemMaterialForm(self, cost_item_id)
                form.exec()
            else:
                QMessageBox.information(self, "Информация", "Материалы можно добавлять только к элементам затрат, не к группам")
    
    def on_search_text_changed(self):
        """Handle search text change"""
        search_text = self.search_edit.text().strip().lower()
        
        if not search_text:
            self.load_data()
            return
        
        # Filter cost items
        cost_items = self.cost_item_repo.find_all()
        filtered_items = []
        
        for item in cost_items:
            if (item['code'] and search_text in item['code'].lower()) or \
               (item['description'] and search_text in item['description'].lower()):
                filtered_items.append(item)
        
        self.populate_table(filtered_items)
    
    def show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu(self)
        
        new_action = menu.addAction("Создать")
        new_action.triggered.connect(self.on_insert_pressed)
        
        edit_action = menu.addAction("Изменить")
        edit_action.triggered.connect(self.on_enter_pressed)
        
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self.on_delete_pressed)
        
        menu.addSeparator()
        
        materials_action = menu.addAction("Материалы")
        materials_action.triggered.connect(self.on_materials)
        
        menu.exec(self.table_view.mapToGlobal(position))
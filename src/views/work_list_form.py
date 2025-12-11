"""Work list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu, QStyle)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QEvent
from .base_list_form import BaseListForm
from .work_form import WorkForm
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository
from ..data.repositories.reference_repository import ReferenceRepository
from ..data.models.sqlalchemy_models import Work


class WorkListForm(BaseListForm):
    def __init__(self, current_id=None):
        self.db_manager = DatabaseManager()
        self.work_repo = WorkRepository(self.db_manager)
        self.ref_repo = ReferenceRepository()
        self.show_hierarchy = True  # Default to hierarchical view
        self.current_parent_id = None  # Current parent for hierarchical navigation
        self.current_id = current_id  # ID to select/highlight
        super().__init__()
        self.setWindowTitle("Справочник: Работы")
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search bar
        self.search_layout = QHBoxLayout()
        
        # Add Up button for hierarchy
        self.up_button = QPushButton()
        self.up_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.up_button.setToolTip("На уровень выше")
        self.up_button.clicked.connect(self.go_up)
        self.up_button.setEnabled(False)
        self.search_layout.addWidget(self.up_button)
        
        self.search_layout.addWidget(QLabel("Поиск (Ctrl+F):"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_layout.addWidget(self.search_edit)
        
        layout.addLayout(self.search_layout)
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.installEventFilter(self)
        self.table_view.setColumnCount(6)  # Reduced from 7 (removed Nomenclature column)
        self.table_view.setHorizontalHeaderLabels(["ID", "Код", "Наименование", "Ед. изм.", "Цена", "Норма трудозатрат"])
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_enter_pressed)
        
        # Context menu
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_context_menu)
        
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("Создать (Insert/F9)")
        self.new_button.clicked.connect(self.on_insert_pressed)
        button_layout.addWidget(self.new_button)
        
        self.new_group_button = QPushButton("Создать группу")
        self.new_group_button.clicked.connect(self.on_create_group)
        button_layout.addWidget(self.new_group_button)
        
        self.edit_button = QPushButton("Открыть (Enter)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Пометить на удаление (Delete)")
        self.delete_button.clicked.connect(self.on_delete_pressed)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def load_data(self, search_text=""):
        """Load data from database"""
        
        # If we have a current_id and this is the first load (or search is cleared),
        # we might need to navigate to the correct parent in hierarchy mode
        if self.current_id and not search_text and self.show_hierarchy and self.current_parent_id is None:
            work = self.work_repo.find_by_id(self.current_id)
            if work and work['parent_id']:
                self.current_parent_id = work['parent_id']
                
        if search_text:
            works = self.work_repo.search_by_name(search_text)
            self.up_button.setEnabled(False)
        else:
            if self.show_hierarchy:
                # Hierarchical navigation: show children of current_parent_id
                works = self.work_repo.find_children(self.current_parent_id)
                self.up_button.setEnabled(self.current_parent_id is not None)
            else:
                # Flat view
                works = self.work_repo.find_all()
                self.up_button.setEnabled(False)
        
        self.table_view.setRowCount(len(works))
        
        row_to_select = None
        for row_idx, work in enumerate(works):
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(work['id'])))
            
            # Icon for groups
            name_text = work['name']
            if work.get('is_group', False):
                 name_text = "📁 " + name_text
            
            self.table_view.setItem(row_idx, 1, QTableWidgetItem(work['code'] or ""))
            
            name_item = QTableWidgetItem(name_text)
            if work['marked_for_deletion']:
                name_item.setForeground(Qt.GlobalColor.red)
            
            # Store full object for easier access
            name_item.setData(Qt.ItemDataRole.UserRole, work)
            self.table_view.setItem(row_idx, 2, name_item)
            
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(work['unit'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(f"{work['price']:.2f}" if work['price'] is not None else ""))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(f"{work['labor_rate']:.2f}" if work['labor_rate'] is not None else ""))
            # Nomenclature column removed - feature was deprecated
            
            # Check if this is the row to select
            if self.current_id and work['id'] == self.current_id:
                row_to_select = row_idx
        
        # Hide ID column
        self.table_view.setColumnHidden(0, True)
        
        # Select row if found
        if row_to_select is not None:
            self.table_view.selectRow(row_to_select)
            self.table_view.scrollToItem(self.table_view.item(row_to_select, 2))

    def on_enter_pressed(self, index=None):
        """Handle enter press or double click"""
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
            
        work_id = int(self.table_view.item(selected_row, 0).text())
        
        # Get work data to check if it's a group
        name_item = self.table_view.item(selected_row, 2)
        work = name_item.data(Qt.ItemDataRole.UserRole)
        
        # Check if this is a group and we should drill down
        if (self.show_hierarchy and 
            not self.search_edit.text() and 
            work and 
            work.get('is_group', False)):
            # Drill down into group
            self.current_parent_id = work_id
            self.load_data()
        else:
            # Open work form for editing
            form = WorkForm(work_id)
            form.show()

    def on_edit_work(self):
        """Handle edit action - explicitly open work form (ignoring group navigation)"""
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
            
        work_id = int(self.table_view.item(selected_row, 0).text())
        form = WorkForm(work_id)
        form.show()

    def go_up(self):
        """Go to parent level (Ctrl+Up)"""
        if not self.show_hierarchy:
            return
            
        if not self.current_parent_id:
            return
            
        # Get current parent to find its parent
        current_parent = self.work_repo.find_by_id(self.current_parent_id)
        if current_parent:
            self.current_parent_id = current_parent['parent_id']
        else:
            self.current_parent_id = None
            
        self.load_data()

    def go_down(self):
        """Go down into selected group (Ctrl+Down)"""
        if not self.show_hierarchy:
            return
            
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
            
        # Get work data to check if it's a group
        name_item = self.table_view.item(selected_row, 2)
        if not name_item:
            return
            
        work = name_item.data(Qt.ItemDataRole.UserRole)
        
        # Check if this is a group that we can drill down into
        if work and work.get('is_group', False):
            work_id = int(self.table_view.item(selected_row, 0).text())
            
            # Check if this group has children
            children = self.work_repo.find_children(work_id)
            if children:
                # Drill down into group
                self.current_parent_id = work_id
                self.load_data()
            else:
                # No children, just open the work form
                self.on_enter_pressed()
        else:
            # Not a group, open work form
            self.on_enter_pressed()

    def on_toggle_hierarchy(self, checked):
        """Toggle hierarchy view"""
        self.show_hierarchy = checked
        if not checked:
            self.current_parent_id = None # Reset when switching to flat
        self.load_data(self.search_edit.text())

    def on_context_menu(self, position):
        """Handle context menu"""
        menu = QMenu()
        
        edit_action = QAction("Изменить", self)
        edit_action.triggered.connect(self.on_edit_work)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        toggle_hierarchy_action = QAction("Режим вывода по группам", self)
        toggle_hierarchy_action.setCheckable(True)
        toggle_hierarchy_action.setChecked(self.show_hierarchy)
        toggle_hierarchy_action.triggered.connect(self.on_toggle_hierarchy)
        menu.addAction(toggle_hierarchy_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def on_toggle_hierarchy(self, checked):
        """Toggle hierarchy view"""
        self.show_hierarchy = checked
        self.load_data(self.search_edit.text())
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_insert_pressed(self):
        """Handle insert key - create new work"""
        form = WorkForm(0)
        form.show()
    

    
    def on_delete_pressed(self):
        """Handle delete key - mark for deletion"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                work_id = int(id_item.text())
                name_item = self.table_view.item(current_row, 2)
                
                # Check if can delete
                can_delete, usages = self.ref_repo.can_delete_work(work_id)
                
                if not can_delete:
                    usage_text = "\n".join([f"- {doc_type}: {doc_info}" for doc_type, doc_info in usages])
                    QMessageBox.warning(
                        self, "Невозможно удалить",
                        f"Работа '{name_item.text()}' используется в следующих документах:\n\n{usage_text}\n\nУдаление невозможно."
                    )
                    return
                
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    f"Пометить на удаление работу '{name_item.text()}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.work_repo.delete(work_id):
                        self.load_data()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Не удалось пометить работу на удаление")
    
    def on_create_group(self):
        """Create new group"""
        form = WorkForm(0, is_group=True)
        form.show()
    
    def on_search_activated(self):
        """Handle search activation"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_F9 and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            # F9 without modifiers = copy work
            self.on_copy_work()
        else:
            # Pass all other keys to base class (including Ctrl+Down, Enter, etc.)
            super().keyPressEvent(event)

    def eventFilter(self, source, event):
        """Handle events from child widgets"""
        if source == self.table_view and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Left:
                if self.show_hierarchy and self.current_parent_id:
                    self.go_up()
                    return True
            elif event.key() == Qt.Key.Key_Right:
                if self.show_hierarchy:
                    selected_row = self.table_view.currentRow()
                    if selected_row >= 0:
                        name_item = self.table_view.item(selected_row, 2)
                        work = name_item.data(Qt.ItemDataRole.UserRole)
                        if work and work.get('is_group', False):
                            self.go_down()
                            return True
        return super().eventFilter(source, event)

    
    def on_copy_work(self):
        """Copy selected work with composition (F9)"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите работу для копирования")
            return
            
        # Get selected work data
        id_item = self.table_view.item(current_row, 0)
        name_item = self.table_view.item(current_row, 2)
        
        if not id_item or not name_item:
            return
            
        source_work_id = int(id_item.text())
        work_data = name_item.data(Qt.ItemDataRole.UserRole)
        
        if not work_data:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить данные работы")
            return
        
        # Confirm copy
        reply = QMessageBox.question(
            self, "Копирование работы",
            f"Создать копию работы '{work_data['name']}'?\n\nБудут скопированы:\n- Основные данные\n- Статьи затрат\n- Материалы",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # Copy work with composition
            new_work_id = self.copy_work_with_composition(source_work_id, work_data)
            
            if new_work_id:
                # Refresh list
                self.load_data(self.search_edit.text())
                
                # Open copied work for editing
                form = WorkForm(new_work_id)
                form.show()
                
                QMessageBox.information(self, "Успех", f"Работа скопирована успешно (ID: {new_work_id})")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось скопировать работу")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при копировании: {str(e)}")
    
    def copy_work_with_composition(self, source_work_id: int, source_work_data: dict) -> int:
        """Copy work with all composition data"""
        from ..data.repositories.cost_item_material_repository import CostItemMaterialRepository
        
        cim_repo = CostItemMaterialRepository()
        
        # Create new work with modified name
        new_work = Work()
        new_work.name = f"Копия - {source_work_data['name']}"
        new_work.code = None  # Clear code to avoid duplicates
        new_work.unit = source_work_data.get('unit')
        new_work.unit_id = source_work_data.get('unit_id')
        new_work.price = source_work_data.get('price', 0.0)
        new_work.labor_rate = source_work_data.get('labor_rate', 0.0)
        new_work.parent_id = source_work_data.get('parent_id')
        new_work.is_group = source_work_data.get('is_group', False)
        
        # Save new work
        new_work_id = self.work_repo.save(new_work)
        if not new_work_id:
            raise Exception("Failed to create new work")
        
        # Copy cost items
        cost_items = cim_repo.get_cost_items_for_work(source_work_id)
        for cost_item, quantity in cost_items:
            cim_repo.create_or_update_association(new_work_id, cost_item.id, None, quantity)
        
        # Copy materials
        materials = cim_repo.get_materials_for_work(source_work_id)
        for material, quantity, cost_item in materials:
            cim_repo.create_or_update_association(new_work_id, cost_item.id, material.id, quantity)
        
        return new_work_id

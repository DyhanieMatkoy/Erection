"""Work list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from .base_list_form import BaseListForm
from .work_form import WorkForm
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_repository import WorkRepository
from ..data.repositories.reference_repository import ReferenceRepository


class WorkListForm(BaseListForm):
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.work_repo = WorkRepository(self.db_manager)
        self.ref_repo = ReferenceRepository()
        self.show_hierarchy = True  # Default to hierarchical view
        self.current_parent_id = None  # Current parent for hierarchical navigation
        super().__init__()
        self.setWindowTitle("Справочник: Работы")
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search bar
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(QLabel("Поиск (Ctrl+F):"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_layout.addWidget(self.search_edit)
        
        # Add Up button for hierarchy
        self.up_button = QPushButton("Вверх")
        self.up_button.clicked.connect(self.go_up)
        self.up_button.setEnabled(False)
        self.search_layout.addWidget(self.up_button)
        
        layout.addLayout(self.search_layout)
        
        # Table
        self.table_view = QTableWidget()
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
        if search_text:
            works = self.work_repo.search_by_name(search_text)
            self.up_button.setEnabled(False)
        else:
            if self.show_hierarchy:
                # Hierarchical navigation: show children of current_parent_id
                if self.current_parent_id:
                     works = self.work_repo.find_children(self.current_parent_id)
                     self.up_button.setEnabled(True)
                else:
                     # Root level
                     works = self.work_repo.find_children(None) # Assuming find_children(None) returns roots or modify repo
                     # If find_children(None) is not supported, we filter find_all manually or add find_roots
                     # Let's check repository. find_children does filter(Work.parent_id == parent_id).
                     # In SQLAlchemy None translates to IS NULL usually, let's verify or fallback.
                     self.up_button.setEnabled(False)
            else:
                # Flat view
                works = self.work_repo.find_all()
                self.up_button.setEnabled(False)
        
        self.table_view.setRowCount(len(works))
        
        for row_idx, work in enumerate(works):
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(work['id'])))
            
            # Icon for groups
            name_text = work['name']
            if work['is_group']:
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
        
        # Hide ID column
        self.table_view.setColumnHidden(0, True)

    def on_enter_pressed(self, index=None):
        """Handle enter press or double click"""
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
            
        work_id = int(self.table_view.item(selected_row, 0).text())
        
        # Get work data to check if it's a group
        # We stored it in name item
        name_item = self.table_view.item(selected_row, 2)
        work = name_item.data(Qt.ItemDataRole.UserRole)
        
        if self.show_hierarchy and not self.search_edit.text() and work['is_group']:
            # Drill down
            self.current_parent_id = work_id
            self.load_data()
        else:
            # Edit
            self.edit_work(work_id)

    def go_up(self):
        """Go to parent level"""
        if not self.current_parent_id:
            return
            
        # Get current parent to find its parent
        current_parent = self.work_repo.find_by_id(self.current_parent_id)
        if current_parent:
            self.current_parent_id = current_parent['parent_id']
        else:
            self.current_parent_id = None
            
        self.load_data()

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
        edit_action.triggered.connect(self.on_enter_pressed)
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
    
    def on_enter_pressed(self):
        """Handle enter key - open selected work"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                work_id = int(id_item.text())
                form = WorkForm(work_id)
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

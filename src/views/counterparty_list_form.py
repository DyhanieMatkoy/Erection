"""Counterparty list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from .base_list_form import BaseListForm
from .counterparty_form import CounterpartyForm
from ..data.database_manager import DatabaseManager
from ..data.repositories.reference_repository import ReferenceRepository


class CounterpartyListForm(BaseListForm):
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.ref_repo = ReferenceRepository()
        self.show_hierarchy = True
        self.current_parent_id = None
        super().__init__()
        self.setWindowTitle("Справочник: Контрагенты")
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search bar and navigation
        search_layout = QHBoxLayout()
        
        self.up_button = QPushButton("⬆")
        self.up_button.setFixedWidth(30)
        self.up_button.clicked.connect(self.go_up)
        self.up_button.setEnabled(False)
        search_layout.addWidget(self.up_button)
        
        self.parent_label = QLabel("Корень")
        search_layout.addWidget(self.parent_label)
        
        search_layout.addStretch()
        
        search_layout.addWidget(QLabel("Поиск (Ctrl+F):"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(5)
        self.table_view.setHorizontalHeaderLabels(["ID", "Наименование", "ИНН", "Контактное лицо", "Телефон"])
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_enter_pressed)
        
        # Context menu
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
        cursor = self.db.cursor()
        
        # Update navigation UI
        self.up_button.setEnabled(self.current_parent_id is not None)
        if self.current_parent_id:
            cursor.execute("SELECT name FROM counterparties WHERE id = ?", (self.current_parent_id,))
            row = cursor.fetchone()
            if row:
                self.parent_label.setText(f"Группа: {row['name']}")
        else:
            self.parent_label.setText("Корень")
        
        params = []
        if search_text:
            query = """
                SELECT id, name, inn, contact_person, phone, marked_for_deletion, is_group
                FROM counterparties
                WHERE name LIKE ? OR inn LIKE ? OR contact_person LIKE ?
                ORDER BY is_group DESC, name
            """
            params = [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]
        elif self.show_hierarchy:
            query = """
                SELECT id, name, inn, contact_person, phone, marked_for_deletion, is_group
                FROM counterparties
                WHERE (parent_id IS NULL OR parent_id = 0)
            """
            if self.current_parent_id:
                query = query.replace("(parent_id IS NULL OR parent_id = 0)", "parent_id = ?")
                params = [self.current_parent_id]
            
            query += " ORDER BY is_group DESC, name"
        else:
            query = """
                SELECT id, name, inn, contact_person, phone, marked_for_deletion, is_group
                FROM counterparties
                ORDER BY is_group DESC, name
            """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        self.table_view.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            
            name_text = row['name']
            if row['is_group']:
                name_text = "📁 " + name_text
            
            name_item = QTableWidgetItem(name_text)
            if row['marked_for_deletion']:
                name_item.setForeground(Qt.GlobalColor.red)
            self.table_view.setItem(row_idx, 1, name_item)
            
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(row['inn'] or ""))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(row['contact_person'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(row['phone'] or ""))
            
            # Store is_group in hidden data
            name_item.setData(Qt.ItemDataRole.UserRole, row['is_group'])
        
        # Hide ID column
        self.table_view.setColumnHidden(0, True)
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_insert_pressed(self):
        """Handle insert key - create new counterparty"""
        form = CounterpartyForm(0)
        form.show()
    
    def on_enter_pressed(self):
        """Handle enter press or double click"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            name_item = self.table_view.item(current_row, 1)
            is_group = name_item.data(Qt.ItemDataRole.UserRole)
            
            if is_group and self.show_hierarchy:
                # Drill down
                id_item = self.table_view.item(current_row, 0)
                if id_item:
                    self.current_parent_id = int(id_item.text())
                    self.load_data()
            else:
                # Open for editing
                id_item = self.table_view.item(current_row, 0)
                if id_item:
                    try:
                        cp_id = int(id_item.text())
                        self.form = CounterpartyForm(counterparty_id=cp_id)
                        self.form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                        self.form.destroyed.connect(lambda: self.load_data())
                        self.form.show()
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")

    def go_up(self):
        """Go up one level"""
        if self.current_parent_id:
            cursor = self.db.cursor()
            cursor.execute("SELECT parent_id FROM counterparties WHERE id = ?", (self.current_parent_id,))
            row = cursor.fetchone()
            if row:
                self.current_parent_id = row['parent_id']
                if self.current_parent_id == 0:
                    self.current_parent_id = None
            else:
                self.current_parent_id = None
            self.load_data()

    def show_context_menu(self, position):
        menu = QMenu()
        edit_action = QAction("Изменить", self)
        edit_action.triggered.connect(self.on_enter_pressed)
        menu.addAction(edit_action)
        
        hierarchy_action = QAction("Режим вывода по группам", self)
        hierarchy_action.setCheckable(True)
        hierarchy_action.setChecked(self.show_hierarchy)
        hierarchy_action.triggered.connect(self.toggle_hierarchy_mode)
        menu.addAction(hierarchy_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def toggle_hierarchy_mode(self):
        self.show_hierarchy = not self.show_hierarchy
        self.current_parent_id = None # Reset when toggling
        self.load_data()

    def on_delete_pressed(self):
        """Handle delete key - mark for deletion"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                counterparty_id = int(id_item.text())
                name_item = self.table_view.item(current_row, 1)
                
                # Check if can delete
                can_delete, usages = self.ref_repo.can_delete_counterparty(counterparty_id)
                
                if not can_delete:
                    usage_text = "\n".join([f"- {doc_type}: {doc_info}" for doc_type, doc_info in usages])
                    QMessageBox.warning(
                        self, "Невозможно удалить",
                        f"Контрагент '{name_item.text()}' используется в следующих документах:\n\n{usage_text}\n\nУдаление невозможно."
                    )
                    return
                
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    f"Пометить на удаление контрагента '{name_item.text()}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    cursor = self.db.cursor()
                    cursor.execute("""
                        UPDATE counterparties 
                        SET marked_for_deletion = 1 
                        WHERE id = ?
                    """, (counterparty_id,))
                    self.db.commit()
                    self.load_data()
    
    def on_create_group(self):
        """Create new group"""
        form = CounterpartyForm(0, is_group=True)
        form.show()
    
    def on_search_activated(self):
        """Handle search activation"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()

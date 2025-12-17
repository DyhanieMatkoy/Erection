"""Reference picker dialog"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, QLabel, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from ..data.database_manager import DatabaseManager


class ReferencePickerDialog(QDialog):
    def __init__(self, table_name, title="Выбор из справочника", parent=None, owner_id=None, current_id=None):
        super().__init__(parent)
        self.table_name = table_name
        self.title = title
        self.owner_id = owner_id
        self.current_id = current_id  # Current value to position cursor on
        self.current_parent_id = None  # Current parent for hierarchical navigation
        self.db = DatabaseManager().get_connection()
        self._selected_id = 0
        self._selected_value = ""
        
        # Determine display column based on table
        self.display_column = self._get_display_column()
        self.is_hierarchical = self._check_is_hierarchical()
        
        self.setup_ui()
        self.load_data()
    
    def _check_is_hierarchical(self):
        """Check if table supports hierarchy"""
        return self.table_name in ["works", "objects", "organizations", "counterparties", "persons", "cost_items"]
    
    def _get_display_column(self):
        """Get display column name based on table"""
        if self.table_name in ["counterparties", "organizations", "objects", "works"]:
            return "name"
        elif self.table_name == "persons":
            return "full_name"
        else:
            return "name"
    
    def on_context_menu(self, position):
        """Handle context menu"""
        menu = QMenu()
        
        add_action = QAction("Добавить", self)
        add_action.triggered.connect(self.on_add)
        menu.addAction(add_action)
        
        menu.addSeparator()
        
        edit_action = QAction("Изменить", self)
        edit_action.triggered.connect(self.on_edit)
        menu.addAction(edit_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle(self.title)
        self.setModal(False)  # Make non-modal
        self.resize(800, 500)  # Increase size for additional columns
        
        layout = QVBoxLayout()
        
        # Hierarchical navigation bar
        nav_layout = QHBoxLayout()
        self.up_button = QPushButton("↑ Вверх")
        self.up_button.clicked.connect(self.on_navigate_up)
        self.up_button.setEnabled(False)
        nav_layout.addWidget(self.up_button)
        
        self.parent_label = QLabel("Корень")
        nav_layout.addWidget(self.parent_label)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.table_view = QTableWidget()
        
        # Set columns based on table type
        if self.table_name == "works":
            self.table_view.setColumnCount(6)
            self.table_view.setHorizontalHeaderLabels(["ID", "Наименование", "Код", "Ед.изм.", "Цена", "parent_id"])
            # Set column widths for works
            self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table_view.setColumnWidth(2, 100)  # Code
            self.table_view.setColumnWidth(3, 80)   # Unit
            self.table_view.setColumnWidth(4, 100)  # Price
        else:
            self.table_view.setColumnCount(3)
            self.table_view.setHorizontalHeaderLabels(["ID", "Наименование", "parent_id"])
            self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)
        
        # Context menu
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_context_menu)
        
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.drill_down_button = QPushButton("Открыть группу (Enter)")
        self.drill_down_button.clicked.connect(self.on_drill_down)
        button_layout.addWidget(self.drill_down_button)
        
        self.add_button = QPushButton("Добавить (Ins)")
        self.add_button.clicked.connect(self.on_add)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Изменить (F4)")
        self.edit_button.clicked.connect(self.on_edit)
        button_layout.addWidget(self.edit_button)
        
        button_layout.addStretch()
        
        self.select_button = QPushButton("Выбрать (Ctrl+Enter)")
        self.select_button.clicked.connect(self.on_select)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Отмена (Esc)")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self, search_text=""):
        """Load data from database"""
        cursor = self.db.cursor()
        
        # Build WHERE clause
        where_clauses = ["marked_for_deletion = 0"]
        params = []
        
        if self.owner_id and self.table_name == "objects":
            where_clauses.append("owner_id = ?")
            params.append(self.owner_id)
        
        # Determine if we need to navigate to the current item's parent first
        # Only do this on initial load (when search is empty and we have a current_id)
        if self.current_id and not search_text and self.is_hierarchical and self.current_parent_id is None:
            # Find parent of current item
            cursor.execute(f"SELECT parent_id FROM {self.table_name} WHERE id = ?", (self.current_id,))
            row = cursor.fetchone()
            if row:
                self.current_parent_id = row['parent_id'] if row['parent_id'] else None
        
        if search_text:
            # When searching, show all levels
            if self.table_name == "works":
                where_clauses.append(f"(name LIKE ? OR code LIKE ?)")
                params.append(f"%{search_text}%")
                params.append(f"%{search_text}%")
            else:
                where_clauses.append(f"{self.display_column} LIKE ?")
                params.append(f"%{search_text}%")
        elif self.is_hierarchical:
            # When not searching and hierarchical, show only current level
            if self.current_parent_id is None:
                where_clauses.append("(parent_id IS NULL OR parent_id = 0)")
            else:
                where_clauses.append("parent_id = ?")
                params.append(self.current_parent_id)
        
        where_clause = " AND ".join(where_clauses)
        
        parent_col = "parent_id" if self.is_hierarchical else "NULL as parent_id"
        
        # Build SELECT clause based on table type
        if self.table_name == "works":
            select_clause = f"""
                SELECT w.id, w.{self.display_column}, w.code, COALESCE(u.name, w.unit) as unit, w.price, {parent_col}
                FROM {self.table_name} w
                LEFT JOIN units u ON w.unit_id = u.id
            """
        else:
            select_clause = f"""
                SELECT id, {self.display_column}, {parent_col}
                FROM {self.table_name}
            """
        
        cursor.execute(f"""
            {select_clause}
            WHERE {where_clause}
            ORDER BY {self.display_column}
        """, params)
        
        rows = cursor.fetchall()
        self.table_view.setRowCount(len(rows))
        
        row_to_select = None
        for row_idx, row in enumerate(rows):
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            
            has_children = False
            if self.is_hierarchical:
                # Check if this row has children (is a group)
                cursor.execute(f"""
                    SELECT COUNT(*) as cnt FROM {self.table_name}
                    WHERE parent_id = ? AND marked_for_deletion = 0
                """, (row['id'],))
                has_children = cursor.fetchone()['cnt'] > 0
            
            name_text = row[self.display_column]
            if has_children:
                name_text = "📁 " + name_text
            
            self.table_view.setItem(row_idx, 1, QTableWidgetItem(name_text))
            
            if self.table_name == "works":
                # Fill additional columns for works
                self.table_view.setItem(row_idx, 2, QTableWidgetItem(row.get('code', '') or ''))
                self.table_view.setItem(row_idx, 3, QTableWidgetItem(row.get('unit', '') or ''))
                self.table_view.setItem(row_idx, 4, QTableWidgetItem(str(row.get('price', 0) or 0)))
                self.table_view.setItem(row_idx, 5, QTableWidgetItem(str(row['parent_id']) if row['parent_id'] else ""))
            else:
                self.table_view.setItem(row_idx, 2, QTableWidgetItem(str(row['parent_id']) if row['parent_id'] else ""))
            
            # Remember row to select if it matches current_id
            if self.current_id and row['id'] == self.current_id:
                row_to_select = row_idx
        
        # Hide ID and parent_id columns
        self.table_view.setColumnHidden(0, True)
        if self.table_name == "works":
            self.table_view.setColumnHidden(5, True)  # Hide parent_id for works
        else:
            self.table_view.setColumnHidden(2, True)  # Hide parent_id for other tables
        self.table_view.setColumnHidden(2, True)
        
        # Position cursor on current value
        if row_to_select is not None:
            self.table_view.selectRow(row_to_select)
            self.table_view.scrollToItem(self.table_view.item(row_to_select, 1))
        elif self.table_view.rowCount() > 0:
            self.table_view.selectRow(0)
        
        # Update navigation state
        self.update_navigation_state()
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_navigate_up(self):
        """Navigate to parent level"""
        if self.current_parent_id is not None:
            cursor = self.db.cursor()
            cursor.execute(f"""
                SELECT parent_id FROM {self.table_name}
                WHERE id = ?
            """, (self.current_parent_id,))
            row = cursor.fetchone()
            
            if row:
                self.current_parent_id = row['parent_id'] if row['parent_id'] else None
            else:
                self.current_parent_id = None
            
            self.load_data()
    
    def on_drill_down(self):
        """Drill down into selected group"""
        if not self.is_hierarchical:
            return

        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                # Check if this item has children
                cursor = self.db.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) as cnt FROM {self.table_name}
                    WHERE parent_id = ? AND marked_for_deletion = 0
                """, (selected_id,))
                has_children = cursor.fetchone()['cnt'] > 0
                
                if has_children:
                    self.current_parent_id = selected_id
                    self.load_data()
    
    def on_row_double_clicked(self, index):
        """Handle row double click - drill down if group, select if item"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                has_children = False
                if self.is_hierarchical:
                    # Check if this item has children
                    cursor = self.db.cursor()
                    cursor.execute(f"""
                        SELECT COUNT(*) as cnt FROM {self.table_name}
                        WHERE parent_id = ? AND marked_for_deletion = 0
                    """, (selected_id,))
                    has_children = cursor.fetchone()['cnt'] > 0
                
                if has_children:
                    # Drill down
                    self.current_parent_id = selected_id
                    self.load_data()
                else:
                    # Select
                    self.on_select()
    
    def update_navigation_state(self):
        """Update navigation buttons and label"""
        # Enable/disable up button
        self.up_button.setEnabled(self.current_parent_id is not None)
        self.up_button.setVisible(self.is_hierarchical)
        self.drill_down_button.setVisible(self.is_hierarchical)
        self.parent_label.setVisible(self.is_hierarchical)
        
        # Update parent label
        if self.current_parent_id is None:
            self.parent_label.setText("Корень")
        else:
            cursor = self.db.cursor()
            cursor.execute(f"""
                SELECT {self.display_column} FROM {self.table_name}
                WHERE id = ?
            """, (self.current_parent_id,))
            row = cursor.fetchone()
            if row:
                self.parent_label.setText(f"Группа: {row[self.display_column]}")
    
    def on_select(self):
        """Handle select button"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            value_item = self.table_view.item(current_row, 1)
            if id_item and value_item:
                self._selected_id = int(id_item.text())
                # Remove folder icon from value
                self._selected_value = value_item.text().replace("📁 ", "")
                self.accept()
    
    def selected_id(self):
        """Get selected ID"""
        return self._selected_id
    
    def selected_value(self):
        """Get selected value"""
        return self._selected_value
    
    def get_selected(self):
        """Get selected ID and value as tuple"""
        return (self._selected_id, self._selected_value)
    
    def on_edit(self):
        """Handle edit button - open selected item for editing"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                
                # Open appropriate form based on table
                form = None
                if self.table_name == "works":
                    from .work_form import WorkForm
                    form = WorkForm(selected_id)
                elif self.table_name == "counterparties":
                    from .counterparty_form import CounterpartyForm
                    form = CounterpartyForm(selected_id)
                elif self.table_name == "objects":
                    from .object_form import ObjectForm
                    form = ObjectForm(selected_id)
                elif self.table_name == "organizations":
                    from .organization_form import OrganizationForm
                    form = OrganizationForm(selected_id)
                elif self.table_name == "persons":
                    from .person_form import PersonForm
                    form = PersonForm(selected_id)
                
                if form:
                    # Store reference to prevent garbage collection
                    self._edit_form = form
                    
                    # Connect to form closed signal to refresh data
                    if hasattr(form, 'finished'):
                        # If it's a dialog
                        form.finished.connect(self._on_edit_form_closed)
                    elif hasattr(form, 'destroyed'):
                        # If it's a widget
                        form.destroyed.connect(self._on_edit_form_closed)
                    
                    form.show()
                    
                    # Bring form to front
                    form.raise_()
                    form.activateWindow()
    
    def _on_edit_form_closed(self):
        """Handle edit form closed - refresh data"""
        self.load_data()
        self._edit_form = None
    
    def on_add(self):
        """Handle add button - open form for creating new item"""
        # Open appropriate form based on table
        form = None
        if self.table_name == "works":
            from .work_form import WorkForm
            form = WorkForm(0)  # 0 for new item
        elif self.table_name == "counterparties":
            from .counterparty_form import CounterpartyForm
            form = CounterpartyForm(0)
        elif self.table_name == "objects":
            from .object_form import ObjectForm
            form = ObjectForm(0)
        elif self.table_name == "organizations":
            from .organization_form import OrganizationForm
            form = OrganizationForm(0)
        elif self.table_name == "persons":
            from .person_form import PersonForm
            form = PersonForm(0)
        
        if form:
            # Store reference to prevent garbage collection
            self._add_form = form
            
            # Connect to form closed signal to refresh data
            if hasattr(form, 'finished'):
                # If it's a dialog
                form.finished.connect(self._on_add_form_closed)
            elif hasattr(form, 'destroyed'):
                # If it's a widget
                form.destroyed.connect(self._on_add_form_closed)
            
            form.show()
            
            # Bring form to front
            form.raise_()
            form.activateWindow()
    
    def _on_add_form_closed(self):
        """Handle add form closed - refresh data"""
        self.load_data()
        self._add_form = None
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Enter - select
                self.on_select()
            else:
                # Enter - drill down or select
                current_row = self.table_view.currentRow()
                if current_row >= 0:
                    id_item = self.table_view.item(current_row, 0)
                    if id_item:
                        selected_id = int(id_item.text())
                        
                        # Check if this item has children
                        cursor = self.db.cursor()
                        cursor.execute(f"""
                            SELECT COUNT(*) as cnt FROM {self.table_name}
                            WHERE parent_id = ? AND marked_for_deletion = 0
                        """, (selected_id,))
                        has_children = cursor.fetchone()['cnt'] > 0
                        
                        if has_children:
                            self.on_drill_down()
                        else:
                            self.on_select()
        elif event.key() == Qt.Key.Key_F4:
            # F4 - edit
            self.on_edit()
        elif event.key() == Qt.Key.Key_Insert:
            # Insert - add new
            self.on_add()
        elif event.key() == Qt.Key.Key_Backspace:
            # Backspace - navigate up
            if self.current_parent_id is not None:
                self.on_navigate_up()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

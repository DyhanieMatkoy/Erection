"""Timesheet list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from .base_list_form import BaseListForm
from ..data.database_manager import DatabaseManager
from ..services.timesheet_posting_service import TimesheetPostingService
from ..services.auth_service import AuthService


class TimesheetListForm(BaseListForm):
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.posting_service = TimesheetPostingService()
        self.auth_service = AuthService()
        self.opened_forms = []  # Keep references to opened forms
        super().__init__()
        self.setWindowTitle("Документы: Табели")
        self.resize(1000, 600)
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
        
        # Posting status filter
        search_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все", None)
        self.status_filter.addItem("Проведенные", 1)
        self.status_filter.addItem("Не проведенные", 0)
        self.status_filter.currentIndexChanged.connect(self.on_filter_changed)
        search_layout.addWidget(self.status_filter)
        
        layout.addLayout(search_layout)
        
        # Additional filters
        filter_layout = QHBoxLayout()
        
        # Object filter
        filter_layout.addWidget(QLabel("Объект:"))
        self.object_filter = QComboBox()
        self.object_filter.addItem("Все", None)
        self.load_objects()
        self.object_filter.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.object_filter)
        
        # Foreman filter (only show for non-foremen)
        if not self.auth_service.is_foreman():
            filter_layout.addWidget(QLabel("Бригадир:"))
            self.foreman_filter = QComboBox()
            self.foreman_filter.addItem("Все", None)
            self.load_foremen()
            self.foreman_filter.currentIndexChanged.connect(self.on_filter_changed)
            filter_layout.addWidget(self.foreman_filter)
        
        # Clear filters button
        self.clear_filters_button = QPushButton("Очистить фильтры")
        self.clear_filters_button.clicked.connect(self.on_clear_filters)
        filter_layout.addWidget(self.clear_filters_button)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(7)
        self.table_view.setHorizontalHeaderLabels([
            "Проведен", "Номер", "Дата", "Объект", "Смета", "Бригадир", "ID"
        ])
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_enter_pressed)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_context_menu)
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("Создать (Insert/F9)")
        self.new_button.clicked.connect(self.on_insert_pressed)
        self.new_button.setEnabled(self.can_create_timesheet())
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Открыть (Enter)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.refresh_button = QPushButton("Обновить (F5)")
        self.refresh_button.clicked.connect(self.on_refresh_pressed)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_objects(self):
        """Load objects for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT DISTINCT o.id, o.name
            FROM objects o
            INNER JOIN timesheets t ON t.object_id = o.id
            WHERE o.marked_for_deletion = 0
            ORDER BY o.name
        """)
        for row in cursor.fetchall():
            self.object_filter.addItem(row['name'], row['id'])
    
    def load_foremen(self):
        """Load foremen for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT DISTINCT p.id, p.full_name
            FROM persons p
            INNER JOIN timesheets t ON t.foreman_id = p.id
            WHERE p.marked_for_deletion = 0
            ORDER BY p.full_name
        """)
        for row in cursor.fetchall():
            self.foreman_filter.addItem(row['full_name'], row['id'])
    
    def on_clear_filters(self):
        """Clear all filters"""
        self.search_edit.clear()
        self.status_filter.setCurrentIndex(0)
        if hasattr(self, 'object_filter'):
            self.object_filter.setCurrentIndex(0)
        if hasattr(self, 'foreman_filter'):
            self.foreman_filter.setCurrentIndex(0)
    
    def load_data(self, search_text=""):
        """Load data from database"""
        cursor = self.db.cursor()
        
        # Build WHERE clause
        where_clauses = ["(t.marked_for_deletion = 0 OR t.marked_for_deletion IS NULL)"]
        params = []
        
        # Apply permission-based filtering for foremen
        if self.auth_service.is_foreman():
            person_id = self.auth_service.current_person_id()
            if person_id:
                where_clauses.append("t.foreman_id = ?")
                params.append(person_id)
        
        if search_text:
            where_clauses.append("(t.number LIKE ? OR o.name LIKE ? OR p.full_name LIKE ?)")
            params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])
        
        # Add status filter
        status_filter = self.status_filter.currentData() if hasattr(self, 'status_filter') else None
        if status_filter is not None:
            where_clauses.append("t.is_posted = ?")
            params.append(status_filter)
        
        # Add object filter
        if hasattr(self, 'object_filter'):
            object_id = self.object_filter.currentData()
            if object_id is not None:
                where_clauses.append("t.object_id = ?")
                params.append(object_id)
        
        # Add foreman filter (only if not already filtered by permission)
        if hasattr(self, 'foreman_filter') and not self.auth_service.is_foreman():
            foreman_id = self.foreman_filter.currentData()
            if foreman_id is not None:
                where_clauses.append("t.foreman_id = ?")
                params.append(foreman_id)
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT t.id, t.number, t.date, 
                   o.name as object_name,
                   e.number as estimate_number,
                   p.full_name as foreman_name,
                   t.is_posted
            FROM timesheets t
            LEFT JOIN objects o ON t.object_id = o.id
            LEFT JOIN estimates e ON t.estimate_id = e.id
            LEFT JOIN persons p ON t.foreman_id = p.id
            WHERE {where_clause}
            ORDER BY t.date DESC, t.number DESC
        """
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        self.table_view.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            is_posted = row['is_posted'] if 'is_posted' in row.keys() else 0
            
            # Column 0: Posted status
            posted_item = QTableWidgetItem("✓" if is_posted else "")
            if is_posted:
                font = posted_item.font()
                font.setBold(True)
                posted_item.setFont(font)
            self.table_view.setItem(row_idx, 0, posted_item)
            
            # Column 1: Number
            number_item = QTableWidgetItem(row['number'] or "")
            if is_posted:
                font = number_item.font()
                font.setBold(True)
                number_item.setFont(font)
            self.table_view.setItem(row_idx, 1, number_item)
            
            # Column 2-5: Other fields
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(str(row['date']) if row['date'] else ""))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(row['object_name'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(row['estimate_number'] or ""))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(row['foreman_name'] or ""))
            
            # Column 6: ID (hidden)
            self.table_view.setItem(row_idx, 6, QTableWidgetItem(str(row['id'])))
        
        # Hide ID column
        self.table_view.setColumnHidden(6, True)
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.load_data(self.search_edit.text())
    
    def can_create_timesheet(self) -> bool:
        """Check if user can create timesheets"""
        # Similar to daily reports - foremen and above can create
        return self.auth_service.can_create_daily_report()
    
    def can_edit_timesheet(self, timesheet_id: int) -> bool:
        """Check if user can edit a specific timesheet"""
        if not self.auth_service.current_user():
            return False
        
        role = self.auth_service.current_user().role
        
        # Administrators and Managers can edit all
        if role in ["Администратор", "Руководитель"]:
            return True
        
        # Foremen can only edit their own timesheets
        if role == "Бригадир":
            person_id = self.auth_service.current_person_id()
            if person_id:
                cursor = self.db.cursor()
                cursor.execute("SELECT foreman_id FROM timesheets WHERE id = ?", (timesheet_id,))
                row = cursor.fetchone()
                if row and row['foreman_id'] == person_id:
                    return True
        
        return False
    
    def can_delete_timesheet(self, timesheet_id: int) -> bool:
        """Check if user can delete a specific timesheet"""
        return self.can_edit_timesheet(timesheet_id)
    
    def can_post_timesheet(self, timesheet_id: int) -> bool:
        """Check if user can post a specific timesheet"""
        return self.can_edit_timesheet(timesheet_id)
    
    def on_insert_pressed(self):
        """Handle insert key - create new timesheet"""
        if not self.can_create_timesheet():
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для создания табеля")
            return
        
        try:
            # Import here to avoid circular import
            from .timesheet_document_form import TimesheetDocumentForm
            form = TimesheetDocumentForm(0)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            self.opened_forms.append(form)
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")
    
    def on_enter_pressed(self):
        """Handle enter key - open selected timesheet"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 6)
            if id_item:
                try:
                    timesheet_id = int(id_item.text())
                    # Import here to avoid circular import
                    from .timesheet_document_form import TimesheetDocumentForm
                    form = TimesheetDocumentForm(timesheet_id)
                    form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                    form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
                    self.opened_forms.append(form)
                    form.show()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")
    
    def on_delete_pressed(self):
        """Handle delete key - mark timesheet for deletion"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 6)
        if not id_item:
            return
        
        timesheet_id = int(id_item.text())
        
        # Check permissions
        if not self.can_delete_timesheet(timesheet_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для удаления этого табеля")
            return
        
        number_item = self.table_view.item(current_row, 1)
        number = number_item.text() if number_item else ""
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Пометить табель '{number}' на удаление?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE timesheets SET marked_for_deletion = 1 WHERE id = ?",
                (timesheet_id,)
            )
            self.db.commit()
            
            QMessageBox.information(self, "Успех", "Табель помечен на удаление")
            self.load_data(self.search_edit.text())
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось пометить на удаление: {str(e)}")
    
    def on_search_activated(self):
        """Handle search activation"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()
    
    def on_context_menu(self, position):
        """Handle context menu"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        menu = QMenu(self)
        
        # Get posting status
        id_item = self.table_view.item(current_row, 6)
        posted_item = self.table_view.item(current_row, 0)
        is_posted = posted_item.text() == "✓" if posted_item else False
        
        if not id_item:
            return
        
        timesheet_id = int(id_item.text())
        
        # Post/Unpost actions
        if is_posted:
            if self.can_post_timesheet(timesheet_id):
                unpost_action = QAction("Отменить проведение", self)
                unpost_action.triggered.connect(self.on_unpost_selected)
                menu.addAction(unpost_action)
        else:
            if self.can_post_timesheet(timesheet_id):
                post_action = QAction("Провести", self)
                post_action.triggered.connect(self.on_post_selected)
                menu.addAction(post_action)
        
        if menu.actions():
            menu.exec(self.table_view.viewport().mapToGlobal(position))
    
    def on_post_selected(self):
        """Post selected timesheet"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 6)
        if not id_item:
            return
        
        timesheet_id = int(id_item.text())
        
        # Check permissions
        if not self.can_post_timesheet(timesheet_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для проведения этого табеля")
            return
        
        try:
            success, error = self.posting_service.post_timesheet(timesheet_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Табель проведен")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось провести табель")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при проведении: {str(e)}")
    
    def on_unpost_selected(self):
        """Unpost selected timesheet"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 6)
        if not id_item:
            return
        
        timesheet_id = int(id_item.text())
        
        # Check permissions
        if not self.can_post_timesheet(timesheet_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для отмены проведения этого табеля")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Отменить проведение табеля?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            success, error = self.posting_service.unpost_timesheet(timesheet_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Проведение отменено")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось отменить проведение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене проведения: {str(e)}")

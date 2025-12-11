"""Daily report list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from .base_list_form import BaseListForm
from .daily_report_document_form import DailyReportDocumentForm
from ..data.database_manager import DatabaseManager
from ..services.document_posting_service import DocumentPostingService
from ..services.auth_service import AuthService


class DailyReportListForm(BaseListForm):
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.posting_service = DocumentPostingService()
        self.auth_service = AuthService()
        self.opened_forms = []  # Keep references to opened forms
        super().__init__()
        self.setWindowTitle("Документы: Ежедневные отчеты")
        self.resize(900, 600)
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
        from PyQt6.QtWidgets import QComboBox
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
        
        # Estimate filter
        filter_layout.addWidget(QLabel("Смета:"))
        self.estimate_filter = QComboBox()
        self.estimate_filter.addItem("Все", None)
        self.load_estimates()
        self.estimate_filter.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.estimate_filter)
        
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
        self.table_view.setColumnCount(6)
        self.table_view.setHorizontalHeaderLabels([
            "Проведен", "Дата", "Смета", "Бригадир", "Строк", "ID"
        ])
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
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
        self.new_button.setEnabled(self.auth_service.can_create_daily_report())
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Открыть (Enter)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.print_settings_button = QPushButton("Настройки печати")
        self.print_settings_button.clicked.connect(self.on_print_settings)
        button_layout.addWidget(self.print_settings_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_estimates(self):
        """Load estimates for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT DISTINCT e.id, e.number, e.date
            FROM estimates e
            INNER JOIN daily_reports dr ON dr.estimate_id = e.id
            WHERE e.marked_for_deletion = 0
            ORDER BY e.date DESC, e.number
        """)
        for row in cursor.fetchall():
            display = f"{row['number']} от {row['date']}"
            self.estimate_filter.addItem(display, row['id'])
    
    def load_foremen(self):
        """Load foremen for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT DISTINCT p.id, p.full_name
            FROM persons p
            INNER JOIN daily_reports dr ON dr.foreman_id = p.id
            WHERE p.marked_for_deletion = 0
            ORDER BY p.full_name
        """)
        for row in cursor.fetchall():
            self.foreman_filter.addItem(row['full_name'], row['id'])
    
    def on_clear_filters(self):
        """Clear all filters"""
        self.search_edit.clear()
        self.status_filter.setCurrentIndex(0)
        if hasattr(self, 'estimate_filter'):
            self.estimate_filter.setCurrentIndex(0)
        if hasattr(self, 'foreman_filter'):
            self.foreman_filter.setCurrentIndex(0)
    
    def load_data(self, search_text=""):
        """Load data from database"""
        cursor = self.db.cursor()
        
        # Build WHERE clause
        where_clauses = ["(dr.marked_for_deletion = 0 OR dr.marked_for_deletion IS NULL)"]
        params = []
        
        # Apply permission-based filtering for foremen
        if self.auth_service.is_foreman():
            person_id = self.auth_service.current_person_id()
            if person_id:
                where_clauses.append("dr.foreman_id = ?")
                params.append(person_id)
        
        if search_text:
            where_clauses.append("(e.number LIKE ? OR p.full_name LIKE ?)")
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        
        # Add status filter
        status_filter = self.status_filter.currentData() if hasattr(self, 'status_filter') else None
        if status_filter is not None:
            where_clauses.append("dr.is_posted = ?")
            params.append(status_filter)
        
        # Add estimate filter
        if hasattr(self, 'estimate_filter'):
            estimate_id = self.estimate_filter.currentData()
            if estimate_id is not None:
                where_clauses.append("dr.estimate_id = ?")
                params.append(estimate_id)
        
        # Add foreman filter (only if not already filtered by permission)
        if hasattr(self, 'foreman_filter') and not self.auth_service.is_foreman():
            foreman_id = self.foreman_filter.currentData()
            if foreman_id is not None:
                where_clauses.append("dr.foreman_id = ?")
                params.append(foreman_id)
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT dr.id, dr.date, 
                   e.number as estimate_number,
                   p.full_name as foreman_name,
                   (SELECT COUNT(*) FROM daily_report_lines WHERE daily_report_id = dr.id) as line_count,
                   dr.is_posted
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            LEFT JOIN persons p ON dr.foreman_id = p.id
            WHERE {where_clause}
            ORDER BY dr.date DESC
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
            
            # Column 1: Date
            date_item = QTableWidgetItem(str(row['date']) if row['date'] else "")
            if is_posted:
                font = date_item.font()
                font.setBold(True)
                date_item.setFont(font)
            self.table_view.setItem(row_idx, 1, date_item)
            
            # Column 2-4: Other fields
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(row['estimate_number'] or ""))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(row['foreman_name'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(str(row['line_count'])))
            
            # Column 5: ID (hidden)
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(str(row['id'])))
        
        # Hide ID column
        self.table_view.setColumnHidden(5, True)
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.load_data(self.search_edit.text())
    
    def on_insert_pressed(self):
        """Handle insert key - create new daily report"""
        if not self.auth_service.can_create_daily_report():
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для создания ежедневного отчета")
            return
        
        try:
            form = DailyReportDocumentForm(0)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            self.opened_forms.append(form)
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")
    
    def on_enter_pressed(self):
        """Handle enter key - open selected daily report"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 5)
            if id_item:
                try:
                    report_id = int(id_item.text())
                    form = DailyReportDocumentForm(report_id)
                    form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                    form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
                    self.opened_forms.append(form)
                    form.show()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")
    
    def on_delete_pressed(self):
        """Handle delete key - mark daily report for deletion"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 5)
        if not id_item:
            return
        
        report_id = int(id_item.text())
        
        # Check permissions
        if not self.auth_service.can_delete_daily_report(report_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для удаления этого отчета")
            return
        
        date_item = self.table_view.item(current_row, 1)
        date = date_item.text() if date_item else ""
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Пометить отчет от '{date}' на удаление?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE daily_reports SET marked_for_deletion = 1 WHERE id = ?",
                (report_id,)
            )
            self.db.commit()
            
            QMessageBox.information(self, "Успех", "Отчет помечен на удаление")
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
        id_item = self.table_view.item(current_row, 5)
        posted_item = self.table_view.item(current_row, 0)
        is_posted = posted_item.text() == "✓" if posted_item else False
        
        # Post/Unpost actions
        if is_posted:
            unpost_action = QAction("Отменить проведение", self)
            unpost_action.triggered.connect(self.on_unpost_selected)
            menu.addAction(unpost_action)
        else:
            post_action = QAction("Провести", self)
            post_action.triggered.connect(self.on_post_selected)
            menu.addAction(post_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))
    
    def on_post_selected(self):
        """Post selected daily report"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 5)
        if not id_item:
            return
        
        report_id = int(id_item.text())
        
        # Check permissions
        if not self.auth_service.can_post_daily_report(report_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для проведения этого отчета")
            return
        
        try:
            success, error = self.posting_service.post_daily_report(report_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Отчет проведен")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось провести отчет")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при проведении: {str(e)}")
    
    def on_unpost_selected(self):
        """Unpost selected daily report"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 5)
        if not id_item:
            return
        
        report_id = int(id_item.text())
        
        # Check permissions
        if not self.auth_service.can_post_daily_report(report_id):
            QMessageBox.warning(self, "Доступ запрещен", 
                              "Недостаточно прав для отмены проведения этого отчета")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Отменить проведение отчета?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            success, error = self.posting_service.unpost_daily_report(report_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Проведение отменено")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось отменить проведение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене проведения: {str(e)}")
    
    def on_print_settings(self):
        """Open print settings dialog"""
        from .print_settings_dialog import PrintSettingsDialog
        dialog = PrintSettingsDialog(self)
        dialog.exec()

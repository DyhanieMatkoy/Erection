"""Estimate list form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel,
                              QFileDialog, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from .base_list_form import BaseListForm
from .estimate_document_form import EstimateDocumentForm
from ..data.database_manager import DatabaseManager
from ..services.document_posting_service import DocumentPostingService


class EstimateListForm(BaseListForm):
    def __init__(self):
        self.db = DatabaseManager().get_connection()
        self.posting_service = DocumentPostingService()
        self.opened_forms = []  # Keep references to opened forms
        super().__init__()
        self.setWindowTitle("Документы: Сметы")
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
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(8)
        self.table_view.setHorizontalHeaderLabels([
            "Проведен", "Номер", "Дата", "Заказчик", "Объект", "Ответственный", "Итого сумма", "ID"
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
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Открыть (Enter)")
        self.edit_button.clicked.connect(self.on_enter_pressed)
        button_layout.addWidget(self.edit_button)
        
        self.import_button = QPushButton("Импорт из Excel")
        self.import_button.clicked.connect(self.on_import_from_excel)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self, search_text=""):
        """Load data from database"""
        cursor = self.db.cursor()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if search_text:
            where_clauses.append("(e.number LIKE ? OR c.name LIKE ? OR o.name LIKE ?)")
            params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])
        
        # Add status filter
        status_filter = self.status_filter.currentData() if hasattr(self, 'status_filter') else None
        if status_filter is not None:
            where_clauses.append("e.is_posted = ?")
            params.append(status_filter)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT e.id, e.number, e.date, 
                   c.name as customer_name,
                   o.name as object_name,
                   p.full_name as responsible_name,
                   e.total_sum, e.is_posted
            FROM estimates e
            LEFT JOIN counterparties c ON e.customer_id = c.id
            LEFT JOIN objects o ON e.object_id = o.id
            LEFT JOIN persons p ON e.responsible_id = p.id
            WHERE {where_clause}
            ORDER BY e.date DESC, e.number
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
            
            # Column 2-6: Other fields
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(str(row['date']) if row['date'] else ""))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(row['customer_name'] or ""))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(row['object_name'] or ""))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(row['responsible_name'] or ""))
            self.table_view.setItem(row_idx, 6, QTableWidgetItem(f"{row['total_sum']:.2f}"))
            
            # Column 7: ID (hidden)
            self.table_view.setItem(row_idx, 7, QTableWidgetItem(str(row['id'])))
        
        # Hide ID column
        self.table_view.setColumnHidden(7, True)
    
    def on_search_text_changed(self, text):
        """Handle search text change"""
        self.load_data(text)
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.load_data(self.search_edit.text())
    
    def on_insert_pressed(self):
        """Handle insert key - create new estimate"""
        try:
            form = EstimateDocumentForm(0)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            self.opened_forms.append(form)
            form.show()
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error creating estimate form:\n{error_details}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}\n\nПодробности в консоли")
    
    def on_enter_pressed(self):
        """Handle enter key - open selected estimate"""
        current_row = self.table_view.currentRow()
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 7)
            if id_item:
                try:
                    estimate_id = int(id_item.text())
                    form = EstimateDocumentForm(estimate_id)
                    form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                    form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
                    self.opened_forms.append(form)
                    form.show()
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Error opening estimate form:\n{error_details}")
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}\n\nПодробности в консоли")
    
    def on_import_from_excel(self):
        """Handle import from Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            from ..services.excel_import_service import ExcelImportService
            from .estimate_document_form import EstimateDocumentForm
            
            # Import estimate
            service = ExcelImportService()
            estimate, error = service.import_estimate(file_path)
            
            if error:
                QMessageBox.critical(self, "Ошибка импорта", error)
                return
            
            if not estimate:
                QMessageBox.warning(self, "Импорт", "Не удалось импортировать смету")
                return
            
            # Save estimate to database
            cursor = self.db.cursor()
            try:
                cursor.execute("""
                    INSERT INTO estimates (number, date, customer_id, object_id, contractor_id, 
                                         responsible_id, total_sum, total_labor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (estimate.number, estimate.date, estimate.customer_id, estimate.object_id,
                      estimate.contractor_id, estimate.responsible_id, estimate.total_sum, estimate.total_labor))
                
                estimate_id = cursor.lastrowid
                
                # Insert lines
                for line in estimate.lines:
                    cursor.execute("""
                        INSERT INTO estimate_lines (estimate_id, line_number, work_id, quantity, unit,
                                                   price, labor_rate, sum, planned_labor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (estimate_id, line.line_number, line.work_id, line.quantity, line.unit,
                          line.price, line.labor_rate, line.sum, line.planned_labor))
                
                self.db.commit()
                
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Смета успешно импортирована!\n\nНомер: {estimate.number}\nСтрок: {len(estimate.lines)}\nИтого: {estimate.total_sum:.2f}"
                )
                
                # Reload list
                self.load_data()
                
                # Open imported estimate
                form = EstimateDocumentForm(estimate_id)
                form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
                self.opened_forms.append(form)
                form.show()
                
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
    
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
        id_item = self.table_view.item(current_row, 7)
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
        
        menu.addSeparator()
        
        # Create daily report action
        create_report_action = QAction("Создать Ежедневный отчет", self)
        create_report_action.triggered.connect(self.on_create_daily_report)
        menu.addAction(create_report_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))
    
    def on_create_daily_report(self):
        """Create daily report from selected estimate"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 7)
        if not id_item:
            return
        
        try:
            estimate_id = int(id_item.text())
            
            # Import dialog and form here to avoid circular import
            from .estimate_line_picker_dialog import EstimateLinePickerDialog
            from .daily_report_document_form import DailyReportDocumentForm
            
            # Open line picker dialog
            dialog = EstimateLinePickerDialog(estimate_id, self)
            if dialog.exec():
                selected_line_ids = dialog.get_selected_line_ids()
                if not selected_line_ids:
                    QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одной строки")
                    return
                
                # Create new daily report
                from ..data.models.daily_report import DailyReport
                from ..services.daily_report_service import DailyReportService
                
                service = DailyReportService()
                report = DailyReport()
                report.estimate_id = estimate_id
                
                # Fill from estimate
                if service.fill_from_estimate(report, selected_line_ids):
                    # Save report
                    if service.save(report):
                        QMessageBox.information(self, "Успех", f"Создан ежедневный отчет с {len(report.lines)} строками")
                        
                        # Open report form
                        form = DailyReportDocumentForm(report.id)
                        form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                        form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
                        self.opened_forms.append(form)
                        form.show()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Ошибка при сохранении отчета")
                else:
                    QMessageBox.critical(self, "Ошибка", "Ошибка при заполнении из сметы")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать отчет: {str(e)}")
    
    def on_post_selected(self):
        """Post selected estimate"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 7)
        if not id_item:
            return
        
        try:
            estimate_id = int(id_item.text())
            success, error = self.posting_service.post_estimate(estimate_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Смета проведена")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось провести смету")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при проведении: {str(e)}")
    
    def on_unpost_selected(self):
        """Unpost selected estimate"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        id_item = self.table_view.item(current_row, 7)
        if not id_item:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Отменить проведение сметы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            estimate_id = int(id_item.text())
            success, error = self.posting_service.unpost_estimate(estimate_id)
            
            if success:
                QMessageBox.information(self, "Успех", "Проведение отменено")
                self.load_data(self.search_edit.text())
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось отменить проведение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене проведения: {str(e)}")

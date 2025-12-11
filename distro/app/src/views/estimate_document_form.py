"""Estimate document form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDateEdit,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QLabel, QWidget, QGroupBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import date
from .base_document_form import BaseDocumentForm
from .reference_picker_dialog import ReferencePickerDialog
from ..data.database_manager import DatabaseManager
from ..data.models.estimate import Estimate, EstimateLine
from ..services.document_posting_service import DocumentPostingService


class EstimateDocumentForm(BaseDocumentForm):
    def __init__(self, estimate_id: int = 0):
        super().__init__()
        self.db = DatabaseManager().get_connection()
        self.estimate_id = estimate_id
        self.is_posted = False
        self.posting_service = DocumentPostingService()
        self.recalc_timer = QTimer()
        self.recalc_timer.setSingleShot(True)
        self.recalc_timer.timeout.connect(self.recalculate_totals)
        
        self.setup_ui()
        self.setWindowTitle("Смета")
        self.resize(1000, 700)
        
        if estimate_id > 0:
            self.load_estimate()
        else:
            self.create_new_estimate()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Header section
        header_group = QGroupBox("Реквизиты")
        header_layout = QFormLayout()
        
        # Number
        self.number_edit = QLineEdit()
        self.number_edit.setMaxLength(20)
        self.number_edit.textChanged.connect(self.on_field_changed)
        header_layout.addRow("Номер:", self.number_edit)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.on_field_changed)
        header_layout.addRow("Дата:", self.date_edit)
        
        # Customer
        customer_layout = QHBoxLayout()
        self.customer_edit = QLineEdit()
        self.customer_edit.setReadOnly(True)
        self.customer_id = 0
        customer_layout.addWidget(self.customer_edit)
        self.customer_button = QPushButton("...")
        self.customer_button.setMaximumWidth(30)
        self.customer_button.clicked.connect(self.on_select_customer)
        customer_layout.addWidget(self.customer_button)
        header_layout.addRow("Заказчик:", customer_layout)
        
        # Object
        object_layout = QHBoxLayout()
        self.object_edit = QLineEdit()
        self.object_edit.setReadOnly(True)
        self.object_id = 0
        object_layout.addWidget(self.object_edit)
        self.object_button = QPushButton("...")
        self.object_button.setMaximumWidth(30)
        self.object_button.clicked.connect(self.on_select_object)
        object_layout.addWidget(self.object_button)
        header_layout.addRow("Объект:", object_layout)
        
        # Contractor
        contractor_layout = QHBoxLayout()
        self.contractor_edit = QLineEdit()
        self.contractor_edit.setReadOnly(True)
        self.contractor_id = 0
        contractor_layout.addWidget(self.contractor_edit)
        self.contractor_button = QPushButton("...")
        self.contractor_button.setMaximumWidth(30)
        self.contractor_button.clicked.connect(self.on_select_contractor)
        contractor_layout.addWidget(self.contractor_button)
        header_layout.addRow("Подрядчик:", contractor_layout)
        
        # Responsible
        responsible_layout = QHBoxLayout()
        self.responsible_edit = QLineEdit()
        self.responsible_edit.setReadOnly(True)
        self.responsible_id = 0
        responsible_layout.addWidget(self.responsible_edit)
        self.responsible_button = QPushButton("...")
        self.responsible_button.setMaximumWidth(30)
        self.responsible_button.clicked.connect(self.on_select_responsible)
        responsible_layout.addWidget(self.responsible_button)
        header_layout.addRow("Ответственный:", responsible_layout)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Table part section
        table_group = QGroupBox("Табличная часть")
        table_layout = QVBoxLayout()
        
        # Table
        self.table_part = QTableWidget()
        self.table_part.setColumnCount(8)
        self.table_part.setHorizontalHeaderLabels([
            "Работа", "Количество", "Ед. изм.", "Цена", "Норма трудозатрат", "Сумма", "Плановые трудозатраты", "work_id"
        ])
        self.table_part.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_part.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_part.setColumnHidden(7, True)  # Hide work_id column
        self.table_part.cellChanged.connect(self.on_cell_changed)
        self.table_part.itemDoubleClicked.connect(self.on_cell_double_clicked)
        table_layout.addWidget(self.table_part)
        
        # Table buttons
        table_button_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Добавить строку (Insert)")
        self.add_row_button.clicked.connect(self.on_add_row)
        table_button_layout.addWidget(self.add_row_button)
        
        self.add_group_button = QPushButton("Добавить группу")
        self.add_group_button.clicked.connect(self.on_add_group)
        table_button_layout.addWidget(self.add_group_button)
        
        self.delete_row_button = QPushButton("Удалить строку (Delete)")
        self.delete_row_button.clicked.connect(self.on_delete_row)
        table_button_layout.addWidget(self.delete_row_button)
        
        table_button_layout.addStretch()
        table_layout.addLayout(table_button_layout)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Totals section
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        
        self.total_sum_label = QLabel("Итого сумма: 0.00")
        self.total_sum_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_layout.addWidget(self.total_sum_label)
        
        totals_layout.addSpacing(20)
        
        self.total_labor_label = QLabel("Итого трудозатраты: 0.00")
        self.total_labor_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_layout.addWidget(self.total_labor_label)
        
        layout.addLayout(totals_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить (Ctrl+S)")
        self.save_button.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_button)
        
        self.save_close_button = QPushButton("Сохранить и закрыть (Ctrl+Shift+S)")
        self.save_close_button.clicked.connect(self.on_save_and_close)
        self.save_close_button.setDefault(True)  # Set as default button
        button_layout.addWidget(self.save_close_button)
        
        self.post_button = QPushButton("Провести (Ctrl+K)")
        self.post_button.clicked.connect(self.on_post)
        button_layout.addWidget(self.post_button)
        
        self.unpost_button = QPushButton("Отменить проведение")
        self.unpost_button.clicked.connect(self.on_unpost)
        button_layout.addWidget(self.unpost_button)
        
        self.print_button = QPushButton("Печать (Ctrl+P)")
        self.print_button.clicked.connect(self.on_print)
        button_layout.addWidget(self.print_button)
        
        self.import_button = QPushButton("Загрузить из Excel")
        self.import_button.clicked.connect(self.on_import_from_excel)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_new_estimate(self):
        """Create new estimate"""
        self.number_edit.setText("")
        self.date_edit.setDate(QDate.currentDate())
        
        # Load default contractor and responsible from constants
        cursor = self.db.cursor()
        cursor.execute("SELECT value FROM constants WHERE key = 'default_organization_id'")
        row = cursor.fetchone()
        if row:
            org_id = int(row['value'])
            self.load_organization(org_id)
    
    def load_estimate(self):
        """Load estimate from database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, number, date, customer_id, object_id, contractor_id, 
                   responsible_id, total_sum, total_labor, is_posted
            FROM estimates
            WHERE id = ?
        """, (self.estimate_id,))
        
        row = cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Ошибка", "Смета не найдена")
            self.close()
            return
        
        # Load header
        self.number_edit.setText(row['number'] or "")
        
        # Parse date (handle both string and date object)
        if isinstance(row['date'], str):
            from datetime import datetime
            date_obj = datetime.strptime(row['date'], "%Y-%m-%d").date()
            self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        else:
            self.date_edit.setDate(QDate(row['date'].year, row['date'].month, row['date'].day))
        
        # Load references
        if row['customer_id']:
            self.load_customer(row['customer_id'])
        if row['object_id']:
            self.load_object(row['object_id'])
        if row['contractor_id']:
            self.load_organization(row['contractor_id'])
        if row['responsible_id']:
            self.load_responsible(row['responsible_id'])
        
        # Load table part
        cursor.execute("""
            SELECT line_number, work_id, quantity, unit, price, labor_rate, sum, planned_labor
            FROM estimate_lines
            WHERE estimate_id = ?
            ORDER BY line_number
        """, (self.estimate_id,))
        
        self.table_part.setRowCount(0)
        for line_row in cursor.fetchall():
            line = EstimateLine()
            line.line_number = line_row['line_number']
            line.work_id = line_row['work_id']
            line.quantity = line_row['quantity']
            line.unit = line_row['unit']
            line.price = line_row['price']
            line.labor_rate = line_row['labor_rate']
            line.sum = line_row['sum']
            line.planned_labor = line_row['planned_labor']
            
            # Handle group rows
            if line.work_id == -1:
                self.add_table_row(line)
                row = self.table_part.rowCount() - 1
                self.table_part.setItem(row, 0, QTableWidgetItem(line.unit))  # Group name stored in unit
            else:
                self.add_table_row(line)
        
        self.update_totals()
        self.modified = False
        
        # Load posting status
        self.is_posted = (row['is_posted'] if 'is_posted' in row.keys() else 0) == 1
        self.update_posting_state()
    
    def add_table_row(self, line: EstimateLine = None):
        """Add row to table"""
        row = self.table_part.rowCount()
        self.table_part.insertRow(row)
        
        if line:
            if line.work_id == -1:
                # Group row
                self.table_part.setItem(row, 0, QTableWidgetItem("=== ГРУППА ==="))
                for col in range(1, 7):
                    self.table_part.setItem(row, col, QTableWidgetItem(""))
                self.table_part.setItem(row, 7, QTableWidgetItem("-1"))
            else:
                # Load work name and code
                cursor = self.db.cursor()
                cursor.execute("SELECT code, name FROM works WHERE id = ?", (line.work_id,))
                work_row = cursor.fetchone()
                if work_row:
                    work_name = f"[{work_row['code']}] {work_row['name']}" if work_row['code'] else work_row['name']
                else:
                    work_name = ""
                
                self.table_part.setItem(row, 0, QTableWidgetItem(work_name))
                self.table_part.setItem(row, 1, QTableWidgetItem(str(line.quantity)))
                self.table_part.setItem(row, 2, QTableWidgetItem(line.unit))
                self.table_part.setItem(row, 3, QTableWidgetItem(str(line.price)))
                self.table_part.setItem(row, 4, QTableWidgetItem(str(line.labor_rate)))
                self.table_part.setItem(row, 5, QTableWidgetItem(f"{line.sum:.2f}"))
                self.table_part.setItem(row, 6, QTableWidgetItem(f"{line.planned_labor:.2f}"))
                self.table_part.setItem(row, 7, QTableWidgetItem(str(line.work_id)))
        else:
            for col in range(7):
                self.table_part.setItem(row, col, QTableWidgetItem(""))
            self.table_part.setItem(row, 7, QTableWidgetItem("0"))
        
        # Make calculated columns read-only
        if self.table_part.item(row, 5):
            self.table_part.item(row, 5).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if self.table_part.item(row, 6):
            self.table_part.item(row, 6).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    
    def on_add_row(self):
        """Handle add row"""
        self.add_table_row()
        self.modified = True
    
    def on_add_group(self):
        """Handle add group row"""
        line = EstimateLine()
        line.work_id = -1  # Special marker for group
        self.add_table_row(line)
        
        # Set group marker in work name
        row = self.table_part.rowCount() - 1
        self.table_part.setItem(row, 0, QTableWidgetItem("=== ГРУППА ==="))
        # Make all cells in group row read-only except name
        for col in range(1, 7):
            item = self.table_part.item(row, col)
            if item:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        
        self.modified = True
    
    def on_delete_row(self):
        """Handle delete row"""
        current_row = self.table_part.currentRow()
        if current_row >= 0:
            self.table_part.removeRow(current_row)
            self.schedule_recalculation()
            self.modified = True
    
    def on_move_row_up(self):
        """Move current row up"""
        current_row = self.table_part.currentRow()
        if current_row > 0:
            self.swap_rows(current_row, current_row - 1)
            self.table_part.setCurrentCell(current_row - 1, self.table_part.currentColumn())
            self.modified = True
    
    def on_move_row_down(self):
        """Move current row down"""
        current_row = self.table_part.currentRow()
        if current_row >= 0 and current_row < self.table_part.rowCount() - 1:
            self.swap_rows(current_row, current_row + 1)
            self.table_part.setCurrentCell(current_row + 1, self.table_part.currentColumn())
            self.modified = True
    
    def swap_rows(self, row1, row2):
        """Swap two rows in table"""
        for col in range(self.table_part.columnCount()):
            item1 = self.table_part.takeItem(row1, col)
            item2 = self.table_part.takeItem(row2, col)
            if item1:
                self.table_part.setItem(row2, col, item1)
            if item2:
                self.table_part.setItem(row1, col, item2)
    
    def on_cell_double_clicked(self, item):
        """Handle cell double click - open reference picker for work column"""
        if item.column() == 0:  # Work column
            self.on_select_work(item.row())
    
    def on_cell_changed(self, row, col):
        """Handle cell change"""
        if col in [1, 3, 4]:  # Quantity, Price, Labor rate
            self.schedule_recalculation()
            self.modified = True
    
    def schedule_recalculation(self):
        """Schedule recalculation with debounce"""
        self.recalc_timer.start(100)  # 100ms debounce
    
    def recalculate_totals(self):
        """Recalculate row and totals"""
        total_sum = 0.0
        total_labor = 0.0
        
        for row in range(self.table_part.rowCount()):
            try:
                quantity_item = self.table_part.item(row, 1)
                price_item = self.table_part.item(row, 3)
                labor_rate_item = self.table_part.item(row, 4)
                
                quantity = float(quantity_item.text()) if quantity_item and quantity_item.text() else 0.0
                price = float(price_item.text()) if price_item and price_item.text() else 0.0
                labor_rate = float(labor_rate_item.text()) if labor_rate_item and labor_rate_item.text() else 0.0
                
                # Calculate sum and labor
                row_sum = quantity * price
                row_labor = quantity * labor_rate
                
                # Update cells
                self.table_part.blockSignals(True)
                self.table_part.setItem(row, 5, QTableWidgetItem(f"{row_sum:.2f}"))
                self.table_part.setItem(row, 6, QTableWidgetItem(f"{row_labor:.2f}"))
                self.table_part.item(row, 5).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_part.item(row, 6).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_part.blockSignals(False)
                
                total_sum += row_sum
                total_labor += row_labor
            except (ValueError, AttributeError):
                pass
        
        self.update_totals(total_sum, total_labor)
    
    def update_totals(self, total_sum=None, total_labor=None):
        """Update totals display"""
        if total_sum is None or total_labor is None:
            # Calculate from table
            total_sum = 0.0
            total_labor = 0.0
            for row in range(self.table_part.rowCount()):
                try:
                    sum_item = self.table_part.item(row, 5)
                    labor_item = self.table_part.item(row, 6)
                    if sum_item:
                        total_sum += float(sum_item.text())
                    if labor_item:
                        total_labor += float(labor_item.text())
                except (ValueError, AttributeError):
                    pass
        
        self.total_sum_label.setText(f"Итого сумма: {total_sum:.2f}")
        self.total_labor_label.setText(f"Итого трудозатраты: {total_labor:.2f}")
    
    def on_select_customer(self):
        """Select customer"""
        dialog = ReferencePickerDialog("counterparties", "Выбор заказчика", self, current_id=self.customer_id if self.customer_id > 0 else None)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.customer_id = selected_id
            self.customer_edit.setText(selected_name)
            self.modified = True
    
    def on_select_object(self):
        """Select object"""
        if not self.customer_id:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите заказчика")
            return
        
        dialog = ReferencePickerDialog("objects", "Выбор объекта", self, owner_id=self.customer_id, current_id=self.object_id if self.object_id > 0 else None)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.object_id = selected_id
            self.object_edit.setText(selected_name)
            self.modified = True
    
    def on_select_contractor(self):
        """Select contractor"""
        dialog = ReferencePickerDialog("organizations", "Выбор подрядчика", self, current_id=self.contractor_id if self.contractor_id > 0 else None)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.contractor_id = selected_id
            self.contractor_edit.setText(selected_name)
            self.modified = True
    
    def on_select_responsible(self):
        """Select responsible"""
        dialog = ReferencePickerDialog("persons", "Выбор ответственного", self, current_id=self.responsible_id if self.responsible_id > 0 else None)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.responsible_id = selected_id
            self.responsible_edit.setText(selected_name)
            self.modified = True
    
    def on_select_work(self, row):
        """Select work for table row"""
        # Get current work_id from the row
        work_id_item = self.table_part.item(row, 7)
        current_work_id = int(work_id_item.text()) if work_id_item and work_id_item.text() and work_id_item.text() not in ["0", "-1"] else None
        
        dialog = ReferencePickerDialog("works", "Выбор работы", self, current_id=current_work_id)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            
            # Load work details
            cursor = self.db.cursor()
            cursor.execute("SELECT code, unit, price, labor_rate FROM works WHERE id = ?", (selected_id,))
            work_row = cursor.fetchone()
            
            if work_row:
                # Format name with code if available
                display_name = f"[{work_row['code']}] {selected_name}" if work_row['code'] else selected_name
                
                self.table_part.blockSignals(True)
                self.table_part.setItem(row, 0, QTableWidgetItem(display_name))
                self.table_part.setItem(row, 2, QTableWidgetItem(work_row['unit'] or ""))
                self.table_part.setItem(row, 3, QTableWidgetItem(str(work_row['price'] or 0)))
                self.table_part.setItem(row, 4, QTableWidgetItem(str(work_row['labor_rate'] or 0)))
                self.table_part.setItem(row, 7, QTableWidgetItem(str(selected_id)))
                self.table_part.blockSignals(False)
                
                self.schedule_recalculation()
                self.modified = True
    
    def load_customer(self, customer_id):
        """Load customer by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM counterparties WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        if row:
            self.customer_id = customer_id
            self.customer_edit.setText(row['name'])
    
    def load_object(self, object_id):
        """Load object by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM objects WHERE id = ?", (object_id,))
        row = cursor.fetchone()
        if row:
            self.object_id = object_id
            self.object_edit.setText(row['name'])
    
    def load_organization(self, org_id):
        """Load organization by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name, default_responsible_id FROM organizations WHERE id = ?", (org_id,))
        row = cursor.fetchone()
        if row:
            self.contractor_id = org_id
            self.contractor_edit.setText(row['name'])
            
            # Load default responsible
            if row['default_responsible_id'] and not self.responsible_id:
                self.load_responsible(row['default_responsible_id'])
    
    def load_responsible(self, person_id):
        """Load responsible by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT full_name FROM persons WHERE id = ?", (person_id,))
        row = cursor.fetchone()
        if row:
            self.responsible_id = person_id
            self.responsible_edit.setText(row['full_name'])
    
    def on_field_changed(self):
        """Handle field change"""
        self.modified = True
    
    def on_save(self):
        """Save estimate"""
        # Validate
        if not self.number_edit.text():
            QMessageBox.warning(self, "Ошибка", "Укажите номер сметы")
            return
        
        if not self.customer_id:
            QMessageBox.warning(self, "Ошибка", "Выберите заказчика")
            return
        
        # Prepare estimate data
        estimate = Estimate()
        estimate.id = self.estimate_id
        estimate.number = self.number_edit.text()
        estimate.date = self.date_edit.date().toPyDate()
        estimate.customer_id = self.customer_id
        estimate.object_id = self.object_id
        estimate.contractor_id = self.contractor_id
        estimate.responsible_id = self.responsible_id
        
        # Calculate totals
        total_sum = 0.0
        total_labor = 0.0
        
        # Prepare lines
        estimate.lines = []
        for row in range(self.table_part.rowCount()):
            try:
                work_id_item = self.table_part.item(row, 7)
                if not work_id_item or not work_id_item.text() or work_id_item.text() == "0":
                    continue
                
                work_id = int(work_id_item.text())
                
                # Handle group rows
                if work_id == -1:
                    name_item = self.table_part.item(row, 0)
                    line = EstimateLine()
                    line.line_number = row + 1
                    line.work_id = -1
                    line.quantity = 0
                    line.unit = name_item.text() if name_item else "=== ГРУППА ==="
                    line.price = 0
                    line.labor_rate = 0
                    line.sum = 0
                    line.planned_labor = 0
                    estimate.lines.append(line)
                    continue
                
                quantity_item = self.table_part.item(row, 1)
                unit_item = self.table_part.item(row, 2)
                price_item = self.table_part.item(row, 3)
                labor_rate_item = self.table_part.item(row, 4)
                sum_item = self.table_part.item(row, 5)
                labor_item = self.table_part.item(row, 6)
                
                line = EstimateLine()
                line.line_number = row + 1
                line.work_id = work_id
                line.quantity = float(quantity_item.text()) if quantity_item and quantity_item.text() else 0.0
                line.unit = unit_item.text() if unit_item else ""
                line.price = float(price_item.text()) if price_item and price_item.text() else 0.0
                line.labor_rate = float(labor_rate_item.text()) if labor_rate_item and labor_rate_item.text() else 0.0
                line.sum = float(sum_item.text()) if sum_item and sum_item.text() else 0.0
                line.planned_labor = float(labor_item.text()) if labor_item and labor_item.text() else 0.0
                
                estimate.lines.append(line)
                total_sum += line.sum
                total_labor += line.planned_labor
            except (ValueError, AttributeError) as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка в строке {row + 1}: {str(e)}")
                return
        
        estimate.total_sum = total_sum
        estimate.total_labor = total_labor
        
        # Save to database
        try:
            cursor = self.db.cursor()
            
            if self.estimate_id == 0:
                # Insert new
                cursor.execute("""
                    INSERT INTO estimates (number, date, customer_id, object_id, contractor_id, 
                                         responsible_id, total_sum, total_labor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (estimate.number, estimate.date, estimate.customer_id, estimate.object_id,
                      estimate.contractor_id, estimate.responsible_id, estimate.total_sum, estimate.total_labor))
                
                self.estimate_id = cursor.lastrowid
            else:
                # Update existing
                cursor.execute("""
                    UPDATE estimates 
                    SET number = ?, date = ?, customer_id = ?, object_id = ?, 
                        contractor_id = ?, responsible_id = ?, total_sum = ?, total_labor = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (estimate.number, estimate.date, estimate.customer_id, estimate.object_id,
                      estimate.contractor_id, estimate.responsible_id, estimate.total_sum, 
                      estimate.total_labor, self.estimate_id))
                
                # Delete old lines
                cursor.execute("DELETE FROM estimate_lines WHERE estimate_id = ?", (self.estimate_id,))
            
            # Insert lines
            for line in estimate.lines:
                cursor.execute("""
                    INSERT INTO estimate_lines (estimate_id, line_number, work_id, quantity, unit,
                                               price, labor_rate, sum, planned_labor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.estimate_id, line.line_number, line.work_id, line.quantity, line.unit,
                      line.price, line.labor_rate, line.sum, line.planned_labor))
            
            self.db.commit()
            self.modified = False
            
            # Show message in status bar instead of modal dialog
            if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                self.parent().parent().statusBar().showMessage("Смета сохранена", 3000)
            self.setWindowTitle(f"Смета {estimate.number}")
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def on_import_from_excel(self):
        """Import estimate from Excel file"""
        from PyQt6.QtWidgets import QFileDialog
        from ..services.excel_import_service import ExcelImportService
        
        # Check if document is posted
        if self.is_posted:
            QMessageBox.warning(self, "Предупреждение", "Нельзя загружать данные в проведенный документ")
            return
        
        # Check if there are unsaved changes
        if self.modified:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Есть несохраненные изменения. Продолжить загрузку из Excel?\nВсе текущие данные будут заменены.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Import estimate
            service = ExcelImportService()
            estimate, error = service.import_estimate(file_path)
            
            if error:
                QMessageBox.critical(self, "Ошибка импорта", error)
                return
            
            if not estimate:
                QMessageBox.warning(self, "Ошибка", "Не удалось импортировать смету")
                return
            
            # Load imported data into form
            self.number_edit.setText(estimate.number or "")
            
            if estimate.date:
                self.date_edit.setDate(QDate(estimate.date.year, estimate.date.month, estimate.date.day))
            
            # Load references
            if estimate.customer_id:
                self.load_customer(estimate.customer_id)
            if estimate.object_id:
                self.load_object(estimate.object_id)
            if estimate.contractor_id:
                self.load_organization(estimate.contractor_id)
            if estimate.responsible_id:
                self.load_responsible(estimate.responsible_id)
            
            # Clear and load table
            self.table_part.setRowCount(0)
            for line in estimate.lines:
                self.add_table_row(line)
            
            self.update_totals()
            self.modified = True
            
            QMessageBox.information(
                self, "Успех",
                f"Импортировано строк: {len(estimate.lines)}\n"
                f"Итого сумма: {estimate.total_sum:.2f}\n"
                f"Итого трудозатраты: {estimate.total_labor:.2f}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте: {str(e)}")
    
    def on_print(self):
        """Print estimate"""
        if self.estimate_id == 0:
            QMessageBox.warning(self, "Предупреждение", "Сначала сохраните смету")
            return
        
        try:
            from ..services.print_form_service import PrintFormService
            import tempfile
            import os
            
            # Generate print form using service
            service = PrintFormService()
            result = service.generate_estimate(self.estimate_id)
            
            if not result:
                QMessageBox.warning(self, "Ошибка", "Не удалось сгенерировать печатную форму")
                return
            
            content, extension = result
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix=f'.{extension}', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            # Open with default application
            os.startfile(temp_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при печати: {str(e)}")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Handle table shortcuts
        if self.table_part.hasFocus():
            if event.key() == Qt.Key.Key_Insert:
                self.on_add_row()
                return
            elif event.key() == Qt.Key.Key_Delete:
                self.on_delete_row()
                return
            elif event.key() == Qt.Key.Key_F4:
                current_row = self.table_part.currentRow()
                if current_row >= 0 and self.table_part.currentColumn() == 0:
                    self.on_select_work(current_row)
                return
            elif event.key() == Qt.Key.Key_Up and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                self.on_move_row_up()
                return
            elif event.key() == Qt.Key.Key_Down and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                self.on_move_row_down()
                return
        
        # Call parent handler for document shortcuts
        super().keyPressEvent(event)

    def on_post(self):
        """Handle post button"""
        if self.estimate_id == 0:
            QMessageBox.warning(self, "Предупреждение", "Сначала сохраните смету")
            return
        
        # Save before posting
        self.on_save()
        if self.estimate_id == 0:  # Save failed
            return
        
        success, error = self.posting_service.post_estimate(self.estimate_id)
        if success:
            # Show message in status bar instead of modal dialog
            if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                self.parent().parent().statusBar().showMessage("Документ проведен", 3000)
            self.load_estimate()
        else:
            QMessageBox.critical(self, "Ошибка", error)
    
    def on_unpost(self):
        """Handle unpost button"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Отменить проведение документа?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, error = self.posting_service.unpost_estimate(self.estimate_id)
            if success:
                # Show message in status bar instead of modal dialog
                if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                    self.parent().parent().statusBar().showMessage("Проведение отменено", 3000)
                self.load_estimate()
            else:
                QMessageBox.critical(self, "Ошибка", error)
    
    def update_posting_state(self):
        """Update form state based on posting status"""
        is_editable = not self.is_posted
        
        # Block/unblock fields
        self.number_edit.setReadOnly(not is_editable)
        self.date_edit.setEnabled(is_editable)
        self.customer_button.setEnabled(is_editable)
        self.object_button.setEnabled(is_editable)
        self.contractor_button.setEnabled(is_editable)
        self.responsible_button.setEnabled(is_editable)
        self.table_part.setEnabled(is_editable)
        self.add_row_button.setEnabled(is_editable)
        self.add_group_button.setEnabled(is_editable)
        self.delete_row_button.setEnabled(is_editable)
        
        # Update buttons
        self.save_button.setEnabled(is_editable)
        self.save_close_button.setEnabled(is_editable)
        self.post_button.setEnabled(not self.is_posted and self.estimate_id > 0)
        self.unpost_button.setEnabled(self.is_posted)
        self.import_button.setEnabled(is_editable)
        
        # Update window title
        status = " [ПРОВЕДЕН]" if self.is_posted else ""
        number = self.number_edit.text() or "новая"
        self.setWindowTitle(f"Смета {number}{status}")

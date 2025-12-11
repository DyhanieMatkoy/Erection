"""Timesheet document form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDateEdit,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QLabel, QWidget, QGroupBox, QDialog)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from datetime import date, datetime
from calendar import monthrange
from .base_document_form import BaseDocumentForm
from .reference_picker_dialog import ReferencePickerDialog
from .employee_picker_dialog import EmployeePickerDialog
from ..data.database_manager import DatabaseManager
from ..data.repositories.timesheet_repository import TimesheetRepository
from ..services.timesheet_posting_service import TimesheetPostingService
from ..services.auto_fill_service import AutoFillService


class TimesheetDocumentForm(BaseDocumentForm):
    def __init__(self, timesheet_id: int = 0):
        super().__init__()
        self.db = DatabaseManager().get_connection()
        self.timesheet_id = timesheet_id
        self.is_posted = False
        self.repository = TimesheetRepository()
        self.posting_service = TimesheetPostingService()
        self.auto_fill_service = AutoFillService()
        self.recalc_timer = QTimer()
        self.recalc_timer.setSingleShot(True)
        self.recalc_timer.timeout.connect(self.recalculate_totals)
        
        self.setup_ui()
        self.setWindowTitle("Табель")
        self.resize(1200, 700)
        
        if timesheet_id > 0:
            self.load_timesheet()
        else:
            self.create_new_timesheet()
    
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
        self.date_edit.dateChanged.connect(self.on_date_changed)
        header_layout.addRow("Дата:", self.date_edit)
        
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
        
        # Estimate
        estimate_layout = QHBoxLayout()
        self.estimate_edit = QLineEdit()
        self.estimate_edit.setReadOnly(True)
        self.estimate_id = 0
        estimate_layout.addWidget(self.estimate_edit)
        self.estimate_button = QPushButton("...")
        self.estimate_button.setMaximumWidth(30)
        self.estimate_button.clicked.connect(self.on_select_estimate)
        estimate_layout.addWidget(self.estimate_button)
        header_layout.addRow("Смета:", estimate_layout)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_employee_button = QPushButton("Добавить сотрудника")
        self.add_employee_button.clicked.connect(self.on_add_employee)
        toolbar_layout.addWidget(self.add_employee_button)
        
        self.fill_button = QPushButton("Заполнить из ежедневных отчетов")
        self.fill_button.clicked.connect(self.on_fill_from_daily_reports)
        toolbar_layout.addWidget(self.fill_button)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Table part section
        table_group = QGroupBox("Табличная часть")
        table_layout = QVBoxLayout()
        
        # Table
        self.table_part = QTableWidget()
        self.setup_table_columns()
        self.table_part.cellChanged.connect(self.on_cell_changed)
        table_layout.addWidget(self.table_part)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить (Ctrl+S)")
        self.save_button.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_button)
        
        self.save_close_button = QPushButton("Сохранить и закрыть (Ctrl+Shift+S)")
        self.save_close_button.clicked.connect(self.on_save_and_close)
        self.save_close_button.setDefault(True)
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
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def setup_table_columns(self):
        """Setup table columns based on current month"""
        # Get number of days in current month
        current_date = self.date_edit.date().toPyDate()
        year = current_date.year
        month = current_date.month
        days_in_month = monthrange(year, month)[1]
        
        # Columns: Employee, Rate, Day 1-31, Total, Amount, employee_id
        num_columns = 2 + days_in_month + 2 + 1  # Employee, Rate, Days, Total, Amount, ID
        self.table_part.setColumnCount(num_columns)
        
        headers = ["Сотрудник", "Ставка"]
        for day in range(1, days_in_month + 1):
            headers.append(str(day))
        headers.extend(["Итого", "Сумма", "ID"])
        
        self.table_part.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        self.table_part.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_part.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        # Set day columns to fixed width
        for col in range(2, 2 + days_in_month):
            self.table_part.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.table_part.setColumnWidth(col, 40)
            
            # Highlight weekends
            day_num = col - 1  # Day number (1-31)
            day_date = date(year, month, day_num)
            if day_date.weekday() >= 5:  # Saturday=5, Sunday=6
                # Set header background color for weekend
                header_item = self.table_part.horizontalHeaderItem(col)
                if header_item:
                    header_item.setBackground(QColor(255, 200, 200))
        
        self.table_part.horizontalHeader().setSectionResizeMode(2 + days_in_month, QHeaderView.ResizeMode.ResizeToContents)
        self.table_part.horizontalHeader().setSectionResizeMode(2 + days_in_month + 1, QHeaderView.ResizeMode.ResizeToContents)
        
        # Hide ID column
        self.table_part.setColumnHidden(num_columns - 1, True)
    
    def on_date_changed(self):
        """Handle date change - rebuild table columns"""
        # Save current data
        current_data = self.get_table_data()
        
        # Rebuild columns
        self.setup_table_columns()
        
        # Restore data
        if current_data:
            self.populate_table(current_data)
        
        self.modified = True
    
    def create_new_timesheet(self):
        """Create new timesheet"""
        # Generate number
        cursor = self.db.cursor()
        cursor.execute("SELECT MAX(CAST(number AS INTEGER)) as max_num FROM timesheets")
        row = cursor.fetchone()
        max_num = row['max_num'] if row and row['max_num'] else 0
        self.number_edit.setText(str(max_num + 1))
        
        self.date_edit.setDate(QDate.currentDate())
        self.object_id = 0
        self.object_edit.setText("")
        self.estimate_id = 0
        self.estimate_edit.setText("")
        
        # Get current user's person_id as foreman
        from ..services.auth_service import AuthService
        auth_service = AuthService()
        self.foreman_id = auth_service.current_person_id()
    
    def load_timesheet(self):
        """Load timesheet from database"""
        timesheet = self.repository.find_by_id(self.timesheet_id)
        
        if not timesheet:
            QMessageBox.warning(self, "Ошибка", "Табель не найден")
            self.close()
            return
        
        # Load header
        self.number_edit.setText(timesheet['number'] or "")
        
        # Parse date
        if isinstance(timesheet['date'], str):
            date_obj = datetime.strptime(timesheet['date'], "%Y-%m-%d").date()
            self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        else:
            self.date_edit.setDate(QDate(timesheet['date'].year, timesheet['date'].month, timesheet['date'].day))
        
        # Load references
        if timesheet.get('object_id'):
            self.load_object(timesheet['object_id'])
        if timesheet.get('estimate_id'):
            self.load_estimate(timesheet['estimate_id'])
        
        self.foreman_id = timesheet.get('foreman_id')
        
        # Load lines
        self.populate_table(timesheet.get('lines', []))
        
        self.modified = False
        
        # Load posting status
        self.is_posted = timesheet.get('is_posted', False)
        self.update_posting_state()
    
    def populate_table(self, lines):
        """Populate table with lines"""
        self.table_part.blockSignals(True)
        self.table_part.setRowCount(0)
        
        for line in lines:
            self.add_table_row(line)
        
        self.table_part.blockSignals(False)
    
    def add_table_row(self, line=None):
        """Add row to table"""
        row = self.table_part.rowCount()
        self.table_part.insertRow(row)
        
        # Get number of days in current month
        current_date = self.date_edit.date().toPyDate()
        days_in_month = monthrange(current_date.year, current_date.month)[1]
        
        if line:
            # Load employee name
            employee_name = line.get('employee_name', '')
            if not employee_name and line.get('employee_id'):
                cursor = self.db.cursor()
                cursor.execute("SELECT full_name FROM persons WHERE id = ?", (line['employee_id'],))
                emp_row = cursor.fetchone()
                employee_name = emp_row['full_name'] if emp_row else ""
            
            # Column 0: Employee name
            self.table_part.setItem(row, 0, QTableWidgetItem(employee_name))
            self.table_part.item(row, 0).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            
            # Column 1: Hourly rate
            self.table_part.setItem(row, 1, QTableWidgetItem(str(line.get('hourly_rate', 0))))
            
            # Columns 2 to 2+days_in_month: Day values
            days = line.get('days', {})
            for day in range(1, days_in_month + 1):
                col = 1 + day
                hours = days.get(day, 0)
                self.table_part.setItem(row, col, QTableWidgetItem(str(hours) if hours > 0 else ""))
            
            # Total hours
            total_hours = line.get('total_hours', sum(days.values()))
            self.table_part.setItem(row, 2 + days_in_month, QTableWidgetItem(f"{total_hours:.2f}"))
            self.table_part.item(row, 2 + days_in_month).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            
            # Total amount
            total_amount = line.get('total_amount', total_hours * line.get('hourly_rate', 0))
            self.table_part.setItem(row, 2 + days_in_month + 1, QTableWidgetItem(f"{total_amount:.2f}"))
            self.table_part.item(row, 2 + days_in_month + 1).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            
            # Employee ID (hidden)
            self.table_part.setItem(row, 2 + days_in_month + 2, QTableWidgetItem(str(line.get('employee_id', 0))))
        else:
            # Empty row
            for col in range(self.table_part.columnCount()):
                self.table_part.setItem(row, col, QTableWidgetItem(""))

    def on_add_employee(self):
        """Add employee to table"""
        dialog = EmployeePickerDialog(self, self.foreman_id)
        if dialog.exec():
            employee_id, employee_name, hourly_rate = dialog.get_selected()
            
            if employee_id:
                # Check if employee already exists
                for row in range(self.table_part.rowCount()):
                    id_item = self.table_part.item(row, self.table_part.columnCount() - 1)
                    if id_item and int(id_item.text()) == employee_id:
                        QMessageBox.warning(self, "Предупреждение", "Сотрудник уже добавлен")
                        return
                
                # Create line with hourly rate from picker
                line = {
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'hourly_rate': hourly_rate,
                    'days': {},
                    'total_hours': 0,
                    'total_amount': 0
                }
                
                self.add_table_row(line)
                self.modified = True
    
    def on_fill_from_daily_reports(self):
        """Fill table from daily reports"""
        if not self.object_id or not self.estimate_id:
            QMessageBox.warning(self, "Предупреждение", 
                              "Сначала выберите объект и смету")
            return
        
        # Check if table has data
        if self.table_part.rowCount() > 0:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Табличная часть уже содержит данные. Заменить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get month_year from date
        current_date = self.date_edit.date().toPyDate()
        month_year = f"{current_date.year:04d}-{current_date.month:02d}"
        
        # Call auto-fill service
        try:
            lines = self.auto_fill_service.fill_from_daily_reports(
                self.object_id,
                self.estimate_id,
                month_year
            )
            
            if not lines:
                QMessageBox.information(self, "Информация", 
                                      "Не найдено ежедневных отчетов за указанный период")
                return
            
            # Populate table
            self.populate_table(lines)
            self.modified = True
            
            QMessageBox.information(self, "Успех", 
                                  f"Добавлено сотрудников: {len(lines)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Ошибка при заполнении: {str(e)}")
    
    def on_cell_changed(self, row, col):
        """Handle cell change"""
        # Get number of days in current month
        current_date = self.date_edit.date().toPyDate()
        days_in_month = monthrange(current_date.year, current_date.month)[1]
        
        # Check if it's a rate or day column
        if col == 1 or (col >= 2 and col < 2 + days_in_month):
            # Validate input
            item = self.table_part.item(row, col)
            if item:
                try:
                    value = float(item.text()) if item.text() else 0
                    
                    # Validate hours (0-24)
                    if col >= 2 and col < 2 + days_in_month:
                        if value < 0 or value > 24:
                            QMessageBox.warning(self, "Ошибка", 
                                              "Часы должны быть от 0 до 24")
                            self.table_part.blockSignals(True)
                            item.setText("0")
                            self.table_part.blockSignals(False)
                            return
                    
                    # Validate rate (> 0)
                    if col == 1 and value < 0:
                        QMessageBox.warning(self, "Ошибка", 
                                          "Ставка должна быть положительной")
                        self.table_part.blockSignals(True)
                        item.setText("0")
                        self.table_part.blockSignals(False)
                        return
                    
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", 
                                      "Введите числовое значение")
                    self.table_part.blockSignals(True)
                    item.setText("0")
                    self.table_part.blockSignals(False)
                    return
            
            # Schedule recalculation
            self.schedule_recalculation()
            self.modified = True
    
    def schedule_recalculation(self):
        """Schedule recalculation with debounce"""
        self.recalc_timer.start(100)  # 100ms debounce
    
    def recalculate_totals(self):
        """Recalculate totals for all rows"""
        current_date = self.date_edit.date().toPyDate()
        days_in_month = monthrange(current_date.year, current_date.month)[1]
        
        self.table_part.blockSignals(True)
        
        for row in range(self.table_part.rowCount()):
            try:
                # Get rate
                rate_item = self.table_part.item(row, 1)
                rate = float(rate_item.text()) if rate_item and rate_item.text() else 0
                
                # Calculate total hours
                total_hours = 0
                for day in range(1, days_in_month + 1):
                    col = 1 + day
                    day_item = self.table_part.item(row, col)
                    if day_item and day_item.text():
                        try:
                            hours = float(day_item.text())
                            total_hours += hours
                        except ValueError:
                            pass
                
                # Calculate total amount
                total_amount = total_hours * rate
                
                # Update totals
                total_col = 2 + days_in_month
                amount_col = 2 + days_in_month + 1
                
                self.table_part.setItem(row, total_col, QTableWidgetItem(f"{total_hours:.2f}"))
                self.table_part.item(row, total_col).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                
                self.table_part.setItem(row, amount_col, QTableWidgetItem(f"{total_amount:.2f}"))
                self.table_part.item(row, amount_col).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                
            except (ValueError, AttributeError):
                pass
        
        self.table_part.blockSignals(False)
    
    def get_table_data(self):
        """Get data from table"""
        current_date = self.date_edit.date().toPyDate()
        days_in_month = monthrange(current_date.year, current_date.month)[1]
        
        lines = []
        for row in range(self.table_part.rowCount()):
            try:
                # Get employee ID
                id_item = self.table_part.item(row, self.table_part.columnCount() - 1)
                if not id_item or not id_item.text() or id_item.text() == "0":
                    continue
                
                employee_id = int(id_item.text())
                
                # Get rate
                rate_item = self.table_part.item(row, 1)
                hourly_rate = float(rate_item.text()) if rate_item and rate_item.text() else 0
                
                # Get days
                days = {}
                for day in range(1, days_in_month + 1):
                    col = 1 + day
                    day_item = self.table_part.item(row, col)
                    if day_item and day_item.text():
                        try:
                            hours = float(day_item.text())
                            if hours > 0:
                                days[day] = hours
                        except ValueError:
                            pass
                
                line = {
                    'line_number': row + 1,
                    'employee_id': employee_id,
                    'hourly_rate': hourly_rate,
                    'days': days
                }
                lines.append(line)
                
            except (ValueError, AttributeError):
                pass
        
        return lines

    def on_select_object(self):
        """Select object"""
        dialog = ReferencePickerDialog("objects", "Выбор объекта", self)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.object_id = selected_id
            self.object_edit.setText(selected_name)
            self.modified = True
    
    def on_select_estimate(self):
        """Select estimate"""
        if not self.object_id:
            QMessageBox.warning(self, "Предупреждение", 
                              "Сначала выберите объект")
            return
        
        # Use estimate list form for selection
        from .estimate_list_form import EstimateListForm
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор сметы")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Create list form
        list_form = EstimateListForm()
        list_form.setParent(dialog)
        layout.addWidget(list_form)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        select_button = QPushButton("Выбрать")
        select_button.clicked.connect(dialog.accept)
        button_layout.addWidget(select_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_row = list_form.table_view.currentRow()
            if current_row >= 0:
                estimate_id_item = list_form.table_view.item(current_row, 0)
                if estimate_id_item:
                    estimate_id = int(estimate_id_item.text())
                    self.load_estimate(estimate_id)
                    self.modified = True
    
    def load_object(self, object_id):
        """Load object by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM objects WHERE id = ?", (object_id,))
        row = cursor.fetchone()
        if row:
            self.object_id = object_id
            self.object_edit.setText(row['name'])
    
    def load_estimate(self, estimate_id):
        """Load estimate by ID"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT e.number, e.date, o.name as object_name
            FROM estimates e
            LEFT JOIN objects o ON e.object_id = o.id
            WHERE e.id = ?
        """, (estimate_id,))
        row = cursor.fetchone()
        if row:
            self.estimate_id = estimate_id
            display_text = f"{row['number']} от {row['date']}"
            if row['object_name']:
                display_text += f" - {row['object_name']}"
            self.estimate_edit.setText(display_text)
            
            # Also set object if not set
            if not self.object_id:
                cursor.execute("SELECT object_id FROM estimates WHERE id = ?", (estimate_id,))
                est_row = cursor.fetchone()
                if est_row and est_row['object_id']:
                    self.load_object(est_row['object_id'])
    
    def on_field_changed(self):
        """Handle field change"""
        self.modified = True
    
    def on_save(self):
        """Save timesheet"""
        # Validate
        if not self.number_edit.text():
            QMessageBox.warning(self, "Ошибка", "Укажите номер табеля")
            return
        
        if not self.object_id:
            QMessageBox.warning(self, "Ошибка", "Выберите объект")
            return
        
        if not self.estimate_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смету")
            return
        
        # Get table data
        lines = self.get_table_data()
        
        if not lines:
            QMessageBox.warning(self, "Ошибка", 
                              "Добавьте хотя бы одного сотрудника")
            return
        
        # Prepare timesheet data
        current_date = self.date_edit.date().toPyDate()
        month_year = f"{current_date.year:04d}-{current_date.month:02d}"
        
        timesheet_data = {
            'number': self.number_edit.text(),
            'date': current_date.isoformat(),
            'object_id': self.object_id,
            'estimate_id': self.estimate_id,
            'month_year': month_year,
            'lines': lines
        }
        
        # Save to database
        try:
            if self.timesheet_id == 0:
                # Create new
                result = self.repository.create(timesheet_data, self.foreman_id)
                self.timesheet_id = result['id']
            else:
                # Update existing
                result = self.repository.update(self.timesheet_id, timesheet_data)
            
            self.modified = False
            
            # Show message in status bar
            if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                self.parent().parent().statusBar().showMessage("Табель сохранен", 3000)
            
            self.setWindowTitle(f"Табель {self.number_edit.text()}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Ошибка при сохранении: {str(e)}")
    
    def on_post(self):
        """Post timesheet"""
        if self.timesheet_id == 0:
            QMessageBox.warning(self, "Предупреждение", 
                              "Сначала сохраните табель")
            return
        
        # Save before posting
        self.on_save()
        if self.timesheet_id == 0:
            return
        
        try:
            success, error = self.posting_service.post_timesheet(self.timesheet_id)
            
            if success:
                if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                    self.parent().parent().statusBar().showMessage("Табель проведен", 3000)
                self.load_timesheet()
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось провести табель")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Ошибка при проведении: {str(e)}")
    
    def on_unpost(self):
        """Unpost timesheet"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Отменить проведение табеля?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            success, error = self.posting_service.unpost_timesheet(self.timesheet_id)
            
            if success:
                if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                    self.parent().parent().statusBar().showMessage("Проведение отменено", 3000)
                self.load_timesheet()
            else:
                QMessageBox.critical(self, "Ошибка", error or "Не удалось отменить проведение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Ошибка при отмене проведения: {str(e)}")
    
    def update_posting_state(self):
        """Update UI based on posting state"""
        # Disable editing if posted
        self.number_edit.setEnabled(not self.is_posted)
        self.date_edit.setEnabled(not self.is_posted)
        self.object_button.setEnabled(not self.is_posted)
        self.estimate_button.setEnabled(not self.is_posted)
        self.add_employee_button.setEnabled(not self.is_posted)
        self.fill_button.setEnabled(not self.is_posted)
        self.table_part.setEnabled(not self.is_posted)
        self.save_button.setEnabled(not self.is_posted)
        self.save_close_button.setEnabled(not self.is_posted)
        
        # Update button visibility
        self.post_button.setVisible(not self.is_posted)
        self.unpost_button.setVisible(self.is_posted)
    
    def on_print(self):
        """Print timesheet"""
        if self.timesheet_id == 0:
            QMessageBox.warning(self, "Предупреждение", 
                              "Сначала сохраните табель")
            return
        
        try:
            from ..services.excel_timesheet_print_form import ExcelTimesheetPrintForm
            import tempfile
            import os
            import subprocess
            
            # Generate Excel file
            print_form = ExcelTimesheetPrintForm()
            excel_bytes = print_form.generate(self.timesheet_id)
            
            if not excel_bytes:
                QMessageBox.critical(self, "Ошибка", 
                                   "Не удалось сгенерировать печатную форму")
                return
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
                tmp_file.write(excel_bytes)
                tmp_path = tmp_file.name
            
            # Open file in default application
            try:
                os.startfile(tmp_path)
                
                if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                    self.parent().parent().statusBar().showMessage("Печатная форма открыта", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", 
                                   f"Не удалось открыть файл: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Ошибка при печати: {str(e)}")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Handle Ctrl+K for posting
        if event.key() == Qt.Key.Key_K and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if not self.is_posted:
                self.on_post()
            return
        
        # Call parent handler for other shortcuts
        super().keyPressEvent(event)

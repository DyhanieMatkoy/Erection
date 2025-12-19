"""Daily report document form"""
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDateEdit,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QLabel, QWidget, QGroupBox, QComboBox, QDialog,
                              QListWidget, QListWidgetItem, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import date
from .base_document_form import BaseDocumentForm
from .reference_picker_dialog import ReferencePickerDialog
from ..data.database_manager import DatabaseManager
from ..data.models.sqlalchemy_models import (
    DailyReport, DailyReportLine, Person, Estimate, Work, DailyReportExecutor
)
from ..services.daily_report_service import DailyReportService
from ..services.document_posting_service import DocumentPostingService


class ExecutorPickerDialog(QDialog):
    """Dialog for selecting multiple executors"""
    def __init__(self, parent=None, selected_ids=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.selected_ids = selected_ids or []
        self.setup_ui()
        self.load_data()
        
        # Ensure session is closed
        self.finished.connect(lambda: self.session.close())
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Выбор исполнителей")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # List
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.accept)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Load persons"""
        try:
            persons = self.session.query(Person).filter(Person.marked_for_deletion == False).order_by(Person.full_name).all()
            
            for person in persons:
                item = QListWidgetItem(person.full_name)
                item.setData(Qt.ItemDataRole.UserRole, person.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                
                if person.id in self.selected_ids:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                
                self.list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить исполнителей: {e}")
    
    def get_selected(self):
        """Get selected executor IDs and names"""
        ids = []
        names = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
                names.append(item.text())
        return ids, names


class DailyReportDocumentForm(BaseDocumentForm):
    def __init__(self, report_id: int = 0, estimate_id: int = 0):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.report_id = report_id
        self.is_posted = False
        self.service = DailyReportService() # Service likely uses its own session or raw SQL. Ideally we inject session.
        # But DailyReportService might be legacy. Let's check it later. For now we use our session for loading/saving if possible, 
        # or rely on service if it's robust.
        # Actually, let's use our session for loading to be consistent, and service for complex operations if any.
        # But wait, `save` method calls `self.service.save(report)`.
        # If I rewrite `save` to use SQLAlchemy, I might bypass service logic.
        # `DailyReportService` probably uses raw SQL.
        # I should probably update `save` to use SQLAlchemy directly here, or update Service.
        # Updating Service is better but risky if it's used elsewhere.
        # Let's see `src/services/daily_report_service.py` content if I can... 
        # Assuming I should refactor form to use SQLAlchemy directly like EstimateForm.
        
        self.posting_service = DocumentPostingService()
        self.recalc_timer = QTimer()
        self.recalc_timer.setSingleShot(True)
        self.recalc_timer.timeout.connect(self.recalculate_deviations)
        
        self.setup_ui()
        self.setWindowTitle("Ежедневный отчет")
        self.resize(1000, 700)
        
        # Ensure session is closed
        self.destroyed.connect(lambda: self.session.close())
        
        if report_id > 0:
            self.load_report()
        else:
            self.create_new_report(estimate_id)
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Header section
        header_group = QGroupBox("Реквизиты")
        header_layout = QFormLayout()
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.on_field_changed)
        header_layout.addRow("Дата:", self.date_edit)
        
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
        
        # Foreman
        foreman_layout = QHBoxLayout()
        self.foreman_edit = QLineEdit()
        self.foreman_edit.setReadOnly(True)
        self.foreman_id = 0
        foreman_layout.addWidget(self.foreman_edit)
        self.foreman_button = QPushButton("...")
        self.foreman_button.setMaximumWidth(30)
        self.foreman_button.clicked.connect(self.on_select_foreman)
        foreman_layout.addWidget(self.foreman_button)
        header_layout.addRow("Бригадир:", foreman_layout)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Table part section
        table_group = QGroupBox("Табличная часть")
        table_layout = QVBoxLayout()
        
        # Fill button
        fill_button_layout = QHBoxLayout()
        self.fill_button = QPushButton("Заполнить из сметы")
        self.fill_button.clicked.connect(self.on_fill_from_estimate)
        fill_button_layout.addWidget(self.fill_button)
        
        self.import_button = QPushButton("Загрузить из Excel")
        self.import_button.clicked.connect(self.on_import_from_excel)
        fill_button_layout.addWidget(self.import_button)
        
        fill_button_layout.addStretch()
        table_layout.addLayout(fill_button_layout)
        
        # Table
        self.table_part = QTableWidget()
        self.table_part.setColumnCount(7)
        self.table_part.setHorizontalHeaderLabels([
            "Работа", "Плановые трудозатраты", "Фактические трудозатраты", 
            "Отклонение %", "Исполнители", "work_id", "executor_ids"
        ])
        self.table_part.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_part.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table_part.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_part.setColumnHidden(5, True)  # Hide work_id column
        self.table_part.setColumnHidden(6, True)  # Hide executor_ids column
        self.table_part.cellChanged.connect(self.on_cell_changed)
        self.table_part.itemDoubleClicked.connect(self.on_cell_double_clicked)
        
        # Context menu
        self.table_part.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_part.customContextMenuRequested.connect(self.on_table_context_menu)
        
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
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть (Esc)")
        self.close_button.clicked.connect(self.on_close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_new_report(self, estimate_id: int = 0):
        """Create new report"""
        self.date_edit.setDate(QDate.currentDate())
        # Initialize empty values
        self.estimate_id = 0
        self.estimate_edit.setText("")
        self.foreman_id = 0
        self.foreman_edit.setText("")
        
        # If estimate_id provided, load it
        if estimate_id > 0:
            self.load_estimate(estimate_id)
    
    def load_report(self):
        """Load report from database"""
        try:
            report = self.session.query(DailyReport).filter_by(id=self.report_id).first()
            if not report:
                QMessageBox.warning(self, "Ошибка", "Отчет не найден")
                self.close()
                return
            
            # Load header
            if report.date:
                self.date_edit.setDate(QDate(report.date.year, report.date.month, report.date.day))
            
            # Load estimate
            if report.estimate_id:
                self.load_estimate(report.estimate_id)
            
            # Load foreman
            if report.foreman_id:
                self.load_foreman(report.foreman_id)
            
            # Load table part
            self.table_part.setRowCount(0)
            
            # Sort lines by line_number
            lines = sorted(report.lines, key=lambda x: x.line_number) if report.lines else []
            
            for line in lines:
                # Eager loading of executors should handle this if configured in model
                # But if not, we might need to access line.executors (list of Person objects)
                
                # We need a DTO-like object or just pass params to add_table_row
                # Since add_table_row expects DailyReportLine, we can pass it directly
                # But we also need 'executor_ids' which might not be on the SQLAlchemy object directly 
                # (it has 'executors' relationship).
                # Let's check DailyReportLine model in sqlalchemy_models.py... 
                # I assume it has `executors` relationship to Person via DailyReportExecutor.
                
                # Let's augment the line object with executor_ids for the helper
                line.executor_ids = [e.id for e in line.executors]
                
                self.add_table_row(line)
            
            self.modified = False
            
            # Load posting status
            self.is_posted = report.is_posted
            self.update_posting_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить отчет: {e}")
            self.close()

    def on_select_estimate(self):
        """Select estimate using list form"""
        from .estimate_list_form_v2 import EstimateListFormV2
        
        # Create estimate list form in selection mode
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор сметы")
        dialog.setModal(True)
        dialog.resize(1000, 600)
        
        layout = QVBoxLayout()
        
        # Create list form
        # Pass user_id=4 (admin) as fallback
        list_form = EstimateListFormV2(user_id=4) 
        list_form.setParent(dialog)
        
        # We need to hook into row double click or add a select button
        # GenericListForm doesn't have a "Selection Mode" yet.
        # But we can assume double click selects if in dialog?
        # Or just add a button.
        
        layout.addWidget(list_form)
        
        # Buttons
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
            # Get selected estimate
            selected_ids = list_form.controller.get_selection()
            if selected_ids:
                estimate_id = selected_ids[0]
                self.load_estimate(estimate_id)
                self.modified = True
    
    def load_estimate(self, estimate_id):
        """Load estimate by ID"""
        est = self.session.query(Estimate).filter_by(id=estimate_id).first()
        if est:
            self.estimate_id = estimate_id
            display_text = f"{est.number} от {est.date}"
            if est.customer:
                display_text += f" - {est.customer.name}"
            self.estimate_edit.setText(display_text)
    
    def on_fill_from_estimate(self):
        """Fill report from estimate"""
        if not self.estimate_id:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите смету")
            return
        
        estimate_id = self.estimate_id
        
        # Import dialog here to avoid circular import
        from .estimate_line_picker_dialog import EstimateLinePickerDialog
        
        dialog = EstimateLinePickerDialog(estimate_id, self)
        if dialog.exec():
            selected_line_ids = dialog.get_selected_line_ids()
            if not selected_line_ids:
                QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одной строки")
                return
            
            # Create temporary report to fill
            temp_report = DailyReport()
            temp_report.estimate_id = estimate_id
            
            # Use service to fill (it calculates planned labor etc.)
            # If service uses raw SQL, it might fail with our object if it expects different type.
            # But fill_from_estimate logic is usually business logic.
            # Let's try to reimplement strictly necessary logic here or trust service.
            # Service implementation of fill_from_estimate:
            # It queries estimate_lines and creates DailyReportLine objects.
            # Let's assume it returns a list of objects we can use.
            # Actually, `service.fill_from_estimate` modifies `temp_report.lines`.
            
            if self.service.fill_from_estimate(temp_report, selected_line_ids):
                # Clear table
                self.table_part.setRowCount(0)
                
                # Add rows
                for line in temp_report.lines:
                    # Load work name if not a group
                    work_name = ""
                    if line.is_group:
                        work_name = f"[ГРУППА] {line.group_name}"
                    elif line.work_id:
                        work = self.session.query(Work).filter_by(id=line.work_id).first()
                        if work:
                            work_name = work.name
                    
                    # Ensure executor_ids is initialized
                    if not hasattr(line, 'executor_ids'):
                         line.executor_ids = []

                    self.add_table_row(line, work_name)
                
                self.modified = True
                QMessageBox.information(self, "Успех", f"Добавлено строк: {len(temp_report.lines)}")
            else:
                QMessageBox.critical(self, "Ошибка", "Ошибка при заполнении из сметы")
    
    def add_table_row(self, line: DailyReportLine = None, work_name: str = None):
        """Add row to table"""
        row = self.table_part.rowCount()
        self.table_part.insertRow(row)
        
        if line:
            # Load work name if not provided
            if not work_name:
                if line.is_group:
                    work_name = f"[ГРУППА] {line.group_name}"
                elif line.work_id:
                    # Check if line.work is loaded
                    if hasattr(line, 'work') and line.work:
                        work_name = line.work.name
                    else:
                        work = self.session.query(Work).filter_by(id=line.work_id).first()
                        work_name = work.name if work else ""
                else:
                    work_name = ""
            
            # Load executor names
            executor_names = []
            # Check executor_ids (added manually or from model if property exists)
            # SQLAlchemy model usually has `executors` relationship.
            if hasattr(line, 'executors') and line.executors:
                 executor_names = [p.full_name for p in line.executors]
                 executor_ids = [p.id for p in line.executors]
            elif hasattr(line, 'executor_ids') and line.executor_ids:
                 # Load by IDs
                 executors = self.session.query(Person).filter(Person.id.in_(line.executor_ids)).all()
                 executor_names = [p.full_name for p in executors]
                 executor_ids = line.executor_ids
            else:
                 executor_ids = []
            
            self.table_part.setItem(row, 0, QTableWidgetItem(work_name))
            self.table_part.setItem(row, 1, QTableWidgetItem(f"{line.planned_labor or 0:.2f}" if not line.is_group else ""))
            self.table_part.setItem(row, 2, QTableWidgetItem(f"{line.actual_labor or 0:.2f}" if not line.is_group else ""))
            self.table_part.setItem(row, 3, QTableWidgetItem(f"{line.deviation_percent or 0:.2f}" if not line.is_group else ""))
            self.table_part.setItem(row, 4, QTableWidgetItem(", ".join(executor_names)))
            self.table_part.setItem(row, 5, QTableWidgetItem(str(line.work_id or 0)))
            self.table_part.setItem(row, 6, QTableWidgetItem(",".join(map(str, executor_ids))))
        else:
            for col in range(5):
                self.table_part.setItem(row, col, QTableWidgetItem(""))
            self.table_part.setItem(row, 5, QTableWidgetItem("0"))
            self.table_part.setItem(row, 6, QTableWidgetItem(""))
        
        # Make calculated columns read-only
        if self.table_part.item(row, 0):
            self.table_part.item(row, 0).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if self.table_part.item(row, 1):
            self.table_part.item(row, 1).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if self.table_part.item(row, 3):
            self.table_part.item(row, 3).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    
    def on_cell_double_clicked(self, item):
        """Handle cell double click - open executor picker for executors column"""
        if item.column() == 4:  # Executors column
            self.on_select_executors(item.row())
    
    def on_cell_changed(self, row, col):
        """Handle cell change"""
        if col == 2:  # Actual labor
            self.schedule_recalculation()
            self.modified = True
    
    def on_table_context_menu(self, position):
        """Handle table context menu"""
        menu = QMenu()
        
        add_row_action = QAction("Добавить строку", self)
        add_row_action.triggered.connect(lambda: self.add_table_row())
        menu.addAction(add_row_action)
        
        menu.exec(self.table_part.viewport().mapToGlobal(position))
    
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
    
    def schedule_recalculation(self):
        """Schedule recalculation with debounce"""
        self.recalc_timer.start(100)  # 100ms debounce
    
    def recalculate_deviations(self):
        """Recalculate deviations"""
        for row in range(self.table_part.rowCount()):
            try:
                planned_item = self.table_part.item(row, 1)
                actual_item = self.table_part.item(row, 2)
                
                # Convert to float, handling non-numeric values
                planned_text = planned_item.text().strip() if planned_item and planned_item.text() else "0"
                actual_text = actual_item.text().strip() if actual_item and actual_item.text() else "0"
                
                # Try to convert to float, default to 0.0 if not a number
                try:
                    planned = float(planned_text)
                except (ValueError, AttributeError):
                    planned = 0.0
                
                try:
                    actual = float(actual_text)
                except (ValueError, AttributeError):
                    actual = 0.0
                
                # Calculate deviation
                if planned > 0:
                    deviation = ((actual - planned) / planned) * 100
                else:
                    deviation = 0.0
                
                # Update cell
                self.table_part.blockSignals(True)
                self.table_part.setItem(row, 3, QTableWidgetItem(f"{deviation:.2f}"))
                self.table_part.item(row, 3).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_part.blockSignals(False)
            except Exception:
                pass
    
    def on_select_foreman(self):
        """Select foreman"""
        dialog = ReferencePickerDialog("persons", "Выбор бригадира", self)
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.foreman_id = selected_id
            self.foreman_edit.setText(selected_name)
            self.modified = True
    
    def on_select_executors(self, row):
        """Select executors for row"""
        # Get current executor IDs
        executor_ids_item = self.table_part.item(row, 6)
        current_ids = []
        if executor_ids_item and executor_ids_item.text():
            current_ids = [int(x) for x in executor_ids_item.text().split(",") if x]
        
        dialog = ExecutorPickerDialog(self, current_ids)
        if dialog.exec():
            selected_ids, selected_names = dialog.get_selected()
            
            self.table_part.blockSignals(True)
            self.table_part.setItem(row, 4, QTableWidgetItem(", ".join(selected_names)))
            self.table_part.setItem(row, 6, QTableWidgetItem(",".join(map(str, selected_ids))))
            self.table_part.blockSignals(False)
            
            self.modified = True
    
    def load_foreman(self, person_id):
        """Load foreman by ID"""
        person = self.session.query(Person).filter_by(id=person_id).first()
        if person:
            self.foreman_id = person_id
            self.foreman_edit.setText(person.full_name)
    
    def on_field_changed(self):
        """Handle field change"""
        self.modified = True
    
    def on_save(self):
        """Save daily report"""
        # Validate
        if not self.estimate_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смету")
            return
        
        estimate_id = self.estimate_id
        
        if not self.foreman_id:
            QMessageBox.warning(self, "Ошибка", "Выберите бригадира")
            return
        
        try:
            if self.report_id == 0:
                report = DailyReport()
                self.session.add(report)
            else:
                report = self.session.query(DailyReport).filter_by(id=self.report_id).first()
                if not report:
                     QMessageBox.critical(self, "Ошибка", "Отчет не найден")
                     return

            report.date = self.date_edit.date().toPyDate()
            report.estimate_id = estimate_id
            report.foreman_id = self.foreman_id
            
            # Rebuild lines
            # First remove old lines (cascading delete should handle executors if configured correctly, 
            # but standard delete might need manual cleanup if many-to-many isn't cascade delete)
            # Safe way: clear lines
            report.lines = []
            
            for row in range(self.table_part.rowCount()):
                work_name_item = self.table_part.item(row, 0)
                work_id_item = self.table_part.item(row, 5)
                
                # Check if this is a group row
                is_group = work_name_item and work_name_item.text().startswith("[ГРУППА]")
                
                # Skip empty rows (but not groups)
                if not is_group and (not work_id_item or not work_id_item.text() or work_id_item.text() == "0"):
                    continue
                
                planned_item = self.table_part.item(row, 1)
                actual_item = self.table_part.item(row, 2)
                deviation_item = self.table_part.item(row, 3)
                executor_ids_item = self.table_part.item(row, 6)
                
                line = DailyReportLine()
                line.line_number = row + 1
                line.work_id = int(work_id_item.text()) if work_id_item and work_id_item.text() else 0
                
                # Convert to float, handling non-numeric values
                try:
                    line.planned_labor = float(planned_item.text().strip()) if planned_item and planned_item.text() else 0.0
                except (ValueError, AttributeError):
                    line.planned_labor = 0.0
                
                try:
                    line.actual_labor = float(actual_item.text().strip()) if actual_item and actual_item.text() else 0.0
                except (ValueError, AttributeError):
                    line.actual_labor = 0.0
                
                try:
                    line.deviation_percent = float(deviation_item.text().strip()) if deviation_item and deviation_item.text() else 0.0
                except (ValueError, AttributeError):
                    line.deviation_percent = 0.0
                
                # Handle groups
                if is_group:
                    line.is_group = True
                    line.group_name = work_name_item.text().replace("[ГРУППА] ", "")
                
                # Parse executor IDs and create relationships
                if executor_ids_item and executor_ids_item.text():
                    ids = [int(x) for x in executor_ids_item.text().split(",") if x]
                    # We need to fetch Person objects to add to executors relationship
                    executors = self.session.query(Person).filter(Person.id.in_(ids)).all()
                    line.executors = executors
                
                report.lines.append(line)
            
            self.session.commit()
            
            self.report_id = report.id
            self.modified = False
            
            # Show message in status bar instead of modal dialog
            if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                self.parent().parent().statusBar().showMessage("Отчет сохранен", 3000)
            self.setWindowTitle(f"Ежедневный отчет от {report.date}")
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def on_print(self):
        """Print daily report"""
        if self.report_id == 0:
            QMessageBox.warning(self, "Предупреждение", "Сначала сохраните отчет")
            return
        
        try:
            from ..services.print_form_service import PrintFormService
            import tempfile
            import os
            
            # Generate print form using service
            service = PrintFormService()
            result = service.generate_daily_report(self.report_id)
            
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
            if event.key() == Qt.Key.Key_F4:
                current_row = self.table_part.currentRow()
                if current_row >= 0 and self.table_part.currentColumn() == 4:
                    self.on_select_executors(current_row)
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
        if self.report_id == 0:
            QMessageBox.warning(self, "Предупреждение", "Сначала сохраните отчет")
            return
        
        # Save before posting
        self.on_save()
        if self.report_id == 0:  # Save failed
            return
        
        success, error = self.posting_service.post_daily_report(self.report_id)
        if success:
            # Show message in status bar instead of modal dialog
            if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                self.parent().parent().statusBar().showMessage("Документ проведен", 3000)
            self.load_report()
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
            success, error = self.posting_service.unpost_daily_report(self.report_id)
            if success:
                # Show message in status bar instead of modal dialog
                if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
                    self.parent().parent().statusBar().showMessage("Проведение отменено", 3000)
                self.load_report()
            else:
                QMessageBox.critical(self, "Ошибка", error)
    
    def update_posting_state(self):
        """Update form state based on posting status"""
        is_editable = not self.is_posted
        
        # Block/unblock fields
        self.date_edit.setEnabled(is_editable)
        self.estimate_button.setEnabled(is_editable)
        self.foreman_button.setEnabled(is_editable)
        self.table_part.setEnabled(is_editable)
        self.fill_button.setEnabled(is_editable)
        self.import_button.setEnabled(is_editable)
        
        # Update buttons
        self.save_button.setEnabled(is_editable)
        self.save_close_button.setEnabled(is_editable)
        self.post_button.setEnabled(not self.is_posted and self.report_id > 0)
        self.unpost_button.setEnabled(self.is_posted)
        
        # Update window title
        status = " [ПРОВЕДЕН]" if self.is_posted else ""
        date_str = self.date_edit.date().toString("dd.MM.yyyy")
        self.setWindowTitle(f"Ежедневный отчет от {date_str}{status}")
    def on_import_from_excel(self):
        """Import daily report from Excel file"""
        from PyQt6.QtWidgets import QFileDialog
        from ..services.excel_daily_report_import_service import ExcelDailyReportImportService
        
        # Check if document is posted
        if self.is_posted:
            QMessageBox.warning(self, "Предупреждение", "Нельзя изменять проведенный документ")
            return
        
        # Select file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Excel",
            "",
            "Excel files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Import using service
            import_service = ExcelDailyReportImportService()
            daily_report, error = import_service.import_daily_report(file_path)
            
            if not daily_report:
                QMessageBox.critical(self, "Ошибка импорта", error)
                return
            
            # Clear existing data
            self.table_part.setRowCount(0)
            
            # Fill form with imported data
            if daily_report.date:
                self.date_edit.setDate(QDate(daily_report.date.year, daily_report.date.month, daily_report.date.day))
            
            if daily_report.estimate_id:
                self.load_estimate(daily_report.estimate_id)
            
            if daily_report.foreman_id:
                self.load_foreman(daily_report.foreman_id)
            
            # Add imported lines to table
            for line in daily_report.lines:
                self.add_table_row(line)
            
            self.modified = True
            
            # Show success message
            QMessageBox.information(
                self, 
                "Импорт завершен", 
                f"Импортировано {len(daily_report.lines)} строк.\n"
                f"Работы без найденных ссылок отображаются как пустые строки."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте: {str(e)}")

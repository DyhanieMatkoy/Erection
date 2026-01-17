"""Work execution report form"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QDateEdit, QComboBox, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository
from ..services.auth_service import AuthService
from ..data.models.sqlalchemy_models import Object, Estimate, Work, Person


class WorkExecutionReportForm(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.register_repo = WorkExecutionRegisterRepository()
        self.auth_service = AuthService(self.session)
        self.setup_ui()
        self.setWindowTitle("Отчет: Выполнение работ")
        self.resize(1200, 700)
        
        # Ensure session is closed when widget is destroyed
        self.destroyed.connect(lambda: self.session.close())
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Parameters section
        params_group = QGroupBox("Параметры отчета")
        params_layout = QFormLayout()
        
        # Period
        period_layout = QHBoxLayout()
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd.MM.yyyy")
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        period_layout.addWidget(QLabel("с"))
        period_layout.addWidget(self.date_start)
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd.MM.yyyy")
        self.date_end.setDate(QDate.currentDate())
        period_layout.addWidget(QLabel("по"))
        period_layout.addWidget(self.date_end)
        period_layout.addStretch()
        params_layout.addRow("Период:", period_layout)
        
        # Object filter
        self.object_combo = QComboBox()
        self.object_combo.addItem("Все объекты", 0)
        self.load_objects()
        params_layout.addRow("Объект:", self.object_combo)
        
        # Estimate filter
        self.estimate_combo = QComboBox()
        self.estimate_combo.addItem("Все сметы", 0)
        self.load_estimates()
        params_layout.addRow("Смета:", self.estimate_combo)
        
        # Work filter
        self.work_combo = QComboBox()
        self.work_combo.addItem("Все работы", 0)
        self.load_works()
        params_layout.addRow("Работа:", self.work_combo)
        
        # Executor filter (only show for non-foremen and non-employees)
        if not (self.auth_service.is_foreman() or self.auth_service.is_employee()):
            self.executor_combo = QComboBox()
            self.executor_combo.addItem("Все исполнители", 0)
            self.load_executors()
            params_layout.addRow("Исполнитель:", self.executor_combo)
        
        # Grouping 1
        self.grouping1_combo = QComboBox()
        self.grouping1_combo.addItem("Без группировки", "")
        self.grouping1_combo.addItem("По объектам", "object")
        self.grouping1_combo.addItem("По сметам", "estimate")
        self.grouping1_combo.addItem("По работам", "work")
        self.grouping1_combo.addItem("По датам", "period")
        self.grouping1_combo.setCurrentIndex(2)  # По сметам по умолчанию
        params_layout.addRow("Группировка 1:", self.grouping1_combo)
        
        # Grouping 2
        self.grouping2_combo = QComboBox()
        self.grouping2_combo.addItem("Без группировки", "")
        self.grouping2_combo.addItem("По объектам", "object")
        self.grouping2_combo.addItem("По сметам", "estimate")
        self.grouping2_combo.addItem("По работам", "work")
        self.grouping2_combo.addItem("По датам", "period")
        self.grouping2_combo.setCurrentIndex(3)  # По работам по умолчанию
        params_layout.addRow("Группировка 2:", self.grouping2_combo)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Сформировать")
        self.generate_button.clicked.connect(self.generate_report)
        button_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Экспорт в Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        self.export_brigade_button = QPushButton("Сдельная форма по бригаде")
        self.export_brigade_button.clicked.connect(self.export_brigade_piecework)
        self.export_brigade_button.setEnabled(False)
        button_layout.addWidget(self.export_brigade_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(8)
        self.table_view.setHorizontalHeaderLabels([
            "Группировка", "План кол-во", "Факт кол-во", "Остаток кол-во",
            "План сумма", "Факт сумма", "Остаток сумма", "% выполнения"
        ])
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table_view)
        
        self.setLayout(layout)
    
    def load_objects(self):
        """Load objects for filter"""
        try:
            objects = self.session.query(Object).filter(Object.marked_for_deletion == False).order_by(Object.name).all()
            for obj in objects:
                self.object_combo.addItem(obj.name, obj.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить объекты: {e}")
    
    def load_estimates(self):
        """Load estimates for filter"""
        try:
            estimates = self.session.query(Estimate).filter(Estimate.marked_for_deletion == False).order_by(Estimate.date.desc(), Estimate.number).all()
            for est in estimates:
                display = f"{est.number} от {est.date}"
                self.estimate_combo.addItem(display, est.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сметы: {e}")
    
    def load_works(self):
        """Load works for filter"""
        try:
            works = self.session.query(Work).filter(Work.marked_for_deletion == False).order_by(Work.name).all()
            for work in works:
                self.work_combo.addItem(work.name, work.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить виды работ: {e}")
    
    def load_executors(self):
        """Load executors for filter"""
        try:
            # Filter persons who are executors (maybe add role check if needed, but for now showing all persons)
            persons = self.session.query(Person).filter(Person.marked_for_deletion == False).order_by(Person.full_name).all()
            for person in persons:
                self.executor_combo.addItem(person.full_name, person.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить исполнителей: {e}")
    
    def generate_report(self):
        """Generate report"""
        # Get parameters
        period_start = self.date_start.date().toString("yyyy-MM-dd")
        period_end = self.date_end.date().toString("yyyy-MM-dd")
        
        filters = {}
        if self.object_combo.currentData() > 0:
            filters['object_id'] = self.object_combo.currentData()
        if self.estimate_combo.currentData() > 0:
            filters['estimate_id'] = self.estimate_combo.currentData()
        if self.work_combo.currentData() > 0:
            filters['work_id'] = self.work_combo.currentData()
        
        # Apply permission-based filtering for foremen and employees
        if self.auth_service.is_foreman() or self.auth_service.is_employee():
            person_id = self.auth_service.current_person_id()
            if person_id:
                filters['executor_id'] = person_id
        elif hasattr(self, 'executor_combo') and self.executor_combo.currentData() > 0:
            filters['executor_id'] = self.executor_combo.currentData()
        
        # Build grouping list
        grouping = []
        grouping1_key = self.grouping1_combo.currentData()
        grouping2_key = self.grouping2_combo.currentData()
        
        if grouping1_key:
            grouping.append(grouping1_key)
        if grouping2_key and grouping2_key != grouping1_key:
            grouping.append(grouping2_key)
        
        # Validate grouping
        if grouping1_key == grouping2_key and grouping1_key:
            QMessageBox.warning(self, "Предупреждение", 
                              "Группировка 1 и Группировка 2 не могут быть одинаковыми")
            return
        
        # Get data from register
        try:
            data = self.register_repo.get_turnovers(period_start, period_end, filters, grouping)
            
            # Build hierarchical structure if we have 2 groupings
            if len(grouping) == 2:
                self._fill_table_hierarchical(data, grouping)
            else:
                self._fill_table_flat(data, grouping)
            
            self.export_button.setEnabled(True)
            self.export_brigade_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при формировании отчета: {str(e)}")
    
    def _fill_table_flat(self, data: list, grouping: list):
        """Fill table with flat data (no hierarchy or single grouping)"""
        self.table_view.setRowCount(len(data))
        
        grouping_key = grouping[0] if grouping else None
        
        for row_idx, row in enumerate(data):
            # Determine group name
            group_name = self._get_group_name(row, grouping_key)
            
            plan_qty = row.get('quantity_income', 0)
            fact_qty = row.get('quantity_expense', 0)
            balance_qty = plan_qty - fact_qty
            
            plan_sum = row.get('sum_income', 0)
            fact_sum = row.get('sum_expense', 0)
            balance_sum = plan_sum - fact_sum
            
            percent = (fact_qty / plan_qty * 100) if plan_qty > 0 else 0
            
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(group_name))
            self.table_view.setItem(row_idx, 1, QTableWidgetItem(f"{plan_qty:.2f}"))
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(f"{fact_qty:.2f}"))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(f"{balance_qty:.2f}"))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(f"{plan_sum:.2f}"))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(f"{fact_sum:.2f}"))
            self.table_view.setItem(row_idx, 6, QTableWidgetItem(f"{balance_sum:.2f}"))
            self.table_view.setItem(row_idx, 7, QTableWidgetItem(f"{percent:.1f}%"))
    
    def _fill_table_hierarchical(self, data: list, grouping: list):
        """Fill table with hierarchical data (2 levels of grouping)"""
        from PyQt6.QtGui import QFont, QBrush, QColor
        
        # Group data by first level
        grouped_data = {}
        for row in data:
            key1 = self._get_group_key(row, grouping[0])
            if key1 not in grouped_data:
                grouped_data[key1] = {
                    'name': self._get_group_name(row, grouping[0]),
                    'rows': [],
                    'totals': {
                        'quantity_income': 0,
                        'quantity_expense': 0,
                        'sum_income': 0,
                        'sum_expense': 0
                    }
                }
            grouped_data[key1]['rows'].append(row)
            grouped_data[key1]['totals']['quantity_income'] += row.get('quantity_income', 0)
            grouped_data[key1]['totals']['quantity_expense'] += row.get('quantity_expense', 0)
            grouped_data[key1]['totals']['sum_income'] += row.get('sum_income', 0)
            grouped_data[key1]['totals']['sum_expense'] += row.get('sum_expense', 0)
        
        # Calculate total rows needed
        total_rows = 0
        for group in grouped_data.values():
            total_rows += 1  # Group header
            total_rows += len(group['rows'])  # Detail rows
        
        self.table_view.setRowCount(total_rows)
        
        # Fill table
        current_row = 0
        for key1 in sorted(grouped_data.keys()):
            group = grouped_data[key1]
            
            # Group header row
            totals = group['totals']
            plan_qty = totals['quantity_income']
            fact_qty = totals['quantity_expense']
            balance_qty = plan_qty - fact_qty
            plan_sum = totals['sum_income']
            fact_sum = totals['sum_expense']
            balance_sum = plan_sum - fact_sum
            percent = (fact_qty / plan_qty * 100) if plan_qty > 0 else 0
            
            # Create bold font for group headers
            bold_font = QFont()
            bold_font.setBold(True)
            
            # Create light blue background for group headers
            header_brush = QBrush(QColor(230, 240, 255))
            
            header_item = QTableWidgetItem(group['name'])
            header_item.setFont(bold_font)
            header_item.setBackground(header_brush)
            self.table_view.setItem(current_row, 0, header_item)
            
            for col_idx, value in enumerate([
                f"{plan_qty:.2f}",
                f"{fact_qty:.2f}",
                f"{balance_qty:.2f}",
                f"{plan_sum:.2f}",
                f"{fact_sum:.2f}",
                f"{balance_sum:.2f}",
                f"{percent:.1f}%"
            ], 1):
                item = QTableWidgetItem(value)
                item.setFont(bold_font)
                item.setBackground(header_brush)
                self.table_view.setItem(current_row, col_idx, item)
            
            current_row += 1
            
            # Detail rows
            for row in group['rows']:
                group_name = "  " + self._get_group_name(row, grouping[1])  # Indent for hierarchy
                
                plan_qty = row.get('quantity_income', 0)
                fact_qty = row.get('quantity_expense', 0)
                balance_qty = plan_qty - fact_qty
                
                plan_sum = row.get('sum_income', 0)
                fact_sum = row.get('sum_expense', 0)
                balance_sum = plan_sum - fact_sum
                
                percent = (fact_qty / plan_qty * 100) if plan_qty > 0 else 0
                
                self.table_view.setItem(current_row, 0, QTableWidgetItem(group_name))
                self.table_view.setItem(current_row, 1, QTableWidgetItem(f"{plan_qty:.2f}"))
                self.table_view.setItem(current_row, 2, QTableWidgetItem(f"{fact_qty:.2f}"))
                self.table_view.setItem(current_row, 3, QTableWidgetItem(f"{balance_qty:.2f}"))
                self.table_view.setItem(current_row, 4, QTableWidgetItem(f"{plan_sum:.2f}"))
                self.table_view.setItem(current_row, 5, QTableWidgetItem(f"{fact_sum:.2f}"))
                self.table_view.setItem(current_row, 6, QTableWidgetItem(f"{balance_sum:.2f}"))
                self.table_view.setItem(current_row, 7, QTableWidgetItem(f"{percent:.1f}%"))
                
                current_row += 1
    
    def _get_group_key(self, row: dict, grouping_key: str) -> str:
        """Get grouping key for a row"""
        if grouping_key == 'object':
            return f"obj_{row.get('object_id', 0)}"
        elif grouping_key == 'estimate':
            return f"est_{row.get('estimate_id', 0)}"
        elif grouping_key == 'work':
            return f"work_{row.get('work_id', 0)}"
        elif grouping_key == 'period':
            return f"period_{row.get('period', '')}"
        return "unknown"
    
    def _get_group_name(self, row: dict, grouping_key: str) -> str:
        """Get display name for a grouping"""
        if grouping_key == 'object':
            return row.get('object_name', '')
        elif grouping_key == 'estimate':
            return row.get('estimate_number', '')
        elif grouping_key == 'work':
            return row.get('work_name', '')
        elif grouping_key == 'period':
            return str(row.get('period', ''))
        return ''
    
    def export_to_excel(self):
        """Export report to Excel"""
        QMessageBox.information(self, "Экспорт", "Функция экспорта будет реализована позже")
    
    def export_brigade_piecework(self):
        """Export brigade piecework report to Excel"""
        from PyQt6.QtWidgets import QFileDialog
        from ..services.excel_brigade_piecework_report import ExcelBrigadePieceworkReport
        
        try:
            # Get parameters
            period_start = self.date_start.date().toString("yyyy-MM-dd")
            period_end = self.date_end.date().toString("yyyy-MM-dd")
            
            filters = {}
            if self.object_combo.currentData() > 0:
                filters['object_id'] = self.object_combo.currentData()
            if self.estimate_combo.currentData() > 0:
                filters['estimate_id'] = self.estimate_combo.currentData()
            if self.work_combo.currentData() > 0:
                filters['work_id'] = self.work_combo.currentData()
            
            # Apply permission-based filtering for foremen and employees
            if self.auth_service.is_foreman() or self.auth_service.is_employee():
                person_id = self.auth_service.current_person_id()
                if person_id:
                    filters['executor_id'] = person_id
            elif hasattr(self, 'executor_combo') and self.executor_combo.currentData() > 0:
                filters['executor_id'] = self.executor_combo.currentData()
            
            # Generate report
            generator = ExcelBrigadePieceworkReport()
            excel_bytes = generator.generate(period_start, period_end, filters)
            
            if not excel_bytes:
                QMessageBox.warning(self, "Предупреждение", "Нет данных для формирования отчета")
                return
            
            # Save file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                f"Сдельная_форма_{period_start}_{period_end}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(excel_bytes)
                
                QMessageBox.information(self, "Успех", f"Отчет сохранен: {file_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при формировании отчета: {str(e)}")
    
    def on_row_double_clicked(self):
        """Handle row double click - show detail"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        # Get grouping parameters
        grouping1_key = self.grouping1_combo.currentData()
        grouping2_key = self.grouping2_combo.currentData()
        
        # Get filters
        filters = {}
        if self.object_combo.currentData() > 0:
            filters['object_id'] = self.object_combo.currentData()
        if self.estimate_combo.currentData() > 0:
            filters['estimate_id'] = self.estimate_combo.currentData()
        if self.work_combo.currentData() > 0:
            filters['work_id'] = self.work_combo.currentData()
        
        # Get period
        period_start = self.date_start.date().toString("yyyy-MM-dd")
        period_end = self.date_end.date().toString("yyyy-MM-dd")
        
        # Show detail dialog
        from .work_execution_detail_dialog import WorkExecutionDetailDialog
        dialog = WorkExecutionDetailDialog(
            period_start, period_end, filters, grouping1_key, self
        )
        dialog.exec()

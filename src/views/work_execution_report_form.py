"""Work execution report form"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QDateEdit, QComboBox, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from ..data.database_manager import DatabaseManager
from ..data.repositories.work_execution_register_repository import WorkExecutionRegisterRepository


class WorkExecutionReportForm(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager().get_connection()
        self.register_repo = WorkExecutionRegisterRepository()
        self.setup_ui()
        self.setWindowTitle("Отчет: Выполнение работ")
        self.resize(1200, 700)
    
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
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        period_layout.addWidget(QLabel("с"))
        period_layout.addWidget(self.date_start)
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
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
        
        # Grouping
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItem("По объектам", "object")
        self.grouping_combo.addItem("По сметам", "estimate")
        self.grouping_combo.addItem("По работам", "work")
        self.grouping_combo.addItem("По датам", "period")
        params_layout.addRow("Группировка:", self.grouping_combo)
        
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
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, name
            FROM objects
            WHERE marked_for_deletion = 0
            ORDER BY name
        """)
        
        for row in cursor.fetchall():
            self.object_combo.addItem(row['name'], row['id'])
    
    def load_estimates(self):
        """Load estimates for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, number, date
            FROM estimates
            ORDER BY date DESC, number
        """)
        
        for row in cursor.fetchall():
            display = f"{row['number']} от {row['date']}"
            self.estimate_combo.addItem(display, row['id'])
    
    def load_works(self):
        """Load works for filter"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, name
            FROM works
            WHERE marked_for_deletion = 0
            ORDER BY name
        """)
        
        for row in cursor.fetchall():
            self.work_combo.addItem(row['name'], row['id'])
    
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
        
        grouping_key = self.grouping_combo.currentData()
        grouping = [grouping_key]
        
        # Get data from register
        try:
            data = self.register_repo.get_turnovers(period_start, period_end, filters, grouping)
            
            # Fill table
            self.table_view.setRowCount(len(data))
            
            for row_idx, row in enumerate(data):
                # Determine group name
                if grouping_key == 'object':
                    group_name = row.get('object_name', '')
                elif grouping_key == 'estimate':
                    group_name = row.get('estimate_number', '')
                elif grouping_key == 'work':
                    group_name = row.get('work_name', '')
                elif grouping_key == 'period':
                    group_name = str(row.get('period', ''))
                else:
                    group_name = ''
                
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
            
            self.export_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при формировании отчета: {str(e)}")
    
    def export_to_excel(self):
        """Export report to Excel"""
        QMessageBox.information(self, "Экспорт", "Функция экспорта будет реализована позже")
    
    def on_row_double_clicked(self):
        """Handle row double click - show detail"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        # Get grouping parameters
        grouping_key = self.grouping_combo.currentData()
        
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
            period_start, period_end, filters, grouping_key, self
        )
        dialog.exec()

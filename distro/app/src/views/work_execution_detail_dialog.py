"""Work execution detail dialog"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from ..data.database_manager import DatabaseManager


class WorkExecutionDetailDialog(QDialog):
    def __init__(self, period_start, period_end, filters, grouping_key, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager().get_connection()
        self.period_start = period_start
        self.period_end = period_end
        self.filters = filters
        self.grouping_key = grouping_key
        
        self.setWindowTitle("Детализация выполнения работ")
        self.resize(900, 600)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Info label
        info_text = f"Период: {self.period_start} - {self.period_end}"
        layout.addWidget(QLabel(info_text))
        
        # Table
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(7)
        self.table_view.setHorizontalHeaderLabels([
            "Тип документа", "Номер/Дата", "Дата движения", 
            "Приход кол-во", "Расход кол-во", "Приход сумма", "Расход сумма"
        ])
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_data(self):
        """Load detail data"""
        cursor = self.db.cursor()
        
        # Build WHERE clause
        where_clauses = ['r.period >= ?', 'r.period <= ?']
        params = [self.period_start, self.period_end]
        
        if self.filters:
            if 'object_id' in self.filters:
                where_clauses.append('r.object_id = ?')
                params.append(self.filters['object_id'])
            
            if 'estimate_id' in self.filters:
                where_clauses.append('r.estimate_id = ?')
                params.append(self.filters['estimate_id'])
            
            if 'work_id' in self.filters:
                where_clauses.append('r.work_id = ?')
                params.append(self.filters['work_id'])
        
        where_clause = ' AND '.join(where_clauses)
        
        # Query movements with document info
        query = f"""
            SELECT 
                r.recorder_type,
                r.recorder_id,
                r.period,
                r.quantity_income,
                r.quantity_expense,
                r.sum_income,
                r.sum_expense,
                CASE 
                    WHEN r.recorder_type = 'estimate' THEN e.number
                    WHEN r.recorder_type = 'daily_report' THEN dr.date
                END as doc_number
            FROM work_execution_register r
            LEFT JOIN estimates e ON r.recorder_type = 'estimate' AND r.recorder_id = e.id
            LEFT JOIN daily_reports dr ON r.recorder_type = 'daily_report' AND r.recorder_id = dr.id
            WHERE {where_clause}
            ORDER BY r.period, r.recorder_type, r.recorder_id
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        self.table_view.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            doc_type = "Смета" if row['recorder_type'] == 'estimate' else "Ежедневный отчет"
            
            self.table_view.setItem(row_idx, 0, QTableWidgetItem(doc_type))
            self.table_view.setItem(row_idx, 1, QTableWidgetItem(str(row['doc_number'] or "")))
            self.table_view.setItem(row_idx, 2, QTableWidgetItem(str(row['period'])))
            self.table_view.setItem(row_idx, 3, QTableWidgetItem(f"{row['quantity_income']:.2f}"))
            self.table_view.setItem(row_idx, 4, QTableWidgetItem(f"{row['quantity_expense']:.2f}"))
            self.table_view.setItem(row_idx, 5, QTableWidgetItem(f"{row['sum_income']:.2f}"))
            self.table_view.setItem(row_idx, 6, QTableWidgetItem(f"{row['sum_expense']:.2f}"))
            
            # Store document info in first column
            item = self.table_view.item(row_idx, 0)
            item.setData(Qt.ItemDataRole.UserRole, {
                'recorder_type': row['recorder_type'],
                'recorder_id': row['recorder_id']
            })
    
    def on_row_double_clicked(self):
        """Handle row double click - open document"""
        current_row = self.table_view.currentRow()
        if current_row < 0:
            return
        
        item = self.table_view.item(current_row, 0)
        if not item:
            return
        
        doc_info = item.data(Qt.ItemDataRole.UserRole)
        if not doc_info:
            return
        
        recorder_type = doc_info['recorder_type']
        recorder_id = doc_info['recorder_id']
        
        try:
            if recorder_type == 'estimate':
                from .estimate_document_form import EstimateDocumentForm
                form = EstimateDocumentForm(recorder_id)
                form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                form.show()
            elif recorder_type == 'daily_report':
                from .daily_report_document_form import DailyReportDocumentForm
                form = DailyReportDocumentForm(recorder_id)
                form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                form.show()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть документ: {str(e)}")

"""Estimate line picker dialog"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from ..data.database_manager import DatabaseManager


class EstimateLinePickerDialog(QDialog):
    """Dialog for selecting estimate lines"""
    def __init__(self, estimate_id: int, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager().get_connection()
        self.estimate_id = estimate_id
        self.selected_line_ids = []
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Выбор строк сметы")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Выберите строки для переноса в ежедневный отчет:")
        layout.addWidget(info_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "✓", "Работа", "Количество", "Ед. изм.", "Цена", "Плановые трудозатраты", "id"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(6, True)  # Hide id column
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Выбрать все")
        self.select_all_button.clicked.connect(self.on_select_all)
        button_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Снять все")
        self.deselect_all_button.clicked.connect(self.on_deselect_all)
        button_layout.addWidget(self.deselect_all_button)
        
        button_layout.addStretch()
        
        self.ok_button = QPushButton("Выбрать")
        self.ok_button.clicked.connect(self.on_ok)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Load estimate lines"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT el.id, el.work_id, el.quantity, el.unit, el.price, el.planned_labor,
                   el.is_group, el.group_name, w.name as work_name
            FROM estimate_lines el
            LEFT JOIN works w ON el.work_id = w.id
            WHERE el.estimate_id = ?
            ORDER BY el.line_number
        """, (self.estimate_id,))
        
        self.table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, checkbox_item)
            
            # Work name or group name
            if row_data['is_group']:
                work_display = f"[ГРУППА] {row_data['group_name']}"
            else:
                work_display = row_data['work_name'] or ""
            
            self.table.setItem(row, 1, QTableWidgetItem(work_display))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data['quantity']) if not row_data['is_group'] else ""))
            self.table.setItem(row, 3, QTableWidgetItem(row_data['unit'] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(row_data['price']) if not row_data['is_group'] else ""))
            self.table.setItem(row, 5, QTableWidgetItem(f"{row_data['planned_labor']:.2f}" if not row_data['is_group'] else ""))
            self.table.setItem(row, 6, QTableWidgetItem(str(row_data['id'])))
            
            # Make all cells read-only except checkbox
            for col in range(1, 7):
                if self.table.item(row, col):
                    self.table.item(row, col).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    
    def on_select_all(self):
        """Select all lines"""
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked)
    
    def on_deselect_all(self):
        """Deselect all lines"""
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
    
    def on_ok(self):
        """Collect selected line IDs and accept"""
        self.selected_line_ids = []
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                id_item = self.table.item(row, 6)
                if id_item:
                    self.selected_line_ids.append(int(id_item.text()))
        
        self.accept()
    
    def get_selected_line_ids(self):
        """Get selected line IDs"""
        return self.selected_line_ids

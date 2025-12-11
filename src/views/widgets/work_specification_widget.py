from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

class WorkSpecificationTable(QTableWidget):
    """Table widget for displaying and editing work specifications"""
    
    entryChanged = pyqtSignal(int, str, float) # row, column_name, new_value
    specSelectionChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.itemChanged.connect(self.on_item_changed)
        self.itemSelectionChanged.connect(self.specSelectionChanged.emit)
        self._updating = False
        
    def setup_table(self):
        columns = [
            "Тип",           # 0: Component Type
            "Наименование",  # 1: Component Name
            "Ед.изм.",       # 2: Unit
            "Норма расхода", # 3: Consumption Rate
            "Цена",          # 4: Unit Price
            "Стоимость"      # 5: Total Cost
        ]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name stretches
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
    def load_data(self, specifications):
        """
        Load specifications into table.
        specifications: List of dicts from repository
        """
        self._updating = True
        self.setRowCount(0)
        self.setRowCount(len(specifications))
        
        for row, spec in enumerate(specifications):
            # Type
            self.setItem(row, 0, QTableWidgetItem(spec.get('component_type', '')))
            
            # Name
            self.setItem(row, 1, QTableWidgetItem(spec.get('component_name', '')))
            
            # Unit
            unit_name = spec.get('unit_name')
            self.setItem(row, 2, QTableWidgetItem(unit_name if unit_name else ""))
            
            # Consumption Rate (Editable)
            rate = spec.get('consumption_rate', 0)
            rate_item = QTableWidgetItem(f"{rate:.6f}")
            rate_item.setFlags(rate_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 3, rate_item)
            
            # Unit Price (Editable)
            price = spec.get('unit_price', 0)
            price_item = QTableWidgetItem(f"{price:.2f}")
            price_item.setFlags(price_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 4, price_item)
            
            # Total Cost (Calculated)
            total = spec.get('total_cost', 0)
            # If total is None (e.g. newly created), calc it
            if total is None:
                total = float(rate) * float(price)
            
            total_item = QTableWidgetItem(f"{total:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Read only
            self.setItem(row, 5, total_item)
            
            # Store ID in first column user data
            self.item(row, 0).setData(Qt.ItemDataRole.UserRole, spec.get('id'))
            
            # Make non-editable columns read-only
            for col in [0, 1, 2, 5]:
                item = self.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
        self._updating = False

    def on_item_changed(self, item):
        if self._updating:
            return
            
        row = item.row()
        col = item.column()
        
        try:
            text = item.text().replace(',', '.')
            value = float(text)
            
            column_name = None
            if col == 3:
                column_name = 'consumption_rate'
            elif col == 4:
                column_name = 'unit_price'
                
            if column_name:
                self.entryChanged.emit(row, column_name, value)
                
                # Recalculate total locally for immediate feedback
                rate_item = self.item(row, 3)
                price_item = self.item(row, 4)
                if rate_item and price_item:
                    rate = float(rate_item.text().replace(',', '.'))
                    price = float(price_item.text().replace(',', '.'))
                    total = rate * price
                    
                    self._updating = True
                    self.item(row, 5).setText(f"{total:.2f}")
                    self._updating = False
                    
        except ValueError:
            pass # Invalid number

    def get_selected_id(self):
        current_row = self.currentRow()
        if current_row >= 0:
            return self.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        return None


class WorkSpecificationWidget(QWidget):
    """
    Widget for managing work specifications.
    Contains a toolbar and the specification table.
    """
    
    # Signals
    addRequested = pyqtSignal()
    editRequested = pyqtSignal(int) # spec_id
    deleteRequested = pyqtSignal(int) # spec_id
    copyRequested = pyqtSignal()
    importRequested = pyqtSignal()
    exportRequested = pyqtSignal()
    saveTemplateRequested = pyqtSignal()
    entryChanged = pyqtSignal(int, str, float) # row, column_name, new_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)
        
        # Add Actions
        self.action_add = QAction("Добавить", self)
        self.action_add.triggered.connect(self.addRequested.emit)
        self.toolbar.addAction(self.action_add)
        
        self.action_edit = QAction("Изменить", self)
        self.action_edit.triggered.connect(self.on_edit)
        self.toolbar.addAction(self.action_edit)
        
        self.action_delete = QAction("Удалить", self)
        self.action_delete.triggered.connect(self.on_delete)
        self.toolbar.addAction(self.action_delete)
        
        self.action_copy = QAction("Копировать из...", self)
        self.action_copy.triggered.connect(self.copyRequested.emit)
        self.toolbar.addAction(self.action_copy)
        
        self.toolbar.addSeparator()
        
        self.action_import = QAction("Импорт", self)
        self.action_import.triggered.connect(self.importRequested.emit)
        self.toolbar.addAction(self.action_import)
        
        self.action_export = QAction("Экспорт", self)
        self.action_export.triggered.connect(self.exportRequested.emit)
        self.toolbar.addAction(self.action_export)
        
        self.toolbar.addSeparator()
        
        self.action_save_template = QAction("Сохранить как шаблон", self)
        self.action_save_template.triggered.connect(self.saveTemplateRequested.emit)
        self.toolbar.addAction(self.action_save_template)
        
        # Table
        self.table = WorkSpecificationTable()
        self.table.specSelectionChanged.connect(self.update_actions)
        self.table.entryChanged.connect(self.entryChanged.emit)
        layout.addWidget(self.table)
        
        # Initial state
        self.update_actions()
        
    def load_data(self, specifications):
        self.table.load_data(specifications)
        
    def on_edit(self):
        spec_id = self.table.get_selected_id()
        if spec_id:
            self.editRequested.emit(spec_id)
            
    def on_delete(self):
        spec_id = self.table.get_selected_id()
        if spec_id:
            self.deleteRequested.emit(spec_id)
            
    def update_actions(self):
        has_selection = self.table.currentRow() >= 0
        self.action_edit.setEnabled(has_selection)
        self.action_delete.setEnabled(has_selection)

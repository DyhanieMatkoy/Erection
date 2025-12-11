
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal

class CostItemsTable(QTableWidget):
    quantityChanged = pyqtSignal(int, float) # row, new_quantity

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.itemChanged.connect(self.on_item_changed)
        self._updating = False
        
    def setup_table(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Код", "Наименование", "Ед.изм", "Цена", "Норма труда", "Количество"
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # We allow editing by default, but restrict flags in load_cost_items
        
    def load_cost_items(self, cost_items):
        """
        Load cost items into table.
        cost_items: List of (CostItem object, quantity) tuples
        """
        self._updating = True
        self.setRowCount(0)
        self.setRowCount(len(cost_items))
        for row, (cost_item, quantity) in enumerate(cost_items):
            self.setItem(row, 0, QTableWidgetItem(cost_item.code or ""))
            self.setItem(row, 1, QTableWidgetItem(cost_item.description or ""))
            
            # Try to get unit name, fallback to unit field
            unit_name = ""
            try:
                if hasattr(cost_item, 'unit_name') and cost_item.unit_name:
                     unit_name = cost_item.unit_name
                elif cost_item.unit:
                     unit_name = cost_item.unit
            except:
                unit_name = ""
                
            self.setItem(row, 2, QTableWidgetItem(unit_name))
            self.setItem(row, 3, QTableWidgetItem(f"{cost_item.price:.2f}"))
            self.setItem(row, 4, QTableWidgetItem(f"{cost_item.labor_coefficient:.2f}"))
            
            # Quantity (Editable)
            qty_item = QTableWidgetItem(f"{quantity:.4f}")
            qty_item.setFlags(qty_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 5, qty_item)
            
            # Make other columns read-only
            for col in [0, 1, 2, 3, 4]:
                item = self.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Store ID
            self.item(row, 0).setData(Qt.ItemDataRole.UserRole, cost_item.id)
            
        self._updating = False

    def on_item_changed(self, item):
        if self._updating:
            return
            
        if item.column() == 5: # Quantity column
            try:
                row = item.row()
                text = item.text().replace(',', '.')
                value = float(text)
                self.quantityChanged.emit(row, value)
            except ValueError:
                pass
            
    def get_selected_cost_item_id(self):
        current_row = self.currentRow()
        if current_row >= 0:
            return self.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        return None

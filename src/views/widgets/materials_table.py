
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

class MaterialsTable(QTableWidget):
    quantityChanged = pyqtSignal(int, float) # row, new_quantity
    addMaterialRequested = pyqtSignal()
    deleteMaterialRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.itemChanged.connect(self.on_item_changed)
        self._updating = False
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def setup_table(self):
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "Статья затрат", "Код", "Наименование", "Ед.изм", "Цена", "Количество", "Сумма"
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # We allow editing by default, but restrict flags in load_materials

    def load_materials(self, materials):
        """
        Load materials into table.
        materials: List of (Material object, quantity, CostItem object) tuples
        """
        self._updating = True
        self.setRowCount(0)
        self.setRowCount(len(materials))
        
        for row, (material, quantity, cost_item) in enumerate(materials):
            # Cost Item
            self.setItem(row, 0, QTableWidgetItem(cost_item.description or ""))
            # Code
            self.setItem(row, 1, QTableWidgetItem(material.code or ""))
            # Description
            self.setItem(row, 2, QTableWidgetItem(material.description or ""))
            # Unit
            unit_name = material.unit or ""
            self.setItem(row, 3, QTableWidgetItem(unit_name))
            # Price
            self.setItem(row, 4, QTableWidgetItem(f"{material.price:.2f}"))
            
            # Quantity (Editable)
            qty_item = QTableWidgetItem(f"{quantity:.4f}")
            qty_item.setFlags(qty_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 5, qty_item)
            
            # Total
            total = material.price * quantity
            self.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
            
            # Make other columns read-only
            for col in [0, 1, 2, 3, 4, 6]:
                item = self.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
            # Store ID in first column
            self.item(row, 0).setData(Qt.ItemDataRole.UserRole, material.id)
            
        self._updating = False

    def on_item_changed(self, item):
        if self._updating:
            return
            
        if item.column() == 5: # Quantity column
            try:
                row = item.row()
                text = item.text().replace(',', '.')
                value = float(text)
                
                # Emit signal
                self.quantityChanged.emit(row, value)
                
            except ValueError:
                pass

    def get_selected_material_id(self):
        current_row = self.currentRow()
        if current_row >= 0:
            return self.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        return None
    
    def show_context_menu(self, position):
        """Show context menu for materials"""
        menu = QMenu(self)
        
        # Add material action
        add_action = QAction("Добавить материал", self)
        add_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        add_action.triggered.connect(self.addMaterialRequested.emit)
        menu.addAction(add_action)
        
        # Delete material action (only if row is selected)
        current_row = self.currentRow()
        if current_row >= 0:
            menu.addSeparator()
            delete_action = QAction("Удалить материал", self)
            delete_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
            delete_action.triggered.connect(self.deleteMaterialRequested.emit)
            menu.addAction(delete_action)
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(position))

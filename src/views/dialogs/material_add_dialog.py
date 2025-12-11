
from PyQt6.QtWidgets import QDialog, QInputDialog
from .cost_item_selector_dialog import CostItemSelectorDialog
from .material_selector_dialog import MaterialSelectorDialog

class MaterialAddDialog(QDialog):
    def __init__(self, parent=None, work_id=0):
        super().__init__(parent)
        self.work_id = work_id
        self.selected_cost_item_id = None
        self.selected_material_id = None
        self.quantity = 0.0

    def exec(self):
        # Step 1: Select Cost Item
        # We pass self.parent() so the dialog is modal to the main window, not this invisible dialog
        parent = self.parent()
        
        # Allow selecting any cost item (filter_by_work=False) to enable adding new cost items via adding materials
        cost_item_dialog = CostItemSelectorDialog(parent, work_id=self.work_id, filter_by_work=False, current_id=self.selected_cost_item_id)
        if cost_item_dialog.exec() != QDialog.DialogCode.Accepted:
            return QDialog.DialogCode.Rejected
            
        self.selected_cost_item_id = cost_item_dialog.get_selected_cost_item_id()
        if not self.selected_cost_item_id:
            return QDialog.DialogCode.Rejected
        
        # Step 2: Select Material
        material_dialog = MaterialSelectorDialog(parent, current_id=self.selected_material_id)
        if material_dialog.exec() != QDialog.DialogCode.Accepted:
            return QDialog.DialogCode.Rejected
            
        self.selected_material_id = material_dialog.get_selected_material_id()
        if not self.selected_material_id:
            return QDialog.DialogCode.Rejected
        
        # Step 3: Quantity
        quantity, ok = QInputDialog.getDouble(
            parent,
            "Количество",
            "Введите количество на единицу работы:",
            value=1.0,
            min=0.0001,
            max=999999.999,
            decimals=4
        )
        
        if not ok:
            return QDialog.DialogCode.Rejected
            
        self.quantity = quantity
        return QDialog.DialogCode.Accepted

    def get_result(self):
        return (self.selected_cost_item_id, self.selected_material_id, self.quantity)

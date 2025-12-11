
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
                             QHeaderView, QTreeWidgetItemIterator)
from PyQt6.QtCore import Qt
from ...data.repositories.cost_item_repository import CostItemRepository
from ...data.repositories.cost_item_material_repository import CostItemMaterialRepository

class CostItemSelectorDialog(QDialog):
    def __init__(self, parent=None, work_id=None, filter_by_work=False):
        super().__init__(parent)
        self.work_id = work_id
        self.filter_by_work = filter_by_work
        self.repo = CostItemRepository()
        self.cim_repo = CostItemMaterialRepository()
        self.selected_cost_item_id = None
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Выбор статьи затрат")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Код или наименование...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Код", "Наименование", "Ед.изм", "Цена"])
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Выбрать")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        self.tree.clear()
        
        # Get all cost items
        all_items = self.repo.find_all()
        
        # If filtering by work, get cost items in work
        work_item_ids = set()
        if self.filter_by_work and self.work_id:
            associations = self.cim_repo.get_cost_items_for_work(self.work_id)
            # associations is list of (CostItem, quantity)
            work_item_ids = {item.id for item, _ in associations}
            
        # Build map and filter
        items_to_show = []
        items_map = {}
        
        for item in all_items:
            # item is a dict from find_all
            item_id = item['id']
            items_map[item_id] = item
            
            if self.filter_by_work and self.work_id:
                if item_id in work_item_ids:
                    items_to_show.append(item)
            else:
                items_to_show.append(item)
                
        # Group by parent
        items_by_parent = {}
        for item in items_to_show:
            parent_id = item['parent_id']
            # If we are filtering, and the parent is NOT in the list, 
            # we might want to show it at root level or handle it.
            # For now, let's treat them as roots if parent is missing from the filtered list.
            
            # However, if we filter by work, we just have a flat list of cost items used in work.
            # They might not form a tree.
            # But CostItemSelectorDialog is used in two contexts:
            # 1. Adding Cost Item to Work (filter_by_work=False) -> Show full tree
            # 2. Adding Material to Work (filter_by_work=True) -> Show cost items ALREADY in work.
            
            if self.filter_by_work:
                # Flat list might be better or just put them all at root
                parent_id = None 
            else:
                # Ensure parent exists in our map, otherwise treat as root
                # (unless it is actually None/0)
                if parent_id and parent_id not in items_map:
                    parent_id = None
                    
            if parent_id not in items_by_parent:
                items_by_parent[parent_id] = []
            items_by_parent[parent_id].append(item)
            
        # Add roots
        self._add_items_recursive(None, items_by_parent, self.tree.invisibleRootItem())
        self._add_items_recursive(0, items_by_parent, self.tree.invisibleRootItem())

    def _add_items_recursive(self, parent_id, items_by_parent, parent_widget):
        if parent_id not in items_by_parent:
            return
            
        for item in items_by_parent[parent_id]:
            tree_item = QTreeWidgetItem(parent_widget)
            tree_item.setText(0, item['code'] or "")
            tree_item.setText(1, item['description'] or "")
            tree_item.setText(2, item['unit_name'] or "")
            tree_item.setText(3, f"{item['price']:.2f}")
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item['id'])
            
            # Icon for folder
            if item['is_folder']:
                tree_item.setText(1, "📁 " + tree_item.text(1))
                
            self._add_items_recursive(item['id'], items_by_parent, tree_item)
            
        # Expand if root
        if parent_widget == self.tree.invisibleRootItem():
            self.tree.expandToDepth(0)

    def on_search(self, text):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if not text:
                item.setHidden(False)
            else:
                match = (text.lower() in item.text(0).lower() or 
                         text.lower() in item.text(1).lower())
                item.setHidden(not match)
                if match:
                    parent = item.parent()
                    while parent:
                        parent.setHidden(False)
                        parent.setExpanded(True)
                        parent = parent.parent()
            iterator += 1

    def on_item_double_clicked(self, item, column):
        self.accept()

    def accept(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        self.selected_cost_item_id = item.data(0, Qt.ItemDataRole.UserRole)
        super().accept()

    def get_selected_cost_item_id(self):
        return self.selected_cost_item_id

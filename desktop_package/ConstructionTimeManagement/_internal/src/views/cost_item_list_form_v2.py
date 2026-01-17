from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import CostItem
from src.views.cost_item_form import CostItemForm

class CostItemListFormV2(GenericListForm):
    """
    New Cost Item List Form using Generic List Architecture.
    Supports hierarchy (groups).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("cost_items", user_id, CostItem)
        self.setWindowTitle("Справочник: Элементы затрат")
        self.resize(1000, 600)
        
        self.current_parent_id = None
        self.opened_forms = []

        # Enable hierarchical navigation
        self.enable_hierarchical_navigation(True)

        # Configure columns
        self.configure_columns([
            {'id': 'code', 'name': 'Код', 'width': 100},
            {'id': 'description', 'name': 'Наименование', 'width': 400},
            {'id': 'unit', 'name': 'Ед. изм.', 'width': 80},
            {'id': 'price', 'name': 'Цена', 'width': 100},
            {'id': 'labor_coefficient', 'name': 'Коэфф.', 'width': 80},
            {'id': 'is_folder', 'name': 'Группа', 'width': 50, 'visible': False},
            {'id': 'parent_id', 'name': 'Parent', 'width': 50, 'visible': False}
        ])
        
        # Enable navigation in filter bar
        self.filter_bar.enable_navigation(True)
        
        # Initial filter for root items
        self.controller.set_filter('parent_id', None)
        
        # Connect signals
        self.open_document_requested.connect(self.handle_open_request)
        
        # Load initial data
        self.load_data()

    def on_navigation_up(self):
        """Handle navigation up from filter bar"""
        self.go_up()

    def handle_open_request(self, object_id: int):
        """Handle open request"""
        if object_id == 0:
            self.open_cost_item_form(0)
            return

        item_data = next((i for i in self.table.data_map if getattr(i, 'id', None) == object_id or (isinstance(i, dict) and i.get('id') == object_id)), None)
        
        if item_data:
            is_folder = getattr(item_data, 'is_folder', False)
            if is_folder:
                self.enter_group(object_id, getattr(item_data, 'description', ''))
            else:
                self.open_cost_item_form(object_id)

    def enter_group(self, group_id: int, group_name: str):
        """Drill down into group"""
        # Add current parent to navigation path
        if self.current_parent_id is not None:
            self.navigation_path.append(self.current_parent_id)
        elif len(self.navigation_path) == 0:
            # We're at root, add None to represent root
            self.navigation_path.append(None)
            
        self.current_parent_id = group_id
        self.controller.set_filter('parent_id', group_id)
        self.filter_bar.set_navigation_state(True, f"Группа: {group_name}")
        
        # Update keyboard context
        self.update_keyboard_context()

    def go_up(self):
        """Go up one level"""
        if not self.current_parent_id and len(self.navigation_path) == 0:
            return

        try:
            # Use navigation path if available
            if len(self.navigation_path) > 0:
                new_parent_id = self.navigation_path.pop()
                self.current_parent_id = new_parent_id
                self.controller.set_filter('parent_id', new_parent_id)
                
                if new_parent_id:
                    # Get group name for display
                    result = self.controller.data_service.get_documents(
                        CostItem, 
                        filters={'id': new_parent_id},
                        page_size=1
                    )
                    items = result.get('items', [])
                    if items:
                        group_name = getattr(items[0], 'description', f'Group {new_parent_id}')
                        self.filter_bar.set_navigation_state(True, f"Группа: {group_name}")
                    else:
                        self.filter_bar.set_navigation_state(True, f"Group ID: {new_parent_id}")
                else:
                    self.filter_bar.set_navigation_state(False, "Корень")
            else:
                # Fallback to old method
                result = self.controller.data_service.get_documents(
                    CostItem, 
                    filters={'id': self.current_parent_id},
                    page_size=1
                )
                items = result.get('items', [])
                if items:
                    current_group = items[0]
                    new_parent_id = getattr(current_group, 'parent_id', None)
                    
                    self.current_parent_id = new_parent_id
                    self.controller.set_filter('parent_id', new_parent_id)
                    
                    if new_parent_id:
                         # Ideally we should fetch parent name too, but ID is enough for now or just "Group"
                         self.filter_bar.set_navigation_state(True, f"Group ID: {new_parent_id}")
                    else:
                        self.filter_bar.set_navigation_state(False, "Корень")
            
            # Update keyboard context
            self.update_keyboard_context()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def open_cost_item_form(self, cost_item_id: int):
        try:
            # Pass parent_id to new form
            form = CostItemForm(cost_item_id=cost_item_id if cost_item_id else None, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {e}")

    def go_to_root(self):
        """Navigate to root level - override from base class"""
        self.current_parent_id = None
        self.navigation_path.clear()
        self.controller.set_filter('parent_id', None)
        self.filter_bar.set_navigation_state(False, "Корень")
        self.update_keyboard_context()

    def on_search(self, text: str):
        """Override search to handle hierarchy"""
        if text:
            self.controller.filters.pop('parent_id', None)
            self.controller.set_filter('description', text) # Search by description
            self.filter_bar.set_navigation_state(False, f"Поиск: {text}")
        else:
            self.controller.set_filter('description', None)
            self.controller.set_filter('parent_id', self.current_parent_id)
            can_go_up = self.current_parent_id is not None
            path_text = "Корень" if not self.current_parent_id else "Группа"
            self.filter_bar.set_navigation_state(can_go_up, path_text)

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        if getattr(item, 'is_folder', False):
            style['font_bold'] = True
            style['background'] = "#F0F0F0"
        return style
    
    def on_command_create_group(self):
        """Create new group"""
        try:
            # We need to tell the form to create a group. 
            # CostItemForm has a checkbox "is_folder", we can set it?
            # Or we pass is_folder=True arg.
            # I need to update CostItemForm to accept is_folder arg.
            form = CostItemForm(cost_item_id=None, parent_id=self.current_parent_id, is_folder=True)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")

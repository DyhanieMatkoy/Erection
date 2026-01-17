from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Object
from src.views.object_form import ObjectForm

class ObjectListFormV2(GenericListForm):
    """
    New Object List Form using Generic List Architecture.
    Supports hierarchy (groups).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("objects", user_id, Object)
        self.setWindowTitle("Справочник: Объекты")
        self.resize(1000, 600)
        
        self.current_parent_id = None
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'name', 'name': 'Наименование', 'width': 300},
            {'id': 'owner.name', 'name': 'Владелец', 'width': 200},
            {'id': 'address', 'name': 'Адрес', 'width': 300},
            {'id': 'is_group', 'name': 'Группа', 'width': 50, 'visible': False},
            {'id': 'parent_id', 'name': 'Parent', 'width': 50, 'visible': False}
        ])
        
        # Enable navigation in filter bar
        self.filter_bar.enable_navigation(True)
        
        # Initial filter for root items (if no search)
        # Assuming root items have parent_id = None
        self.controller.set_filter('parent_id', None)
        
        # Connect signals
        self.open_document_requested.connect(self.handle_open_request)
        
        # Load initial data
        self.load_data()

    def on_navigation_up(self):
        """Handle navigation up from filter bar"""
        self.go_up()

    def handle_open_request(self, object_id: int):
        """Handle open request (double click or 'edit' command)"""
        if object_id == 0:
            # Create new
            self.open_object_form(0)
            return

        # Check if it is a group or item
        # We need to find the item in the loaded data to check 'is_group'
        # Controller data is in self.controller.data_service... wait, controller doesn't expose data directly easily
        # But Table has data_map.
        
        # Find item in table data
        item_data = next((i for i in self.table.data_map if getattr(i, 'id', None) == object_id or (isinstance(i, dict) and i.get('id') == object_id)), None)
        
        if item_data:
            is_group = getattr(item_data, 'is_group', False)
            if is_group:
                self.enter_group(object_id, getattr(item_data, 'name', ''))
            else:
                self.open_object_form(object_id)

    def enter_group(self, group_id: int, group_name: str):
        """Drill down into group"""
        self.current_parent_id = group_id
        self.controller.set_filter('parent_id', group_id)
        self.filter_bar.set_navigation_state(True, f"Группа: {group_name}")
        # Clear search if any? 
        # Usually drilling down implies clearing search or searching within group.
        # For now, let's assume filtering applies.

    def go_up(self):
        """Go up one level"""
        if not self.current_parent_id:
            return

        # We need to find the parent of current_parent_id to know where to go
        # This requires a query. 
        # Quick hack: fetch current object to get its parent_id.
        # We can use DataService via Controller.
        
        try:
            # We need a method to get single object. DataService doesn't have get_by_id exposed directly?
            # It relies on generic query.
            # self.controller.session is available? No, but controller has it.
            # Let's add a helper or use direct session if possible, but cleaner to use service.
            # DataService.get_documents with id filter.
            
            result = self.controller.data_service.get_documents(
                Object, 
                filters={'id': self.current_parent_id},
                page_size=1
            )
            items = result.get('items', [])
            if items:
                current_group = items[0]
                new_parent_id = getattr(current_group, 'parent_id', None)
                
                self.current_parent_id = new_parent_id
                self.controller.set_filter('parent_id', new_parent_id)
                
                # Update label
                if new_parent_id:
                     # Need to fetch name of new parent... generic recursion issue.
                     # For now, just "..." or "Back"
                     self.filter_bar.set_navigation_state(True, f"Group ID: {new_parent_id}") # Placeholder
                else:
                    self.filter_bar.set_navigation_state(False, "Корень")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def open_object_form(self, object_id: int):
        try:
            form = ObjectForm(object_id, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data()) # Refresh on close
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {e}")

    def on_search(self, text: str):
        """Override search to handle hierarchy"""
        if text:
            # Disable hierarchy mode when searching
            self.controller.filters.pop('parent_id', None) # Remove parent filter
            self.controller.set_filter('name', text) # Use name for search
            self.filter_bar.set_navigation_state(False, f"Поиск: {text}")
        else:
            # Restore hierarchy
            self.controller.set_filter('name', None) # Clear name filter
            self.controller.set_filter('parent_id', self.current_parent_id)
            can_go_up = self.current_parent_id is not None
            path_text = "Корень" if not self.current_parent_id else "Группа"
            self.filter_bar.set_navigation_state(can_go_up, path_text)

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        if getattr(item, 'is_group', False):
            style['font_bold'] = True
            style['background'] = "#F0F0F0" # Light gray for groups
        return style
    
    # Custom commands
    def on_command_create_group(self):
        """Create new group"""
        try:
            form = ObjectForm(0, is_group=True, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")

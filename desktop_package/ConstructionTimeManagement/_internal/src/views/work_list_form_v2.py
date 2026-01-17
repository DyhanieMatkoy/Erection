from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Work
from src.views.work_form import WorkForm

class WorkListFormV2(GenericListForm):
    """
    New Work List Form using Generic List Architecture.
    Supports hierarchy (groups).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("works", user_id, Work)
        self.setWindowTitle("Справочник: Виды работ")
        self.resize(1000, 600)
        
        self.current_parent_id = None
        self.opened_forms = []

        # Enable hierarchical navigation
        self.enable_hierarchical_navigation(True)

        # Configure columns
        self.configure_columns([
            {'id': 'name', 'name': 'Наименование', 'width': 300},
            {'id': 'code', 'name': 'Код', 'width': 80},
            {'id': 'unit', 'name': 'Ед.изм.', 'width': 60},
            {'id': 'price', 'name': 'Цена', 'width': 100},
            {'id': 'labor_rate', 'name': 'Трудозатраты', 'width': 100},
            {'id': 'is_group', 'name': 'Группа', 'width': 50, 'visible': False},
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
            self.open_work_form(0)
            return

        item_data = next((i for i in self.table.data_map if getattr(i, 'id', None) == object_id or (isinstance(i, dict) and i.get('id') == object_id)), None)
        
        if item_data:
            is_group = getattr(item_data, 'is_group', False)
            if is_group:
                self.enter_group(object_id, getattr(item_data, 'name', ''))
            else:
                self.open_work_form(object_id)

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
                        Work, 
                        filters={'id': new_parent_id},
                        page_size=1
                    )
                    items = result.get('items', [])
                    if items:
                        group_name = getattr(items[0], 'name', f'Group {new_parent_id}')
                        self.filter_bar.set_navigation_state(True, f"Группа: {group_name}")
                    else:
                        self.filter_bar.set_navigation_state(True, f"Group ID: {new_parent_id}")
                else:
                    self.filter_bar.set_navigation_state(False, "Корень")
            else:
                # Fallback to old method
                result = self.controller.data_service.get_documents(
                    Work, 
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
                        self.filter_bar.set_navigation_state(True, f"Group ID: {new_parent_id}")
                    else:
                        self.filter_bar.set_navigation_state(False, "Корень")
            
            # Update keyboard context
            self.update_keyboard_context()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def open_work_form(self, work_id: int):
        try:
            form = WorkForm(work_id, parent_id=self.current_parent_id)
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
            self.controller.set_filter('name', text)
            self.filter_bar.set_navigation_state(False, f"Поиск: {text}")
        else:
            self.controller.set_filter('name', None)
            self.controller.set_filter('parent_id', self.current_parent_id)
            can_go_up = self.current_parent_id is not None
            path_text = "Корень" if not self.current_parent_id else "Группа"
            self.filter_bar.set_navigation_state(can_go_up, path_text)

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        if getattr(item, 'is_group', False):
            style['font_bold'] = True
            style['background'] = "#F0F0F0"
        return style
    
    def on_command_create_group(self):
        """Create new group"""
        try:
            form = WorkForm(0, is_group=True, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")

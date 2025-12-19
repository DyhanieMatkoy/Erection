from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Organization
from src.views.organization_form import OrganizationForm

class OrganizationListFormV2(GenericListForm):
    """
    New Organization List Form using Generic List Architecture.
    Supports hierarchy (groups).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("organizations", user_id, Organization)
        self.setWindowTitle("Справочник: Организации")
        self.resize(1000, 600)
        
        self.current_parent_id = None
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'name', 'name': 'Наименование', 'width': 300},
            {'id': 'inn', 'name': 'ИНН', 'width': 120},
            {'id': 'default_responsible.full_name', 'name': 'Ответственный', 'width': 200},
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
            self.open_organization_form(0)
            return

        item_data = next((i for i in self.table.data_map if getattr(i, 'id', None) == object_id or (isinstance(i, dict) and i.get('id') == object_id)), None)
        
        if item_data:
            is_group = getattr(item_data, 'is_group', False)
            if is_group:
                self.enter_group(object_id, getattr(item_data, 'name', ''))
            else:
                self.open_organization_form(object_id)

    def enter_group(self, group_id: int, group_name: str):
        """Drill down into group"""
        self.current_parent_id = group_id
        self.controller.set_filter('parent_id', group_id)
        self.filter_bar.set_navigation_state(True, f"Группа: {group_name}")

    def go_up(self):
        """Go up one level"""
        if not self.current_parent_id:
            return

        try:
            result = self.controller.data_service.get_documents(
                Organization, 
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
                
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def open_organization_form(self, organization_id: int):
        try:
            form = OrganizationForm(organization_id, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {e}")

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
            form = OrganizationForm(0, is_group=True, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")

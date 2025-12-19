from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Counterparty
from src.views.counterparty_form import CounterpartyForm

class CounterpartyListFormV2(GenericListForm):
    """
    New Counterparty List Form using Generic List Architecture.
    Supports hierarchy (groups).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("counterparties", user_id, Counterparty)
        self.setWindowTitle("Справочник: Контрагенты")
        self.resize(1000, 600)
        
        self.current_parent_id = None
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'name', 'name': 'Наименование', 'width': 300},
            {'id': 'inn', 'name': 'ИНН', 'width': 120},
            {'id': 'phone', 'name': 'Телефон', 'width': 150},
            {'id': 'contact_person', 'name': 'Контактное лицо', 'width': 200},
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
            self.open_counterparty_form(0)
            return

        item_data = next((i for i in self.table.data_map if getattr(i, 'id', None) == object_id or (isinstance(i, dict) and i.get('id') == object_id)), None)
        
        if item_data:
            is_group = getattr(item_data, 'is_group', False)
            if is_group:
                self.enter_group(object_id, getattr(item_data, 'name', ''))
            else:
                self.open_counterparty_form(object_id)

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
                Counterparty, 
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

    def open_counterparty_form(self, counterparty_id: int):
        try:
            form = CounterpartyForm(counterparty_id, parent_id=self.current_parent_id)
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
            form = CounterpartyForm(0, is_group=True, parent_id=self.current_parent_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {str(e)}")
    
    def on_command_copy(self):
        """Copy selected counterparty"""
        try:
            sel = self.controller.get_selection()
            if len(sel) != 1:
                QMessageBox.warning(self, "Ошибка", "Выберите один элемент для копирования")
                return
            
            source_id = list(sel)[0]
            
            # Get source counterparty data
            try:
                result = self.controller.data_service.get_documents(
                    None,  # model_class will use table name
                    filters={'id': source_id, 'marked_for_deletion': False},
                    page_size=1
                )
                items = result.get('items', [])
                source_data = items[0] if items else None
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")
                return
            if not source_data:
                QMessageBox.warning(self, "Ошибка", "Элемент не найден")
                return
            
            # Create new counterparty form with copied data
            form = CounterpartyForm(0)
            
            # Copy all fields except ID
            # Handle both dict and object types
            get_val = lambda key: source_data.get(key) if isinstance(source_data, dict) else getattr(source_data, key, None)
            
            # Get values safely
            name = get_val('name')
            inn = get_val('inn')
            contact_person = get_val('contact_person')
            phone = get_val('phone')
            parent_id = get_val('parent_id')
            is_group = get_val('is_group')
            
            # Set form fields
            if name:
                form.name_edit.setText(f"Копия - {name}")
            if inn:
                form.inn_edit.setText(str(inn))
            if contact_person:
                form.contact_person_edit.setText(str(contact_person))
            if phone:
                form.phone_edit.setText(str(phone))
            
            # Set parent
            if parent_id:
                form.load_parent(parent_id)
            
            # Set group flag
            if is_group is not None:
                form.is_group = bool(is_group)
            
            # Mark as modified
            form.is_modified = True
            
            # Show form
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать элемент: {str(e)}")

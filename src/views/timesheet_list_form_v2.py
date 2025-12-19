from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Timesheet
from src.controllers.timesheet_list_controller import TimesheetListFormController
from src.views.timesheet_document_form import TimesheetDocumentForm

class TimesheetListFormV2(GenericListForm):
    """
    New Timesheet List Form using Generic List Architecture.
    """
    def __init__(self, user_id: int = 4):
        # Initialize custom controller
        self._custom_controller = TimesheetListFormController("timesheets", user_id, Timesheet)
        super().__init__("timesheets", user_id, Timesheet, controller=self._custom_controller)
        # Callbacks are set in GenericListForm but we can override if needed
        # self.controller is already set by super
        self.controller.initialize()
        
        self.setWindowTitle("Документы: Табели")
        self.resize(1000, 600)
        
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'is_posted', 'name': 'Ст.', 'width': 30},
            {'id': 'number', 'name': 'Номер', 'width': 100},
            {'id': 'date', 'name': 'Дата', 'width': 100},
            {'id': 'object.name', 'name': 'Объект', 'width': 200},
            {'id': 'estimate.number', 'name': 'Смета', 'width': 150},
            {'id': 'foreman.full_name', 'name': 'Бригадир', 'width': 200},
            {'id': 'month_year', 'name': 'Период', 'width': 100},
        ])
        
        # Configure filters
        self.setup_filters()
        
        # Connect signals
        self.open_document_requested.connect(self.open_timesheet)
        self.table.context_menu_requested.connect(self.on_context_menu)
        
        # Load initial data
        self.load_data()

    def setup_filters(self):
        """Setup custom filters"""
        self.add_filter("is_posted", "Статус", [("Проведенные", True), ("Черновики", False)])
        
        # Objects
        objects = self.controller.get_object_filter_options()
        obj_options = [(o['name'], o['id']) for o in objects]
        self.add_filter("object_id", "Объект", obj_options)
        
        # Foremen
        if not self.controller.user_role == 'Бригадир':
             foremen = self.controller.get_foreman_filter_options()
             foreman_options = [(f['name'], f['id']) for f in foremen]
             self.add_filter("foreman_id", "Бригадир", foreman_options)

    def open_timesheet(self, timesheet_id):
        try:
            form = TimesheetDocumentForm(timesheet_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть табель: {e}")

    def on_context_menu(self, pos, row_index):
        """Handle context menu"""
        if 0 <= row_index < len(self.table.data_map):
            item = self.table.data_map[row_index]
            menu = QMenu(self)
            
            is_posted = getattr(item, 'is_posted', False)
            if is_posted:
                action = QAction("Отменить проведение", self)
                action.triggered.connect(lambda: self.on_command_unpost())
                menu.addAction(action)
            else:
                action = QAction("Провести", self)
                action.triggered.connect(lambda: self.on_command_post())
                menu.addAction(action)
                
            menu.exec(self.table.viewport().mapToGlobal(pos))

    def on_command_post(self):
        """Handle post command"""
        ids = self.controller.get_selection()
        if not ids:
            return
        
        self.controller.post_timesheets(ids)

    def on_command_unpost(self):
        """Handle unpost command"""
        ids = self.controller.get_selection()
        if not ids:
            return
            
        self.controller.unpost_timesheets(ids)

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        if getattr(item, 'is_posted', False):
            style['font_bold'] = True
        return style

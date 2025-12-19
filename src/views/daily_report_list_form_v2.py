from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import DailyReport
from src.controllers.daily_report_list_controller import DailyReportListFormController
from src.views.daily_report_document_form import DailyReportDocumentForm
from src.services.document_posting_service import DocumentPostingService

class DailyReportListFormV2(GenericListForm):
    """
    New Daily Report List Form using Generic List Architecture.
    """
    def __init__(self, user_id: int = 4):
        # Initialize controller first
        self._custom_controller = DailyReportListFormController("daily_reports", user_id, DailyReport)
        
        # Initialize parent with our custom controller
        super().__init__("daily_reports", user_id, DailyReport)
        # Override the controller created by super() with our custom one
        # (This is a bit hacky, better if GenericListForm accepted controller_class)
        # But GenericListForm creates ListFormController in __init__.
        # So we swap it.
        self.controller = self._custom_controller
        # Re-connect callbacks since we replaced the controller
        self.controller.set_callbacks(self.on_data_loaded, self.on_error)
        self.controller.initialize() # Re-initialize if needed, or just set it
        
        self.setWindowTitle("Документы: Ежедневные отчеты")
        self.resize(1000, 600)
        
        self.posting_service = DocumentPostingService()
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'is_posted', 'name': 'Ст.', 'width': 30, 'format': 'bool_icon'}, # Custom format needed?
            {'id': 'date', 'name': 'Дата', 'width': 100},
            {'id': 'estimate.number', 'name': 'Смета', 'width': 150},
            {'id': 'foreman.full_name', 'name': 'Бригадир', 'width': 200},
            # Line count omitted for now
        ])
        
        # Configure filters
        self.setup_filters()
        
        # Connect signals
        self.open_document_requested.connect(self.open_daily_report)
        
        # Setup context menu (GenericListForm doesn't have it yet, we add it)
        self.table.context_menu_requested.connect(self.on_context_menu)
        
        # Load initial data
        self.load_data()

    def setup_filters(self):
        """Setup custom filters"""
        # Status
        self.add_filter("is_posted", "Статус", [("Проведенные", True), ("Черновики", False)])
        
        # Estimates
        estimates = self.controller.get_estimate_filter_options()
        est_options = [(e['name'], e['id']) for e in estimates]
        self.add_filter("estimate_id", "Смета", est_options)
        
        # Foremen (check permissions first? Controller handles data, but View decides logic)
        # Assuming we show it unless restricted. Legacy form checked is_foreman.
        if not self.controller.user_role == 'Бригадир': # Simple check, ideally use auth_service
             foremen = self.controller.get_foreman_filter_options()
             foreman_options = [(f['name'], f['id']) for f in foremen]
             self.add_filter("foreman_id", "Бригадир", foreman_options)

    def open_daily_report(self, report_id):
        try:
            form = DailyReportDocumentForm(report_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть отчет: {e}")

    def on_context_menu(self, pos, row_index):
        """Handle context menu"""
        # Get item at row
        # We need data. GenericListForm table has data_map.
        if 0 <= row_index < len(self.table.data_map):
            item = self.table.data_map[row_index]
            menu = QMenu(self)
            
            # Post/Unpost
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
            
        # Post all selected
        success_count = 0
        errors = []
        for doc_id in ids:
            # Check permission? Service handles it?
            # Legacy checked permission.
            res, err = self.posting_service.post_daily_report(doc_id)
            if res:
                success_count += 1
            else:
                errors.append(f"ID {doc_id}: {err}")
        
        if errors:
            QMessageBox.warning(self, "Ошибка проведения", "\n".join(errors))
            
        if success_count > 0:
            self.load_data()

    def on_command_unpost(self):
        """Handle unpost command"""
        ids = self.controller.get_selection()
        if not ids:
            return
            
        # Unpost all selected
        success_count = 0
        errors = []
        for doc_id in ids:
            res, err = self.posting_service.unpost_daily_report(doc_id)
            if res:
                success_count += 1
            else:
                errors.append(f"ID {doc_id}: {err}")
        
        if errors:
            QMessageBox.warning(self, "Ошибка отмены проведения", "\n".join(errors))
            
        if success_count > 0:
            self.load_data()

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        if getattr(item, 'is_posted', False):
            style['font_bold'] = True
        return style

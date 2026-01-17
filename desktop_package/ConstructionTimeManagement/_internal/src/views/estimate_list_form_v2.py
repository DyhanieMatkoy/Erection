from typing import Optional, List, Any
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Estimate
from src.views.estimate_document_form import EstimateDocumentForm

class EstimateListFormV2(GenericListForm):
    """
    New Estimate List Form using Generic List Architecture.
    (Task 12 Integration)
    """
    def __init__(self, user_id: int = 4):
        # Use admin user as fallback instead of non-existent user_id=1
        # MainWindow should pass current user via get_current_user_id()
        # But here we just take the arg.
        super().__init__("estimates", user_id, Estimate)
        self.setWindowTitle("Документы: Сметы")
        self.resize(1000, 600)
        
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'estimate_type', 'name': 'Тип', 'width': 80},
            {'id': 'number', 'name': 'Номер', 'width': 100},
            {'id': 'date', 'name': 'Дата', 'width': 100},
            {'id': 'customer.name', 'name': 'Заказчик', 'width': 200},
            {'id': 'object.name', 'name': 'Объект', 'width': 200},
            {'id': 'responsible.full_name', 'name': 'Ответственный', 'width': 150},
            {'id': 'total_sum', 'name': 'Сумма', 'width': 100, 'format': '{:.2f}'},
            {'id': 'is_posted', 'name': 'Проведен', 'width': 80, 'visible': False}
        ])
        
        # Configure filters
        self.add_filter("is_posted", "Статус", [("Проведенные", True), ("Черновики", False)])
        self.add_filter("estimate_type", "Тип", [("Генеральная", "General"), ("Плановая", "Plan")])
        
        # Connect signals
        self.open_document_requested.connect(self.open_estimate)
        
        # Load initial data
        self.load_data()

    def open_estimate(self, estimate_id):
        try:
            form = EstimateDocumentForm(estimate_id)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            
            self.opened_forms.append(form)
            form.destroyed.connect(lambda f=form: self.opened_forms.remove(f) if f in self.opened_forms else None)
            
            form.show()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть смету: {e}")

    # Custom command handlers
    def on_command_post(self):
        # Logic to post selected estimates
        # Ideally this should be in controller or service
        pass

    def on_command_unpost(self):
        pass

    def get_row_style(self, item: Any) -> dict:
        style = super().get_row_style(item)
        
        # Additional estimate-specific styling
        if hasattr(item, 'estimate_type') and item.estimate_type == 'General':
            # Maybe bold or different color?
            pass
            
        return style

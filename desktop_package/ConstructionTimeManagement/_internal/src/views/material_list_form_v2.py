from typing import Optional, List, Any, Dict
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from src.views.generic_list_form import GenericListForm
from src.data.models.sqlalchemy_models import Material
from src.views.material_form import MaterialForm

class MaterialListFormV2(GenericListForm):
    """
    New Material List Form using Generic List Architecture.
    Flat list (no hierarchy).
    """
    def __init__(self, user_id: int = 4):
        super().__init__("materials", user_id, Material)
        self.setWindowTitle("Справочник: Материалы")
        self.resize(1000, 600)
        
        self.opened_forms = []

        # Configure columns
        self.configure_columns([
            {'id': 'code', 'name': 'Код', 'width': 100},
            {'id': 'description', 'name': 'Наименование', 'width': 400},
            {'id': 'unit', 'name': 'Ед. изм.', 'width': 80},
            {'id': 'price', 'name': 'Цена', 'width': 100},
        ])
        
        # Connect signals
        self.open_document_requested.connect(self.handle_open_request)
        
        # Load initial data
        self.load_data()

    def handle_open_request(self, object_id: int):
        """Handle open request"""
        self.open_material_form(object_id)

    def open_material_form(self, material_id: int):
        try:
            form = MaterialForm(material_id=material_id if material_id else None)
            form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.opened_forms.append(form)
            form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)
            form.destroyed.connect(lambda: self.load_data())
            form.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму: {e}")

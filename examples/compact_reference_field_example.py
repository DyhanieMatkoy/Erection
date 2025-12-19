"""Example usage of CompactReferenceField component"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QFormLayout
from src.views.components.compact_reference_field import CompactReferenceField


class CompactReferenceFieldExample(QMainWindow):
    """Example window demonstrating CompactReferenceField usage"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compact Reference Field Example")
        self.resize(600, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("<h2>Compact Reference Field Examples</h2>")
        main_layout.addWidget(title)
        
        # Form layout for examples
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)
        
        # Example 1: Works reference
        self.works_field = CompactReferenceField()
        self.works_field.set_reference_config(
            reference_type="works",
            title="Выбор работы",
            related_fields=["unit", "price"],
            allow_edit=True
        )
        self.works_field.value_changed.connect(self.on_works_changed)
        self.works_field.open_requested.connect(self.on_works_open)
        self.works_field.selector_requested.connect(self.on_works_selector)
        form_layout.addRow("Работа:", self.works_field)
        
        # Example 2: Counterparty reference
        self.counterparty_field = CompactReferenceField()
        self.counterparty_field.set_reference_config(
            reference_type="counterparties",
            title="Выбор контрагента",
            allow_edit=True
        )
        self.counterparty_field.value_changed.connect(self.on_counterparty_changed)
        form_layout.addRow("Контрагент:", self.counterparty_field)
        
        # Example 3: Object reference
        self.object_field = CompactReferenceField()
        self.object_field.set_reference_config(
            reference_type="objects",
            title="Выбор объекта",
            allow_edit=True
        )
        self.object_field.value_changed.connect(self.on_object_changed)
        form_layout.addRow("Объект:", self.object_field)
        
        # Example 4: Person reference (read-only)
        self.person_field = CompactReferenceField()
        self.person_field.set_reference_config(
            reference_type="persons",
            title="Выбор сотрудника",
            allow_edit=False  # Read-only, can't open
        )
        self.person_field.value_changed.connect(self.on_person_changed)
        form_layout.addRow("Сотрудник:", self.person_field)
        
        # Status label
        self.status_label = QLabel("Статус: Готов")
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
        
        # Instructions
        instructions = QLabel("""
        <h3>Инструкции:</h3>
        <ul>
            <li>Нажмите кнопку 'o' для открытия выбранного элемента</li>
            <li>Нажмите кнопку '▼' для выбора из списка</li>
            <li>Используйте F4 для открытия селектора</li>
            <li>Используйте Enter для выбора из списка</li>
        </ul>
        """)
        main_layout.addWidget(instructions)
    
    def on_works_changed(self, ref_id: int, name: str):
        """Handle works reference change"""
        self.status_label.setText(f"Работа изменена: ID={ref_id}, Название={name}")
        print(f"Works changed: {ref_id} - {name}")
    
    def on_works_open(self):
        """Handle works open request"""
        self.status_label.setText("Запрос на открытие работы")
        print("Open works requested")
    
    def on_works_selector(self):
        """Handle works selector request"""
        self.status_label.setText("Открыт селектор работ")
        print("Works selector opened")
    
    def on_counterparty_changed(self, ref_id: int, name: str):
        """Handle counterparty reference change"""
        self.status_label.setText(f"Контрагент изменен: ID={ref_id}, Название={name}")
        print(f"Counterparty changed: {ref_id} - {name}")
    
    def on_object_changed(self, ref_id: int, name: str):
        """Handle object reference change"""
        self.status_label.setText(f"Объект изменен: ID={ref_id}, Название={name}")
        print(f"Object changed: {ref_id} - {name}")
    
    def on_person_changed(self, ref_id: int, name: str):
        """Handle person reference change"""
        self.status_label.setText(f"Сотрудник изменен: ID={ref_id}, Название={name}")
        print(f"Person changed: {ref_id} - {name}")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = CompactReferenceFieldExample()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

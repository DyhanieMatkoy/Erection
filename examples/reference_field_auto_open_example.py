#!/usr/bin/env python3
"""
Example demonstrating reference field auto-open functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                              QLabel, QHBoxLayout, QPushButton, QGroupBox)
from PyQt6.QtCore import Qt
from src.views.components.reference_field import ReferenceField
from src.views.components.compact_reference_field import CompactReferenceField

class ReferenceFieldAutoOpenExample(QMainWindow):
    """Example window demonstrating reference field auto-open functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reference Field Auto-Open Example")
        self.resize(700, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Instructions
        instructions = QLabel("""
<h3>Reference Field Auto-Open Functionality</h3>
<p><b>Instructions:</b></p>
<ul>
<li>Click on empty reference fields below - they will automatically open the selector dialog</li>
<li>Pre-filled fields will not auto-open when focused</li>
<li>You can still use F4 or the buttons to manually open selectors</li>
<li>Use the "Clear" buttons to test auto-open on previously filled fields</li>
</ul>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Standard Reference Fields
        std_group = QGroupBox("Standard Reference Fields")
        std_layout = QVBoxLayout(std_group)
        
        # Empty work field
        std_layout.addWidget(QLabel("Work Reference (empty - will auto-open):"))
        self.work_field = ReferenceField()
        self.work_field.set_reference("works", "Выбор работы")
        self.work_field.value_changed.connect(lambda id, name: print(f"Work selected: {id} - {name}"))
        
        work_layout = QHBoxLayout()
        work_layout.addWidget(self.work_field)
        clear_work_btn = QPushButton("Clear")
        clear_work_btn.clicked.connect(self.work_field.clear_value)
        work_layout.addWidget(clear_work_btn)
        std_layout.addLayout(work_layout)
        
        # Pre-filled object field
        std_layout.addWidget(QLabel("Object Reference (pre-filled - will NOT auto-open):"))
        self.object_field = ReferenceField()
        self.object_field.set_reference("objects", "Выбор объекта")
        self.object_field.set_value(1, "Sample Object")  # Pre-fill
        self.object_field.value_changed.connect(lambda id, name: print(f"Object selected: {id} - {name}"))
        
        object_layout = QHBoxLayout()
        object_layout.addWidget(self.object_field)
        clear_object_btn = QPushButton("Clear")
        clear_object_btn.clicked.connect(self.object_field.clear_value)
        object_layout.addWidget(clear_object_btn)
        std_layout.addLayout(object_layout)
        
        layout.addWidget(std_group)
        
        # Compact Reference Fields
        compact_group = QGroupBox("Compact Reference Fields")
        compact_layout = QVBoxLayout(compact_group)
        
        # Empty counterparty field
        compact_layout.addWidget(QLabel("Counterparty Reference (empty - will auto-open):"))
        self.counterparty_field = CompactReferenceField()
        self.counterparty_field.set_reference_config("counterparties", "Выбор контрагента")
        self.counterparty_field.value_changed.connect(lambda id, name: print(f"Counterparty selected: {id} - {name}"))
        
        counterparty_layout = QHBoxLayout()
        counterparty_layout.addWidget(self.counterparty_field)
        clear_counterparty_btn = QPushButton("Clear")
        clear_counterparty_btn.clicked.connect(self.counterparty_field.clear_value)
        counterparty_layout.addWidget(clear_counterparty_btn)
        compact_layout.addLayout(counterparty_layout)
        
        # Pre-filled person field
        compact_layout.addWidget(QLabel("Person Reference (pre-filled - will NOT auto-open):"))
        self.person_field = CompactReferenceField()
        self.person_field.set_reference_config("persons", "Выбор сотрудника")
        self.person_field.set_value(1, "Sample Person")  # Pre-fill
        self.person_field.value_changed.connect(lambda id, name: print(f"Person selected: {id} - {name}"))
        
        person_layout = QHBoxLayout()
        person_layout.addWidget(self.person_field)
        clear_person_btn = QPushButton("Clear")
        clear_person_btn.clicked.connect(self.person_field.clear_value)
        person_layout.addWidget(clear_person_btn)
        compact_layout.addLayout(person_layout)
        
        layout.addWidget(compact_group)
        
        # Test buttons
        button_group = QGroupBox("Test Actions")
        button_layout = QHBoxLayout(button_group)
        
        clear_all_btn = QPushButton("Clear All Fields")
        clear_all_btn.clicked.connect(self.clear_all_fields)
        button_layout.addWidget(clear_all_btn)
        
        fill_all_btn = QPushButton("Fill All Fields")
        fill_all_btn.clicked.connect(self.fill_all_fields)
        button_layout.addWidget(fill_all_btn)
        
        layout.addWidget(button_group)
        
        layout.addStretch()
        
        # Status
        self.status_label = QLabel("Ready. Click on empty fields to see auto-open functionality.")
        layout.addWidget(self.status_label)
    
    def clear_all_fields(self):
        """Clear all reference fields"""
        self.work_field.clear_value()
        self.object_field.clear_value()
        self.counterparty_field.clear_value()
        self.person_field.clear_value()
        self.status_label.setText("All fields cleared. Click on them to see auto-open functionality.")
    
    def fill_all_fields(self):
        """Fill all reference fields with sample data"""
        self.work_field.set_value(1, "Sample Work")
        self.object_field.set_value(1, "Sample Object")
        self.counterparty_field.set_value(1, "Sample Counterparty")
        self.person_field.set_value(1, "Sample Person")
        self.status_label.setText("All fields filled. They will NOT auto-open when focused.")

def main():
    app = QApplication(sys.argv)
    
    window = ReferenceFieldAutoOpenExample()
    window.show()
    
    print("Reference Field Auto-Open Example")
    print("=" * 40)
    print("Click on empty reference fields to see auto-open functionality")
    print("Use Clear/Fill buttons to test different scenarios")
    print("Close the window to exit")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
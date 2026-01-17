from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QDateEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Dict, Any
from ..utils.button_styler import get_button_styler

class FilterBar(QWidget):
    """
    Generic filter bar component (Task 7.5).
    Contains search box, date range, and custom filters.
    Now supports navigation elements (up button, breadcrumbs).
    """
    
    filter_changed = pyqtSignal(str, object) # key, value
    search_changed = pyqtSignal(str)
    navigation_up_clicked = pyqtSignal()  # Signal for up navigation
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.filters = {} # active filters
        self.navigation_enabled = False

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation elements (initially hidden)
        self.up_button = QPushButton("⬆")
        self.up_button.setFixedWidth(30)
        self.up_button.clicked.connect(self.navigation_up_clicked.emit)
        self.up_button.setEnabled(False)
        self.up_button.setToolTip("На уровень вверх")
        self.up_button.setVisible(False)
        layout.addWidget(self.up_button)
        
        self.path_label = QLabel("Корень")
        self.path_label.setStyleSheet("font-weight: bold; margin-right: 10px;")
        self.path_label.setVisible(False)
        layout.addWidget(self.path_label)
        
        # Search
        layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ctrl+F...")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.textChanged.connect(self.update_clear_button_visibility)
        layout.addWidget(self.search_edit)
        
        # Container for dynamic filters
        self.dynamic_filters_layout = QHBoxLayout()
        layout.addLayout(self.dynamic_filters_layout)
        
        # Clear button
        styler = get_button_styler()
        self.clear_btn = QPushButton()
        styler.apply_style(self.clear_btn, 'clear_filter', "Очистить")
        self.clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
        self.setLayout(layout)

    def add_filter(self, key: str, label: str, options: list):
        """
        Add a dropdown filter.
        options: list of (label, value) tuples
        """
        container = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(QLabel(f"{label}:"))
        
        combo = QComboBox()
        combo.addItem("Все", None)
        for opt_label, opt_value in options:
            combo.addItem(str(opt_label), opt_value)
            
        combo.currentIndexChanged.connect(lambda: self.on_combo_changed(key, combo))
        l.addWidget(combo)
        container.setLayout(l)
        
        self.dynamic_filters_layout.addWidget(container)
        self.filters[key] = combo

    def on_search_text_changed(self, text):
        self.search_changed.emit(text)

    def on_combo_changed(self, key, combo):
        value = combo.currentData()
        self.filter_changed.emit(key, value)

    def clear_all(self):
        self.search_edit.clear()
        for combo in self.filters.values():
            if isinstance(combo, QComboBox):
                combo.setCurrentIndex(0)

    def enable_navigation(self, enabled: bool = True):
        """Enable/disable navigation elements"""
        self.navigation_enabled = enabled
        self.up_button.setVisible(enabled)
        self.path_label.setVisible(enabled)

    def set_navigation_state(self, can_go_up: bool, path_text: str = "Корень"):
        """Update navigation state"""
        if self.navigation_enabled:
            self.up_button.setEnabled(can_go_up)
            self.path_label.setText(path_text)
    
    def update_clear_button_visibility(self):
        """Update clear button visibility based on filter state"""
        has_search_text = bool(self.search_edit.text().strip())
        has_active_filters = any(
            hasattr(combo, 'currentData') and combo.currentData() is not None
            for combo in self.filters.values()
            if isinstance(combo, QComboBox)
        )
        
        # Show clear button if there's something to clear
        self.clear_btn.setVisible(has_search_text or has_active_filters)

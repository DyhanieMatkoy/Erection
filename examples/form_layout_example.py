"""
Form Layout Manager Example

Demonstrates the responsive form layout manager for desktop applications.
Shows how to create forms with intelligent two-column layout based on field types and counts.
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QCheckBox,
    QPushButton, QLabel, QGroupBox, QScrollArea, QComboBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont

# Add src to path for imports
sys.path.insert(0, 'src')

from services.form_layout_manager import (
    FormLayoutManager, FormField, FieldType, LayoutAnalysis
)
from services.responsive_layout_adapter import ResponsiveLayoutAdapter, ResponsiveFormWidget


class FormLayoutExampleWindow(QMainWindow):
    """Main window demonstrating form layout manager"""
    
    def __init__(self):
        super().__init__()
        self.layout_manager = FormLayoutManager()
        self.current_fields = []
        self.setup_ui()
        self.setWindowTitle("Form Layout Manager Example")
        self.resize(1000, 700)
    
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Form Layout Manager Example")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "This example demonstrates the responsive form layout with different field types and counts.\n"
            "Resize the window to see responsive behavior."
        )
        desc.setWordWrap(True)
        main_layout.addWidget(desc)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.few_fields_btn = QPushButton("Show Few Fields (< 6)")
        self.few_fields_btn.clicked.connect(self.show_few_fields)
        controls_layout.addWidget(self.few_fields_btn)
        
        self.many_fields_btn = QPushButton("Show Many Fields (≥ 6)")
        self.many_fields_btn.clicked.connect(self.show_many_fields)
        controls_layout.addWidget(self.many_fields_btn)
        
        self.add_long_field_btn = QPushButton("Add Long Text Field")
        self.add_long_field_btn.clicked.connect(self.add_long_text_field)
        controls_layout.addWidget(self.add_long_field_btn)
        
        self.toggle_responsive_btn = QPushButton("Toggle Responsive Widget")
        self.toggle_responsive_btn.clicked.connect(self.toggle_responsive_widget)
        controls_layout.addWidget(self.toggle_responsive_btn)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        # Form container (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.form_container = QWidget()
        scroll_area.setWidget(self.form_container)
        main_layout.addWidget(scroll_area)
        
        # Analysis display
        self.analysis_group = QGroupBox("Layout Analysis")
        self.analysis_layout = QVBoxLayout(self.analysis_group)
        self.analysis_label = QLabel("No fields configured")
        self.analysis_layout.addWidget(self.analysis_label)
        main_layout.addWidget(self.analysis_group)
        
        # Responsive widget (initially hidden)
        self.responsive_widget = None
        self.using_responsive = False
        
        # Start with few fields
        self.show_few_fields()
    
    def create_few_fields(self):
        """Create a small set of fields (< 6)"""
        fields = []
        
        # Name (short text)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter name")
        name_edit.setMaxLength(50)
        fields.append(FormField(
            "name", "Name:", name_edit, FieldType.SHORT_TEXT, 
            max_length=50, is_required=True
        ))
        
        # Email (short text)
        email_edit = QLineEdit()
        email_edit.setPlaceholderText("Enter email")
        email_edit.setMaxLength(100)
        fields.append(FormField(
            "email", "Email:", email_edit, FieldType.SHORT_TEXT,
            max_length=100, is_required=True
        ))
        
        # Phone (short text)
        phone_edit = QLineEdit()
        phone_edit.setPlaceholderText("Enter phone")
        phone_edit.setMaxLength(20)
        fields.append(FormField(
            "phone", "Phone:", phone_edit, FieldType.SHORT_TEXT,
            max_length=20
        ))
        
        # Birth date (date)
        birth_date = QDateEdit()
        birth_date.setCalendarPopup(True)
        birth_date.setDate(QDate.currentDate())
        fields.append(FormField(
            "birth_date", "Birth Date:", birth_date, FieldType.DATE
        ))
        
        return fields
    
    def create_many_fields(self):
        """Create a large set of fields (≥ 6)"""
        fields = self.create_few_fields()
        
        # Address (long text)
        address_edit = QTextEdit()
        address_edit.setPlaceholderText("Enter full address")
        address_edit.setMaximumHeight(80)
        fields.append(FormField(
            "address", "Address:", address_edit, FieldType.LONG_TEXT,
            is_multiline=True
        ))
        
        # City (short text)
        city_edit = QLineEdit()
        city_edit.setPlaceholderText("Enter city")
        city_edit.setMaxLength(50)
        fields.append(FormField(
            "city", "City:", city_edit, FieldType.SHORT_TEXT,
            max_length=50, is_required=True
        ))
        
        # State (reference)
        state_combo = QComboBox()
        state_combo.addItems(["Select State", "CA", "NY", "TX", "FL", "WA"])
        fields.append(FormField(
            "state", "State:", state_combo, FieldType.REFERENCE
        ))
        
        # ZIP Code (short text)
        zip_edit = QLineEdit()
        zip_edit.setPlaceholderText("Enter ZIP")
        zip_edit.setMaxLength(10)
        fields.append(FormField(
            "zip", "ZIP Code:", zip_edit, FieldType.SHORT_TEXT,
            max_length=10
        ))
        
        # Salary (numeric)
        salary_spin = QDoubleSpinBox()
        salary_spin.setRange(0, 999999)
        salary_spin.setSuffix(" USD")
        salary_spin.setDecimals(2)
        fields.append(FormField(
            "salary", "Salary:", salary_spin, FieldType.NUMERIC
        ))
        
        # Start Date (date)
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate())
        fields.append(FormField(
            "start_date", "Start Date:", start_date, FieldType.DATE,
            is_required=True
        ))
        
        # Active (boolean)
        active_check = QCheckBox("Active Employee")
        fields.append(FormField(
            "active", "Status:", active_check, FieldType.BOOLEAN
        ))
        
        return fields
    
    def show_few_fields(self):
        """Show form with few fields"""
        self.current_fields = self.create_few_fields()
        self.rebuild_form()
        self.few_fields_btn.setEnabled(False)
        self.many_fields_btn.setEnabled(True)
    
    def show_many_fields(self):
        """Show form with many fields"""
        self.current_fields = self.create_many_fields()
        self.rebuild_form()
        self.few_fields_btn.setEnabled(True)
        self.many_fields_btn.setEnabled(False)
    
    def add_long_text_field(self):
        """Add a long text field dynamically"""
        field_count = len([f for f in self.current_fields if f.name.startswith("long_text")])
        field_num = field_count + 1
        
        long_text_edit = QTextEdit()
        long_text_edit.setPlaceholderText(f"Enter long text for field {field_num}")
        long_text_edit.setMaximumHeight(100)
        
        field = FormField(
            f"long_text_{field_num}",
            f"Long Text Field {field_num}:",
            long_text_edit,
            FieldType.LONG_TEXT,
            max_length=500,
            is_multiline=True
        )
        
        self.current_fields.append(field)
        self.rebuild_form()
    
    def toggle_responsive_widget(self):
        """Toggle between manual layout and responsive widget"""
        self.using_responsive = not self.using_responsive
        self.rebuild_form()
        
        if self.using_responsive:
            self.toggle_responsive_btn.setText("Use Manual Layout")
        else:
            self.toggle_responsive_btn.setText("Use Responsive Widget")
    
    def rebuild_form(self):
        """Rebuild the form layout"""
        # Clear existing layout
        if self.form_container.layout():
            self.clear_layout(self.form_container.layout())
        
        if self.using_responsive:
            # Use responsive widget
            if self.responsive_widget:
                self.responsive_widget.setParent(None)
            
            self.responsive_widget = ResponsiveFormWidget()
            self.responsive_widget.set_fields(self.current_fields)
            
            container_layout = QVBoxLayout(self.form_container)
            container_layout.addWidget(self.responsive_widget)
        else:
            # Use manual layout manager
            form_layout = self.layout_manager.create_form_layout(
                self.form_container,
                self.current_fields
            )
            self.form_container.setLayout(form_layout)
        
        # Update analysis
        self.update_analysis()
    
    def clear_layout(self, layout):
        """Clear all items from layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self.clear_layout(child.layout())
    
    def update_analysis(self):
        """Update the layout analysis display"""
        analysis = self.layout_manager.analyze_fields(self.current_fields)
        
        analysis_text = f"""
        Total Fields: {analysis.total_fields}
        Short Fields: {len(analysis.short_fields)}
        Long String Fields: {len(analysis.long_string_fields)}
        Recommended Layout: {analysis.recommended_layout}
        
        Short Fields: {', '.join([f.name for f in analysis.short_fields])}
        Long Fields: {', '.join([f.name for f in analysis.long_string_fields])}
        
        Layout Mode: {'Responsive Widget' if self.using_responsive else 'Manual Layout Manager'}
        """
        
        self.analysis_label.setText(analysis_text.strip())
    
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        if self.responsive_widget:
            # Responsive widget handles this automatically
            pass


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = FormLayoutExampleWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
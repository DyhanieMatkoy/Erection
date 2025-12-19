"""
Integration tests for Form Layout Manager

Tests integration with existing document forms to ensure the layout manager
works correctly with real form scenarios.
"""
import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit, QDateEdit, QComboBox
from PyQt6.QtCore import QDate

# Ensure QApplication exists for widget tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.services.form_layout_manager import FormLayoutManager, FormField, FieldType
from src.services.responsive_layout_adapter import ResponsiveFormWidget


class TestFormLayoutIntegration:
    """Test form layout manager integration with document forms"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.layout_manager = FormLayoutManager()
    
    def create_estimate_form_fields(self) -> list[FormField]:
        """Create fields similar to estimate document form"""
        fields = []
        
        # Number (short)
        number_edit = QLineEdit()
        number_edit.setMaxLength(20)
        fields.append(FormField(
            "number", "Номер:", number_edit, FieldType.SHORT_TEXT,
            max_length=20, is_required=True
        ))
        
        # Date (date)
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        fields.append(FormField(
            "date", "Дата:", date_edit, FieldType.DATE,
            is_required=True
        ))
        
        # Customer (reference)
        customer_combo = QComboBox()
        fields.append(FormField(
            "customer", "Заказчик:", customer_combo, FieldType.REFERENCE,
            is_required=True
        ))
        
        # Object (reference)
        object_combo = QComboBox()
        fields.append(FormField(
            "object", "Объект:", object_combo, FieldType.REFERENCE
        ))
        
        # Contractor (reference)
        contractor_combo = QComboBox()
        fields.append(FormField(
            "contractor", "Подрядчик:", contractor_combo, FieldType.REFERENCE
        ))
        
        # Responsible (reference)
        responsible_combo = QComboBox()
        fields.append(FormField(
            "responsible", "Ответственный:", responsible_combo, FieldType.REFERENCE
        ))
        
        # Description (long text)
        description_edit = QTextEdit()
        fields.append(FormField(
            "description", "Описание:", description_edit, FieldType.LONG_TEXT,
            is_multiline=True
        ))
        
        return fields
    
    def test_estimate_form_layout_analysis(self):
        """Test layout analysis for estimate-like form"""
        fields = self.create_estimate_form_fields()
        analysis = self.layout_manager.analyze_fields(fields)
        
        # Should have 7 total fields
        assert analysis.total_fields == 7
        
        # Should have 6 short fields (all except description)
        assert len(analysis.short_fields) == 6
        
        # Should have 1 long field (description)
        assert len(analysis.long_string_fields) == 1
        
        # Should recommend two-column layout (≥6 total fields, ≥4 short fields)
        assert analysis.recommended_layout == "two_column"
    
    def test_estimate_form_two_column_layout(self):
        """Test two-column layout creation for estimate form"""
        fields = self.create_estimate_form_fields()
        config = self.layout_manager.create_two_column_layout(fields)
        
        # Should distribute short fields between columns
        assert len(config.left_column) == 3  # Half of 6 short fields
        assert len(config.right_column) == 3  # Half of 6 short fields
        
        # Should put long field in full width
        assert len(config.full_width_fields) == 1
        assert config.full_width_fields[0].name == "description"
        
        # Should have reasonable column ratio
        assert 0 < config.column_ratio < 1
    
    def test_few_fields_single_column(self):
        """Test single column layout for forms with few fields"""
        # Create form with only 4 fields
        fields = self.create_estimate_form_fields()[:4]
        
        analysis = self.layout_manager.analyze_fields(fields)
        
        # Should recommend single column (< 6 total fields)
        assert analysis.recommended_layout == "single_column"
        assert analysis.total_fields == 4
        assert len(analysis.short_fields) == 4
    
    def test_responsive_widget_integration(self):
        """Test responsive form widget with estimate fields"""
        widget = ResponsiveFormWidget()
        fields = self.create_estimate_form_fields()
        
        # Set fields
        widget.set_fields(fields)
        
        # Should have all fields
        assert len(widget.fields) == 7
        
        # Should have layout
        assert widget.current_layout is not None
    
    def test_field_type_detection_from_widgets(self):
        """Test automatic field type detection from Qt widgets"""
        # Test various widget types
        line_edit = QLineEdit()
        assert self.layout_manager.get_field_type_from_widget(line_edit) == FieldType.SHORT_TEXT
        
        text_edit = QTextEdit()
        assert self.layout_manager.get_field_type_from_widget(text_edit) == FieldType.LONG_TEXT
        
        date_edit = QDateEdit()
        assert self.layout_manager.get_field_type_from_widget(date_edit) == FieldType.DATE
        
        combo_box = QComboBox()
        assert self.layout_manager.get_field_type_from_widget(combo_box) == FieldType.REFERENCE
    
    def test_long_text_field_identification(self):
        """Test identification of long text fields"""
        fields = self.create_estimate_form_fields()
        long_fields = self.layout_manager.handle_long_string_fields(fields)
        
        # Should identify description as long field
        assert len(long_fields) == 1
        assert long_fields[0].name == "description"
        assert long_fields[0].is_multiline
    
    def test_required_field_handling(self):
        """Test handling of required fields in layout"""
        fields = self.create_estimate_form_fields()
        
        # Count required fields
        required_fields = [f for f in fields if f.is_required]
        assert len(required_fields) == 3  # number, date, customer
        
        # Required fields should be handled same as non-required for layout
        config = self.layout_manager.create_two_column_layout(fields)
        
        # Required fields should be distributed across columns
        all_column_fields = config.left_column + config.right_column
        required_in_columns = [f for f in all_column_fields if f.is_required]
        assert len(required_in_columns) > 0
    
    def test_mixed_field_types_layout(self):
        """Test layout with mixed field types"""
        fields = []
        
        # Add various field types
        for i in range(3):
            # Short text
            line_edit = QLineEdit()
            fields.append(FormField(f"short_{i}", f"Short {i}:", line_edit, FieldType.SHORT_TEXT))
            
            # Reference
            combo = QComboBox()
            fields.append(FormField(f"ref_{i}", f"Reference {i}:", combo, FieldType.REFERENCE))
        
        # Add one long text
        text_edit = QTextEdit()
        fields.append(FormField("long", "Long Text:", text_edit, FieldType.LONG_TEXT, is_multiline=True))
        
        # Should have 7 fields total
        assert len(fields) == 7
        
        analysis = self.layout_manager.analyze_fields(fields)
        assert analysis.total_fields == 7
        assert len(analysis.short_fields) == 6  # 3 short + 3 reference
        assert len(analysis.long_string_fields) == 1  # 1 long text
        assert analysis.recommended_layout == "two_column"


if __name__ == '__main__':
    pytest.main([__file__])
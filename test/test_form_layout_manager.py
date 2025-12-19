"""
Tests for Form Layout Manager

Tests the form layout manager functionality including field analysis,
two-column layout creation, and responsive behavior.
"""
import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit, QSpinBox, QDateEdit, QCheckBox
from PyQt6.QtCore import QDate

# Ensure QApplication exists for widget tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.services.form_layout_manager import (
    FormLayoutManager, FormField, FieldType, LayoutAnalysis, LayoutConfiguration
)
from src.services.responsive_layout_adapter import (
    ResponsiveLayoutAdapter, WindowSize, ResponsiveLayoutRules, ResponsiveFormWidget
)


class TestFormLayoutManager:
    """Test form layout manager functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.layout_manager = FormLayoutManager()
    
    def create_test_fields(self, count: int = 6) -> list[FormField]:
        """Create test fields for testing"""
        fields = []
        
        # Short fields
        for i in range(min(count, 4)):
            widget = QLineEdit()
            widget.setMaxLength(50)
            field = FormField(
                f"short_{i}",
                f"Short Field {i}:",
                widget,
                FieldType.SHORT_TEXT,
                max_length=50
            )
            fields.append(field)
        
        # Add long fields if needed
        if count > 4:
            for i in range(count - 4):
                widget = QTextEdit()
                field = FormField(
                    f"long_{i}",
                    f"Long Field {i}:",
                    widget,
                    FieldType.LONG_TEXT,
                    is_multiline=True
                )
                fields.append(field)
        
        return fields
    
    def test_field_type_classification(self):
        """Test field type classification"""
        # Short text field
        short_field = FormField("test", "Test:", QLineEdit(), FieldType.SHORT_TEXT, max_length=50)
        assert short_field.is_short_field()
        assert not short_field.is_long_string_field()
        
        # Long text field
        long_field = FormField("test", "Test:", QTextEdit(), FieldType.LONG_TEXT, is_multiline=True)
        assert not long_field.is_short_field()
        assert long_field.is_long_string_field()
        
        # Long field by max_length
        long_by_length = FormField("test", "Test:", QLineEdit(), FieldType.SHORT_TEXT, max_length=150)
        assert not long_by_length.is_short_field()
        assert long_by_length.is_long_string_field()
    
    def test_analyze_fields_few_fields(self):
        """Test field analysis with few fields (< 6)"""
        fields = self.create_test_fields(4)
        analysis = self.layout_manager.analyze_fields(fields)
        
        assert analysis.total_fields == 4
        assert len(analysis.short_fields) == 4
        assert len(analysis.long_string_fields) == 0
        assert analysis.recommended_layout == "single_column"
    
    def test_analyze_fields_many_fields(self):
        """Test field analysis with many fields (≥ 6)"""
        fields = self.create_test_fields(8)
        analysis = self.layout_manager.analyze_fields(fields)
        
        assert analysis.total_fields == 8
        assert len(analysis.short_fields) == 4  # First 4 are short
        assert len(analysis.long_string_fields) == 4  # Last 4 are long
        assert analysis.recommended_layout == "two_column"
    
    def test_create_two_column_layout(self):
        """Test two-column layout creation"""
        fields = self.create_test_fields(8)
        config = self.layout_manager.create_two_column_layout(fields)
        
        assert isinstance(config, LayoutConfiguration)
        assert len(config.left_column) == 2  # Half of short fields
        assert len(config.right_column) == 2  # Half of short fields
        assert len(config.full_width_fields) == 4  # All long fields
        assert 0 < config.column_ratio < 1
    
    def test_handle_long_string_fields(self):
        """Test long string field identification"""
        fields = self.create_test_fields(6)
        long_fields = self.layout_manager.handle_long_string_fields(fields)
        
        assert len(long_fields) == 2  # Last 2 fields are long
        for field in long_fields:
            assert field.is_long_string_field()
    
    def test_get_field_type_from_widget(self):
        """Test widget type detection"""
        # Test different widget types
        assert self.layout_manager.get_field_type_from_widget(QLineEdit()) == FieldType.SHORT_TEXT
        assert self.layout_manager.get_field_type_from_widget(QTextEdit()) == FieldType.LONG_TEXT
        assert self.layout_manager.get_field_type_from_widget(QSpinBox()) == FieldType.NUMERIC
        assert self.layout_manager.get_field_type_from_widget(QDateEdit()) == FieldType.DATE
        assert self.layout_manager.get_field_type_from_widget(QCheckBox()) == FieldType.BOOLEAN


class TestResponsiveLayoutAdapter:
    """Test responsive layout adapter functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.adapter = ResponsiveLayoutAdapter()
        self.rules = ResponsiveLayoutRules()
    
    def test_window_size_classification(self):
        """Test window size classification"""
        # Narrow window
        narrow = WindowSize(600, 400)
        assert narrow.is_narrow()
        assert not narrow.is_wide()
        
        # Wide window
        wide = WindowSize(1400, 800)
        assert not wide.is_narrow()
        assert wide.is_wide()
        
        # Medium window
        medium = WindowSize(1000, 600)
        assert not medium.is_narrow()
        assert not medium.is_wide()
    
    def test_should_use_two_columns(self):
        """Test two-column layout decision"""
        # Wide window with many fields
        wide_window = WindowSize(1000, 600)
        assert self.rules.should_use_two_columns(wide_window, 8)
        
        # Narrow window with many fields
        narrow_window = WindowSize(600, 400)
        assert not self.rules.should_use_two_columns(narrow_window, 8)
        
        # Wide window with few fields
        assert not self.rules.should_use_two_columns(wide_window, 4)
    
    def test_get_column_ratio(self):
        """Test column ratio calculation"""
        # Small screen
        small = WindowSize(600, 400)
        ratio_small = self.rules.get_column_ratio(small)
        assert ratio_small == 0.5
        
        # Medium screen
        medium = WindowSize(900, 600)
        ratio_medium = self.rules.get_column_ratio(medium)
        assert ratio_medium == 0.45
        
        # Large screen
        large = WindowSize(1200, 800)
        ratio_large = self.rules.get_column_ratio(large)
        assert ratio_large == 0.4
    
    def test_adapt_to_window_size(self):
        """Test layout adaptation to window size"""
        # Create initial layout
        layout_manager = FormLayoutManager()
        fields = []
        for i in range(6):
            widget = QLineEdit()
            field = FormField(f"field_{i}", f"Field {i}:", widget, FieldType.SHORT_TEXT)
            fields.append(field)
        
        config = layout_manager.create_two_column_layout(fields)
        
        # Adapt to different window sizes
        small_window = WindowSize(600, 400)
        adapted_small = self.adapter.adapt_to_window_size(config, small_window)
        assert adapted_small.column_ratio == 0.5
        
        large_window = WindowSize(1400, 800)
        adapted_large = self.adapter.adapt_to_window_size(config, large_window)
        assert adapted_large.column_ratio == 0.4
    
    def test_get_current_breakpoint(self):
        """Test breakpoint detection"""
        # Test different window sizes
        self.adapter.current_window_size = WindowSize(400, 300)
        assert self.adapter.get_current_breakpoint() == "mobile"
        
        self.adapter.current_window_size = WindowSize(700, 500)
        assert self.adapter.get_current_breakpoint() == "tablet"
        
        self.adapter.current_window_size = WindowSize(1100, 700)
        assert self.adapter.get_current_breakpoint() == "desktop"
        
        self.adapter.current_window_size = WindowSize(1500, 900)
        assert self.adapter.get_current_breakpoint() == "wide"
    
    def test_should_force_single_column(self):
        """Test single column forcing"""
        # Narrow window should force single column
        self.adapter.current_window_size = WindowSize(600, 400)
        assert self.adapter.should_force_single_column()
        
        # Wide window should not force single column
        self.adapter.current_window_size = WindowSize(1000, 600)
        assert not self.adapter.should_force_single_column()
    
    def test_get_field_width_for_breakpoint(self):
        """Test field width calculation for breakpoints"""
        # Mobile breakpoint
        self.adapter.current_window_size = WindowSize(400, 300)
        mobile_width = self.adapter.get_field_width_for_breakpoint("short")
        assert mobile_width > 0.3  # Should be wider on mobile
        
        # Desktop breakpoint
        self.adapter.current_window_size = WindowSize(1200, 800)
        desktop_width = self.adapter.get_field_width_for_breakpoint("short")
        assert desktop_width < 0.3  # Should be narrower on desktop


class TestResponsiveFormWidget:
    """Test responsive form widget"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.widget = ResponsiveFormWidget()
    
    def test_set_fields(self):
        """Test setting fields on responsive widget"""
        fields = []
        for i in range(4):
            widget = QLineEdit()
            field = FormField(f"field_{i}", f"Field {i}:", widget, FieldType.SHORT_TEXT)
            fields.append(field)
        
        self.widget.set_fields(fields)
        assert len(self.widget.fields) == 4
        assert len(self.widget.adapter.fields) == 4
    
    def test_add_field(self):
        """Test adding field to responsive widget"""
        # Start with empty
        assert len(self.widget.fields) == 0
        
        # Add field
        widget = QLineEdit()
        field = FormField("test", "Test:", widget, FieldType.SHORT_TEXT)
        self.widget.add_field(field)
        
        assert len(self.widget.fields) == 1
        assert self.widget.fields[0].name == "test"
    
    def test_remove_field(self):
        """Test removing field from responsive widget"""
        # Add fields
        fields = []
        for i in range(3):
            widget = QLineEdit()
            field = FormField(f"field_{i}", f"Field {i}:", widget, FieldType.SHORT_TEXT)
            fields.append(field)
        
        self.widget.set_fields(fields)
        assert len(self.widget.fields) == 3
        
        # Remove field
        self.widget.remove_field("field_1")
        assert len(self.widget.fields) == 2
        assert not any(f.name == "field_1" for f in self.widget.fields)


if __name__ == '__main__':
    pytest.main([__file__])
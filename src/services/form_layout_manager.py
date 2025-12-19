"""
Form Layout Manager

Manages form field layout with intelligent two-column arrangement based on field types and counts.
Implements requirements 12.1-12.4 for document table parts.
"""
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
from PyQt6.QtWidgets import QWidget, QFormLayout, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt6.QtCore import QSize


class FieldType(Enum):
    """Field type classification for layout decisions"""
    SHORT_TEXT = "short_text"  # Text fields with maxLength <= 100
    LONG_TEXT = "long_text"    # Text fields with maxLength > 100 or multiline
    NUMERIC = "numeric"         # Numeric fields (int, float, spinbox)
    DATE = "date"               # Date/datetime fields
    BOOLEAN = "boolean"         # Checkbox fields
    REFERENCE = "reference"     # Reference selector fields
    CALCULATED = "calculated"   # Read-only calculated fields


class FormField:
    """Represents a form field with layout metadata"""
    
    def __init__(
        self,
        name: str,
        label: str,
        widget: QWidget,
        field_type: FieldType = FieldType.SHORT_TEXT,
        max_length: Optional[int] = None,
        is_multiline: bool = False,
        is_required: bool = False
    ):
        self.name = name
        self.label = label
        self.widget = widget
        self.field_type = field_type
        self.max_length = max_length
        self.is_multiline = is_multiline
        self.is_required = is_required
    
    def is_long_string_field(self) -> bool:
        """Check if this field should span full width"""
        if self.field_type == FieldType.LONG_TEXT:
            return True
        if self.is_multiline:
            return True
        if self.max_length and self.max_length > 100:
            return True
        return False
    
    def is_short_field(self) -> bool:
        """Check if this field is suitable for column layout"""
        return not self.is_long_string_field()


class LayoutAnalysis:
    """Analysis result for form layout"""
    
    def __init__(self):
        self.total_fields: int = 0
        self.long_string_fields: List[FormField] = []
        self.short_fields: List[FormField] = []
        self.recommended_layout: str = "single_column"  # or "two_column"
    
    def __repr__(self) -> str:
        return (
            f"LayoutAnalysis(total={self.total_fields}, "
            f"long={len(self.long_string_fields)}, "
            f"short={len(self.short_fields)}, "
            f"layout={self.recommended_layout})"
        )


class LayoutConfiguration:
    """Configuration for two-column layout"""
    
    def __init__(self):
        self.left_column: List[FormField] = []
        self.right_column: List[FormField] = []
        self.full_width_fields: List[FormField] = []
        self.column_ratio: float = 0.5  # 50/50 split by default
    
    def get_left_column_count(self) -> int:
        return len(self.left_column)
    
    def get_right_column_count(self) -> int:
        return len(self.right_column)
    
    def __repr__(self) -> str:
        return (
            f"LayoutConfiguration(left={len(self.left_column)}, "
            f"right={len(self.right_column)}, "
            f"full_width={len(self.full_width_fields)})"
        )


class FormLayoutManager:
    """
    Manages form field layout with intelligent two-column arrangement.
    
    Features:
    - Analyzes field types and counts to determine optimal layout
    - Creates two-column layout for forms with 6+ fields
    - Keeps long string fields in single column
    - Ensures proper field distribution between columns
    """
    
    def __init__(self, min_fields_for_two_columns: int = 6):
        """
        Initialize form layout manager.
        
        Args:
            min_fields_for_two_columns: Minimum number of fields to trigger two-column layout
        """
        self.min_fields_for_two_columns = min_fields_for_two_columns
    
    def analyze_fields(self, fields: List[FormField]) -> LayoutAnalysis:
        """
        Analyze fields to determine optimal layout strategy.
        
        Args:
            fields: List of form fields to analyze
            
        Returns:
            LayoutAnalysis with recommendations
        """
        analysis = LayoutAnalysis()
        analysis.total_fields = len(fields)
        
        # Classify fields
        for field in fields:
            if field.is_long_string_field():
                analysis.long_string_fields.append(field)
            else:
                analysis.short_fields.append(field)
        
        # Determine recommended layout
        # Use two-column if we have enough total fields and enough short fields
        if analysis.total_fields >= self.min_fields_for_two_columns and len(analysis.short_fields) >= 4:
            analysis.recommended_layout = "two_column"
        else:
            analysis.recommended_layout = "single_column"
        
        return analysis
    
    def create_two_column_layout(self, fields: List[FormField]) -> LayoutConfiguration:
        """
        Create two-column layout configuration.
        
        Args:
            fields: List of form fields to arrange
            
        Returns:
            LayoutConfiguration with field distribution
        """
        config = LayoutConfiguration()
        
        # Separate long and short fields
        short_fields = [f for f in fields if f.is_short_field()]
        long_fields = [f for f in fields if not f.is_short_field()]
        
        # Long fields go to full width
        config.full_width_fields = long_fields
        
        # Distribute short fields between columns
        # Try to balance the number of fields in each column
        mid_point = len(short_fields) // 2
        
        config.left_column = short_fields[:mid_point]
        config.right_column = short_fields[mid_point:]
        
        # Adjust ratio if columns are unbalanced
        if len(config.left_column) > 0 and len(config.right_column) > 0:
            ratio = len(config.left_column) / (len(config.left_column) + len(config.right_column))
            config.column_ratio = ratio
        
        return config
    
    def handle_long_string_fields(self, fields: List[FormField]) -> List[FormField]:
        """
        Identify and mark long string fields for full-width layout.
        
        Args:
            fields: List of form fields
            
        Returns:
            List of fields that should span full width
        """
        return [f for f in fields if f.is_long_string_field()]
    
    def create_form_layout(
        self,
        parent: QWidget,
        fields: List[FormField],
        force_layout: Optional[str] = None
    ) -> QVBoxLayout:
        """
        Create complete form layout with fields.
        
        Args:
            parent: Parent widget
            fields: List of form fields to layout
            force_layout: Force specific layout ("single_column" or "two_column")
            
        Returns:
            QVBoxLayout containing the form
        """
        main_layout = QVBoxLayout()
        
        # Analyze fields
        analysis = self.analyze_fields(fields)
        layout_type = force_layout or analysis.recommended_layout
        
        if layout_type == "two_column" and len(analysis.short_fields) >= self.min_fields_for_two_columns:
            # Create two-column layout
            config = self.create_two_column_layout(fields)
            
            # Create grid layout for columns
            grid_layout = QGridLayout()
            
            # Add left column fields
            for i, field in enumerate(config.left_column):
                label_text = field.label
                if field.is_required:
                    label_text += " *"
                grid_layout.addWidget(self._create_label(label_text), i, 0)
                grid_layout.addWidget(field.widget, i, 1)
            
            # Add right column fields
            for i, field in enumerate(config.right_column):
                label_text = field.label
                if field.is_required:
                    label_text += " *"
                grid_layout.addWidget(self._create_label(label_text), i, 2)
                grid_layout.addWidget(field.widget, i, 3)
            
            # Set column stretches
            grid_layout.setColumnStretch(1, 1)  # Left field column
            grid_layout.setColumnStretch(3, 1)  # Right field column
            
            main_layout.addLayout(grid_layout)
            
            # Add full-width fields below
            for field in config.full_width_fields:
                form_layout = QFormLayout()
                label_text = field.label
                if field.is_required:
                    label_text += " *"
                form_layout.addRow(label_text, field.widget)
                main_layout.addLayout(form_layout)
        else:
            # Create single-column layout
            form_layout = QFormLayout()
            for field in fields:
                label_text = field.label
                if field.is_required:
                    label_text += " *"
                form_layout.addRow(label_text, field.widget)
            main_layout.addLayout(form_layout)
        
        return main_layout
    
    def _create_label(self, text: str) -> QWidget:
        """Create label widget"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label
    
    def get_field_type_from_widget(self, widget: QWidget) -> FieldType:
        """
        Determine field type from widget class.
        
        Args:
            widget: Qt widget
            
        Returns:
            FieldType classification
        """
        from PyQt6.QtWidgets import (
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
            QDateEdit, QDateTimeEdit, QCheckBox, QComboBox
        )
        
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            return FieldType.LONG_TEXT
        elif isinstance(widget, QLineEdit):
            max_len = widget.maxLength()
            # QLineEdit default maxLength is 32767, so check for reasonable limits
            if max_len != 32767 and max_len > 100:
                return FieldType.LONG_TEXT
            return FieldType.SHORT_TEXT
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return FieldType.NUMERIC
        elif isinstance(widget, (QDateEdit, QDateTimeEdit)):
            return FieldType.DATE
        elif isinstance(widget, QCheckBox):
            return FieldType.BOOLEAN
        elif isinstance(widget, QComboBox):
            return FieldType.REFERENCE
        else:
            return FieldType.SHORT_TEXT

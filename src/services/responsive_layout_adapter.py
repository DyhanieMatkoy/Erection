"""
Responsive Layout Adapter

Handles window size-based layout adjustments and dynamic layout changes.
Implements requirement 12.5 for document table parts.
"""
from typing import Dict, Any, Optional, Callable
from PyQt6.QtWidgets import QWidget, QLayout
from PyQt6.QtCore import QObject, QSize, QTimer, pyqtSignal
from .form_layout_manager import FormLayoutManager, FormField, LayoutConfiguration


class WindowSize:
    """Window size classification"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
    
    def is_narrow(self, threshold: int = 800) -> bool:
        """Check if window is narrow"""
        return self.width < threshold
    
    def is_wide(self, threshold: int = 1200) -> bool:
        """Check if window is wide"""
        return self.width >= threshold
    
    def __repr__(self) -> str:
        return f"WindowSize({self.width}x{self.height})"


class ResponsiveLayoutRules:
    """Rules for responsive layout behavior"""
    
    def __init__(self):
        # Minimum window width for 2-column layout
        self.min_width_for_two_columns: int = 800
        
        # Field width ratios for different types
        self.field_width_ratios: Dict[str, float] = {
            'short': 0.3,
            'medium': 0.5,
            'long': 1.0,
            'reference': 0.4
        }
        
        # Breakpoints for layout adaptation
        self.breakpoints: Dict[str, int] = {
            'mobile': 480,
            'tablet': 768,
            'desktop': 1024,
            'wide': 1440
        }
    
    def should_use_two_columns(self, window_size: WindowSize, field_count: int) -> bool:
        """Determine if two-column layout should be used"""
        return (
            window_size.width >= self.min_width_for_two_columns and
            field_count >= 6
        )
    
    def get_column_ratio(self, window_size: WindowSize) -> float:
        """Get optimal column ratio based on window size"""
        if window_size.width < self.breakpoints['tablet']:
            return 0.5  # Equal columns on small screens
        elif window_size.width < self.breakpoints['desktop']:
            return 0.45  # Slightly favor right column
        else:
            return 0.4  # More space for right column on large screens


class ResponsiveLayoutAdapter(QObject):
    """
    Handles responsive layout adaptation based on window size changes.
    
    Features:
    - Monitors window size changes
    - Adapts layout based on breakpoints
    - Handles dynamic layout transitions
    - Maintains field distribution optimization
    """
    
    # Signal emitted when layout should be updated
    layout_update_requested = pyqtSignal(str)  # layout_type: "single_column" or "two_column"
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.rules = ResponsiveLayoutRules()
        self.layout_manager = FormLayoutManager()
        self.current_window_size: Optional[WindowSize] = None
        self.current_layout_type: str = "single_column"
        self.fields: list[FormField] = []
        
        # Debounce timer for resize events
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._handle_resize_timeout)
        self.resize_debounce_ms = 150
    
    def set_fields(self, fields: list[FormField]) -> None:
        """Set the fields to be managed"""
        self.fields = fields
    
    def handle_window_resize(self, new_size: QSize) -> None:
        """
        Handle window resize event with debouncing.
        
        Args:
            new_size: New window size
        """
        self.current_window_size = WindowSize(new_size.width(), new_size.height())
        
        # Debounce resize events
        self.resize_timer.start(self.resize_debounce_ms)
    
    def _handle_resize_timeout(self) -> None:
        """Handle resize timeout - perform actual layout adaptation"""
        if not self.current_window_size or not self.fields:
            return
        
        # Determine optimal layout
        should_use_two_columns = self.rules.should_use_two_columns(
            self.current_window_size,
            len([f for f in self.fields if f.is_short_field()])
        )
        
        new_layout_type = "two_column" if should_use_two_columns else "single_column"
        
        # Only emit signal if layout type changed
        if new_layout_type != self.current_layout_type:
            self.current_layout_type = new_layout_type
            self.layout_update_requested.emit(new_layout_type)
    
    def adapt_to_window_size(
        self,
        layout: LayoutConfiguration,
        window_size: WindowSize
    ) -> LayoutConfiguration:
        """
        Adapt layout configuration to window size.
        
        Args:
            layout: Current layout configuration
            window_size: Current window size
            
        Returns:
            Adapted layout configuration
        """
        adapted_layout = LayoutConfiguration()
        adapted_layout.full_width_fields = layout.full_width_fields.copy()
        
        # Get optimal column ratio
        optimal_ratio = self.rules.get_column_ratio(window_size)
        adapted_layout.column_ratio = optimal_ratio
        
        # Redistribute fields based on new ratio
        all_short_fields = layout.left_column + layout.right_column
        if all_short_fields:
            split_point = int(len(all_short_fields) * optimal_ratio)
            adapted_layout.left_column = all_short_fields[:split_point]
            adapted_layout.right_column = all_short_fields[split_point:]
        
        return adapted_layout
    
    def get_current_breakpoint(self) -> str:
        """Get current breakpoint name"""
        if not self.current_window_size:
            return "desktop"
        
        width = self.current_window_size.width
        
        if width < self.rules.breakpoints['mobile']:
            return "mobile"
        elif width < self.rules.breakpoints['tablet']:
            return "tablet"
        elif width < self.rules.breakpoints['wide']:
            return "desktop"
        else:
            return "wide"
    
    def should_force_single_column(self) -> bool:
        """Check if single column should be forced due to narrow window"""
        if not self.current_window_size:
            return False
        
        return self.current_window_size.width < self.rules.min_width_for_two_columns
    
    def get_field_width_for_breakpoint(self, field_type: str) -> float:
        """Get optimal field width ratio for current breakpoint"""
        breakpoint = self.get_current_breakpoint()
        base_ratio = self.rules.field_width_ratios.get(field_type, 0.5)
        
        # Adjust based on breakpoint
        if breakpoint == "mobile":
            return min(base_ratio * 1.2, 1.0)  # Wider fields on mobile
        elif breakpoint == "tablet":
            return base_ratio
        else:
            return base_ratio * 0.9  # Slightly narrower on desktop


class ResponsiveFormWidget(QWidget):
    """
    Widget that automatically adapts its form layout based on window size.
    
    This is a convenience widget that combines FormLayoutManager and ResponsiveLayoutAdapter
    to provide automatic responsive behavior.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.layout_manager = FormLayoutManager()
        self.adapter = ResponsiveLayoutAdapter(self)
        self.fields: list[FormField] = []
        self.current_layout: Optional[QLayout] = None
        
        # Connect adapter signals
        self.adapter.layout_update_requested.connect(self._rebuild_layout)
    
    def set_fields(self, fields: list[FormField]) -> None:
        """Set form fields and build initial layout"""
        self.fields = fields
        self.adapter.set_fields(fields)
        self._rebuild_layout()
    
    def add_field(self, field: FormField) -> None:
        """Add a single field and rebuild layout"""
        self.fields.append(field)
        self.adapter.set_fields(self.fields)
        self._rebuild_layout()
    
    def remove_field(self, field_name: str) -> None:
        """Remove field by name and rebuild layout"""
        self.fields = [f for f in self.fields if f.name != field_name]
        self.adapter.set_fields(self.fields)
        self._rebuild_layout()
    
    def _rebuild_layout(self, layout_type: Optional[str] = None) -> None:
        """Rebuild the form layout"""
        if not self.fields:
            return
        
        # Clear existing layout
        if self.current_layout:
            self._clear_layout(self.current_layout)
        
        # Create new layout
        new_layout = self.layout_manager.create_form_layout(
            self,
            self.fields,
            force_layout=layout_type
        )
        
        self.setLayout(new_layout)
        self.current_layout = new_layout
    
    def _clear_layout(self, layout: QLayout) -> None:
        """Clear all items from layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self._clear_layout(child.layout())
    
    def resizeEvent(self, event) -> None:
        """Handle resize events"""
        super().resizeEvent(event)
        self.adapter.handle_window_resize(event.size())
    
    def force_layout_type(self, layout_type: str) -> None:
        """Force specific layout type"""
        self._rebuild_layout(layout_type)
"""Compact reference field component with inline buttons"""
from PyQt6.QtWidgets import QLineEdit, QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter
from typing import Optional, Dict, Any, List


class CompactReferenceField(QLineEdit):
    """
    Compact reference field with inline 'o' and selector buttons positioned inside the field.
    
    Requirements 11.1, 11.2, 11.5:
    - Compact 'o' button and selector button inside field without external spacing
    - Adequate space for text display
    - Buttons positioned inside field
    """
    
    # Signal when reference value changes
    value_changed = pyqtSignal(int, str)  # id, name
    # Signal when open button is clicked
    open_requested = pyqtSignal()
    # Signal when selector button is clicked
    selector_requested = pyqtSignal()
    # Signal when related fields are filled
    related_fields_filled = pyqtSignal(dict)  # related field data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reference_id = 0
        self.reference_name = ""
        self.reference_table = ""
        self.reference_title = "Выбор из справочника"
        self.related_fields: List[str] = []
        self.allow_create = False
        self.allow_edit = True
        
        # Button dimensions
        self.button_width = 24
        self.button_height = 22
        self.button_spacing = 2
        self.right_margin = 4
        
        self.setup_ui()
        self.setup_buttons()
    
    def setup_ui(self):
        """Setup UI components"""
        self.setReadOnly(True)
        self.setPlaceholderText("Не выбрано")
        
        # Calculate padding for buttons
        total_button_width = (self.button_width * 2) + self.button_spacing + self.right_margin
        self.setStyleSheet(f"""
            QLineEdit {{
                padding-right: {total_button_width + 4}px;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding-left: 4px;
                padding-top: 2px;
                padding-bottom: 2px;
            }}
            QLineEdit:focus {{
                border-color: #0056b3;
                outline: none;
            }}
        """)
    
    def setup_buttons(self):
        """Setup inline buttons"""
        # We'll draw buttons manually in paintEvent
        pass
    
    def set_reference_config(self, reference_type: str, title: str = None, 
                           related_fields: List[str] = None, allow_create: bool = False, 
                           allow_edit: bool = True):
        """Set reference configuration"""
        self.reference_table = reference_type
        self.reference_title = title or f"Выбор из справочника: {reference_type}"
        self.related_fields = related_fields or []
        self.allow_create = allow_create
        self.allow_edit = allow_edit
    
    def set_value(self, ref_id: int, name: str):
        """Set reference value"""
        self.reference_id = ref_id
        self.reference_name = name
        self.setText(name if name else "")
        self.value_changed.emit(ref_id, name)
    
    def get_value(self) -> tuple[int, str]:
        """Get current value as (id, name) tuple"""
        return (self.reference_id, self.reference_name)
    
    def clear_value(self):
        """Clear reference value"""
        self.set_value(0, "")
    
    def get_button_rects(self) -> tuple[QRect, QRect]:
        """Calculate button rectangles"""
        widget_rect = self.rect()
        
        # Calculate positions from right edge
        selector_x = widget_rect.width() - self.right_margin - self.button_width
        open_x = selector_x - self.button_spacing - self.button_width
        
        # Center vertically
        y = (widget_rect.height() - self.button_height) // 2
        
        open_rect = QRect(open_x, y, self.button_width, self.button_height)
        selector_rect = QRect(selector_x, y, self.button_width, self.button_height)
        
        return open_rect, selector_rect
    
    def paintEvent(self, event):
        """Paint the field and buttons"""
        # Paint the base line edit
        super().paintEvent(event)
        
        # Paint buttons
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        open_rect, selector_rect = self.get_button_rects()
        
        # Paint open button ('o')
        self.paint_button(painter, open_rect, "o", "Открыть элемент")
        
        # Paint selector button ('▼')
        self.paint_button(painter, selector_rect, "▼", "Выбрать из списка")
    
    def paint_button(self, painter: QPainter, rect: QRect, text: str, tooltip: str):
        """Paint a single button"""
        # Button background
        painter.fillRect(rect, Qt.GlobalColor.lightGray)
        
        # Button border
        painter.setPen(Qt.GlobalColor.gray)
        painter.drawRect(rect)
        
        # Button text
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for buttons"""
        if event.button() == Qt.MouseButton.LeftButton:
            open_rect, selector_rect = self.get_button_rects()
            
            pos = event.pos()
            
            if open_rect.contains(pos):
                self.open_reference()
                return
            elif selector_rect.contains(pos):
                self.select_reference()
                return
        
        super().mousePressEvent(event)
    
    def open_reference(self):
        """Open reference element for viewing/editing"""
        if self.reference_id > 0 and self.allow_edit:
            self.open_requested.emit()
            
            # Open appropriate form based on reference type
            try:
                form = None
                if self.reference_table == "works":
                    from ..work_form import WorkForm
                    form = WorkForm(self.reference_id)
                elif self.reference_table == "counterparties":
                    from ..counterparty_form import CounterpartyForm
                    form = CounterpartyForm(self.reference_id)
                elif self.reference_table == "objects":
                    from ..object_form import ObjectForm
                    form = ObjectForm(self.reference_id)
                elif self.reference_table == "organizations":
                    from ..organization_form import OrganizationForm
                    form = OrganizationForm(self.reference_id)
                elif self.reference_table == "persons":
                    from ..person_form import PersonForm
                    form = PersonForm(self.reference_id)
                
                if form:
                    # Store reference to prevent garbage collection
                    self._edit_form = form
                    
                    # Connect to form closed signal to refresh if needed
                    if hasattr(form, 'finished'):
                        form.finished.connect(self._on_edit_form_closed)
                    elif hasattr(form, 'destroyed'):
                        form.destroyed.connect(self._on_edit_form_closed)
                    
                    form.show()
                    form.raise_()
                    form.activateWindow()
                    
            except ImportError as e:
                print(f"Could not import form for {self.reference_table}: {e}")
            except Exception as e:
                print(f"Error opening reference form: {e}")
    
    def _on_edit_form_closed(self):
        """Handle edit form closed"""
        self._edit_form = None
    
    def select_reference(self):
        """Open reference selector dialog"""
        if not self.reference_table:
            return
        
        self.selector_requested.emit()
        
        from ..reference_picker_dialog import ReferencePickerDialog
        dialog = ReferencePickerDialog(
            self.reference_table, 
            self.reference_title, 
            self.parentWidget(),
            current_id=self.reference_id
        )
        
        if dialog.exec():
            selected_id, selected_name = dialog.get_selected()
            self.set_value(selected_id, selected_name)
            
            # Fill related fields if configured
            if self.related_fields:
                self.fill_related_fields(selected_id)
    
    def fill_related_fields(self, reference_id: int):
        """Fill related fields based on selected reference"""
        if not self.related_fields or reference_id <= 0:
            return
        
        try:
            from ...data.database_manager import DatabaseManager
            db = DatabaseManager().get_connection()
            cursor = db.cursor()
            
            # Get reference data with related fields
            related_data = self._fetch_reference_data(cursor, reference_id)
            
            if related_data:
                # Emit signal with related field data
                self.related_fields_filled.emit(related_data)
                
        except Exception as e:
            print(f"Error filling related fields: {e}")
    
    def _fetch_reference_data(self, cursor, reference_id: int) -> Dict[str, Any]:
        """Fetch reference data for filling related fields"""
        if self.reference_table == "works":
            cursor.execute("""
                SELECT w.*, u.name as unit_name, u.id as unit_id
                FROM works w
                LEFT JOIN units u ON w.unit_id = u.id
                WHERE w.id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'unit_id': row.get('unit_id'),
                    'unit_name': row.get('unit_name'),
                    'price': row.get('price', 0),
                    'code': row.get('code', ''),
                    'name': row.get('name', '')
                }
        
        elif self.reference_table == "counterparties":
            cursor.execute("""
                SELECT c.*, o.name as organization_name, o.id as organization_id
                FROM counterparties c
                LEFT JOIN organizations o ON c.organization_id = o.id
                WHERE c.id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'organization_id': row.get('organization_id'),
                    'organization_name': row.get('organization_name'),
                    'phone': row.get('phone', ''),
                    'email': row.get('email', '')
                }
        
        return {}
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F4:
            # F4: Open selector
            self.select_reference()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter: Open selector
            self.select_reference()
        else:
            super().keyPressEvent(event)
    
    def sizeHint(self):
        """Return appropriate size hint"""
        hint = super().sizeHint()
        # Ensure minimum width for text + buttons
        min_width = 150 + (self.button_width * 2) + self.button_spacing + self.right_margin
        hint.setWidth(max(hint.width(), min_width))
        return hint
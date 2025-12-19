"""Test compact reference field component"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtTest import QTest

# Add src to path for imports
sys.path.insert(0, 'src')

from src.views.components.compact_reference_field import CompactReferenceField


@pytest.fixture
def app():
    """Create QApplication instance"""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def compact_field(app):
    """Create CompactReferenceField instance"""
    field = CompactReferenceField()
    return field


class TestCompactReferenceField:
    """Test cases for CompactReferenceField component"""
    
    def test_initialization(self, compact_field):
        """Test field initialization"""
        assert compact_field.reference_id == 0
        assert compact_field.reference_name == ""
        assert compact_field.reference_table == ""
        assert compact_field.reference_title == "Выбор из справочника"
        assert compact_field.related_fields == []
        assert compact_field.allow_create == False
        assert compact_field.allow_edit == True
    
    def test_set_reference_config(self, compact_field):
        """Test setting reference configuration"""
        compact_field.set_reference_config(
            reference_type="works",
            title="Выбор работы",
            related_fields=["unit", "price"],
            allow_create=True,
            allow_edit=True
        )
        
        assert compact_field.reference_table == "works"
        assert compact_field.reference_title == "Выбор работы"
        assert compact_field.related_fields == ["unit", "price"]
        assert compact_field.allow_create == True
        assert compact_field.allow_edit == True
    
    def test_set_value(self, compact_field):
        """Test setting reference value"""
        # Connect signal to capture emissions
        signal_received = []
        compact_field.value_changed.connect(lambda id, name: signal_received.append((id, name)))
        
        compact_field.set_value(123, "Test Item")
        
        assert compact_field.reference_id == 123
        assert compact_field.reference_name == "Test Item"
        assert compact_field.text() == "Test Item"
        assert len(signal_received) == 1
        assert signal_received[0] == (123, "Test Item")
    
    def test_get_value(self, compact_field):
        """Test getting reference value"""
        compact_field.set_value(456, "Another Item")
        
        id_val, name_val = compact_field.get_value()
        assert id_val == 456
        assert name_val == "Another Item"
    
    def test_clear_value(self, compact_field):
        """Test clearing reference value"""
        compact_field.set_value(789, "Item to Clear")
        compact_field.clear_value()
        
        assert compact_field.reference_id == 0
        assert compact_field.reference_name == ""
        assert compact_field.text() == ""
    
    def test_button_rects_calculation(self, compact_field):
        """Test button rectangle calculation"""
        # Set a known size
        compact_field.resize(200, 30)
        
        open_rect, selector_rect = compact_field.get_button_rects()
        
        # Check that rectangles are properly positioned
        assert open_rect.width() == compact_field.button_width
        assert open_rect.height() == compact_field.button_height
        assert selector_rect.width() == compact_field.button_width
        assert selector_rect.height() == compact_field.button_height
        
        # Selector should be to the right of open button
        assert selector_rect.x() > open_rect.x()
    
    @patch('src.views.components.compact_reference_field.ReferencePickerDialog')
    def test_select_reference(self, mock_dialog_class, compact_field):
        """Test reference selection"""
        # Setup mock dialog
        mock_dialog = Mock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_selected.return_value = (999, "Selected Item")
        mock_dialog_class.return_value = mock_dialog
        
        # Set reference config
        compact_field.set_reference_config("works", "Test Works")
        
        # Connect signals
        signal_received = []
        compact_field.value_changed.connect(lambda id, name: signal_received.append((id, name)))
        
        # Call select_reference
        compact_field.select_reference()
        
        # Verify dialog was created and shown
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # Verify value was set
        assert len(signal_received) == 1
        assert signal_received[0] == (999, "Selected Item")
    
    def test_keyboard_shortcuts(self, compact_field):
        """Test keyboard shortcuts"""
        # Mock the select_reference method
        compact_field.select_reference = Mock()
        
        # Test F4 key
        QTest.keyPress(compact_field, Qt.Key.Key_F4)
        compact_field.select_reference.assert_called_once()
        
        # Reset mock
        compact_field.select_reference.reset_mock()
        
        # Test Enter key
        QTest.keyPress(compact_field, Qt.Key.Key_Return)
        compact_field.select_reference.assert_called_once()
    
    def test_mouse_click_on_buttons(self, compact_field):
        """Test mouse clicks on buttons"""
        # Set size and show widget
        compact_field.resize(200, 30)
        compact_field.show()
        
        # Mock methods
        compact_field.open_reference = Mock()
        compact_field.select_reference = Mock()
        
        # Get button positions
        open_rect, selector_rect = compact_field.get_button_rects()
        
        # Click on open button
        QTest.mouseClick(compact_field, Qt.MouseButton.LeftButton, 
                        Qt.KeyboardModifier.NoModifier, open_rect.center())
        
        # Click on selector button
        QTest.mouseClick(compact_field, Qt.MouseButton.LeftButton, 
                        Qt.KeyboardModifier.NoModifier, selector_rect.center())
        
        # Note: Due to the way mouse events work in tests, we might need to
        # simulate the events differently. This is a basic structure.
    
    def test_size_hint(self, compact_field):
        """Test size hint calculation"""
        hint = compact_field.sizeHint()
        
        # Should have minimum width for text + buttons
        expected_min_width = 150 + (compact_field.button_width * 2) + compact_field.button_spacing + compact_field.right_margin
        assert hint.width() >= expected_min_width
    
    @patch('src.views.components.compact_reference_field.DatabaseManager')
    def test_fill_related_fields_works(self, mock_db_manager, compact_field):
        """Test filling related fields for works reference"""
        # Setup mock database
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        mock_db_manager.return_value.get_connection.return_value = mock_db
        
        # Mock database response
        mock_cursor.fetchone.return_value = {
            'unit_id': 5,
            'unit_name': 'м²',
            'price': 100.50,
            'code': 'W001',
            'name': 'Test Work'
        }
        
        # Set up field
        compact_field.set_reference_config("works", related_fields=["unit", "price"])
        
        # Connect signal
        signal_received = []
        compact_field.related_fields_filled.connect(lambda data: signal_received.append(data))
        
        # Call method
        compact_field.fill_related_fields(123)
        
        # Verify database was queried
        mock_cursor.execute.assert_called_once()
        
        # Verify signal was emitted with correct data
        assert len(signal_received) == 1
        data = signal_received[0]
        assert data['unit_id'] == 5
        assert data['unit_name'] == 'м²'
        assert data['price'] == 100.50


if __name__ == "__main__":
    pytest.main([__file__])
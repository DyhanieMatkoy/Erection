"""Property-based tests for Modal Dialog Manager

This module contains property-based tests using Hypothesis to verify
the correctness of modal dialog z-index management, stacking order,
and focus management in the ModalDialogManager.
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt

from hypothesis import given, strategies as st, settings, HealthCheck

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.modal_dialog_manager import ModalDialogManager, DialogState
from src.views.reference_picker_dialog import ReferencePickerDialog


class TestModalDialogManager:
    """Test suite for ModalDialogManager functionality"""
    
    @pytest.fixture(scope="function")
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # Clean up any remaining dialogs
        manager = ModalDialogManager.instance()
        manager.cleanup_all()
    
    @pytest.fixture
    def dialog_manager(self, app):
        """Create a fresh ModalDialogManager instance"""
        # Reset singleton state for testing
        ModalDialogManager._instance = None
        manager = ModalDialogManager.instance()
        yield manager
        manager.cleanup_all()
        # Reset again after test
        ModalDialogManager._instance = None
    
    @pytest.fixture
    def mock_dialog(self, app):
        """Create a mock QDialog for testing"""
        dialog = Mock(spec=QDialog)
        dialog.finished = Mock()
        dialog.finished.connect = Mock()
        dialog.setModal = Mock()
        dialog.setProperty = Mock()
        dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        dialog.setWindowFlags = Mock()
        dialog.raise_ = Mock()
        dialog.activateWindow = Mock()
        dialog.close = Mock()
        dialog.exec = Mock(return_value=QDialog.DialogCode.Accepted)
        dialog.show = Mock()
        return dialog
    
    def test_singleton_pattern(self, app):
        """Test that ModalDialogManager follows singleton pattern"""
        manager1 = ModalDialogManager.instance()
        manager2 = ModalDialogManager.instance()
        assert manager1 is manager2
    
    def test_dialog_registration_basic(self, dialog_manager, mock_dialog):
        """Test basic dialog registration"""
        dialog_id = dialog_manager.register_dialog(mock_dialog, 'modal')
        
        assert dialog_id is not None
        assert dialog_id in dialog_manager.dialog_registry
        assert len(dialog_manager.dialog_stack) == 1
        assert dialog_manager.get_dialog_count() == 1
    
    def test_dialog_unregistration(self, dialog_manager, mock_dialog):
        """Test dialog unregistration"""
        dialog_id = dialog_manager.register_dialog(mock_dialog, 'modal')
        
        success = dialog_manager.unregister_dialog(dialog_id)
        
        assert success is True
        assert dialog_id not in dialog_manager.dialog_registry
        assert len(dialog_manager.dialog_stack) == 0
        assert dialog_manager.get_dialog_count() == 0
    
    def test_invalid_dialog_type_raises_error(self, dialog_manager):
        """Test that registering non-QWidget raises ValueError"""
        with pytest.raises(ValueError, match="Only QWidget or QDialog instances can be registered"):
            dialog_manager.register_dialog("not a dialog", 'modal')
    
    def test_invalid_modal_type_raises_error(self, dialog_manager, mock_dialog):
        """Test that invalid modal_type raises ValueError"""
        with pytest.raises(ValueError, match="modal_type must be 'modal' or 'non-modal'"):
            dialog_manager.register_dialog(mock_dialog, 'invalid')
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dialog_count=st.integers(min_value=1, max_value=10))
    def test_property_1_modal_dialog_z_index_monotonicity(self, dialog_manager, app, dialog_count):
        """**Feature: modal-dialog-improvements, Property 1: Modal Dialog Z-Index Monotonicity**
        
        For any sequence of modal dialog open operations, each newly opened dialog 
        should have a z-index strictly greater than all previously opened dialogs
        """
        dialogs = []
        dialog_ids = []
        z_indices = []
        
        # Create and register multiple dialogs
        for i in range(dialog_count):
            dialog = Mock(spec=QDialog)
            dialog.finished = Mock()
            dialog.finished.connect = Mock()
            dialog.setModal = Mock()
            dialog.setProperty = Mock()
            dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
            dialog.setWindowFlags = Mock()
            dialog.raise_ = Mock()
            dialog.activateWindow = Mock()
            dialog.close = Mock()
            
            dialog_id = dialog_manager.register_dialog(dialog, 'modal')
            
            dialogs.append(dialog)
            dialog_ids.append(dialog_id)
            
            # Get the z-index that was assigned
            dialog_state = dialog_manager.dialog_registry[dialog_id]
            z_indices.append(dialog_state.z_index)
        
        # Verify z-index monotonicity: each dialog should have higher z-index than previous
        for i in range(1, len(z_indices)):
            assert z_indices[i] > z_indices[i-1], f"Dialog {i} z-index {z_indices[i]} should be > dialog {i-1} z-index {z_indices[i-1]}"
        
        # Verify all z-indices are unique
        assert len(set(z_indices)) == len(z_indices), "All z-indices should be unique"
        
        # Clean up
        for dialog_id in dialog_ids:
            dialog_manager.unregister_dialog(dialog_id)
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        modal_types=st.lists(
            st.sampled_from(['modal', 'non-modal']), 
            min_size=1, 
            max_size=5
        )
    )
    def test_property_2_edit_form_visibility_over_selector(self, dialog_manager, app, modal_types):
        """**Feature: modal-dialog-improvements, Property 2: Edit Form Visibility Over Selector**
        
        For any work selector dialog, when the edit button is clicked, the resulting 
        work form should have a higher z-index than the selector and be fully visible
        """
        parent_dialog = Mock(spec=QDialog)
        parent_dialog.finished = Mock()
        parent_dialog.finished.connect = Mock()
        parent_dialog.setModal = Mock()
        parent_dialog.setProperty = Mock()
        parent_dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        parent_dialog.setWindowFlags = Mock()
        parent_dialog.raise_ = Mock()
        parent_dialog.activateWindow = Mock()
        parent_dialog.close = Mock()
        
        # Register parent dialog (work selector)
        parent_id = dialog_manager.register_dialog(parent_dialog, modal_types[0])
        parent_z_index = dialog_manager.dialog_registry[parent_id].z_index
        
        # Register child dialogs (edit forms)
        child_ids = []
        for i, modal_type in enumerate(modal_types[1:], 1):
            child_dialog = Mock(spec=QDialog)
            child_dialog.finished = Mock()
            child_dialog.finished.connect = Mock()
            child_dialog.setModal = Mock()
            child_dialog.setProperty = Mock()
            child_dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
            child_dialog.setWindowFlags = Mock()
            child_dialog.raise_ = Mock()
            child_dialog.activateWindow = Mock()
            child_dialog.close = Mock()
            
            child_id = dialog_manager.register_dialog(child_dialog, modal_type, parent_id)
            child_ids.append(child_id)
            
            # Verify child has higher z-index than parent
            child_z_index = dialog_manager.dialog_registry[child_id].z_index
            assert child_z_index > parent_z_index, f"Child dialog z-index {child_z_index} should be > parent z-index {parent_z_index}"
        
        # Clean up
        for child_id in child_ids:
            dialog_manager.unregister_dialog(child_id)
        dialog_manager.unregister_dialog(parent_id)
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dialog_sequence=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=8))
    def test_property_3_focus_return_after_dialog_close(self, dialog_manager, app, dialog_sequence):
        """**Feature: modal-dialog-improvements, Property 3: Focus Return After Dialog Close**
        
        For any modal dialog opened from another dialog, closing the child dialog 
        should return focus to the parent dialog
        """
        dialogs = []
        dialog_ids = []
        
        # Create a chain of dialogs where each is a child of the previous
        parent_id = None
        for i, name in enumerate(dialog_sequence):
            dialog = Mock(spec=QDialog)
            dialog.finished = Mock()
            dialog.finished.connect = Mock()
            dialog.setModal = Mock()
            dialog.setProperty = Mock()
            dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
            dialog.setWindowFlags = Mock()
            dialog.raise_ = Mock()
            dialog.activateWindow = Mock()
            dialog.close = Mock()
            dialog.name = name  # For debugging
            
            dialog_id = dialog_manager.register_dialog(dialog, 'modal', parent_id)
            
            dialogs.append(dialog)
            dialog_ids.append(dialog_id)
            parent_id = dialog_id
        
        # Verify that the topmost dialog is the last one added
        top_dialog = dialog_manager.get_top_dialog()
        assert top_dialog is not None
        assert top_dialog.id == dialog_ids[-1]
        
        # Close dialogs from top to bottom and verify focus management
        for i in range(len(dialog_ids) - 1, 0, -1):
            current_dialog_id = dialog_ids[i]
            expected_parent_id = dialog_ids[i - 1]
            
            # Simulate dialog finished signal
            dialog_manager._on_dialog_finished(current_dialog_id)
            
            # Verify the parent dialog is now on top
            top_dialog = dialog_manager.get_top_dialog()
            if top_dialog:  # If there are still dialogs in stack
                assert top_dialog.id == expected_parent_id
                # Verify focus management was called
                parent_dialog = dialog_manager.get_dialog_by_id(expected_parent_id)
                if parent_dialog:
                    parent_dialog.raise_.assert_called()
                    parent_dialog.activateWindow.assert_called()
        
        # Clean up remaining dialog
        if dialog_ids:
            dialog_manager.unregister_dialog(dialog_ids[0])
    
    def test_bring_to_front_functionality(self, dialog_manager, app):
        """Test bring_to_front functionality"""
        # Create three dialogs
        dialogs = []
        dialog_ids = []
        
        for i in range(3):
            dialog = Mock(spec=QDialog)
            dialog.finished = Mock()
            dialog.finished.connect = Mock()
            dialog.setModal = Mock()
            dialog.setProperty = Mock()
            dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
            dialog.setWindowFlags = Mock()
            dialog.raise_ = Mock()
            dialog.activateWindow = Mock()
            dialog.close = Mock()
            
            dialog_id = dialog_manager.register_dialog(dialog, 'modal')
            dialogs.append(dialog)
            dialog_ids.append(dialog_id)
        
        # Bring the first dialog to front
        success = dialog_manager.bring_to_front(dialog_ids[0])
        assert success is True
        
        # Verify it's now on top
        top_dialog = dialog_manager.get_top_dialog()
        assert top_dialog.id == dialog_ids[0]
        
        # Verify focus management was called
        dialogs[0].raise_.assert_called()
        dialogs[0].activateWindow.assert_called()
        
        # Clean up
        for dialog_id in dialog_ids:
            dialog_manager.unregister_dialog(dialog_id)
    
    def test_get_dialogs_by_type(self, dialog_manager, app):
        """Test filtering dialogs by type"""
        modal_dialog = Mock(spec=QDialog)
        modal_dialog.finished = Mock()
        modal_dialog.finished.connect = Mock()
        modal_dialog.setModal = Mock()
        modal_dialog.setProperty = Mock()
        modal_dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        modal_dialog.setWindowFlags = Mock()
        
        non_modal_dialog = Mock(spec=QDialog)
        non_modal_dialog.finished = Mock()
        non_modal_dialog.finished.connect = Mock()
        non_modal_dialog.setModal = Mock()
        non_modal_dialog.setProperty = Mock()
        non_modal_dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        non_modal_dialog.setWindowFlags = Mock()
        
        modal_id = dialog_manager.register_dialog(modal_dialog, 'modal')
        non_modal_id = dialog_manager.register_dialog(non_modal_dialog, 'non-modal')
        
        modal_dialogs = dialog_manager.get_dialogs_by_type('modal')
        non_modal_dialogs = dialog_manager.get_dialogs_by_type('non-modal')
        
        assert len(modal_dialogs) == 1
        assert len(non_modal_dialogs) == 1
        assert modal_dialogs[0].id == modal_id
        assert non_modal_dialogs[0].id == non_modal_id
        
        # Clean up
        dialog_manager.unregister_dialog(modal_id)
        dialog_manager.unregister_dialog(non_modal_id)
    
    def test_get_child_dialogs(self, dialog_manager, app):
        """Test getting child dialogs of a parent"""
        parent_dialog = Mock(spec=QDialog)
        parent_dialog.finished = Mock()
        parent_dialog.finished.connect = Mock()
        parent_dialog.setModal = Mock()
        parent_dialog.setProperty = Mock()
        parent_dialog.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        parent_dialog.setWindowFlags = Mock()
        
        child_dialog1 = Mock(spec=QDialog)
        child_dialog1.finished = Mock()
        child_dialog1.finished.connect = Mock()
        child_dialog1.setModal = Mock()
        child_dialog1.setProperty = Mock()
        child_dialog1.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        child_dialog1.setWindowFlags = Mock()
        
        child_dialog2 = Mock(spec=QDialog)
        child_dialog2.finished = Mock()
        child_dialog2.finished.connect = Mock()
        child_dialog2.setModal = Mock()
        child_dialog2.setProperty = Mock()
        child_dialog2.windowFlags = Mock(return_value=Qt.WindowType.Dialog)
        child_dialog2.setWindowFlags = Mock()
        
        parent_id = dialog_manager.register_dialog(parent_dialog, 'modal')
        child_id1 = dialog_manager.register_dialog(child_dialog1, 'modal', parent_id)
        child_id2 = dialog_manager.register_dialog(child_dialog2, 'modal', parent_id)
        
        child_dialogs = dialog_manager.get_child_dialogs(parent_id)
        
        assert len(child_dialogs) == 2
        child_ids = [dialog.id for dialog in child_dialogs]
        assert child_id1 in child_ids
        assert child_id2 in child_ids
        
        # Clean up
        dialog_manager.unregister_dialog(child_id1)
        dialog_manager.unregister_dialog(child_id2)
        dialog_manager.unregister_dialog(parent_id)


class TestReferencePickerDialogIntegration:
    """Test suite for ReferencePickerDialog integration with ModalDialogManager"""
    
    @pytest.fixture(scope="function")
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # Clean up any remaining dialogs
        manager = ModalDialogManager.instance()
        manager.cleanup_all()
    
    @pytest.fixture
    def dialog_manager(self, app):
        """Create a fresh ModalDialogManager instance"""
        # Reset singleton state for testing
        ModalDialogManager._instance = None
        manager = ModalDialogManager.instance()
        yield manager
        manager.cleanup_all()
        # Reset again after test
        ModalDialogManager._instance = None
    
    @patch('src.views.reference_picker_dialog.DatabaseManager')
    def test_reference_picker_dialog_modal_type_setting(self, mock_db_manager, dialog_manager, app):
        """Test that ReferencePickerDialog respects modal_type parameter"""
        # Mock the database manager
        mock_db_manager.return_value.get_connection.return_value.cursor.return_value.fetchall.return_value = []
        
        # Test modal dialog
        modal_dialog = ReferencePickerDialog("works", modal_type='modal')
        assert modal_dialog.modal_type == 'modal'
        
        # Test non-modal dialog
        non_modal_dialog = ReferencePickerDialog("works", modal_type='non-modal')
        assert non_modal_dialog.modal_type == 'non-modal'
    
    @patch('src.views.reference_picker_dialog.DatabaseManager')
    def test_reference_picker_dialog_manager_integration(self, mock_db_manager, dialog_manager, app):
        """Test that ReferencePickerDialog integrates with ModalDialogManager"""
        # Mock the database manager
        mock_db_manager.return_value.get_connection.return_value.cursor.return_value.fetchall.return_value = []
        
        dialog = ReferencePickerDialog("works", modal_type='modal')
        
        # Verify dialog manager is set
        assert dialog.dialog_manager is not None
        assert isinstance(dialog.dialog_manager, ModalDialogManager)
        
        # Test show_with_proper_z_index method exists
        assert hasattr(dialog, 'show_with_proper_z_index')
        assert hasattr(dialog, 'bring_to_front')
        assert hasattr(dialog, 'closeEvent')


if __name__ == "__main__":
    pytest.main([__file__])
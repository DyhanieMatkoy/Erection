"""Modal Dialog Manager for PyQt6 desktop application

This module provides centralized management of modal dialogs with proper z-index
handling and stacking order management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from PyQt6.QtWidgets import QDialog, QWidget
    from PyQt6.QtCore import QObject, pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    # For testing without PyQt6
    PYQT_AVAILABLE = False
    class QObject:
        def __init__(self):
            pass
    def pyqtSignal(type_):
        return None

logger = logging.getLogger(__name__)


@dataclass
class DialogState:
    """Represents the state of a managed dialog"""
    id: str
    dialog: Any  # QDialog when PyQt6 is available
    z_index: int
    modal_type: str  # 'modal' or 'non-modal'
    parent_id: Optional[str]
    created_at: datetime


class ModalDialogManager:
    """Singleton class for managing modal dialog z-index and stacking order
    
    This class ensures proper layering of modal dialogs by:
    - Tracking all open dialogs in a stack
    - Automatically assigning z-index values based on stack position
    - Managing dialog registration and cleanup
    - Providing focus management when dialogs are closed
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the modal dialog manager"""
        if not self._initialized:
            self.dialog_stack: List[DialogState] = []
            self.dialog_registry: Dict[str, DialogState] = {}
            self.base_z_index = 1000
            self.z_index_increment = 10
            self._dialog_counter = 0
            self._initialized = True
            logger.info("ModalDialogManager initialized")
    
    @classmethod
    def instance(cls) -> 'ModalDialogManager':
        """Get the singleton instance"""
        return cls()
    
    def register_dialog(self, dialog: Any, modal_type: str = 'modal', 
                       parent_dialog_id: Optional[str] = None) -> str:
        """Register a dialog with the manager
        
        Args:
            dialog: The QDialog or QWidget instance to register
            modal_type: Either 'modal' or 'non-modal'
            parent_dialog_id: ID of parent dialog if this is a child dialog
            
        Returns:
            str: Unique dialog ID for tracking
        """
        # Check if it's a valid Qt widget/dialog
        if PYQT_AVAILABLE:
            try:
                from PyQt6.QtWidgets import QWidget
                if not isinstance(dialog, QWidget):
                    raise ValueError("Only QWidget or QDialog instances can be registered")
            except ImportError:
                # Fallback check for basic attributes
                if not hasattr(dialog, 'show') or not hasattr(dialog, 'close'):
                    raise ValueError("Only QWidget or QDialog instances can be registered")
        
        if modal_type not in ['modal', 'non-modal']:
            raise ValueError("modal_type must be 'modal' or 'non-modal'")
        
        # Generate unique dialog ID
        self._dialog_counter += 1
        dialog_id = f"dialog_{self._dialog_counter}_{id(dialog)}"
        
        # Calculate z-index based on stack position
        z_index = self._calculate_z_index()
        
        # Create dialog state
        dialog_state = DialogState(
            id=dialog_id,
            dialog=dialog,
            z_index=z_index,
            modal_type=modal_type,
            parent_id=parent_dialog_id,
            created_at=datetime.now()
        )
        
        # Add to stack and registry
        self.dialog_stack.append(dialog_state)
        self.dialog_registry[dialog_id] = dialog_state
        
        # Apply z-index to dialog
        self._apply_z_index(dialog, z_index)
        
        # Connect to dialog's finished or destroyed signal for cleanup
        if hasattr(dialog, 'finished') and hasattr(dialog.finished, 'connect'):
            # QDialog has finished signal
            dialog.finished.connect(lambda: self._on_dialog_finished(dialog_id))
        elif hasattr(dialog, 'destroyed') and hasattr(dialog.destroyed, 'connect'):
            # QWidget has destroyed signal
            dialog.destroyed.connect(lambda: self._on_dialog_finished(dialog_id))
        
        # Set modal behavior
        if hasattr(dialog, 'setModal'):
            if modal_type == 'modal':
                dialog.setModal(True)
            else:
                dialog.setModal(False)
        
        logger.info(f"Registered dialog {dialog_id} with z-index {z_index}, type: {modal_type}")
        
        return dialog_id
    
    def unregister_dialog(self, dialog_id: str) -> bool:
        """Unregister a dialog from the manager
        
        Args:
            dialog_id: The ID of the dialog to unregister
            
        Returns:
            bool: True if dialog was found and removed, False otherwise
        """
        if dialog_id not in self.dialog_registry:
            logger.warning(f"Attempted to unregister unknown dialog: {dialog_id}")
            return False
        
        dialog_state = self.dialog_registry[dialog_id]
        
        # Remove from stack
        if dialog_state in self.dialog_stack:
            self.dialog_stack.remove(dialog_state)
        
        # Remove from registry
        del self.dialog_registry[dialog_id]
        
        # We no longer recalculate z-indices here to avoid hiding/reshowing other dialogs
        # which can cause flickering and focus issues.
        # self._recalculate_z_indices()
        
        logger.info(f"Unregistered dialog {dialog_id}")
        
        return True
    
    def show_dialog(self, dialog: Any, modal_type: str = 'modal', 
                   parent_dialog_id: Optional[str] = None) -> str:
        """Register and show a dialog with proper z-index management
        
        Args:
            dialog: The QDialog or QWidget instance to show
            modal_type: Either 'modal' or 'non-modal'
            parent_dialog_id: ID of parent dialog if this is a child dialog
            
        Returns:
            str: Unique dialog ID for tracking
        """
        dialog_id = self.register_dialog(dialog, modal_type, parent_dialog_id)
        
        # Show the dialog
        if hasattr(dialog, 'exec') and modal_type == 'modal':
            # QDialog with modal execution
            dialog.exec()
        else:
            # QWidget or non-modal dialog
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        
        return dialog_id
    
    def close_dialog(self, dialog_id: str) -> bool:
        """Close and unregister a dialog
        
        Args:
            dialog_id: The ID of the dialog to close
            
        Returns:
            bool: True if dialog was found and closed, False otherwise
        """
        if dialog_id not in self.dialog_registry:
            return False
        
        dialog_state = self.dialog_registry[dialog_id]
        dialog_state.dialog.close()
        
        return True
    
    def get_dialog_by_id(self, dialog_id: str) -> Optional[QDialog]:
        """Get dialog instance by ID
        
        Args:
            dialog_id: The dialog ID to look up
            
        Returns:
            QDialog instance or None if not found
        """
        if dialog_id in self.dialog_registry:
            return self.dialog_registry[dialog_id].dialog
        return None
    
    def get_top_dialog(self) -> Optional[DialogState]:
        """Get the topmost dialog in the stack
        
        Returns:
            DialogState of the topmost dialog or None if stack is empty
        """
        if self.dialog_stack:
            return self.dialog_stack[-1]
        return None
    
    def get_dialog_count(self) -> int:
        """Get the number of currently managed dialogs
        
        Returns:
            int: Number of dialogs in the stack
        """
        return len(self.dialog_stack)
    
    def get_dialog_stack(self) -> List[DialogState]:
        """Get a copy of the current dialog stack
        
        Returns:
            List of DialogState objects in stack order
        """
        return self.dialog_stack.copy()
    
    def bring_to_front(self, dialog_id: str) -> bool:
        """Bring a dialog to the front of the stack
        
        Args:
            dialog_id: The ID of the dialog to bring to front
            
        Returns:
            bool: True if successful, False if dialog not found
        """
        if dialog_id not in self.dialog_registry:
            return False
        
        dialog_state = self.dialog_registry[dialog_id]
        
        # Remove from current position and add to top
        if dialog_state in self.dialog_stack:
            self.dialog_stack.remove(dialog_state)
        self.dialog_stack.append(dialog_state)
        
        # Assign a new higher z-index to this dialog instead of recalculating everyone
        new_z_index = self._calculate_z_index()
        dialog_state.z_index = new_z_index
        self._apply_z_index(dialog_state.dialog, new_z_index)
        
        # Bring dialog to front
        dialog_state.dialog.raise_()
        dialog_state.dialog.activateWindow()
        
        logger.info(f"Brought dialog {dialog_id} to front with z-index {new_z_index}")
        
        return True
    
    def _calculate_z_index(self) -> int:
        """Calculate z-index for a new dialog based on current stack
        
        Returns:
            int: The z-index value to assign
        """
        if not self.dialog_stack:
            return self.base_z_index
        
        # Get the highest z-index and add increment
        max_z_index = max(state.z_index for state in self.dialog_stack)
        return max_z_index + self.z_index_increment
    
    def _apply_z_index(self, dialog: Any, z_index: int):
        """Apply z-index to a dialog using Qt window flags
        
        Args:
            dialog: The dialog to apply z-index to
            z_index: The z-index value to apply
        """
        # Store z-index as a property for reference
        if hasattr(dialog, 'setProperty'):
            dialog.setProperty("z_index", z_index)
        
        # Use window flags to control stacking
        # Higher z-index dialogs should stay on top
        if hasattr(dialog, 'setWindowFlags') and hasattr(dialog, 'windowFlags') and hasattr(dialog, 'isVisible') and hasattr(dialog, 'show'):
            try:
                from PyQt6.QtCore import Qt
                
                current_flags = dialog.windowFlags()
                was_visible = dialog.isVisible()
                
                if z_index > self.base_z_index:
                    new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint
                
                # Only set flags if they changed to avoid unnecessary hiding
                if new_flags != current_flags:
                    dialog.setWindowFlags(new_flags)
                    # setWindowFlags hides the window, so we need to show it again if it was visible
                    if was_visible:
                        dialog.show()
                        
            except ImportError:
                pass  # Skip if PyQt6 not available
    
    def _recalculate_z_indices(self):
        """Recalculate z-indices for all dialogs in the stack"""
        for i, dialog_state in enumerate(self.dialog_stack):
            new_z_index = self.base_z_index + (i * self.z_index_increment)
            dialog_state.z_index = new_z_index
            self._apply_z_index(dialog_state.dialog, new_z_index)
        
        logger.debug(f"Recalculated z-indices for {len(self.dialog_stack)} dialogs")
    
    def _on_dialog_finished(self, dialog_id: str):
        """Handle dialog finished signal
        
        Args:
            dialog_id: The ID of the dialog that finished
        """
        self.unregister_dialog(dialog_id)
        
        # Return focus to the next dialog in stack if any
        top_dialog = self.get_top_dialog()
        if top_dialog:
            top_dialog.dialog.raise_()
            top_dialog.dialog.activateWindow()
    
    def cleanup_all(self):
        """Clean up all managed dialogs (for shutdown)"""
        dialog_ids = list(self.dialog_registry.keys())
        for dialog_id in dialog_ids:
            self.close_dialog(dialog_id)
        
        self.dialog_stack.clear()
        self.dialog_registry.clear()
        
        logger.info("Cleaned up all managed dialogs")
    
    def get_dialogs_by_type(self, modal_type: str) -> List[DialogState]:
        """Get all dialogs of a specific type
        
        Args:
            modal_type: Either 'modal' or 'non-modal'
            
        Returns:
            List of DialogState objects matching the type
        """
        return [state for state in self.dialog_stack if state.modal_type == modal_type]
    
    def get_child_dialogs(self, parent_dialog_id: str) -> List[DialogState]:
        """Get all child dialogs of a parent dialog
        
        Args:
            parent_dialog_id: The ID of the parent dialog
            
        Returns:
            List of DialogState objects that are children of the parent
        """
        return [state for state in self.dialog_stack if state.parent_id == parent_dialog_id]
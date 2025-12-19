"""Settings dialog for env.ini configuration - IMPROVED VERSION"""
import os
import configparser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QLineEdit, QPushButton,
                             QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
                             QFileDialog, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QTimer


class SettingsDialogImproved(QDialog):
    """Improved dialog for editing env.ini settings with better error handling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config_file = 'env.ini'
        
        # Initialize UI components to None first
        self.button_style_combo = None
        self.position_combo = None
        self.pdf_radio = None
        self.excel_radio = None
        self.format_button_group = None
        
        self.init_ui()
        
        # Use longer delay to ensure all components are fully initialized
        QTimer.singleShot(100, self.safe_load_settings)
    
    def safe_load_settings(self):
        """Safely load settings with comprehensive error handling"""
        try:
            # Double-check that all UI components exist
            required_components = [
                ('button_style_combo', 'Button style dropdown'),
                ('position_combo', 'Position dropdown'),
                ('pdf_radio', 'PDF radio button'),
                ('excel_radio', 'Excel radio button')
            ]
            
            missing_components = []
            for attr_name, description in required_components:
                if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
                    missing_components.append(f"{description} ({attr_name})")
            
            if missing_components:
                print(f"Warning: Missing UI components: {missing_components}")
                return
            
            # Proceed with loading settings
            self.load_settings()
            
        except Exception as e:
            print(f"Error in safe_load_settings: {e}")
            # Set safe defaults without accessing potentially problematic components
            self.set_safe_defaults()
    
    def set_safe_defaults(self):
        """Set safe default values without accessing potentially problematic components"""
        try:
            if hasattr(self, 'button_style_combo') and self.button_style_combo is not None:
                self.button_style_combo.setCurrentIndex(1)  # Default to text
            
            if hasattr(self, 'position_combo') and self.position_combo is not None:
                self.position_combo.setCurrentIndex(1)  # Default to bottom
            
            if hasattr(self, 'pdf_radio') and self.pdf_radio is not None:
                self.pdf_radio.setChecked(True)  # Default to PDF
                
        except Exception as e:
            print(f"Warning: Could not set safe defaults: {e}")
    
    # ... rest of the methods remain the same ...

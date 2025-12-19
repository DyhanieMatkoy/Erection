#!/usr/bin/env python3
"""Test to reproduce and fix the settings dialog QRadioButton error"""

import sys
import os
sys.path.append('src')

def test_settings_dialog_creation():
    """Test creating settings dialog to reproduce the error"""
    try:
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        print("🧪 Testing settings dialog creation...")
        
        # Import and create settings dialog
        from views.settings_dialog import SettingsDialog
        
        print("✅ Settings dialog imported successfully")
        
        # Create dialog
        dialog = SettingsDialog()
        
        print("✅ Settings dialog created successfully")
        
        # Check if all expected attributes exist
        expected_attrs = [
            'button_style_combo',
            'position_combo', 
            'pdf_radio',
            'excel_radio',
            'format_button_group'
        ]
        
        missing_attrs = []
        for attr in expected_attrs:
            if not hasattr(dialog, attr):
                missing_attrs.append(attr)
            else:
                print(f"✅ {attr} exists")
        
        if missing_attrs:
            print(f"❌ Missing attributes: {missing_attrs}")
            return False
        
        # Test load_settings method
        print("\n🧪 Testing load_settings method...")
        try:
            dialog.load_settings()
            print("✅ load_settings completed without error")
        except Exception as e:
            print(f"❌ load_settings error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test apply_settings method
        print("\n🧪 Testing apply_settings method...")
        try:
            result = dialog.apply_settings()
            print(f"✅ apply_settings completed: {result}")
        except Exception as e:
            print(f"❌ apply_settings error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n✅ All tests passed - no QRadioButton errors detected")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'app' in locals():
            app.quit()

def check_for_radio_button_issues():
    """Check for potential radio button issues in the code"""
    print("\n🔍 Checking for potential radio button issues...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Check for QRadioButton import
        if 'QRadioButton' in content:
            print("⚠️  QRadioButton still imported (needed for print forms)")
        
        # Check for radio button creation
        radio_creations = content.count('QRadioButton(')
        print(f"📊 Found {radio_creations} radio button creations")
        
        # Check for hasattr checks
        hasattr_checks = content.count('hasattr(self,')
        print(f"📊 Found {hasattr_checks} hasattr checks")
        
        # Check for QTimer usage
        if 'QTimer.singleShot' in content:
            print("✅ Using QTimer.singleShot for delayed loading")
        else:
            issues.append("Missing QTimer.singleShot for delayed loading")
        
        # Check for button group usage
        if 'QButtonGroup' in content:
            print("📊 QButtonGroup still used (for print forms)")
        
        if issues:
            print(f"❌ Found issues: {issues}")
            return False
        else:
            print("✅ No obvious issues found in code structure")
            return True
            
    except Exception as e:
        print(f"❌ Error checking code: {e}")
        return False

def create_improved_settings_dialog():
    """Create an improved version of the settings dialog with better error handling"""
    print("\n🔧 Creating improved settings dialog...")
    
    improved_content = '''"""Settings dialog for env.ini configuration - IMPROVED VERSION"""
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
'''
    
    with open('settings_dialog_improved.py', 'w', encoding='utf-8') as f:
        f.write(improved_content)
    
    print("✅ Created improved settings dialog: settings_dialog_improved.py")
    return True

if __name__ == "__main__":
    print("🔧 Testing and Fixing Settings Dialog QRadioButton Error...")
    print("=" * 70)
    
    # Run tests
    test_passed = test_settings_dialog_creation()
    code_check_passed = check_for_radio_button_issues()
    improvement_created = create_improved_settings_dialog()
    
    print("\n📊 Results Summary:")
    print(f"  Settings dialog test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print(f"  Code structure check: {'✅ PASSED' if code_check_passed else '❌ FAILED'}")
    print(f"  Improvement created: {'✅ CREATED' if improvement_created else '❌ FAILED'}")
    
    if not test_passed:
        print("\n🚨 ISSUE CONFIRMED: Settings dialog has QRadioButton errors")
        print("\n💡 Recommended fixes:")
        print("  1. Increase QTimer delay from 0 to 100ms")
        print("  2. Add comprehensive error handling in load_settings")
        print("  3. Initialize UI component references to None first")
        print("  4. Add safe_load_settings method with component validation")
        print("  5. Implement set_safe_defaults as fallback")
    else:
        print("\n✅ Settings dialog appears to be working correctly")
    
    sys.exit(0 if test_passed else 1)
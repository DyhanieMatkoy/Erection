#!/usr/bin/env python3
"""
Test script to verify QRadioButton error fix in settings dialog
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.views.settings_dialog import SettingsDialog


def test_settings_dialog_radio_buttons():
    """Test that settings dialog loads without QRadioButton errors"""
    app = QApplication(sys.argv)
    
    print("Creating settings dialog...")
    dialog = SettingsDialog()
    
    # Show dialog
    dialog.show()
    
    # Wait for initialization to complete
    def check_initialization():
        print("Checking initialization status...")
        print(f"UI initialized: {dialog._ui_initialized}")
        print(f"Settings loaded: {dialog._settings_loaded}")
        
        # Test radio button access
        radio_buttons = [
            ('use_font_icons_checkbox', dialog.use_font_icons_checkbox),
            ('use_text_icons_checkbox', dialog.use_text_icons_checkbox),
            ('use_both_icons_checkbox', dialog.use_both_icons_checkbox),
            ('pdf_radio', dialog.pdf_radio),
            ('excel_radio', dialog.excel_radio)
        ]
        
        all_good = True
        for name, button in radio_buttons:
            if button is None:
                print(f"ERROR: {name} is None")
                all_good = False
                continue
                
            try:
                checked = button.isChecked()
                text = button.text()
                print(f"✓ {name}: checked={checked}, text='{text}'")
            except RuntimeError as e:
                print(f"ERROR: {name} - {e}")
                all_good = False
        
        # Test combo box
        if dialog.position_combo is not None:
            try:
                index = dialog.position_combo.currentIndex()
                text = dialog.position_combo.currentText()
                print(f"✓ position_combo: index={index}, text='{text}'")
            except RuntimeError as e:
                print(f"ERROR: position_combo - {e}")
                all_good = False
        else:
            print("ERROR: position_combo is None")
            all_good = False
        
        if all_good:
            print("✅ All radio buttons and components are working correctly!")
        else:
            print("❌ Some components have errors")
        
        # Close dialog and exit
        dialog.close()
        app.quit()
    
    # Check after 1 second to allow full initialization
    QTimer.singleShot(1000, check_initialization)
    
    # Run the application
    app.exec()


if __name__ == "__main__":
    test_settings_dialog_radio_buttons()
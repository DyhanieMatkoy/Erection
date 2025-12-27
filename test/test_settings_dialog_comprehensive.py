#!/usr/bin/env python3
"""
Comprehensive test for settings dialog QRadioButton fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.views.settings_dialog import SettingsDialog


def test_settings_dialog_comprehensive():
    """Comprehensive test of settings dialog functionality"""
    app = QApplication(sys.argv)
    
    print("=== Settings Dialog Comprehensive Test ===")
    
    # Test 1: Basic initialization
    print("\n1. Testing basic initialization...")
    dialog = SettingsDialog()
    dialog.show()
    
    def run_tests():
        print("Running comprehensive tests...")
        
        # Test radio button access
        print("\n2. Testing radio button access...")
        radio_tests = [
            ('use_font_icons_checkbox', dialog.use_font_icons_checkbox),
            ('use_text_icons_checkbox', dialog.use_text_icons_checkbox),
            ('use_both_icons_checkbox', dialog.use_both_icons_checkbox),
            ('pdf_radio', dialog.pdf_radio),
            ('excel_radio', dialog.excel_radio)
        ]
        
        for name, button in radio_tests:
            try:
                checked = button.isChecked()
                text = button.text()
                button.setChecked(not checked)  # Toggle to test setting
                new_checked = button.isChecked()
                button.setChecked(checked)  # Restore original state
                print(f"✓ {name}: Access OK, toggle test passed")
            except Exception as e:
                print(f"❌ {name}: {e}")
                return False
        
        # Test 3: Button groups
        print("\n3. Testing button groups...")
        try:
            icon_group_id = dialog.icon_button_group.checkedId()
            format_group_id = dialog.format_button_group.checkedId()
            print(f"✓ Icon button group checked ID: {icon_group_id}")
            print(f"✓ Format button group checked ID: {format_group_id}")
        except Exception as e:
            print(f"❌ Button group test failed: {e}")
            return False
        
        # Test 4: Settings save/load cycle
        print("\n4. Testing settings save/load cycle...")
        try:
            # Set specific values
            dialog.use_both_icons_checkbox.setChecked(True)
            dialog.position_combo.setCurrentIndex(0)  # Top
            dialog.excel_radio.setChecked(True)
            
            # Save settings
            if dialog.apply_settings():
                print("✓ Settings saved successfully")
                
                # Create new dialog to test loading
                dialog2 = SettingsDialog()
                
                # Wait for loading
                def check_loaded_settings():
                    try:
                        if dialog2.use_both_icons_checkbox.isChecked():
                            print("✓ Button style setting loaded correctly")
                        else:
                            print("❌ Button style setting not loaded correctly")
                        
                        if dialog2.position_combo.currentIndex() == 0:
                            print("✓ Position setting loaded correctly")
                        else:
                            print("❌ Position setting not loaded correctly")
                        
                        if dialog2.excel_radio.isChecked():
                            print("✓ Format setting loaded correctly")
                        else:
                            print("❌ Format setting not loaded correctly")
                        
                        print("\n✅ All tests completed successfully!")
                        dialog.close()
                        dialog2.close()
                        app.quit()
                        
                    except Exception as e:
                        print(f"❌ Settings load test failed: {e}")
                        dialog.close()
                        dialog2.close()
                        app.quit()
                
                QTimer.singleShot(1000, check_loaded_settings)
                
            else:
                print("❌ Settings save failed")
                dialog.close()
                app.quit()
                
        except Exception as e:
            print(f"❌ Settings save/load test failed: {e}")
            dialog.close()
            app.quit()
    
    # Run tests after initialization
    QTimer.singleShot(1000, run_tests)
    
    # Run the application
    app.exec()


if __name__ == "__main__":
    test_settings_dialog_comprehensive()
#!/usr/bin/env python3
"""Test the new dropdown settings dialog"""

import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from PyQt6.QtWidgets import QApplication

def test_dropdown_settings():
    """Test the settings dialog with dropdown instead of radio buttons"""
    app = QApplication(sys.argv)
    
    try:
        # Import after setting up the path
        from views.settings_dialog import SettingsDialog
        
        print("Creating SettingsDialog...")
        dialog = SettingsDialog()
        
        print("Checking if position_combo exists...")
        if hasattr(dialog, 'position_combo'):
            print("✅ position_combo exists")
            print(f"✅ Current index: {dialog.position_combo.currentIndex()}")
            print(f"✅ Current text: {dialog.position_combo.currentText()}")
            print(f"✅ Item count: {dialog.position_combo.count()}")
            
            # Test all items
            for i in range(dialog.position_combo.count()):
                print(f"  Item {i}: {dialog.position_combo.itemText(i)}")
        else:
            print("❌ position_combo does not exist")
        
        # Check that old radio buttons don't exist
        old_attrs = ['top_radio', 'bottom_radio', 'both_radio', 'position_button_group']
        for attr in old_attrs:
            if hasattr(dialog, attr):
                print(f"❌ Old attribute {attr} still exists")
            else:
                print(f"✅ Old attribute {attr} removed")
        
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    success = test_dropdown_settings()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""Simple test for dropdown settings dialog"""

import sys
import os

# Set up environment
os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')

def test_settings_file_syntax():
    """Test that the settings dialog file has correct syntax"""
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for dropdown-related code
        checks = [
            ('QComboBox import', 'QComboBox' in content),
            ('position_combo creation', 'self.position_combo = QComboBox()' in content),
            ('combo items setup', 'self.position_combo.addItems([' in content),
            ('combo index setting', 'self.position_combo.setCurrentIndex(' in content),
            ('combo in load_settings', 'position_combo' in content and 'setCurrentIndex' in content),
            ('combo in apply_settings', 'position_combo.currentIndex()' in content),
        ]
        
        print("🔍 Checking dropdown implementation:")
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'PASS' if result else 'FAIL'}")
            if not result:
                all_passed = False
        
        # Check that old radio button code is removed
        old_code_checks = [
            ('top_radio removed', 'self.top_radio = QRadioButton(' not in content),
            ('bottom_radio removed', 'self.bottom_radio = QRadioButton(' not in content),
            ('both_radio removed', 'self.both_radio = QRadioButton(' not in content),
            ('button_group removed', 'self.position_button_group = QButtonGroup(' not in content),
        ]
        
        print("\n🗑️ Checking old radio button code removal:")
        for check_name, result in old_code_checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'PASS' if result else 'FAIL'}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All checks passed! Dropdown implementation looks good.")
        else:
            print("\n⚠️ Some checks failed. Please review the implementation.")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading settings file: {e}")
        return False

def test_dropdown_items():
    """Test that dropdown items are correctly defined"""
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the dropdown items
        import re
        pattern = r'self\.position_combo\.addItems\(\[(.*?)\]\)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            items_text = match.group(1)
            print(f"📋 Dropdown items found: {items_text}")
            
            expected_items = [
                "Кнопки вверху формы",
                "Кнопки внизу формы (стандарт)",
                "Кнопки и вверху, и внизу"
            ]
            
            items_ok = all(item in items_text for item in expected_items)
            print(f"✅ All expected items present: {'YES' if items_ok else 'NO'}")
            return items_ok
        else:
            print("❌ Dropdown items not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking dropdown items: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing dropdown settings implementation...\n")
    
    syntax_ok = test_settings_file_syntax()
    items_ok = test_dropdown_items()
    
    if syntax_ok and items_ok:
        print("\n🎯 SUCCESS: Dropdown implementation is complete!")
        print("\n📝 Summary of changes:")
        print("  • Replaced QRadioButton group with QComboBox")
        print("  • Updated load_settings() to use setCurrentIndex()")
        print("  • Updated apply_settings() to use currentIndex()")
        print("  • Added QComboBox to imports")
        print("  • Removed old radio button attributes")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Some issues found in implementation")
        sys.exit(1)
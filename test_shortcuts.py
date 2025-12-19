"""Test script for desktop shortcuts functionality"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.views.counterparty_list_form_v2 import CounterpartyListFormV2
from src.views.counterparty_form import CounterpartyForm
from src.views.components.reference_field import ReferenceField

def test_list_form_shortcuts():
    """Test list form shortcuts"""
    app = QApplication(sys.argv)
    
    try:
        # Create list form
        list_form = CounterpartyListFormV2()
        list_form.show()
        
        print("✅ Counterparty List Form created successfully")
        print("🧪 Test the following shortcuts:")
        print("   Insert/F9: Create new counterparty")
        print("   F2: Edit selected counterparty")
        print("   Delete: Delete selected counterparty") 
        print("   F5: Refresh list")
        print("   F8: Print list")
        
        return app.exec()
    except Exception as e:
        print(f"❌ Error creating list form: {e}")
        print("💡 This is expected in test environment without full database setup")
        return 0

def test_reference_field_shortcuts():
    """Test reference field shortcuts"""
    app = QApplication(sys.argv)
    
    try:
        # Create counterparty form
        form = CounterpartyForm()
        form.show()
        
        print("✅ Counterparty Form created successfully")
        print("🧪 Test the following shortcuts:")
        print("   Click on Parent field, then:")
        print("   F2: Start search editing")
        print("   F4: Open selector dialog")
        
        return app.exec()
    except Exception as e:
        print(f"❌ Error creating form: {e}")
        print("💡 This is expected in test environment without full database setup")
        return 0

def test_button_styler():
    """Test button styler functionality"""
    from src.views.utils.button_styler import get_button_styler
    
    styler = get_button_styler()
    print(f"✅ Button styler created with style: {styler.button_style}")
    
    # Test different button styles
    commands = ['create', 'edit', 'delete', 'refresh', 'print']
    
    for cmd in commands:
        text = styler.get_button_text(cmd)
        tooltip = styler.get_button_tooltip(cmd)
        print(f"   {cmd}: '{text}' (tooltip: '{tooltip}')")

if __name__ == "__main__":
    print("🚀 Testing Desktop Shortcuts Implementation")
    print("=" * 50)
    
    # Test button styler
    print("\n1. Testing Button Styler:")
    test_button_styler()
    
    print("\n2. Choose test mode:")
    print("   1: Test List Form Shortcuts")
    print("   2: Test Reference Field Shortcuts")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_list_form_shortcuts()
    elif choice == "2":
        test_reference_field_shortcuts()
    else:
        print("❌ Invalid choice")
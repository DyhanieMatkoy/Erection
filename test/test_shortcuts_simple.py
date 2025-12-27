"""Simple test for shortcuts components"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from src.views.components.reference_field import ReferenceField
from src.views.utils.button_styler import get_button_styler

def test_reference_field():
    """Test reference field component"""
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    window.setWindowTitle("Reference Field Test")
    window.resize(400, 200)
    
    layout = QVBoxLayout()
    
    # Create reference field
    ref_field = ReferenceField()
    ref_field.set_reference("counterparties", "Выбор контрагента")
    layout.addWidget(ref_field)
    
    window.setLayout(layout)
    window.show()
    
    print("✅ Reference Field Test Window created")
    print("🧪 Test shortcuts:")
    print("   F2: Start search editing")
    print("   F4: Open selector dialog")
    print("   Click ... button: Open selector")
    print("   Click ✕ button: Clear value")
    
    return app.exec()

def test_button_styler():
    """Test button styler with different styles"""
    print("🎨 Testing Button Styler")
    print("=" * 40)
    
    # Test different styles by temporarily modifying settings
    import configparser
    
    # Create test config
    config = configparser.ConfigParser()
    config.add_section('Interface')
    
    styles = ['text', 'icons', 'both']
    commands = ['create', 'edit', 'delete', 'refresh', 'print', 'copy', 'save']
    
    for style in styles:
        print(f"\n📋 Style: {style}")
        config.set('Interface', 'button_style', style)
        
        # Save to temporary file
        with open('test_env.ini', 'w', encoding='utf-8') as f:
            config.write(f)
        
        # Temporarily replace env.ini
        if os.path.exists('env.ini'):
            os.rename('env.ini', 'env.ini.backup')
        os.rename('test_env.ini', 'env.ini')
        
        # Test styler
        try:
            # Clear cached styler
            import src.views.utils.button_styler
            src.views.utils.button_styler._button_styler = None
            
            styler = get_button_styler()
            print(f"   Style loaded: {styler.button_style}")
            
            for cmd in commands:
                text = styler.get_button_text(cmd)
                tooltip = styler.get_button_tooltip(cmd)
                print(f"   {cmd:12} -> '{text:15}' (tooltip: '{tooltip}')")
        finally:
            # Restore original env.ini
            if os.path.exists('env.ini'):
                os.remove('env.ini')
            if os.path.exists('env.ini.backup'):
                os.rename('env.ini.backup', 'env.ini')
    
    print("\n✅ Button Styler test completed")

if __name__ == "__main__":
    print("🚀 Testing Shortcuts Components")
    print("=" * 50)
    
    # Test button styler first
    test_button_styler()
    
    print("\n" + "=" * 50)
    print("🧪 For reference field test, run:")
    print("   python test_shortcuts_simple.py ref_field")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'ref_field':
        test_reference_field()
#!/usr/bin/env python3
"""Test that radio buttons are restored for button style selection"""

def test_radio_buttons_restored():
    """Test that radio buttons are back for button style selection"""
    print("🧪 Testing radio buttons restoration...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for radio button restoration
        radio_checks = [
            ('use_font_icons_checkbox created', 'self.use_font_icons_checkbox = QRadioButton(' in content),
            ('use_text_icons_checkbox created', 'self.use_text_icons_checkbox = QRadioButton(' in content),
            ('use_both_icons_checkbox created', 'self.use_both_icons_checkbox = QRadioButton(' in content),
            ('icon_button_group created', 'self.icon_button_group = QButtonGroup(' in content),
            ('Radio buttons added to layout', 'button_layout.addWidget(self.use_font_icons_checkbox)' in content),
            ('Button group setup', 'self.icon_button_group.addButton(' in content),
        ]
        
        # Check that dropdown is removed
        dropdown_checks = [
            ('button_style_combo removed from creation', 'self.button_style_combo = QComboBox()' not in content),
            ('dropdown items removed', 'self.button_style_combo.addItems([' not in content),
        ]
        
        all_passed = True
        
        print("📋 Radio button restoration:")
        for check_name, result in radio_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        print("\n🗑️ Dropdown removal:")
        for check_name, result in dropdown_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking radio buttons: {e}")
        return False

def test_initialization_updated():
    """Test that component initialization is updated"""
    print("\n🔧 Testing component initialization...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        init_checks = [
            ('use_font_icons_checkbox initialized', 'self.use_font_icons_checkbox = None' in content),
            ('use_text_icons_checkbox initialized', 'self.use_text_icons_checkbox = None' in content),
            ('use_both_icons_checkbox initialized', 'self.use_both_icons_checkbox = None' in content),
            ('icon_button_group initialized', 'self.icon_button_group = None' in content),
            ('button_style_combo removed from init', 'self.button_style_combo = None' not in content),
        ]
        
        all_passed = True
        for check_name, result in init_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking initialization: {e}")
        return False

def test_loading_methods_updated():
    """Test that loading methods are updated for radio buttons"""
    print("\n📥 Testing loading methods...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        loading_checks = [
            ('Radio button checks in load_interface_settings', 'use_text_icons_checkbox.setChecked(True)' in content),
            ('Safe radio button access', 'hasattr(self, \'use_text_icons_checkbox\') and self.use_text_icons_checkbox' in content),
            ('Font icons radio check', 'use_font_icons_checkbox.setChecked(True)' in content),
            ('Both icons radio check', 'use_both_icons_checkbox.setChecked(True)' in content),
            ('Dropdown loading removed', 'button_style_combo.setCurrentIndex(' not in content),
        ]
        
        all_passed = True
        for check_name, result in loading_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking loading methods: {e}")
        return False

def test_saving_methods_updated():
    """Test that saving methods are updated for radio buttons"""
    print("\n💾 Testing saving methods...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        saving_checks = [
            ('Radio button isChecked in apply_settings', 'use_font_icons_checkbox.isChecked()' in content),
            ('Safe radio button saving', 'hasattr(self, \'use_font_icons_checkbox\') and self.use_font_icons_checkbox and self.use_font_icons_checkbox.isChecked()' in content),
            ('Both icons saving check', 'use_both_icons_checkbox.isChecked()' in content),
            ('Dropdown saving removed', 'button_style_combo.currentIndex()' not in content),
        ]
        
        all_passed = True
        for check_name, result in saving_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking saving methods: {e}")
        return False

def test_safe_defaults_updated():
    """Test that safe defaults method is updated"""
    print("\n🛡️ Testing safe defaults...")
    
    try:
        with open('src/views/settings_dialog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        defaults_checks = [
            ('Text radio default in set_safe_defaults', 'use_text_icons_checkbox.setChecked(True)' in content),
            ('Safe radio access in defaults', 'hasattr(self, \'use_text_icons_checkbox\') and self.use_text_icons_checkbox is not None' in content),
            ('Dropdown default removed', 'button_style_combo.setCurrentIndex(1)' not in content),
        ]
        
        all_passed = True
        for check_name, result in defaults_checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking safe defaults: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Testing Radio Buttons Restoration for Button Style...")
    print("=" * 65)
    
    # Run tests
    radio_restored = test_radio_buttons_restored()
    init_updated = test_initialization_updated()
    loading_updated = test_loading_methods_updated()
    saving_updated = test_saving_methods_updated()
    defaults_updated = test_safe_defaults_updated()
    
    print("\n📊 Restoration Summary:")
    print(f"  Radio buttons restored: {'✅ YES' if radio_restored else '❌ NO'}")
    print(f"  Initialization updated: {'✅ YES' if init_updated else '❌ NO'}")
    print(f"  Loading methods updated: {'✅ YES' if loading_updated else '❌ NO'}")
    print(f"  Saving methods updated: {'✅ YES' if saving_updated else '❌ NO'}")
    print(f"  Safe defaults updated: {'✅ YES' if defaults_updated else '❌ NO'}")
    
    all_tests_passed = all([radio_restored, init_updated, loading_updated, saving_updated, defaults_updated])
    
    if all_tests_passed:
        print("\n🎉 SUCCESS: Radio buttons successfully restored!")
        print("\n📋 What was restored:")
        print("  • use_font_icons_checkbox - для иконок шрифтов")
        print("  • use_text_icons_checkbox - для текстовых подписей")
        print("  • use_both_icons_checkbox - для иконок и текста")
        print("  • icon_button_group - группа радиокнопок")
        print("  • Обновлены методы загрузки и сохранения")
        print("  • Обновлены безопасные значения по умолчанию")
        print("\n✅ Пользователи теперь могут выбирать стиль кнопок через радиокнопки!")
    else:
        print("\n⚠️  WARNING: Some restoration steps may not be complete")
        print("Please review the changes and complete missing steps manually")
    
    exit(0 if all_tests_passed else 1)
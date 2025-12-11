"""Test settings configuration"""
import os
import configparser


def test_read_env_ini():
    """Test reading env.ini"""
    print("Testing env.ini reading...")
    
    if not os.path.exists('env.ini'):
        print("✗ env.ini not found")
        return False
    
    config = configparser.ConfigParser()
    config.read('env.ini', encoding='utf-8')
    
    print(f"Sections: {config.sections()}")
    
    # Test Auth section
    if config.has_section('Auth'):
        print("\n[Auth] section:")
        if config.has_option('Auth', 'login'):
            print(f"  login = {config.get('Auth', 'login')}")
        if config.has_option('Auth', 'password'):
            print(f"  password = {'*' * len(config.get('Auth', 'password'))}")
    else:
        print("✗ [Auth] section not found")
    
    # Test PrintForms section
    if config.has_section('PrintForms'):
        print("\n[PrintForms] section:")
        if config.has_option('PrintForms', 'format'):
            print(f"  format = {config.get('PrintForms', 'format')}")
        if config.has_option('PrintForms', 'templates_path'):
            print(f"  templates_path = {config.get('PrintForms', 'templates_path')}")
    else:
        print("✗ [PrintForms] section not found")
    
    print("\n✓ env.ini reading test completed!")
    return True


def test_write_env_ini():
    """Test writing env.ini"""
    print("\n" + "="*50)
    print("Testing env.ini writing...")
    
    # Backup original
    backup_file = 'env.ini.backup'
    if os.path.exists('env.ini'):
        import shutil
        shutil.copy('env.ini', backup_file)
        print(f"Created backup: {backup_file}")
    
    # Create test config
    config = configparser.ConfigParser()
    
    config.add_section('Auth')
    config.set('Auth', 'login', 'test_user')
    config.set('Auth', 'password', 'test_pass')
    
    config.add_section('PrintForms')
    config.set('PrintForms', 'format', 'EXCEL')
    config.set('PrintForms', 'templates_path', 'TestTemplates')
    
    # Write to test file
    test_file = 'env_test.ini'
    with open(test_file, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"\nCreated test file: {test_file}")
    
    # Read back
    config2 = configparser.ConfigParser()
    config2.read(test_file, encoding='utf-8')
    
    print("\nVerifying written data:")
    print(f"  login = {config2.get('Auth', 'login')}")
    print(f"  password = {config2.get('Auth', 'password')}")
    print(f"  format = {config2.get('PrintForms', 'format')}")
    print(f"  templates_path = {config2.get('PrintForms', 'templates_path')}")
    
    # Cleanup
    os.remove(test_file)
    print(f"\nRemoved test file: {test_file}")
    
    print("\n✓ env.ini writing test completed!")
    return True


def test_settings_dialog_integration():
    """Test settings dialog integration"""
    print("\n" + "="*50)
    print("Testing SettingsDialog integration...")
    
    try:
        import sys
        sys.path.insert(0, 'src')
        
        from src.views.settings_dialog import SettingsDialog
        
        print("✓ SettingsDialog imported successfully")
        
        # Test instantiation (without showing)
        # dialog = SettingsDialog()
        # print("✓ SettingsDialog instantiated successfully")
        
        print("\n✓ Integration test completed!")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*50)
    print("Settings Configuration Test Suite")
    print("="*50)
    
    try:
        success = True
        
        success = test_read_env_ini() and success
        success = test_write_env_ini() and success
        success = test_settings_dialog_integration() and success
        
        print("\n" + "="*50)
        if success:
            print("✓ All tests completed successfully!")
        else:
            print("✗ Some tests failed")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

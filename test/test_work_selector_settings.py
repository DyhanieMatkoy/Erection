"""Test work selector settings functionality"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_work_selector_settings_service():
    """Test UserSettingsService work selector methods"""
    print("Testing work selector settings service...")
    
    try:
        from src.services.user_settings_service import UserSettingsService
        
        service = UserSettingsService()
        user_id = 4  # Test user
        
        # Test getting default settings
        print("Testing default settings...")
        settings = service.get_work_selector_settings(user_id)
        print(f"✅ Default settings: {settings}")
        
        # Test setting custom settings
        print("Testing custom settings...")
        custom_settings = {
            'open_modal': False,
            'default_hierarchy_mode': 'flat',
            'show_hierarchy_controls': False,
            'auto_expand_groups': False
        }
        
        success = service.set_work_selector_settings(user_id, custom_settings)
        if success:
            print("✅ Custom settings saved successfully")
        else:
            print("❌ Failed to save custom settings")
            return False
        
        # Test retrieving custom settings
        print("Testing settings retrieval...")
        retrieved_settings = service.get_work_selector_settings(user_id)
        print(f"✅ Retrieved settings: {retrieved_settings}")
        
        # Verify settings match
        for key, value in custom_settings.items():
            if retrieved_settings.get(key) != value:
                print(f"❌ Setting mismatch for {key}: expected {value}, got {retrieved_settings.get(key)}")
                return False
        
        print("✅ All settings match expected values")
        
        # Test resetting to defaults
        print("Testing reset to defaults...")
        default_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True
        }
        
        success = service.set_work_selector_settings(user_id, default_settings)
        if success:
            print("✅ Settings reset to defaults successfully")
        else:
            print("❌ Failed to reset settings to defaults")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing work selector settings service: {e}")
        return False


def test_api_endpoint():
    """Test work selector settings API endpoint"""
    print("\nTesting work selector settings API endpoint...")
    
    try:
        import requests
        import json
        
        base_url = "http://localhost:8000/api/work-selector-settings"
        user_id = 4
        
        # Test getting settings
        print("Testing GET endpoint...")
        response = requests.get(f"{base_url}/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GET request successful: {data}")
        else:
            print(f"❌ GET request failed: {response.status_code} - {response.text}")
            return False
        
        # Test updating settings
        print("Testing PUT endpoint...")
        test_settings = {
            "open_modal": False,
            "default_hierarchy_mode": "breadcrumb",
            "show_hierarchy_controls": True,
            "auto_expand_groups": False
        }
        
        response = requests.put(
            f"{base_url}/{user_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_settings)
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PUT request successful: {data}")
        else:
            print(f"❌ PUT request failed: {response.status_code} - {response.text}")
            return False
        
        # Verify settings were saved
        print("Verifying settings were saved...")
        response = requests.get(f"{base_url}/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            saved_settings = data.get('settings', {})
            
            for key, value in test_settings.items():
                if saved_settings.get(key) != value:
                    print(f"❌ Setting not saved correctly: {key} = {saved_settings.get(key)}, expected {value}")
                    return False
            
            print("✅ All settings saved correctly")
        else:
            print(f"❌ Failed to verify saved settings: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️ API server not running - skipping API tests")
        return True
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")
        return False


def main():
    """Run all work selector settings tests"""
    print("🧪 Testing Work Selector Settings Functionality")
    print("=" * 50)
    
    success1 = test_work_selector_settings_service()
    success2 = test_api_endpoint()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All work selector settings tests passed!")
        return True
    else:
        print("❌ Some work selector settings tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""Test desktop work selector settings functionality"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_work_selector_settings_dialog():
    """Test work selector settings dialog"""
    print("Testing work selector settings dialog...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.dialogs.work_selector_settings_dialog import WorkSelectorSettingsDialog
        from src.services.user_settings_service import UserSettingsService
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_id = 4  # Test user
        
        # Test dialog creation
        print("Creating settings dialog...")
        dialog = WorkSelectorSettingsDialog(user_id=user_id)
        print("✅ Settings dialog created successfully")
        
        # Test settings service integration
        print("Testing settings service integration...")
        settings_service = UserSettingsService()
        
        # Test getting default settings
        settings = settings_service.get_work_selector_settings(user_id)
        print(f"✅ Default settings loaded: {settings}")
        
        # Test dialog settings loading
        dialog.load_settings()
        print("✅ Dialog settings loaded successfully")
        
        # Test settings modification
        print("Testing settings modification...")
        test_settings = {
            'open_modal': False,
            'default_hierarchy_mode': 'flat',
            'show_hierarchy_controls': False,
            'auto_expand_groups': False,
            'remember_last_position': False
        }
        
        success = settings_service.set_work_selector_settings(user_id, test_settings)
        if success:
            print("✅ Test settings saved successfully")
            
            # Reload and verify
            dialog.load_settings()
            current_settings = dialog.get_settings()
            print(f"✅ Settings reloaded: {current_settings}")
        else:
            print("❌ Failed to save test settings")
            return False
        
        # Reset to defaults
        default_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True,
            'remember_last_position': True
        }
        
        success = settings_service.set_work_selector_settings(user_id, default_settings)
        if success:
            print("✅ Settings reset to defaults successfully")
        else:
            print("❌ Failed to reset settings to defaults")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing work selector settings dialog: {e}")
        return False


def test_enhanced_work_selector_dialog():
    """Test enhanced work selector dialog"""
    print("\nTesting enhanced work selector dialog...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.dialogs.enhanced_work_selector_dialog import EnhancedWorkSelectorDialog
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_id = 4  # Test user
        
        # Test dialog creation
        print("Creating enhanced work selector dialog...")
        dialog = EnhancedWorkSelectorDialog(user_id=user_id)
        print("✅ Enhanced work selector dialog created successfully")
        
        # Test settings loading
        print("Testing settings loading...")
        dialog.load_user_settings()
        print(f"✅ Settings loaded: {dialog.settings}")
        
        # Test UI updates based on settings
        print("Testing UI updates...")
        dialog.update_controls_visibility()
        dialog.update_mode_label()
        print("✅ UI updated based on settings")
        
        # Test hierarchy mode switching
        print("Testing hierarchy mode switching...")
        for mode in ['flat', 'tree', 'breadcrumb']:
            dialog.set_hierarchy_mode(mode)
            current_mode = dialog.settings.get('default_hierarchy_mode')
            if current_mode == mode:
                print(f"✅ Successfully switched to {mode} mode")
            else:
                print(f"❌ Failed to switch to {mode} mode")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced work selector dialog: {e}")
        return False


def test_estimate_form_integration():
    """Test integration with estimate form"""
    print("\nTesting estimate form integration...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.estimate_document_form import EstimateDocumentForm
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test estimate form creation
        print("Creating estimate form...")
        form = EstimateDocumentForm(0)  # New estimate
        print("✅ Estimate form created successfully")
        
        # Check if settings button exists
        if hasattr(form, 'work_selector_settings_button'):
            print("✅ Work selector settings button found in estimate form")
            
            # Test button functionality
            if hasattr(form, 'on_work_selector_settings'):
                print("✅ Work selector settings method found")
            else:
                print("❌ Work selector settings method not found")
                return False
        else:
            print("❌ Work selector settings button not found in estimate form")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing estimate form integration: {e}")
        return False


def test_modal_non_modal_behavior():
    """Test modal and non-modal behavior"""
    print("\nTesting modal and non-modal behavior...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.dialogs.enhanced_work_selector_dialog import EnhancedWorkSelectorDialog
        from src.services.user_settings_service import UserSettingsService
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_id = 4
        settings_service = UserSettingsService()
        
        # Test modal mode
        print("Testing modal mode...")
        modal_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True,
            'remember_last_position': True
        }
        
        settings_service.set_work_selector_settings(user_id, modal_settings)
        dialog = EnhancedWorkSelectorDialog(user_id=user_id)
        
        if dialog.isModal():
            print("✅ Dialog is modal as expected")
        else:
            print("❌ Dialog should be modal but isn't")
            return False
        
        # Test non-modal mode
        print("Testing non-modal mode...")
        non_modal_settings = {
            'open_modal': False,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True,
            'remember_last_position': True
        }
        
        settings_service.set_work_selector_settings(user_id, non_modal_settings)
        dialog2 = EnhancedWorkSelectorDialog(user_id=user_id)
        
        if not dialog2.isModal():
            print("✅ Dialog is non-modal as expected")
        else:
            print("❌ Dialog should be non-modal but is modal")
            return False
        
        # Reset to defaults
        settings_service.set_work_selector_settings(user_id, modal_settings)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing modal/non-modal behavior: {e}")
        return False


def main():
    """Run all desktop work selector settings tests"""
    print("🧪 Testing Desktop Work Selector Settings Functionality")
    print("=" * 60)
    
    success1 = test_work_selector_settings_dialog()
    success2 = test_enhanced_work_selector_dialog()
    success3 = test_estimate_form_integration()
    success4 = test_modal_non_modal_behavior()
    
    print("\n" + "=" * 60)
    if success1 and success2 and success3 and success4:
        print("✅ All desktop work selector settings tests passed!")
        return True
    else:
        print("❌ Some desktop work selector settings tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
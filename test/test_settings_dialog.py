"""Test settings dialog"""
import sys
from PyQt6.QtWidgets import QApplication
from src.views.settings_dialog import SettingsDialog


def test_settings_dialog():
    """Test settings dialog"""
    app = QApplication(sys.argv)
    
    dialog = SettingsDialog()
    dialog.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    test_settings_dialog()

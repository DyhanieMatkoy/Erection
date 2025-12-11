"""Test delete marked objects dialog"""
import sys
from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.delete_marked_dialog import DeleteMarkedDialog


def main():
    """Test delete marked objects dialog"""
    # Initialize database
    db_manager = DatabaseManager()
    if not db_manager.initialize("construction.db"):
        print("Failed to initialize database")
        return
    
    # Create application
    app = QApplication(sys.argv)
    
    # Show dialog
    dialog = DeleteMarkedDialog()
    dialog.exec()
    
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Система управления рабочим временем строительных бригад
NO AUTHENTICATION VERSION - bypasses login
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Система управления рабочим временем (No Auth)")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
    # Skip login and go directly to main window
    print("⚠️  Running in NO AUTHENTICATION mode")
    print("⚠️  Login check bypassed - direct access granted")
    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

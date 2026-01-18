#!/usr/bin/env python3
"""
Система управления рабочим временем строительных бригад
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.login_form import LoginForm
from src.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Система управления рабочим временем")
    
    # Set working directory to application directory (important for packaged app)
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        os.chdir(sys._MEIPASS)
    else:
        # Running as script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
    # Ensure admin user exists (for packaged applications)
    try:
        from src.data.initial_data import ensure_admin_user_exists
        ensure_admin_user_exists("construction.db")
    except Exception as e:
        print(f"Warning: Could not verify admin user: {e}")
    
    # Show login form
    login_form = LoginForm()
    if login_form.exec() == LoginForm.DialogCode.Accepted:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

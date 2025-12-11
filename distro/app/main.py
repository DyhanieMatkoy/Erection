#!/usr/bin/env python3
"""
Система управления рабочим временем строительных бригад
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.login_form import LoginForm
from src.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Система управления рабочим временем")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
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

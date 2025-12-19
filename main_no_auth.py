#!/usr/bin/env python3
"""
Система управления рабочим временем строительных бригад
NO AUTHENTICATION VERSION - bypasses login and crypto limitations
For systems with crypto/bcrypt issues or when you need direct admin access
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.data.database_manager import DatabaseManager


class NoAuthMainWindow:
    """Custom MainWindow wrapper that disables auto-navigation dialog"""
    
    def __init__(self):
        # Set up authentication bypass first
        self.setup_admin_user()
        
        # Import MainWindow after auth is set up
        from src.views.main_window import MainWindow
        self.main_window = MainWindow()
        
        # Disable automatic quick navigation dialog
        self.disable_auto_navigation()
    
    def setup_admin_user(self):
        """Set up fake admin user for no-auth mode"""
        from src.services.auth_service import AuthService
        from src.data.models.user import User
        
        auth_service = AuthService()
        
        # Create a fake admin user with full privileges
        fake_admin = User()
        fake_admin.id = 4  # Admin user ID
        fake_admin.username = "admin"
        fake_admin.role = "Администратор"  # Russian role name for Administrator
        fake_admin.is_active = True
        fake_admin.can_manage_references = True
        fake_admin.can_manage_settings = True
        fake_admin.can_view_analytics = True
        
        # Set the fake user as current user
        auth_service._current_user = fake_admin
        auth_service._current_person_id = 1  # Default person ID
        
        print("✓ Admin user privileges granted (Администратор role)")
        print("✓ All menu items should now be enabled")
    
    def disable_auto_navigation(self):
        """Disable the automatic quick navigation dialog on startup"""
        # The MainWindow constructor sets up a QTimer.singleShot(100, self.show_quick_navigation)
        # We need to prevent this from executing
        
        # Find and stop any single-shot timers that might show dialogs
        for timer in self.main_window.findChildren(QTimer):
            if timer.isSingleShot() and timer.isActive():
                timer.stop()
                print("✓ Auto-navigation dialog disabled")
    
    def show(self):
        """Show the main window"""
        self.main_window.show()
    
    def __getattr__(self, name):
        """Delegate all other attributes to the main window"""
        return getattr(self.main_window, name)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Система управления рабочим временем (No Auth)")
    
    print("🚀 Starting NO AUTHENTICATION mode")
    print("   For systems with crypto limitations or direct admin access")
    print()
    
    # Initialize database
    print("📊 Initializing database...")
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    print("✓ Database initialized")
    
    # Create main window with no-auth wrapper
    print("🖥️  Creating main window...")
    main_window = NoAuthMainWindow()
    
    # Show the window
    main_window.show()
    
    print("✓ Application started successfully!")
    print()
    print("📋 Available features:")
    print("   • Full admin privileges")
    print("   • All forms and references accessible")
    print("   • Use Ctrl+K for quick navigation")
    print("   • Use menu bar to access all functions")
    print("   • No authentication required")
    print()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

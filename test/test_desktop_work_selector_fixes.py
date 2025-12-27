#!/usr/bin/env python3
"""
Test script for desktop work selector bug fixes

This script tests the three reported bugs:
1. Database column error: "no such column: w.marked_for_deletion"
2. Z-order issue: edit dialog appears behind work selector in non-modal mode
3. Application crashes without console messages

Run this script to verify the fixes work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import Qt
from src.views.dialogs.enhanced_work_selector_dialog import EnhancedWorkSelectorDialog
from src.views.dialogs.work_selector_settings_dialog import WorkSelectorSettingsDialog
from src.data.database_manager import DatabaseManager


class TestMainWindow(QMainWindow):
    """Test main window for work selector testing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Work Selector Bug Fixes Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Test buttons
        self.test_modal_button = QPushButton("Test Modal Work Selector")
        self.test_modal_button.clicked.connect(self.test_modal_selector)
        layout.addWidget(self.test_modal_button)
        
        self.test_non_modal_button = QPushButton("Test Non-Modal Work Selector")
        self.test_non_modal_button.clicked.connect(self.test_non_modal_selector)
        layout.addWidget(self.test_non_modal_button)
        
        self.test_settings_button = QPushButton("Test Settings Dialog")
        self.test_settings_button.clicked.connect(self.test_settings_dialog)
        layout.addWidget(self.test_settings_button)
        
        self.test_database_button = QPushButton("Test Database Query")
        self.test_database_button.clicked.connect(self.test_database_query)
        layout.addWidget(self.test_database_button)
        
        # Status
        self.statusBar().showMessage("Ready to test work selector fixes")
    
    def test_modal_selector(self):
        """Test modal work selector"""
        try:
            # Force modal mode
            dialog = EnhancedWorkSelectorDialog(self, None, 4)
            dialog.settings['open_modal'] = True
            dialog.apply_settings()
            
            def on_work_selected(work_id, work_name):
                self.statusBar().showMessage(f"Selected work: {work_name} (ID: {work_id})")
            
            dialog.work_selected.connect(on_work_selected)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Modal selector test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_non_modal_selector(self):
        """Test non-modal work selector"""
        try:
            # Force non-modal mode
            dialog = EnhancedWorkSelectorDialog(self, None, 4)
            dialog.settings['open_modal'] = False
            dialog.apply_settings()
            
            def on_work_selected(work_id, work_name):
                self.statusBar().showMessage(f"Selected work: {work_name} (ID: {work_id})")
                dialog.close()
            
            dialog.work_selected.connect(on_work_selected)
            dialog.show()
            
            # Store reference to prevent garbage collection
            self._non_modal_dialog = dialog
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Non-modal selector test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_settings_dialog(self):
        """Test settings dialog"""
        try:
            dialog = WorkSelectorSettingsDialog(self, 4)
            result = dialog.exec()
            
            if result:
                self.statusBar().showMessage("Settings saved successfully")
            else:
                self.statusBar().showMessage("Settings dialog cancelled")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Settings dialog test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_database_query(self):
        """Test database query with different column names"""
        try:
            db_manager = DatabaseManager()
            db = db_manager.get_connection()
            cursor = db.cursor()
            
            # Test the same logic as in the fixed code
            where_clauses = []
            deletion_filter_applied = False
            
            # Try marked_for_deletion first
            try:
                cursor.execute("SELECT marked_for_deletion FROM works LIMIT 1")
                where_clauses = ["(w.marked_for_deletion = 0 OR w.marked_for_deletion IS NULL)"]
                deletion_filter_applied = True
                filter_type = "marked_for_deletion"
            except Exception as e:
                print(f"marked_for_deletion column not found: {e}")
                try:
                    # Then try is_deleted
                    cursor.execute("SELECT is_deleted FROM works LIMIT 1") 
                    where_clauses = ["(w.is_deleted = 0 OR w.is_deleted IS NULL)"]
                    deletion_filter_applied = True
                    filter_type = "is_deleted"
                except Exception as e2:
                    print(f"is_deleted column not found: {e2}")
                    # Fallback - no deletion filter
                    where_clauses = ["1=1"]
                    deletion_filter_applied = False
                    filter_type = "none"
            
            # Test query
            where_clause = " AND ".join(where_clauses)
            query = f"""
                SELECT w.id, w.name, w.code, u.name as unit, w.price, w.parent_id
                FROM works w
                LEFT JOIN units u ON w.unit_id = u.id
                WHERE {where_clause}
                ORDER BY w.name
                LIMIT 10
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            message = f"Database query test successful!\n"
            message += f"Filter type: {filter_type}\n"
            message += f"Deletion filter applied: {deletion_filter_applied}\n"
            message += f"Found {len(rows)} works"
            
            QMessageBox.information(self, "Database Test", message)
            self.statusBar().showMessage(f"Database test passed - using {filter_type} filter")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database query test failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Work Selector Bug Fixes Test")
    app.setApplicationVersion("1.0")
    
    try:
        # Create and show main window
        window = TestMainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
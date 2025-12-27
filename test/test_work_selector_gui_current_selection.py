#!/usr/bin/env python3
"""
GUI Test for work selector current selection highlighting

This script tests the actual GUI functionality of the work selector
current selection highlighting fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work
from src.views.dialogs.enhanced_work_selector_dialog import EnhancedWorkSelectorDialog


class WorkSelectorTestWindow(QMainWindow):
    """Test window for work selector current selection"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.db_manager.initialize("construction.db")
        self.session = self.db_manager.get_session()
        
        self.current_work_id = None
        self.current_work_name = ""
        
        self.setup_ui()
        self.load_test_work()
        
        # Auto-close timer for automated testing
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.close)
        self.auto_close_timer.start(30000)  # Close after 30 seconds
    
    def setup_ui(self):
        """Setup test UI"""
        self.setWindowTitle("Work Selector Current Selection Test")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("""
Work Selector Current Selection Test

This test verifies that the current work is properly highlighted
when reopening the work selector dialog.

Instructions:
1. Click 'Select Work' to open the work selector
2. Choose a work and close the dialog
3. Click 'Select Work' again
4. Verify that the previously selected work is highlighted
5. Test different hierarchy modes (Tree, Flat, Breadcrumb)
6. Test with works at different hierarchy levels
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Current work display
        self.current_work_label = QLabel("Current work: None selected")
        self.current_work_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.current_work_label)
        
        # Test buttons
        self.select_work_button = QPushButton("Select Work (Modal)")
        self.select_work_button.clicked.connect(self.on_select_work_modal)
        layout.addWidget(self.select_work_button)
        
        self.select_work_nonmodal_button = QPushButton("Select Work (Non-Modal)")
        self.select_work_nonmodal_button.clicked.connect(self.on_select_work_nonmodal)
        layout.addWidget(self.select_work_nonmodal_button)
        
        # Test with specific work IDs
        self.test_root_work_button = QPushButton("Test Root Level Work")
        self.test_root_work_button.clicked.connect(self.on_test_root_work)
        layout.addWidget(self.test_root_work_button)
        
        self.test_child_work_button = QPushButton("Test Child Work")
        self.test_child_work_button.clicked.connect(self.on_test_child_work)
        layout.addWidget(self.test_child_work_button)
        
        # Results
        self.results_label = QLabel("Test Results: Ready to test")
        self.results_label.setStyleSheet("padding: 10px; background-color: #e8f4f8;")
        layout.addWidget(self.results_label)
        
        central_widget.setLayout(layout)
    
    def load_test_work(self):
        """Load a test work for initial testing"""
        try:
            # Find a work with a parent (child work)
            work = self.session.query(Work).filter(Work.parent_id.isnot(None)).first()
            if work:
                self.current_work_id = work.id
                self.current_work_name = work.name
                self.update_current_work_display()
                print(f"Loaded test work: {work.id} - {work.name[:50]}...")
        except Exception as e:
            print(f"Error loading test work: {e}")
    
    def update_current_work_display(self):
        """Update current work display"""
        if self.current_work_id:
            self.current_work_label.setText(f"Current work: [{self.current_work_id}] {self.current_work_name[:100]}...")
        else:
            self.current_work_label.setText("Current work: None selected")
    
    def on_select_work_modal(self):
        """Open modal work selector"""
        self.open_work_selector(modal=True)
    
    def on_select_work_nonmodal(self):
        """Open non-modal work selector"""
        self.open_work_selector(modal=False)
    
    def open_work_selector(self, modal=True):
        """Open work selector dialog"""
        try:
            # Create dialog with current work ID
            dialog = EnhancedWorkSelectorDialog(self, self.current_work_id, user_id=4)
            
            # Override modal setting for testing
            dialog.settings['open_modal'] = modal
            dialog.apply_settings()
            
            # Connect selection signal
            def on_work_selected(work_id, work_name):
                self.current_work_id = work_id
                self.current_work_name = work_name
                self.update_current_work_display()
                
                # Check if the work was properly highlighted
                current_row = dialog.table_view.currentRow()
                if current_row >= 0:
                    id_item = dialog.table_view.item(current_row, 0)
                    if id_item and int(id_item.text()) == work_id:
                        self.results_label.setText(f"✅ SUCCESS: Work {work_id} was properly selected and highlighted at row {current_row}")
                        self.results_label.setStyleSheet("padding: 10px; background-color: #d4edda; color: #155724;")
                    else:
                        self.results_label.setText(f"❌ ERROR: Work {work_id} was selected but not highlighted correctly")
                        self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
                else:
                    self.results_label.setText(f"❌ ERROR: No row selected after work selection")
                    self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
            
            dialog.work_selected.connect(on_work_selected)
            
            # Show dialog
            if modal:
                result = dialog.exec()
                if result == dialog.DialogCode.Accepted:
                    print(f"Modal dialog accepted with work: {dialog.get_selected()}")
                else:
                    print("Modal dialog cancelled")
            else:
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
                print("Non-modal dialog opened")
                
                # Store reference to prevent garbage collection
                self._work_selector_dialog = dialog
        
        except Exception as e:
            print(f"Error opening work selector: {e}")
            import traceback
            traceback.print_exc()
            self.results_label.setText(f"❌ ERROR: Failed to open work selector: {e}")
            self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
    
    def on_test_root_work(self):
        """Test with a root level work"""
        try:
            # Find a root level work (parent_id is None or 0)
            work = self.session.query(Work).filter(
                (Work.parent_id.is_(None)) | (Work.parent_id == 0)
            ).first()
            
            if work:
                self.current_work_id = work.id
                self.current_work_name = work.name
                self.update_current_work_display()
                self.results_label.setText(f"✅ Set test work to root level work: {work.id}")
                self.results_label.setStyleSheet("padding: 10px; background-color: #d1ecf1; color: #0c5460;")
                print(f"Set test work to root level: {work.id} - {work.name[:50]}...")
            else:
                self.results_label.setText("❌ No root level works found")
                self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
        
        except Exception as e:
            print(f"Error finding root work: {e}")
            self.results_label.setText(f"❌ ERROR: {e}")
            self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
    
    def on_test_child_work(self):
        """Test with a child work"""
        try:
            # Find a child work (has parent_id)
            work = self.session.query(Work).filter(Work.parent_id.isnot(None)).first()
            
            if work:
                self.current_work_id = work.id
                self.current_work_name = work.name
                self.update_current_work_display()
                self.results_label.setText(f"✅ Set test work to child work: {work.id} (parent: {work.parent_id})")
                self.results_label.setStyleSheet("padding: 10px; background-color: #d1ecf1; color: #0c5460;")
                print(f"Set test work to child: {work.id} - {work.name[:50]}... (parent: {work.parent_id})")
            else:
                self.results_label.setText("❌ No child works found")
                self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
        
        except Exception as e:
            print(f"Error finding child work: {e}")
            self.results_label.setText(f"❌ ERROR: {e}")
            self.results_label.setStyleSheet("padding: 10px; background-color: #f8d7da; color: #721c24;")
    
    def closeEvent(self, event):
        """Handle close event"""
        if hasattr(self, 'session'):
            self.session.close()
        event.accept()


def main():
    """Main function"""
    print("🔧 Starting Work Selector Current Selection GUI Test")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Work Selector Test")
    app.setApplicationVersion("1.0")
    
    try:
        # Create and show test window
        window = WorkSelectorTestWindow()
        window.show()
        
        print("✅ Test window opened successfully")
        print("📋 Instructions:")
        print("   1. Click 'Select Work' to open the work selector")
        print("   2. Choose a work and close the dialog")
        print("   3. Click 'Select Work' again")
        print("   4. Verify that the previously selected work is highlighted")
        print("   5. Test different hierarchy modes and work types")
        print("   6. Window will auto-close after 30 seconds")
        print("\n🎯 What to verify:")
        print("   • Current work is highlighted when reopening selector")
        print("   • Automatic navigation to correct hierarchy level")
        print("   • Fallback to flat mode if work not found in tree view")
        print("   • Consistent behavior in modal and non-modal modes")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error starting test application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
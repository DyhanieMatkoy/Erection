"""
Example demonstrating dynamic loading functionality in desktop GenericListForm

This example shows how to use the enhanced GenericListForm with dynamic loading
capabilities for handling large datasets efficiently.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, 'src')

from src.views.generic_list_form import GenericListForm


class MockController:
    """Mock controller that simulates paginated data loading"""
    
    def __init__(self):
        self.selection = []
        self.filters = {}
        self.current_page = 1
        self.page_size = 50
        
        # Generate mock data
        self.all_data = []
        for i in range(500):  # 500 total items to demonstrate pagination
            self.all_data.append({
                'id': i + 1,
                'name': f'Document {i + 1:03d}',
                'type': 'Type A' if i % 3 == 0 else 'Type B' if i % 3 == 1 else 'Type C',
                'date': f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                'status': 'Active' if i % 4 != 0 else 'Inactive',
                'amount': round((i + 1) * 123.45, 2)
            })
    
    def initialize(self):
        """Initialize controller"""
        pass
    
    def set_callbacks(self, on_data_loaded=None, on_error=None):
        """Set callback functions"""
        self.on_data_loaded = on_data_loaded
        self.on_error = on_error
    
    def filter_columns(self, columns):
        """Filter columns based on permissions"""
        return columns
    
    def get_available_commands(self, context=None):
        """Get available commands for toolbar"""
        return [
            {'id': 'create', 'label': 'Создать', 'is_enabled': True},
            {'id': 'open', 'label': 'Открыть', 'is_enabled': len(self.selection) == 1},
            {'id': 'refresh', 'label': 'Обновить', 'is_enabled': True},
        ]
    
    def get_selection(self):
        """Get current selection"""
        return self.selection.copy()
    
    def update_selection(self, selected_ids):
        """Update selection"""
        self.selection = selected_ids.copy()
    
    def set_filter(self, key, value):
        """Set filter value"""
        self.filters[key] = value
        # Reset to first page when filters change
        self.current_page = 1
        # Trigger data reload
        if hasattr(self, 'on_data_loaded'):
            QTimer.singleShot(100, self.load_data)  # Simulate async loading
    
    def get_dynamic_loading_config(self):
        """Get dynamic loading configuration"""
        return {
            'enabled': True,
            'page_size': 50,
            'load_threshold': 10
        }
    
    def load_page(self, page=1, page_size=50):
        """Load a specific page of data"""
        # Apply filters
        filtered_data = self.all_data.copy()
        
        # Apply search filter if present
        search_text = self.filters.get('search_text', '').lower()
        if search_text:
            filtered_data = [
                item for item in filtered_data 
                if search_text in item['name'].lower() or search_text in item['type'].lower()
            ]
        
        # Calculate pagination
        total_items = len(filtered_data)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_items = filtered_data[start_index:end_index]
        
        return {
            'success': True,
            'items': page_items,
            'total_items': total_items,
            'current_page': page,
            'has_more': end_index < total_items
        }
    
    def load_data(self):
        """Load data (first page)"""
        result = self.load_page(page=1, page_size=self.page_size)
        if self.on_data_loaded:
            self.on_data_loaded(result)
    
    def execute_command(self, command_id):
        """Execute a command"""
        if command_id == 'refresh':
            self.load_data()
            return {'success': True, 'refresh_needed': False}
        return {'success': False, 'error': f'Unknown command: {command_id}'}
    
    def close(self):
        """Close controller"""
        pass


class DynamicLoadingDemo(QMainWindow):
    """Demo window showing dynamic loading functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Loading Demo - Desktop GenericListForm")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create mock controller
        self.controller = MockController()
        
        # Create GenericListForm with dynamic loading
        self.list_form = GenericListForm(
            form_id="demo_form",
            user_id=1,
            model_class=None,  # Not needed for this demo
            controller=self.controller
        )
        
        # Configure columns
        columns = [
            {'id': 'id', 'name': 'ID', 'width': 60, 'visible': True},
            {'id': 'name', 'name': 'Наименование', 'width': 200, 'visible': True},
            {'id': 'type', 'name': 'Тип', 'width': 100, 'visible': True},
            {'id': 'date', 'name': 'Дата', 'width': 100, 'visible': True},
            {'id': 'status', 'name': 'Статус', 'width': 100, 'visible': True},
            {'id': 'amount', 'name': 'Сумма', 'width': 120, 'visible': True},
        ]
        self.list_form.configure_columns(columns)
        
        # Add demo controls
        controls_layout = QVBoxLayout()
        
        # Button to load data
        load_button = QPushButton("Загрузить данные (500 записей)")
        load_button.clicked.connect(self.load_demo_data)
        controls_layout.addWidget(load_button)
        
        # Button to test search
        search_button = QPushButton("Тест поиска (Type A)")
        search_button.clicked.connect(self.test_search)
        controls_layout.addWidget(search_button)
        
        # Button to clear search
        clear_button = QPushButton("Очистить поиск")
        clear_button.clicked.connect(self.clear_search)
        controls_layout.addWidget(clear_button)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.list_form)
        
        # Connect to document open signal
        self.list_form.open_document_requested.connect(self.on_document_open)
        
        print("Dynamic Loading Demo initialized")
        print("- Total items: 500")
        print("- Page size: 50 items")
        print("- Load threshold: 10 items from bottom")
        print("- Scroll to bottom to load more data automatically")
    
    def load_demo_data(self):
        """Load demo data"""
        print("Loading demo data...")
        self.list_form.load_data()
    
    def test_search(self):
        """Test search functionality"""
        print("Testing search for 'Type A'...")
        # Simulate search input
        self.list_form.on_search("Type A")
    
    def clear_search(self):
        """Clear search"""
        print("Clearing search...")
        self.list_form.on_search("")
    
    def on_document_open(self, document_id):
        """Handle document open request"""
        if document_id == 0:
            print("Create new document requested")
        else:
            print(f"Open document requested: ID {document_id}")


def main():
    """Run the dynamic loading demo"""
    app = QApplication(sys.argv)
    
    # Create and show demo window
    demo = DynamicLoadingDemo()
    demo.show()
    
    # Load initial data
    QTimer.singleShot(500, demo.load_demo_data)
    
    print("\n=== Dynamic Loading Demo Instructions ===")
    print("1. Click 'Загрузить данные' to load the first 50 items")
    print("2. Scroll down to the bottom to automatically load more items")
    print("3. Use 'Тест поиска' to filter items and see how pagination resets")
    print("4. Double-click items to simulate opening documents")
    print("5. Watch the console for loading messages")
    print("==========================================\n")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
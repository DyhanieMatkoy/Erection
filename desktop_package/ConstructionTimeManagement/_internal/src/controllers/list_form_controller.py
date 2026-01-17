from typing import Optional, List, Dict, Any, Callable
from api.services.data_service import DataService
from api.services.user_settings_manager import UserSettingsManager
from api.services.command_manager import CommandManager
from api.services.auth_service import AuthService
from api.services.permission_service import PermissionService
from src.data.database_manager import DatabaseManager
from src.services.bulk_operation_service import BulkOperationService

class ListFormController:
    """
    Controller for Document List Forms.
    Manages data loading, user settings application, and command execution.
    """
    def __init__(self, form_id: str, user_id: int, model_class: Any):
        self.form_id = form_id
        self.user_id = user_id
        self.model_class = model_class
        
        # Initialize services
        # Note: In a real app we might inject these or use a container
        self.db_manager = DatabaseManager()
        # We need a session for the services. 
        # For a desktop app, we might keep a session open or open per operation.
        # DataService uses a session.
        try:
            self.session = self.db_manager.get_session() 
        except Exception:
            # Fallback for testing/mocking if db manager not initialized
            self.session = None

        self.data_service = DataService(self.session)
        self.settings_manager = UserSettingsManager(self.session)
        self.command_manager = CommandManager(self.session)
        self.auth_service = AuthService(self.session)
        self.permission_service = PermissionService(self.session)
        self.bulk_service = BulkOperationService()
        
        # State
        self.current_page = 1
        self.page_size = 50
        self.filters: Dict[str, Any] = {}
        self.sort_by: Optional[str] = None
        self.sort_order: str = "asc"
        self.column_settings: Optional[Dict] = None
        self.data_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.selection: set = set()
        self.user_role: Optional[str] = None

    def initialize(self):
        """Initialize controller and load settings"""
        self.load_user_role()
        self.load_settings()

    def load_user_role(self):
        """Load user role"""
        user = self.auth_service.get_user_by_id(self.user_id, self.session)
        if user:
            self.user_role = user.get('role', 'executor')
        else:
            self.user_role = 'executor' # Default fallback

    def filter_columns(self, columns: List[Dict]) -> List[Dict]:
        """Filter columns based on permissions"""
        if not self.user_role:
            self.load_user_role()
        return self.permission_service.filter_accessible_columns(columns, self.user_role, self.form_id)

    def set_callbacks(self, on_data_loaded: Callable, on_error: Callable):
        """Set callbacks for async operations (if we were async) or just decoupling"""
        self.data_callback = on_data_loaded
        self.error_callback = on_error

    def update_selection(self, selected_ids: List[Any]):
        """Update current selection"""
        self.selection = set(selected_ids)
        # We might want to trigger command availability update here

    def get_selection(self) -> List[Any]:
        """Get current selection"""
        return list(self.selection)

    def load_settings(self):
        """Load user settings for this form"""
        try:
            self.column_settings = self.settings_manager.load_column_settings(self.user_id, self.form_id)
            # Load sort preferences if any
            sort_prefs = self.settings_manager._load_generic_settings(self.user_id, self.form_id, "sorting")
            if sort_prefs:
                self.sort_by = sort_prefs.get("sort_by")
                self.sort_order = sort_prefs.get("sort_order", "asc")
                
            # Load filter preferences
            filter_prefs = self.settings_manager._load_generic_settings(self.user_id, self.form_id, "filters")
            if filter_prefs:
                self.filters.update(filter_prefs)
                
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Failed to load settings: {str(e)}")

    def load_data(self):
        """Load data based on current state"""
        try:
            result = self.data_service.get_documents(
                model_class=self.model_class,
                page=self.current_page,
                page_size=self.page_size,
                filters=self.filters,
                sort_by=self.sort_by,
                sort_order=self.sort_order
            )
            
            if self.data_callback:
                self.data_callback(result)
                
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Failed to load data: {str(e)}")

    def apply_user_settings(self):
        """Apply settings to the view (helper method)"""
        # This might return the settings object for the view to consume
        return self.column_settings

    def handle_column_resize(self, column_id: str, width: int):
        """Handle column resize event"""
        if not self.column_settings:
            self.column_settings = {}
        
        # Update width
        # self.column_settings[column_id] = {'width': width} ... logic depends on structure
        # Simple implementation:
        if isinstance(self.column_settings, dict):
            if column_id not in self.column_settings:
                self.column_settings[column_id] = {}
            self.column_settings[column_id]['width'] = width
            
            # Save asynchronously or debounce in real app
            self.settings_manager.save_column_settings(self.user_id, self.form_id, self.column_settings)

    def calculate_column_widths(self, total_width: int, columns: List[Dict]) -> Dict[str, int]:
        """
        Calculate column widths based on total width and settings.
        columns: List of dicts with 'id', 'min_width', 'default_width'
        """
        if not columns or total_width <= 0:
            return {}

        # 1. Load saved widths
        saved_widths = {}
        if self.column_settings:
            for col_id, settings in self.column_settings.items():
                if isinstance(settings, dict) and 'width' in settings:
                    saved_widths[col_id] = settings['width']

        # 2. Determine base widths (saved or default)
        final_widths = {}
        used_width = 0
        undefined_cols = []

        for col in columns:
            col_id = col['id']
            if col_id in saved_widths:
                width = saved_widths[col_id]
                final_widths[col_id] = width
                used_width += width
            else:
                # If no saved width, we might want to distribute remaining
                undefined_cols.append(col)
        
        # 3. Distribute remaining space or use defaults
        # This is a simple implementation. A more complex one would scale.
        remaining_width = total_width - used_width
        
        if undefined_cols:
            if remaining_width > 0:
                # Distribute equally
                width_per_col = remaining_width // len(undefined_cols)
                for col in undefined_cols:
                    final_widths[col['id']] = max(width_per_col, col.get('min_width', 50))
            else:
                # Use defaults or min
                for col in undefined_cols:
                    final_widths[col['id']] = col.get('default_width', 100)
        
        return final_widths

    def handle_sorting(self, column_id: str):
        """Handle sort request"""
        if self.sort_by == column_id:
            self.sort_order = "desc" if self.sort_order == "asc" else "asc"
        else:
            self.sort_by = column_id
            self.sort_order = "asc"
            
        # Save preferences
        self.settings_manager._save_generic_settings(
            self.user_id, self.form_id, "sorting", 
            {"sort_by": self.sort_by, "sort_order": self.sort_order}
        )
        
        # Reload data
        self.load_data()

    def set_filter(self, key: str, value: Any):
        """Set a filter value"""
        if value == "":
            if key in self.filters:
                del self.filters[key]
        else:
            self.filters[key] = value
            
        # Save preferences (optional, maybe only manual save?)
        # For now, let's autosave
        self.settings_manager._save_generic_settings(self.user_id, self.form_id, "filters", self.filters)
        
        self.current_page = 1 # Reset to first page
        self.load_data()

    def set_page(self, page: int):
        """Change page"""
        self.current_page = page
        self.load_data()

    def handle_keyboard_shortcut(self, key: str, modifiers: List[str] = None) -> bool:
        """
        Handle keyboard shortcut.
        Returns True if handled.
        
        Shortcuts:
        - Ins: Create
        - F9: Copy
        - F2: Edit
        - Del: Delete
        - F5: Refresh
        - F8: Print
        """
        modifiers = modifiers or []
        
        # Check context (e.g., focus) - UI layer should handle focus check before calling this
        
        if key == "Insert":
            return self.execute_command("create").get("success", False)
        elif key == "F9":
            return self.execute_command("copy").get("success", False)
        elif key == "F2":
            return self.execute_command("edit").get("success", False)
        elif key == "Delete":
            return self.execute_command("delete").get("success", False)
        elif key == "F5":
            return self.execute_command("refresh").get("success", False)
        elif key == "F8":
            return self.execute_command("print").get("success", False)
            
        return False

    def get_available_commands(self, selection_context: Dict = None) -> List[Dict]:
        """Get commands available for current context"""
        return self.command_manager.get_available_commands(self.user_id, self.form_id, selection_context)

    def execute_command(self, command_id: str) -> Dict[str, Any]:
        """
        Execute a command.
        Returns dict with success, message, refresh_needed, error.
        """
        try:
            # 1. Handle standard commands
            if command_id == 'delete':
                return self._handle_delete()
            elif command_id == 'refresh':
                self.load_data()
                return {'success': True}
            elif command_id == 'create':
                # Notify view to open creation dialog
                return {'success': True, 'action': 'create'}
            elif command_id == 'copy':
                if not self.selection or len(self.selection) != 1:
                    return {'success': False, 'error': 'Select exactly one item to copy'}
                return {'success': True, 'action': 'copy', 'item_id': list(self.selection)[0]}
            elif command_id == 'edit':
                if not self.selection or len(self.selection) != 1:
                    return {'success': False, 'error': 'Select exactly one item to edit'}
                return {'success': True, 'action': 'edit', 'item_id': list(self.selection)[0]}
            elif command_id == 'print':
                if not self.selection:
                     return {'success': False, 'error': 'Nothing selected'}
                return {'success': True, 'action': 'print', 'item_ids': list(self.selection)}
            
            # 2. Handle custom commands via handlers (to be registered)
            if hasattr(self, f'handle_{command_id}'):
                handler = getattr(self, f'handle_{command_id}')
                return handler()
            
            return {'success': False, 'error': f"Unknown command: {command_id}"}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_bulk_operation(self, operation_name: str, items: List[Any], handler: Callable[[Any], Dict[str, Any]]) -> str:
        """Execute a bulk operation"""
        return self.bulk_service.execute_operation(operation_name, items, handler)

    def _handle_delete(self) -> Dict[str, Any]:
        """Handle delete command"""
        if not self.selection:
            return {'success': False, 'error': "Nothing selected"}
            
        ids = list(self.selection)
        # Check permission (simple check for now)
        # In real app, check 'delete' permission for resource
        
        count = self.data_service.delete_documents(self.model_class, ids)
        self.selection.clear()
        self.load_data()
        return {'success': True, 'message': f"Deleted {count} items", 'refresh_needed': True}

    def close(self):
        """Cleanup"""
        if self.session:
            self.session.close()

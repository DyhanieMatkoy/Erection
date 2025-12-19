"""User settings service for managing application preferences"""
from typing import Any, Dict, Optional
from src.data.database_manager import DatabaseManager


class UserSettingsService:
    """Service for managing user settings"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        # Ensure database is initialized
        if not hasattr(self.db_manager, '_engine') or self.db_manager._engine is None:
            try:
                self.db_manager.initialize('construction.db')
            except Exception as e:
                print(f"Warning: Could not initialize database in UserSettingsService: {e}")
    
    def get_setting(self, user_id: int, key: str, default_value: Any = None) -> Any:
        """Get user setting value"""
        try:
            query = """
                SELECT setting_value 
                FROM user_settings 
                WHERE user_id = ? AND setting_key = ?
            """
            result = self.db_manager.execute_query(query, (user_id, key))
            
            if result:
                # Try to parse JSON if it's a complex value
                import json
                try:
                    return json.loads(result[0][0])
                except (json.JSONDecodeError, TypeError):
                    return result[0][0]
            
            return default_value
            
        except Exception as e:
            print(f"Error getting setting {key}: {e}")
            return default_value
    
    def set_setting(self, user_id: int, key: str, value: Any) -> bool:
        """Set user setting value"""
        try:
            # Convert complex values to JSON
            import json
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # Check if setting exists
            query = """
                SELECT setting_value FROM user_settings 
                WHERE user_id = ? AND setting_key = ?
            """
            result = self.db_manager.execute_query(query, (user_id, key))
            
            if result:
                # Update existing setting
                update_query = """
                    UPDATE user_settings 
                    SET setting_value = ?
                    WHERE user_id = ? AND setting_key = ?
                """
                self.db_manager.execute_update(update_query, (value_str, user_id, key))
            else:
                # Insert new setting - need to handle the actual table structure
                insert_query = """
                    INSERT OR REPLACE INTO user_settings (user_id, form_name, setting_key, setting_value)
                    VALUES (?, ?, ?, ?)
                """
                # Use empty form_name for general settings
                self.db_manager.execute_update(insert_query, (user_id, '', key, value_str))
            
            return True
            
        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False
    
    def get_delete_marked_settings(self, user_id: int) -> Dict[str, bool]:
        """Get settings for delete marked objects dialog"""
        return {
            'show_marked_objects': self.get_setting(user_id, 'delete_marked.show_marked_objects', False),
            'show_estimates': self.get_setting(user_id, 'delete_marked.show_estimates', True),
            'show_daily_reports': self.get_setting(user_id, 'delete_marked.show_daily_reports', True),
            'show_timesheets': self.get_setting(user_id, 'delete_marked.show_timesheets', True),
            'show_counterparties': self.get_setting(user_id, 'delete_marked.show_counterparties', True),
            'show_objects': self.get_setting(user_id, 'delete_marked.show_objects', True),
            'show_organizations': self.get_setting(user_id, 'delete_marked.show_organizations', True),
            'show_persons': self.get_setting(user_id, 'delete_marked.show_persons', True),
            'show_works': self.get_setting(user_id, 'delete_marked.show_works', True),
        }
    
    def set_delete_marked_settings(self, user_id: int, settings: Dict[str, bool]) -> bool:
        """Set settings for delete marked objects dialog"""
        try:
            for key, value in settings.items():
                self.set_setting(user_id, f'delete_marked.{key}', value)
            return True
        except Exception as e:
            print(f"Error setting delete marked settings: {e}")
            return False
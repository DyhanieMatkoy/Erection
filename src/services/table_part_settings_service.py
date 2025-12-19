"""
Service for managing table part user settings and configuration.

This service handles persistence and retrieval of user-specific
table part settings, command configurations, and preferences.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..data.models.sqlalchemy_models import (
    UserTablePartSettings, TablePartCommandConfig, User
)
from ..data.models.table_part_models import (
    TablePartConfiguration, TablePartSettingsData, TablePartCommand,
    PanelSettings, ShortcutSettings, CommandType
)
import json
import logging
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)

# Current settings version
CURRENT_SETTINGS_VERSION = "1.0"


class TablePartSettingsService:
    """Service for managing table part settings and configuration"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_user_settings(
        self,
        user_id: int,
        document_type: str,
        table_part_id: str
    ) -> Optional[TablePartSettingsData]:
        """
        Get user-specific settings for a table part.
        
        Args:
            user_id: User ID
            document_type: Type of document (e.g., 'estimate', 'daily_report')
            table_part_id: ID of the table part (e.g., 'lines', 'materials')
            
        Returns:
            TablePartSettingsData or None if not found
        """
        try:
            settings_record = self.db_session.query(UserTablePartSettings).filter(
                and_(
                    UserTablePartSettings.user_id == user_id,
                    UserTablePartSettings.document_type == document_type,
                    UserTablePartSettings.table_part_id == table_part_id
                )
            ).first()
            
            if settings_record:
                # Migrate settings if needed
                migrated_data, was_migrated = self.migrate_settings_if_needed(
                    settings_record.settings_data
                )
                
                # Update database if migration occurred
                if was_migrated:
                    settings_record.settings_data = migrated_data
                    self.db_session.commit()
                    logger.info(f"Auto-migrated settings for user {user_id}, document {document_type}, table {table_part_id}")
                
                return TablePartSettingsData.from_json(migrated_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return None
    
    def save_user_settings(
        self,
        user_id: int,
        document_type: str,
        table_part_id: str,
        settings: TablePartSettingsData
    ) -> bool:
        """
        Save user-specific settings for a table part.
        
        Args:
            user_id: User ID
            document_type: Type of document
            table_part_id: ID of the table part
            settings: Settings data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if settings already exist
            existing_settings = self.db_session.query(UserTablePartSettings).filter(
                and_(
                    UserTablePartSettings.user_id == user_id,
                    UserTablePartSettings.document_type == document_type,
                    UserTablePartSettings.table_part_id == table_part_id
                )
            ).first()
            
            # Add version information to settings
            settings_dict = settings.to_dict()
            settings_dict['version'] = CURRENT_SETTINGS_VERSION
            settings_dict['updated_at'] = datetime.now().isoformat()
            settings_json = json.dumps(settings_dict, ensure_ascii=False, indent=2)
            
            if existing_settings:
                # Update existing settings
                existing_settings.settings_data = settings_json
            else:
                # Create new settings record
                new_settings = UserTablePartSettings(
                    user_id=user_id,
                    document_type=document_type,
                    table_part_id=table_part_id,
                    settings_data=settings_json
                )
                self.db_session.add(new_settings)
            
            self.db_session.commit()
            logger.info(f"Saved table part settings for user {user_id}, document {document_type}, table {table_part_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")
            self.db_session.rollback()
            return False
    
    def get_command_configuration(
        self,
        document_type: str,
        table_part_id: str,
        user_id: Optional[int] = None
    ) -> List[TablePartCommand]:
        """
        Get command configuration for a table part.
        
        Args:
            document_type: Type of document
            table_part_id: ID of the table part
            user_id: User ID (None for global settings)
            
        Returns:
            List of configured commands
        """
        try:
            query = self.db_session.query(TablePartCommandConfig).filter(
                and_(
                    TablePartCommandConfig.document_type == document_type,
                    TablePartCommandConfig.table_part_id == table_part_id,
                    TablePartCommandConfig.user_id == user_id
                )
            ).order_by(TablePartCommandConfig.position)
            
            command_configs = query.all()
            
            # Convert to TablePartCommand objects
            commands = []
            for config in command_configs:
                command = TablePartCommand(
                    id=config.command_id,
                    name=self._get_command_name(config.command_id),
                    icon=self._get_command_icon(config.command_id),
                    tooltip=self._get_command_tooltip(config.command_id),
                    enabled=config.is_enabled,
                    visible=config.is_visible,
                    position=config.position
                )
                commands.append(command)
            
            return commands
            
        except Exception as e:
            logger.error(f"Error getting command configuration: {e}")
            return []
    
    def save_command_configuration(
        self,
        document_type: str,
        table_part_id: str,
        commands: List[TablePartCommand],
        user_id: Optional[int] = None
    ) -> bool:
        """
        Save command configuration for a table part.
        
        Args:
            document_type: Type of document
            table_part_id: ID of the table part
            commands: List of commands to save
            user_id: User ID (None for global settings)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing configurations
            self.db_session.query(TablePartCommandConfig).filter(
                and_(
                    TablePartCommandConfig.document_type == document_type,
                    TablePartCommandConfig.table_part_id == table_part_id,
                    TablePartCommandConfig.user_id == user_id
                )
            ).delete()
            
            # Add new configurations
            for command in commands:
                config = TablePartCommandConfig(
                    document_type=document_type,
                    table_part_id=table_part_id,
                    user_id=user_id,
                    command_id=command.id,
                    is_visible=command.visible,
                    is_enabled=command.enabled,
                    position=command.position,
                    is_in_more_menu=not command.visible
                )
                self.db_session.add(config)
            
            self.db_session.commit()
            logger.info(f"Saved command configuration for document {document_type}, table {table_part_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving command configuration: {e}")
            self.db_session.rollback()
            return False
    
    def get_default_settings(
        self,
        document_type: str,
        table_part_id: str
    ) -> TablePartSettingsData:
        """
        Get default settings for a table part.
        
        Args:
            document_type: Type of document
            table_part_id: ID of the table part
            
        Returns:
            Default TablePartSettingsData
        """
        # Create default settings based on document type and table part
        default_visible_commands = self._get_default_visible_commands(document_type, table_part_id)
        
        panel_settings = PanelSettings(
            visible_commands=default_visible_commands,
            button_size="medium",
            show_tooltips=True,
            compact_mode=False
        )
        
        shortcuts = ShortcutSettings(
            enabled=True,
            custom_mappings={}
        )
        
        return TablePartSettingsData(
            panel_settings=panel_settings,
            shortcuts=shortcuts
        )
    
    def reset_user_settings(
        self,
        user_id: int,
        document_type: str,
        table_part_id: str
    ) -> bool:
        """
        Reset user settings to defaults.
        
        Args:
            user_id: User ID
            document_type: Type of document
            table_part_id: ID of the table part
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing settings
            self.db_session.query(UserTablePartSettings).filter(
                and_(
                    UserTablePartSettings.user_id == user_id,
                    UserTablePartSettings.document_type == document_type,
                    UserTablePartSettings.table_part_id == table_part_id
                )
            ).delete()
            
            self.db_session.commit()
            logger.info(f"Reset settings for user {user_id}, document {document_type}, table {table_part_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting user settings: {e}")
            self.db_session.rollback()
            return False
    
    def get_all_user_settings(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all table part settings for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of settings dictionaries
        """
        try:
            settings_records = self.db_session.query(UserTablePartSettings).filter(
                UserTablePartSettings.user_id == user_id
            ).all()
            
            result = []
            for record in settings_records:
                result.append({
                    'document_type': record.document_type,
                    'table_part_id': record.table_part_id,
                    'settings': TablePartSettingsData.from_json(record.settings_data).to_dict(),
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all user settings: {e}")
            return []
    
    def _get_default_visible_commands(self, document_type: str, table_part_id: str) -> List[str]:
        """Get default visible commands based on document type and table part"""
        # Standard commands that are visible by default
        default_commands = [
            CommandType.ADD_ROW.value,
            CommandType.DELETE_ROW.value,
            CommandType.MOVE_UP.value,
            CommandType.MOVE_DOWN.value
        ]
        
        # Add document-specific commands
        if document_type in ['estimate', 'daily_report']:
            default_commands.extend([
                CommandType.IMPORT_DATA.value,
                CommandType.EXPORT_DATA.value
            ])
        
        return default_commands
    
    def _get_command_name(self, command_id: str) -> str:
        """Get localized command name"""
        command_names = {
            CommandType.ADD_ROW.value: "Добавить",
            CommandType.DELETE_ROW.value: "Удалить",
            CommandType.MOVE_UP.value: "Выше",
            CommandType.MOVE_DOWN.value: "Ниже",
            CommandType.IMPORT_DATA.value: "Импорт",
            CommandType.EXPORT_DATA.value: "Экспорт",
            CommandType.PRINT_DATA.value: "Печать",
            CommandType.COPY_ROWS.value: "Копировать",
            CommandType.PASTE_ROWS.value: "Вставить",
            CommandType.DUPLICATE_ROW.value: "Дублировать",
            CommandType.CLEAR_SELECTION.value: "Снять выделение"
        }
        return command_names.get(command_id, command_id)
    
    def _get_command_icon(self, command_id: str) -> str:
        """Get command icon"""
        command_icons = {
            CommandType.ADD_ROW.value: "➕",
            CommandType.DELETE_ROW.value: "🗑",
            CommandType.MOVE_UP.value: "↑",
            CommandType.MOVE_DOWN.value: "↓",
            CommandType.IMPORT_DATA.value: "📥",
            CommandType.EXPORT_DATA.value: "📤",
            CommandType.PRINT_DATA.value: "🖨",
            CommandType.COPY_ROWS.value: "📋",
            CommandType.PASTE_ROWS.value: "📄",
            CommandType.DUPLICATE_ROW.value: "📑",
            CommandType.CLEAR_SELECTION.value: "❌"
        }
        return command_icons.get(command_id, "⚙️")
    
    def _get_command_tooltip(self, command_id: str) -> str:
        """Get command tooltip"""
        command_tooltips = {
            CommandType.ADD_ROW.value: "Добавить новую строку (Insert)",
            CommandType.DELETE_ROW.value: "Удалить выбранные строки (Delete)",
            CommandType.MOVE_UP.value: "Переместить строки выше (Ctrl+Shift+Up)",
            CommandType.MOVE_DOWN.value: "Переместить строки ниже (Ctrl+Shift+Down)",
            CommandType.IMPORT_DATA.value: "Импортировать данные из файла",
            CommandType.EXPORT_DATA.value: "Экспортировать данные в файл",
            CommandType.PRINT_DATA.value: "Печать табличной части",
            CommandType.COPY_ROWS.value: "Копировать выбранные строки (Ctrl+C)",
            CommandType.PASTE_ROWS.value: "Вставить строки (Ctrl+V)",
            CommandType.DUPLICATE_ROW.value: "Дублировать выбранную строку",
            CommandType.CLEAR_SELECTION.value: "Снять выделение строк"
        }
        return command_tooltips.get(command_id, "Выполнить команду")
    
    def migrate_settings_if_needed(
        self,
        settings_data: str,
        current_version: str = CURRENT_SETTINGS_VERSION
    ) -> Tuple[str, bool]:
        """
        Migrate settings data to current version if needed.
        
        Args:
            settings_data: JSON string of settings data
            current_version: Target version to migrate to
            
        Returns:
            Tuple of (migrated_settings_json, was_migrated)
        """
        try:
            settings_dict = json.loads(settings_data)
            
            # Check if migration is needed
            stored_version = settings_dict.get('version', '0.9')  # Default to old version
            
            if stored_version == current_version:
                return settings_data, False
            
            # Apply migrations
            migrated_settings = self._apply_settings_migrations(
                settings_dict, stored_version, current_version
            )
            
            # Update version
            migrated_settings['version'] = current_version
            migrated_settings['migrated_at'] = datetime.now().isoformat()
            
            migrated_json = json.dumps(migrated_settings, ensure_ascii=False, indent=2)
            logger.info(f"Migrated settings from version {stored_version} to {current_version}")
            
            return migrated_json, True
            
        except Exception as e:
            logger.error(f"Error migrating settings: {e}")
            return settings_data, False
    
    def _apply_settings_migrations(
        self,
        settings: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        Apply version-specific migrations to settings.
        
        Args:
            settings: Settings dictionary to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migrated settings dictionary
        """
        migrated_settings = settings.copy()
        
        # Migration from 0.9 to 1.0 (initial version with proper structure)
        if from_version == "0.9" and to_version >= "1.0":
            migrated_settings = self._migrate_0_9_to_1_0(migrated_settings)
        
        # Future migrations can be added here
        # if from_version == "1.0" and to_version >= "1.1":
        #     migrated_settings = self._migrate_1_0_to_1_1(migrated_settings)
        
        return migrated_settings
    
    def _migrate_0_9_to_1_0(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate settings from version 0.9 to 1.0.
        
        Changes:
        - Ensure proper structure for panel_settings
        - Add missing default values
        - Convert old command format to new format
        """
        migrated = settings.copy()
        
        # Ensure panel_settings structure
        if 'panel_settings' not in migrated:
            migrated['panel_settings'] = {}
        
        panel_settings = migrated['panel_settings']
        
        # Add missing panel settings with defaults
        if 'visible_commands' not in panel_settings:
            panel_settings['visible_commands'] = [
                'add_row', 'delete_row', 'move_up', 'move_down'
            ]
        
        if 'hidden_commands' not in panel_settings:
            panel_settings['hidden_commands'] = []
        
        if 'button_size' not in panel_settings:
            panel_settings['button_size'] = 'medium'
        
        if 'show_tooltips' not in panel_settings:
            panel_settings['show_tooltips'] = True
        
        if 'compact_mode' not in panel_settings:
            panel_settings['compact_mode'] = False
        
        # Ensure shortcuts structure
        if 'shortcuts' not in migrated:
            migrated['shortcuts'] = {}
        
        shortcuts = migrated['shortcuts']
        
        if 'enabled' not in shortcuts:
            shortcuts['enabled'] = True
        
        if 'custom_mappings' not in shortcuts:
            shortcuts['custom_mappings'] = {}
        
        # Ensure other required fields
        if 'column_widths' not in migrated:
            migrated['column_widths'] = {}
        
        if 'column_order' not in migrated:
            migrated['column_order'] = []
        
        if 'hidden_columns' not in migrated:
            migrated['hidden_columns'] = []
        
        if 'sort_column' not in migrated:
            migrated['sort_column'] = None
        
        if 'sort_direction' not in migrated:
            migrated['sort_direction'] = 'asc'
        
        return migrated
    
    def export_user_settings(
        self,
        user_id: int,
        document_type: Optional[str] = None,
        table_part_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export user settings for backup or transfer.
        
        Args:
            user_id: User ID
            document_type: Optional filter by document type
            table_part_id: Optional filter by table part ID
            
        Returns:
            Dictionary with exported settings
        """
        try:
            query = self.db_session.query(UserTablePartSettings).filter(
                UserTablePartSettings.user_id == user_id
            )
            
            if document_type:
                query = query.filter(UserTablePartSettings.document_type == document_type)
            
            if table_part_id:
                query = query.filter(UserTablePartSettings.table_part_id == table_part_id)
            
            settings_records = query.all()
            
            export_data = {
                'export_version': CURRENT_SETTINGS_VERSION,
                'export_date': datetime.now().isoformat(),
                'user_id': user_id,
                'settings': []
            }
            
            for record in settings_records:
                # Ensure settings are migrated before export
                migrated_data, _ = self.migrate_settings_if_needed(record.settings_data)
                
                export_data['settings'].append({
                    'document_type': record.document_type,
                    'table_part_id': record.table_part_id,
                    'settings_data': json.loads(migrated_data),
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user settings: {e}")
            return {'error': str(e)}
    
    def import_user_settings(
        self,
        user_id: int,
        import_data: Dict[str, Any],
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import user settings from backup or transfer.
        
        Args:
            user_id: Target user ID
            import_data: Exported settings data
            overwrite_existing: Whether to overwrite existing settings
            
        Returns:
            Dictionary with import results
        """
        try:
            imported_count = 0
            skipped_count = 0
            errors = []
            
            settings_list = import_data.get('settings', [])
            
            for setting_data in settings_list:
                document_type = setting_data['document_type']
                table_part_id = setting_data['table_part_id']
                settings_json = json.dumps(setting_data['settings_data'])
                
                # Check if settings already exist
                existing = self.db_session.query(UserTablePartSettings).filter(
                    and_(
                        UserTablePartSettings.user_id == user_id,
                        UserTablePartSettings.document_type == document_type,
                        UserTablePartSettings.table_part_id == table_part_id
                    )
                ).first()
                
                if existing and not overwrite_existing:
                    skipped_count += 1
                    continue
                
                # Migrate settings to current version
                migrated_json, _ = self.migrate_settings_if_needed(settings_json)
                
                if existing:
                    # Update existing
                    existing.settings_data = migrated_json
                else:
                    # Create new
                    new_settings = UserTablePartSettings(
                        user_id=user_id,
                        document_type=document_type,
                        table_part_id=table_part_id,
                        settings_data=migrated_json
                    )
                    self.db_session.add(new_settings)
                
                imported_count += 1
            
            self.db_session.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error importing user settings: {e}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': str(e),
                'imported_count': 0,
                'skipped_count': 0
            }
    
    def validate_settings_data(self, settings_data: str) -> Tuple[bool, List[str]]:
        """
        Validate settings data structure and content.
        
        Args:
            settings_data: JSON string of settings data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            settings = json.loads(settings_data)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        
        # Validate required top-level keys
        required_keys = ['panel_settings', 'shortcuts']
        for key in required_keys:
            if key not in settings:
                errors.append(f"Missing required key: {key}")
        
        # Validate panel_settings structure
        if 'panel_settings' in settings:
            panel_settings = settings['panel_settings']
            if not isinstance(panel_settings, dict):
                errors.append("panel_settings must be a dictionary")
            else:
                # Validate panel_settings fields
                if 'visible_commands' in panel_settings:
                    if not isinstance(panel_settings['visible_commands'], list):
                        errors.append("visible_commands must be a list")
                
                if 'button_size' in panel_settings:
                    valid_sizes = ['small', 'medium', 'large']
                    if panel_settings['button_size'] not in valid_sizes:
                        errors.append(f"button_size must be one of: {valid_sizes}")
        
        # Validate shortcuts structure
        if 'shortcuts' in settings:
            shortcuts = settings['shortcuts']
            if not isinstance(shortcuts, dict):
                errors.append("shortcuts must be a dictionary")
            else:
                if 'enabled' in shortcuts:
                    if not isinstance(shortcuts['enabled'], bool):
                        errors.append("shortcuts.enabled must be a boolean")
                
                if 'custom_mappings' in shortcuts:
                    if not isinstance(shortcuts['custom_mappings'], dict):
                        errors.append("shortcuts.custom_mappings must be a dictionary")
        
        return len(errors) == 0, errors
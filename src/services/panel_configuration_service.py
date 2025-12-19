"""
Panel Configuration Service for Table Parts.

This service handles persistence and retrieval of panel configurations,
applying settings to all table parts of the same document type, and
managing settings migration and defaults.

Requirements: 9.5
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.services.table_part_settings_service import TablePartSettingsService
from src.data.models.table_part_models import (
    TablePartCommand, PanelSettings, TablePartSettingsData, TablePartFactory
)
import logging

logger = logging.getLogger(__name__)


class PanelConfigurationService:
    """Service for managing panel configurations across table parts"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.settings_service = TablePartSettingsService(db_session)
    
    def save_panel_configuration(
        self,
        user_id: int,
        document_type: str,
        commands: List[TablePartCommand],
        panel_settings: PanelSettings,
        apply_to_all_table_parts: bool = True
    ) -> bool:
        """
        Save panel configuration for a document type.
        
        Args:
            user_id: User ID
            document_type: Type of document (e.g., 'estimate', 'daily_report')
            commands: List of configured commands
            panel_settings: Panel settings
            apply_to_all_table_parts: Whether to apply to all table parts of this document type
            
        Returns:
            True if successful, False otherwise
            
        Requirements: 9.5
        """
        try:
            if apply_to_all_table_parts:
                # Get all table part IDs for this document type
                table_part_ids = self._get_table_part_ids_for_document_type(document_type)
                
                # Apply configuration to all table parts
                for table_part_id in table_part_ids:
                    success = self._save_single_table_part_config(
                        user_id, document_type, table_part_id, commands, panel_settings
                    )
                    if not success:
                        logger.warning(f"Failed to save config for table part {table_part_id}")
            else:
                # Apply to a specific table part (would need table_part_id parameter)
                # For now, we'll apply to the main table part
                main_table_part_id = self._get_main_table_part_id(document_type)
                success = self._save_single_table_part_config(
                    user_id, document_type, main_table_part_id, commands, panel_settings
                )
                if not success:
                    return False
            
            logger.info(f"Saved panel configuration for user {user_id}, document type {document_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving panel configuration: {e}")
            return False
    
    def load_panel_configuration(
        self,
        user_id: int,
        document_type: str,
        table_part_id: Optional[str] = None
    ) -> tuple[List[TablePartCommand], PanelSettings]:
        """
        Load panel configuration for a document type and table part.
        
        Args:
            user_id: User ID
            document_type: Type of document
            table_part_id: ID of the table part (uses main if None)
            
        Returns:
            Tuple of (commands, panel_settings)
            
        Requirements: 9.5
        """
        try:
            if table_part_id is None:
                table_part_id = self._get_main_table_part_id(document_type)
            
            # Load user settings
            settings_data = self.settings_service.get_user_settings(
                user_id, document_type, table_part_id
            )
            
            if settings_data:
                # Load commands from command configuration
                commands = self.settings_service.get_command_configuration(
                    document_type, table_part_id, user_id
                )
                
                # If no commands found, use defaults
                if not commands:
                    commands = self._get_default_commands(document_type)
                
                return commands, settings_data.panel_settings
            else:
                # Return defaults
                default_commands = self._get_default_commands(document_type)
                default_settings = self._get_default_panel_settings(document_type)
                return default_commands, default_settings
                
        except Exception as e:
            logger.error(f"Error loading panel configuration: {e}")
            # Return defaults on error
            default_commands = self._get_default_commands(document_type)
            default_settings = self._get_default_panel_settings(document_type)
            return default_commands, default_settings
    
    def reset_panel_configuration(
        self,
        user_id: int,
        document_type: str,
        apply_to_all_table_parts: bool = True
    ) -> bool:
        """
        Reset panel configuration to defaults.
        
        Args:
            user_id: User ID
            document_type: Type of document
            apply_to_all_table_parts: Whether to reset all table parts of this document type
            
        Returns:
            True if successful, False otherwise
            
        Requirements: 9.5
        """
        try:
            if apply_to_all_table_parts:
                # Get all table part IDs for this document type
                table_part_ids = self._get_table_part_ids_for_document_type(document_type)
                
                # Reset all table parts
                for table_part_id in table_part_ids:
                    success = self.settings_service.reset_user_settings(
                        user_id, document_type, table_part_id
                    )
                    if not success:
                        logger.warning(f"Failed to reset config for table part {table_part_id}")
            else:
                # Reset specific table part
                main_table_part_id = self._get_main_table_part_id(document_type)
                success = self.settings_service.reset_user_settings(
                    user_id, document_type, main_table_part_id
                )
                if not success:
                    return False
            
            logger.info(f"Reset panel configuration for user {user_id}, document type {document_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting panel configuration: {e}")
            return False
    
    def migrate_panel_settings(
        self,
        user_id: int,
        from_version: str,
        to_version: str
    ) -> bool:
        """
        Migrate panel settings between versions.
        
        Args:
            user_id: User ID
            from_version: Source version
            to_version: Target version
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all user settings
            all_settings = self.settings_service.get_all_user_settings(user_id)
            
            for setting in all_settings:
                # Apply version-specific migrations
                migrated_settings = self._apply_version_migration(
                    setting['settings'], from_version, to_version
                )
                
                if migrated_settings != setting['settings']:
                    # Save migrated settings
                    settings_data = TablePartSettingsData.from_dict(migrated_settings)
                    self.settings_service.save_user_settings(
                        user_id,
                        setting['document_type'],
                        setting['table_part_id'],
                        settings_data
                    )
            
            logger.info(f"Migrated panel settings for user {user_id} from {from_version} to {to_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating panel settings: {e}")
            return False
    
    def _save_single_table_part_config(
        self,
        user_id: int,
        document_type: str,
        table_part_id: str,
        commands: List[TablePartCommand],
        panel_settings: PanelSettings
    ) -> bool:
        """Save configuration for a single table part"""
        try:
            # Create settings data
            settings_data = TablePartSettingsData(
                panel_settings=panel_settings
            )
            
            # Save user settings
            success = self.settings_service.save_user_settings(
                user_id, document_type, table_part_id, settings_data
            )
            
            if success:
                # Save command configuration
                success = self.settings_service.save_command_configuration(
                    document_type, table_part_id, commands, user_id
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving single table part config: {e}")
            return False
    
    def _get_table_part_ids_for_document_type(self, document_type: str) -> List[str]:
        """Get all table part IDs for a document type"""
        # Define table parts for each document type
        document_table_parts = {
            'estimate': ['lines', 'materials', 'equipment'],
            'daily_report': ['works', 'materials', 'equipment', 'personnel'],
            'timesheet': ['entries'],
            'work_composition': ['cost_items', 'materials'],
            'counterparty': ['contacts', 'addresses'],
            'object': ['estimates', 'reports']
        }
        
        return document_table_parts.get(document_type, ['main'])
    
    def _get_main_table_part_id(self, document_type: str) -> str:
        """Get the main table part ID for a document type"""
        main_table_parts = {
            'estimate': 'lines',
            'daily_report': 'works',
            'timesheet': 'entries',
            'work_composition': 'cost_items',
            'counterparty': 'contacts',
            'object': 'estimates'
        }
        
        return main_table_parts.get(document_type, 'main')
    
    def _get_default_commands(self, document_type: str) -> List[TablePartCommand]:
        """Get default commands for a document type"""
        return TablePartFactory.create_standard_commands()
    
    def _get_default_panel_settings(self, document_type: str) -> PanelSettings:
        """Get default panel settings for a document type"""
        default_commands = self._get_default_commands(document_type)
        default_visible = [cmd.id for cmd in default_commands[:4]]  # First 4 commands
        
        return PanelSettings(
            visible_commands=default_visible,
            button_size="medium",
            show_tooltips=True,
            compact_mode=False
        )
    
    def _apply_version_migration(
        self,
        settings: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Apply version-specific migrations to settings"""
        migrated_settings = settings.copy()
        
        # Example migrations (add as needed)
        if from_version == "1.0" and to_version == "1.1":
            # Add new compact_mode setting if missing
            if 'panel_settings' in migrated_settings:
                panel_settings = migrated_settings['panel_settings']
                if 'compact_mode' not in panel_settings:
                    panel_settings['compact_mode'] = False
        
        if from_version == "1.1" and to_version == "1.2":
            # Migrate button size values
            if 'panel_settings' in migrated_settings:
                panel_settings = migrated_settings['panel_settings']
                if 'button_size' in panel_settings:
                    # Convert old numeric values to new string values
                    size_map = {0: 'small', 1: 'medium', 2: 'large'}
                    if isinstance(panel_settings['button_size'], int):
                        panel_settings['button_size'] = size_map.get(
                            panel_settings['button_size'], 'medium'
                        )
        
        return migrated_settings
    
    def get_panel_configuration_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of all panel configurations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with configuration summary
        """
        try:
            all_settings = self.settings_service.get_all_user_settings(user_id)
            
            summary = {
                'total_configurations': len(all_settings),
                'document_types': {},
                'last_modified': None
            }
            
            for setting in all_settings:
                doc_type = setting['document_type']
                if doc_type not in summary['document_types']:
                    summary['document_types'][doc_type] = {
                        'table_parts': [],
                        'last_modified': setting['updated_at']
                    }
                
                summary['document_types'][doc_type]['table_parts'].append(
                    setting['table_part_id']
                )
                
                # Track latest modification
                if (summary['last_modified'] is None or 
                    setting['updated_at'] > summary['last_modified']):
                    summary['last_modified'] = setting['updated_at']
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting panel configuration summary: {e}")
            return {
                'total_configurations': 0,
                'document_types': {},
                'last_modified': None
            }
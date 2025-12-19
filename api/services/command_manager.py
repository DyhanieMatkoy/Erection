from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.data.models.ui_settings import FormCommandConfiguration
from api.services.command_registry import StandardCommandRegistry, CommandDefinition
import logging

logger = logging.getLogger(__name__)

class CommandManager:
    """
    Manages command configuration and availability for forms.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_available_commands(self, user_id: int, form_id: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get list of commands for a form, merged with user configuration.
        """
        # 1. Get all potential commands for this form (from registry)
        # In a real app, we might filter based on form_id (e.g. only document forms get 'post')
        registry_commands = StandardCommandRegistry.get_all()
        
        # 2. Get user configuration
        user_config = self.db.query(FormCommandConfiguration).filter_by(
            user_id=user_id,
            form_id=form_id
        ).all()
        
        config_map = {c.command_id: c for c in user_config}
        
        # 3. Merge
        result = []
        for cmd in registry_commands:
            conf = config_map.get(cmd.id)
            
            # Default visibility
            is_visible = True
            is_enabled = True
            position = 0 # Default position logic needed
            is_in_more_menu = False
            
            if conf:
                is_visible = conf.is_visible
                is_enabled = conf.is_enabled
                position = conf.position if conf.position is not None else 0
                is_in_more_menu = conf.is_in_more_menu
            
            # Apply Context Logic (Task 3.3 - Context-Sensitive Availability)
            # This is a simplified check. Real logic might be more complex.
            if context:
                selection_count = context.get('selection_count', 0)
                if cmd.requires_selection and selection_count == 0:
                    is_enabled = False
                if cmd.requires_single_selection and selection_count != 1:
                    is_enabled = False
            
            if is_visible:
                # model_dump() returns a dict, but we want to merge additional fields
                # StandardCommandRegistry.get_all() returns CommandDefinition objects (Pydantic models)
                cmd_dict = cmd.model_dump()
                cmd_dict['is_visible'] = is_visible # Add is_visible explicitly if not in model or just to be sure
                cmd_dict['is_enabled'] = is_enabled
                cmd_dict['position'] = position
                cmd_dict['is_in_more_menu'] = is_in_more_menu
                result.append(cmd_dict)
                
        # Sort by position
        result.sort(key=lambda x: x['position'])
        
        return result

    def save_command_configuration(self, user_id: int, form_id: str, configurations: List[Dict[str, Any]]):
        """
        Save user command configuration (visibility, order).
        configurations: List of dicts with command_id and optional overrides.
        """
        try:
            # Clear existing config for this form/user? 
            # Or upsert. Upsert is safer to preserve partial configs.
            # For simplicity in this iteration, we iterate and upsert.
            
            for index, config_data in enumerate(configurations):
                cmd_id = config_data['command_id']
                
                existing = self.db.query(FormCommandConfiguration).filter_by(
                    user_id=user_id,
                    form_id=form_id,
                    command_id=cmd_id
                ).first()
                
                if existing:
                    if 'is_visible' in config_data:
                        existing.is_visible = config_data['is_visible']
                    if 'is_in_more_menu' in config_data:
                        existing.is_in_more_menu = config_data['is_in_more_menu']
                    existing.position = index # Implicit ordering from list
                else:
                    new_config = FormCommandConfiguration(
                        user_id=user_id,
                        form_id=form_id,
                        command_id=cmd_id,
                        is_visible=config_data.get('is_visible', True),
                        is_enabled=True, # Enabled state is usually runtime, but maybe default enabled?
                        position=index,
                        is_in_more_menu=config_data.get('is_in_more_menu', False)
                    )
                    self.db.add(new_config)
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving command configuration: {e}")
            raise

    def reset_configuration(self, user_id: int, form_id: str):
        """Reset command configuration to defaults"""
        self.db.query(FormCommandConfiguration).filter_by(
            user_id=user_id,
            form_id=form_id
        ).delete()
        self.db.commit()

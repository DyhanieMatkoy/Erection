from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.data.models.ui_settings import UserFormSettings
import logging

logger = logging.getLogger(__name__)

class UserSettingsError(Exception):
    """Base exception for user settings operations"""
    pass

class UserSettingsManager:
    """
    Service for managing user UI settings (columns, filters, etc.)
    """
    def __init__(self, db: Session):
        self.db = db

    def _save_generic_settings(self, user_id: int, form_id: str, settings_type: str, data: Dict[str, Any]) -> UserFormSettings:
        """Helper to save settings of any type"""
        try:
            existing = self.db.query(UserFormSettings).filter_by(
                user_id=user_id,
                form_id=form_id,
                settings_type=settings_type
            ).first()

            if existing:
                existing.settings_data = data
                self.db.add(existing) # Ensure it's marked as modified
            else:
                existing = UserFormSettings(
                    user_id=user_id,
                    form_id=form_id,
                    settings_type=settings_type,
                    settings_data=data
                )
                self.db.add(existing)
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error saving settings: {e}")
            raise UserSettingsError(f"Failed to save settings: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error saving settings: {e}")
            raise UserSettingsError(f"Unexpected error: {str(e)}")

    def _load_generic_settings(self, user_id: int, form_id: str, settings_type: str) -> Optional[Dict[str, Any]]:
        """Helper to load settings of any type"""
        try:
            settings = self.db.query(UserFormSettings).filter_by(
                user_id=user_id,
                form_id=form_id,
                settings_type=settings_type
            ).first()
            
            if settings:
                return settings.settings_data
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error loading settings: {e}")
            # In case of read error, we might want to return None (fallback to default)
            # or raise. Requirement says "graceful fallback".
            return None 

    def save_column_settings(self, user_id: int, form_id: str, columns: Dict[str, Any]) -> UserFormSettings:
        """Save column visibility/ordering/width"""
        return self._save_generic_settings(user_id, form_id, 'columns', columns)

    def load_column_settings(self, user_id: int, form_id: str) -> Optional[Dict[str, Any]]:
        """Load column settings"""
        return self._load_generic_settings(user_id, form_id, 'columns')

    def save_filter_preferences(self, user_id: int, form_id: str, filters: Dict[str, Any]) -> UserFormSettings:
        """Save filter preferences"""
        return self._save_generic_settings(user_id, form_id, 'filters', filters)
    
    def load_filter_preferences(self, user_id: int, form_id: str) -> Optional[Dict[str, Any]]:
        return self._load_generic_settings(user_id, form_id, 'filters')

    def save_sorting_preferences(self, user_id: int, form_id: str, sorting: Dict[str, Any]) -> UserFormSettings:
        """Save sorting preferences"""
        return self._save_generic_settings(user_id, form_id, 'sorting', sorting)

    def load_sorting_preferences(self, user_id: int, form_id: str) -> Optional[Dict[str, Any]]:
        return self._load_generic_settings(user_id, form_id, 'sorting')

    def reset_to_defaults(self, user_id: int, form_id: str, settings_type: Optional[str] = None):
        """
        Reset settings to defaults (by deleting user overrides)
        """
        try:
            query = self.db.query(UserFormSettings).filter_by(
                user_id=user_id,
                form_id=form_id
            )
            if settings_type:
                query = query.filter_by(settings_type=settings_type)
            
            query.delete(synchronize_session=False)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error resetting settings: {e}")
            raise UserSettingsError(f"Failed to reset settings: {str(e)}")

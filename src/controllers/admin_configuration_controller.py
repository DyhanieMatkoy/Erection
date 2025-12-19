from typing import List, Dict, Any
from sqlalchemy.orm import Session
from api.services.permission_service import PermissionService
from src.data.database_manager import DatabaseManager

class AdminConfigurationController:
    """
    Controller for Admin Configuration (Task 11.3).
    Manages global/role-based form rules.
    """
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.permission_service = PermissionService(self.session)

    def get_column_rules(self, form_id: str, role: str) -> List[Dict]:
        """Get rules for UI display"""
        rules = self.permission_service.get_column_rules(form_id, role)
        return [
            {
                'column_id': r.column_id,
                'is_mandatory': r.is_mandatory,
                'is_restricted': r.is_restricted
            }
            for r in rules
        ]

    def save_rules(self, form_id: str, role: str, rules_data: List[Dict]):
        """
        Save rules from UI.
        rules_data: list of dicts with column_id, is_mandatory, is_restricted
        """
        try:
            for rule in rules_data:
                self.permission_service.save_column_rule(
                    form_id, 
                    rule['column_id'], 
                    role,
                    is_mandatory=rule.get('is_mandatory', False),
                    is_restricted=rule.get('is_restricted', False)
                )
        except Exception as e:
            self.session.rollback()
            raise e

    def close(self):
        self.session.close()

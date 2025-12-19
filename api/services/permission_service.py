from typing import List, Dict, Set
from sqlalchemy.orm import Session
from src.data.models.ui_settings import FormColumnRule, FormFormattingRule

class PermissionService:
    """
    Service for handling UI permissions and access control.
    Task 11.1
    """
    def __init__(self, session: Session):
        self.session = session

    def get_column_rules(self, form_id: str, role: str) -> List[FormColumnRule]:
        """Get all rules applicable to the form and role"""
        # Get rules for specific role AND 'all'
        rules = self.session.query(FormColumnRule).filter(
            FormColumnRule.form_id == form_id,
            FormColumnRule.role.in_([role, 'all'])
        ).all()
        return rules

    def get_formatting_rules(self, form_id: str) -> List[FormFormattingRule]:
        """Get active formatting rules for a form"""
        return self.session.query(FormFormattingRule).filter_by(
            form_id=form_id, is_active=True
        ).order_by(FormFormattingRule.priority.desc()).all()

    def filter_accessible_columns(self, columns: List[Dict], role: str, form_id: str) -> List[Dict]:
        """
        Filter columns based on access restrictions.
        Returns list of accessible columns with updated 'mandatory' status.
        """
        rules = self.get_column_rules(form_id, role)
        
        # Build map of restrictions and mandatory flags
        restricted_cols = set()
        mandatory_cols = set()
        
        for rule in rules:
            if rule.is_restricted:
                restricted_cols.add(rule.column_id)
            if rule.is_mandatory:
                mandatory_cols.add(rule.column_id)
        
        filtered_columns = []
        for col in columns:
            col_id = col['id']
            if col_id in restricted_cols:
                continue
                
            # Copy col to avoid mutating original definition
            new_col = col.copy()
            if col_id in mandatory_cols:
                new_col['mandatory'] = True
                new_col['visible'] = True # Mandatory implies visible
            
            filtered_columns.append(new_col)
            
        return filtered_columns

    def save_column_rule(self, form_id: str, column_id: str, role: str, 
                         is_mandatory: bool = False, is_restricted: bool = False):
        """Save or update a column rule (Admin only)"""
        # Check if exists
        rule = self.session.query(FormColumnRule).filter_by(
            form_id=form_id, column_id=column_id, role=role
        ).first()
        
        if rule:
            rule.is_mandatory = is_mandatory
            rule.is_restricted = is_restricted
        else:
            rule = FormColumnRule(
                form_id=form_id, 
                column_id=column_id, 
                role=role,
                is_mandatory=is_mandatory,
                is_restricted=is_restricted
            )
            self.session.add(rule)
        
        self.session.commit()

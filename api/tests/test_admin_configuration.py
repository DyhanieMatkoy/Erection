import pytest
from unittest.mock import MagicMock, patch
from src.controllers.admin_configuration_controller import AdminConfigurationController

class TestAdminConfiguration:
    """
    Task 11.3: Verify Admin Configuration Logic.
    Validates: Requirements 6.2, 6.3, 8.1
    """
    
    @pytest.fixture
    def controller(self):
        # Patch DatabaseManager to avoid real connection attempt
        with patch('src.controllers.admin_configuration_controller.DatabaseManager') as MockDBManager:
            mock_db_instance = MockDBManager.return_value
            mock_db_instance.get_session.return_value = MagicMock()
            
            # Also patch PermissionService to avoid its own DB usage
            with patch('src.controllers.admin_configuration_controller.PermissionService') as MockPermissionService:
                ctrl = AdminConfigurationController()
                # Ensure permission service is the mock
                ctrl.permission_service = MockPermissionService.return_value
                return ctrl

    def test_save_rules_flow(self, controller):
        """Test that rules are passed to permission service correctly"""
        form_id = "test_form"
        role = "manager"
        rules_data = [
            {'column_id': 'col1', 'is_mandatory': True, 'is_restricted': False},
            {'column_id': 'col2', 'is_mandatory': False, 'is_restricted': True}
        ]
        
        controller.save_rules(form_id, role, rules_data)
        
        # Verify calls
        assert controller.permission_service.save_column_rule.call_count == 2
        
        # Check first call
        call1 = controller.permission_service.save_column_rule.call_args_list[0]
        args, kwargs = call1
        assert args == (form_id, 'col1', role)
        assert kwargs == {'is_mandatory': True, 'is_restricted': False}

    def test_get_rules_flow(self, controller):
        """Test retrieval mapping"""
        # Mock service return
        mock_rule = MagicMock()
        mock_rule.column_id = 'col1'
        mock_rule.is_mandatory = True
        mock_rule.is_restricted = False
        
        controller.permission_service.get_column_rules.return_value = [mock_rule]
        
        result = controller.get_column_rules("form", "role")
        
        assert len(result) == 1
        assert result[0]['column_id'] == 'col1'
        assert result[0]['is_mandatory'] is True

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import MagicMock
from src.controllers.list_form_controller import ListFormController

class TestListFormController:
    
    @pytest.fixture
    def controller(self):
        # Mock dependencies
        mock_data_service = MagicMock()
        mock_settings_manager = MagicMock()
        mock_command_manager = MagicMock()
        mock_auth_service = MagicMock()
        mock_permission_service = MagicMock()
        mock_db = MagicMock()
        
        class TestController(ListFormController):
            def __init__(self):
                self.form_id = "test_form"
                self.user_id = 1
                self.model_class = MagicMock()
                self.data_service = mock_data_service
                self.settings_manager = mock_settings_manager
                self.command_manager = mock_command_manager
                self.auth_service = mock_auth_service
                self.permission_service = mock_permission_service
                self.session = MagicMock()
                self.current_page = 1
                self.page_size = 50
                self.filters = {}
                self.sort_by = None
                self.sort_order = "asc"
                self.column_settings = None
                self.data_callback = None
                self.error_callback = None
                self.selection = set()
                self.user_role = None

        return TestController()

    def test_filter_columns_delegation(self, controller):
        """Test that filter_columns delegates to permission service"""
        columns = [{'id': 'c1'}, {'id': 'c2'}]
        controller.auth_service.get_user_by_id.return_value = {'role': 'manager'}
        
        controller.filter_columns(columns)
        
        # Should load role first
        controller.auth_service.get_user_by_id.assert_called_with(1, controller.session)
        assert controller.user_role == 'manager'
        
        # Then call permission service
        controller.permission_service.filter_accessible_columns.assert_called_with(
            columns, 'manager', "test_form"
        )

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.lists(st.integers(), unique=True))
    def test_multi_selection_behavior(self, controller, selection):
        """
        Property 6: Multi-Selection Behavior Consistency
        Selection should be accurately tracked and retrievable.
        """
        controller.update_selection(selection)
        
        current = controller.get_selection()
        assert len(current) == len(selection)
        assert set(current) == set(selection)
        
        # Test updating with subset
        if selection:
            subset = selection[:len(selection)//2]
            controller.update_selection(subset)
            assert set(controller.get_selection()) == set(subset)

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        total_width=st.integers(min_value=100, max_value=2000),
        col_count=st.integers(min_value=1, max_value=10)
    )
    def test_responsive_column_adaptation(self, controller, total_width, col_count):
        """
        Property 3: Responsive Column Width Adaptation
        Columns should fit within total width (if possible) or respect defaults.
        """
        columns = [{'id': f'col_{i}', 'min_width': 50, 'default_width': 100} for i in range(col_count)]
        
        # No saved settings
        controller.column_settings = {}
        
        widths = controller.calculate_column_widths(total_width, columns)
        
        assert len(widths) == col_count
        
        # Check if we filled the width (if we had enough cols)
        # Logic in controller: if undefined_cols (all of them), distribute remaining.
        # remaining = total - 0 = total.
        # width_per_col = total // count.
        # So sum of widths should be close to total_width, unless total < min_width * count
        
        calculated_total = sum(widths.values())
        
        if total_width >= col_count * 50:
            # We expect to use approximately total_width
            # (due to integer division, might be slightly less)
            assert calculated_total <= total_width
            assert calculated_total >= total_width - col_count # rounding errors
        else:
            # If not enough space, we respect min_width (50)
            # Actually implementation says: max(width_per_col, min_width)
            # If width_per_col < min_width, we use min_width.
            # So total will be > total_width.
            assert calculated_total >= col_count * 50

    def test_data_refresh_preserves_state(self, controller):
        """
        Property 4: Data Refresh Position Preservation (Partial)
        Controller should preserve sort/filter state during refresh.
        """
        controller.set_filter("test", "value")
        controller.handle_sorting("col1")
        
        # Trigger reload (mock data service)
        controller.load_data()
        
        # Verify data service called with correct params
        controller.data_service.get_documents.assert_called_with(
            model_class=controller.model_class,
            page=1, # Filter reset page
            page_size=50,
            filters={'test': 'value'},
            sort_by='col1',
            sort_order='asc'
        )

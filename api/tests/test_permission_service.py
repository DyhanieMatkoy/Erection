import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import MagicMock
from api.services.permission_service import PermissionService
from src.data.models.ui_settings import FormColumnRule

class TestPermissionService:
    
    @pytest.fixture
    def service(self):
        session = MagicMock()
        return PermissionService(session)

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        columns=st.lists(st.fixed_dictionaries({
            'id': st.text(min_size=1), 
            'name': st.text()
        }), unique_by=lambda x: x['id']),
        restricted_ids=st.lists(st.text()),
        mandatory_ids=st.lists(st.text())
    )
    def test_access_control_filtering(self, service, columns, restricted_ids, mandatory_ids):
        """
        Task 11.2: Property test for access control column visibility.
        Validates: Requirements 6.4 (Access restrictions) and 6.2 (Mandatory columns).
        """
        # Mock database return
        form_id = "test_form"
        role = "user"
        
        # Prepare mock rules
        rules = []
        # Filter IDs to only those present in columns for realistic scenario (though service handles unknown IDs gracefully)
        col_ids = [c['id'] for c in columns]
        
        real_restricted = [rid for rid in restricted_ids if rid in col_ids]
        real_mandatory = [mid for mid in mandatory_ids if mid in col_ids and mid not in real_restricted]
        
        for rid in real_restricted:
            rules.append(MagicMock(column_id=rid, is_restricted=True, is_mandatory=False))
            
        for mid in real_mandatory:
            rules.append(MagicMock(column_id=mid, is_restricted=False, is_mandatory=True))
            
        service.get_column_rules = MagicMock(return_value=rules)
        
        # Execute
        result = service.filter_accessible_columns(columns, role, form_id)
        
        result_ids = [c['id'] for c in result]
        
        # Assertions
        # 1. Restricted columns should NOT be in result
        for rid in real_restricted:
            assert rid not in result_ids
            
        # 2. Mandatory columns SHOULD be in result and marked mandatory
        for mid in real_mandatory:
            assert mid in result_ids
            col = next(c for c in result if c['id'] == mid)
            assert col.get('mandatory') is True
            assert col.get('visible') is True

        # 3. Columns neither restricted nor mandatory should be present (unchanged)
        for col in columns:
            if col['id'] not in real_restricted:
                assert col['id'] in result_ids

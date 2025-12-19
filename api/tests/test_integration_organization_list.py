import pytest
from datetime import date
import uuid
from PyQt6.QtWidgets import QApplication
from src.views.organization_list_form_v2 import OrganizationListFormV2
from src.data.models.sqlalchemy_models import User, Organization
from src.controllers.list_form_controller import ListFormController
from api.services.data_service import DataService
from src.data.database_manager import DatabaseManager

# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

class TestIntegrationOrganizationList:
    
    def test_organization_list_integration(self, setup_database, qapp):
        """
        Test that OrganizationListFormV2 loads data correctly and handles hierarchy.
        """
        db_manager = setup_database
        
        with db_manager.session_scope() as db_session:
            # 1. Setup Data
            user = User(username="admin_org", password_hash="hash", role="admin", is_active=True)
            db_session.add(user)
            db_session.flush()
            
            # Root items
            root_org = Organization(name="Root Org", is_group=False)
            root_group = Organization(name="Root Group", is_group=True)
            db_session.add_all([root_org, root_group])
            db_session.flush()
            
            # Child item
            child_org = Organization(name="Child Org", parent_id=root_group.id, is_group=False)
            db_session.add(child_org)
            
            db_session.commit()
            
            user_id = user.id
            root_group_id = root_group.id
            
        # 2. Initialize Form
        form = OrganizationListFormV2(user_id=user_id)
        
        # 3. Verify Initial Data (Root level)
        # Should see Root Org and Root Group, but NOT Child Org
        assert form.table.rowCount() == 2
        
        found_root = False
        found_group = False
        found_child = False
        
        for i in range(form.table.rowCount()):
            # Column 0 is Name
            name_item = form.table.item(i, 0)
            if name_item.text() == "Root Org":
                found_root = True
            elif name_item.text() == "Root Group":
                found_group = True
            elif name_item.text() == "Child Org":
                found_child = True
                
        assert found_root, "Root Org not found"
        assert found_group, "Root Group not found"
        assert not found_child, "Child Org should not be visible at root"
        
        # 4. Test Drill Down
        form.enter_group(root_group_id, "Root Group")
        
        # Should now see only Child Org
        assert form.table.rowCount() == 1
        child_item = form.table.item(0, 0)
        assert child_item.text() == "Child Org"
        
        # 5. Test Go Up
        form.go_up()
        
        # Should be back to root
        assert form.table.rowCount() == 2
        
        form.close()

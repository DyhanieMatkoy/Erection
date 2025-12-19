import pytest
from datetime import date
import uuid
from PyQt6.QtWidgets import QApplication
from src.views.object_list_form_v2 import ObjectListFormV2
from src.data.models.sqlalchemy_models import User, Object, Counterparty
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

class TestIntegrationObjectList:
    
    def test_object_list_integration(self, setup_database, qapp):
        """
        Test that ObjectListFormV2 loads data correctly and handles hierarchy.
        """
        db_manager = setup_database
        
        with db_manager.session_scope() as db_session:
            # 1. Setup Data
            user = User(username="admin_obj", password_hash="hash", role="admin", is_active=True)
            db_session.add(user)
            db_session.flush()
            
            customer = Counterparty(name="Test Customer")
            db_session.add(customer)
            db_session.flush()
            
            # Root items
            root_obj = Object(name="Root Object", owner_id=customer.id, is_group=False)
            root_group = Object(name="Root Group", is_group=True)
            db_session.add_all([root_obj, root_group])
            db_session.flush()
            
            # Child item
            child_obj = Object(name="Child Object", parent_id=root_group.id, is_group=False)
            db_session.add(child_obj)
            
            db_session.commit()
            
            user_id = user.id
            root_group_id = root_group.id
            
        # 2. Initialize Form
        form = ObjectListFormV2(user_id=user_id)
        
        # 3. Verify Initial Data (Root level)
        # Should see Root Object and Root Group, but NOT Child Object
        assert form.table.rowCount() == 2
        
        found_root = False
        found_group = False
        found_child = False
        
        for i in range(form.table.rowCount()):
            # Column 0 is Name (based on V2 config: name, owner.name, address, is_group, parent_id)
            name_item = form.table.item(i, 0)
            if name_item.text() == "Root Object":
                found_root = True
            elif name_item.text() == "Root Group":
                found_group = True
            elif name_item.text() == "Child Object":
                found_child = True
                
        assert found_root, "Root Object not found"
        assert found_group, "Root Group not found"
        assert not found_child, "Child Object should not be visible at root"
        
        # 4. Test Drill Down
        form.enter_group(root_group_id, "Root Group")
        
        # Should now see only Child Object
        # Note: load_data is sync in current implementation, so table should update immediately
        assert form.table.rowCount() == 1
        child_item = form.table.item(0, 0)
        assert child_item.text() == "Child Object"
        
        # 5. Test Go Up
        form.go_up()
        
        # Should be back to root
        assert form.table.rowCount() == 2
        
        form.close()

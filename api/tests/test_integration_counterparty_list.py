import pytest
from datetime import date
import uuid
from PyQt6.QtWidgets import QApplication
from src.views.counterparty_list_form_v2 import CounterpartyListFormV2
from src.data.models.sqlalchemy_models import User, Counterparty
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

class TestIntegrationCounterpartyList:
    
    def test_counterparty_list_integration(self, setup_database, qapp):
        """
        Test that CounterpartyListFormV2 loads data correctly and handles hierarchy.
        """
        db_manager = setup_database
        
        with db_manager.session_scope() as db_session:
            # 1. Setup Data
            user = User(username="admin_cp", password_hash="hash", role="admin", is_active=True)
            db_session.add(user)
            db_session.flush()
            
            # Root items
            root_cp = Counterparty(name="Root Customer", is_group=False)
            root_group = Counterparty(name="Root Group", is_group=True)
            db_session.add_all([root_cp, root_group])
            db_session.flush()
            
            # Child item
            child_cp = Counterparty(name="Child Customer", parent_id=root_group.id, is_group=False)
            db_session.add(child_cp)
            
            db_session.commit()
            
            user_id = user.id
            root_group_id = root_group.id
            
        # 2. Initialize Form
        form = CounterpartyListFormV2(user_id=user_id)
        
        # 3. Verify Initial Data (Root level)
        # Should see Root Customer and Root Group, but NOT Child Customer
        assert form.table.rowCount() == 2
        
        found_root = False
        found_group = False
        found_child = False
        
        for i in range(form.table.rowCount()):
            # Column 0 is Name
            name_item = form.table.item(i, 0)
            if name_item.text() == "Root Customer":
                found_root = True
            elif name_item.text() == "Root Group":
                found_group = True
            elif name_item.text() == "Child Customer":
                found_child = True
                
        assert found_root, "Root Customer not found"
        assert found_group, "Root Group not found"
        assert not found_child, "Child Customer should not be visible at root"
        
        # 4. Test Drill Down
        form.enter_group(root_group_id, "Root Group")
        
        # Should now see only Child Customer
        assert form.table.rowCount() == 1
        child_item = form.table.item(0, 0)
        assert child_item.text() == "Child Customer"
        
        # 5. Test Go Up
        form.go_up()
        
        # Should be back to root
        assert form.table.rowCount() == 2
        
        form.close()

import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Base, Person
from src.views.person_list_form_v2 import PersonListFormV2
import sys

# Initialize QApplication for widgets
app = QApplication.instance() or QApplication(sys.argv)

@pytest.fixture
def session():
    """Creates a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_person_list_integration(session):
    """
    Test the full flow of PersonListFormV2:
    1. Setup DB with root persons, groups, and child persons.
    2. Initialize the view and controller.
    3. Verify root level filtering.
    4. Verify drill-down into a group.
    5. Verify navigation back up.
    """
    # 1. Setup Data
    # Root person
    root_person = Person(full_name="Root Person", is_group=False, parent_id=None)
    session.add(root_person)
    
    # Root Group
    root_group = Person(full_name="Root Group", is_group=True, parent_id=None)
    session.add(root_group)
    session.flush() # Get ID for root_group

    # Child Person (inside Root Group)
    child_person = Person(full_name="Child Person", is_group=False, parent_id=root_group.id)
    session.add(child_person)
    
    session.commit()

    # 2. Initialize View and Controller with Mocks
    # We patch DatabaseManager in the controller module to return our test session
    with patch('src.controllers.list_form_controller.DatabaseManager') as MockDBManager:
        # Configure the mock to return our session
        mock_db_instance = MockDBManager.return_value
        mock_db_instance.get_session.return_value = session
        
        # We also need to mock UserSettingsManager, CommandManager etc. if they use the session and break
        # But since they take the session from controller (which gets it from db_manager), it should be fine.
        # However, UserSettingsManager might try to query tables that exist (Base.metadata.create_all created them).
        
        view = PersonListFormV2(user_id=1)
        
        # Refresh to load data
        # view.load_data() is called in __init__, but let's call it again to be sure
        view.load_data()

        # 3. Verify Root Level (Should see Root Person and Root Group, but NOT Child Person)
        # The model rows might be in any order, so we check count and content
        model = view.table.model()
        assert model.rowCount() == 2, f"Expected 2 root items, found {model.rowCount()}"
        
        root_names = [model.index(r, 0).data() for r in range(model.rowCount())]
        assert "Root Person" in root_names
        assert "Root Group" in root_names
        assert "Child Person" not in root_names

        # 4. Verify Drill-down
        # Simulate entering the group via method
        view.enter_group(root_group.id, "Root Group")
        # Refresh is triggered by set_filter inside enter_group? 
        # generic_list_form.set_filter calls load_data.
        # But let's check PersonListFormV2.enter_group implementation.
        
        # Verify Child Level
        model = view.table.model()
        assert model.rowCount() == 1
        child_names = [model.index(r, 0).data() for r in range(model.rowCount())]
        assert "Child Person" in child_names

        # 5. Verify Navigate Up
        # Simulate clicking "Up" button logic
        view.go_up()
        
        # Verify we are back at root
        assert view.current_parent_id is None
        assert model.rowCount() == 2
        root_names_again = [model.index(r, 0).data() for r in range(model.rowCount())]
        assert "Root Person" in root_names_again

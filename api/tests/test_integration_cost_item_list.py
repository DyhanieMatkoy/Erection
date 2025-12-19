import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Base, CostItem
from src.views.cost_item_list_form_v2 import CostItemListFormV2
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

def test_cost_item_list_integration(session):
    """
    Test the CostItemListFormV2 (Hierarchical):
    1. Setup DB with root items, groups, and child items.
    2. Initialize view.
    3. Verify root level filtering.
    4. Verify drill-down.
    5. Verify navigation up.
    """
    # 1. Setup Data
    # Root Item
    root_item = CostItem(code="C001", description="Root Item", is_folder=False, parent_id=None)
    session.add(root_item)
    
    # Root Group
    root_group = CostItem(code="G001", description="Root Group", is_folder=True, parent_id=None)
    session.add(root_group)
    session.flush()

    # Child Item
    child_item = CostItem(code="C002", description="Child Item", is_folder=False, parent_id=root_group.id)
    session.add(child_item)
    
    session.commit()

    # 2. Initialize View and Controller with Mocks
    with patch('src.controllers.list_form_controller.DatabaseManager') as MockDBManager:
        mock_db_instance = MockDBManager.return_value
        mock_db_instance.get_session.return_value = session
        
        view = CostItemListFormV2(user_id=1)
        view.load_data()

        # 3. Verify Root Level
        model = view.table.model()
        assert model.rowCount() == 2
        descriptions = [model.index(r, 1).data() for r in range(model.rowCount())]
        assert "Root Item" in descriptions
        assert "Root Group" in descriptions
        assert "Child Item" not in descriptions

        # 4. Verify Drill-down
        view.enter_group(root_group.id, "Root Group")
        
        model = view.table.model()
        assert model.rowCount() == 1
        descriptions = [model.index(r, 1).data() for r in range(model.rowCount())]
        assert "Child Item" in descriptions

        # 5. Verify Navigate Up
        view.go_up()
        
        model = view.table.model()
        assert model.rowCount() == 2
        descriptions = [model.index(r, 1).data() for r in range(model.rowCount())]
        assert "Root Item" in descriptions

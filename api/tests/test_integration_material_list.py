import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Base, Material
from src.views.material_list_form_v2 import MaterialListFormV2
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

def test_material_list_integration(session):
    """
    Test the MaterialListFormV2 (Flat list):
    1. Setup DB with materials.
    2. Initialize view.
    3. Verify data loading.
    """
    # 1. Setup Data
    m1 = Material(code="M001", description="Material 1", price=100.0)
    session.add(m1)
    
    m2 = Material(code="M002", description="Material 2", price=200.0)
    session.add(m2)
    
    session.commit()

    # 2. Initialize View and Controller with Mocks
    with patch('src.controllers.list_form_controller.DatabaseManager') as MockDBManager:
        mock_db_instance = MockDBManager.return_value
        mock_db_instance.get_session.return_value = session
        
        view = MaterialListFormV2(user_id=1)
        
        # Refresh to load data
        view.load_data()

        # 3. Verify Data
        model = view.table.model()
        assert model.rowCount() == 2
        
        # Check content
        # We don't know the order, so collect descriptions
        # Column 1 is description (based on configuration)
        descriptions = [model.index(r, 1).data() for r in range(model.rowCount())]
        assert "Material 1" in descriptions
        assert "Material 2" in descriptions

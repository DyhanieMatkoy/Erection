import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Base, Timesheet, Object, Person, User
from src.views.timesheet_list_form_v2 import TimesheetListFormV2
import datetime
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

def test_timesheet_list_integration(session):
    """
    Test the TimesheetListFormV2:
    1. Setup DB with timesheet, object, foreman.
    2. Initialize view.
    3. Verify data loading and filtering.
    """
    # 1. Setup Data
    user = User(id=1, username="test", password_hash="hash", role="Администратор")
    session.add(user)

    obj = Object(name="Obj 1")
    session.add(obj)
    session.flush()
    
    foreman = Person(full_name="Petrov", is_group=False)
    session.add(foreman)
    session.flush()

    timesheet = Timesheet(
        date=datetime.date(2023, 2, 1),
        month_year="02.2023",
        number="T-001",
        object_id=obj.id,
        foreman_id=foreman.id,
        is_posted=True
    )
    session.add(timesheet)
    
    session.commit()

    # 2. Initialize View with Mocks
    with patch('src.controllers.list_form_controller.DatabaseManager') as MockDBManager:
        mock_db_instance = MockDBManager.return_value
        mock_db_instance.get_session.return_value = session
        
        with patch('src.views.timesheet_list_form_v2.TimesheetPostingService'):
            view = TimesheetListFormV2(user_id=1)
            view.load_data()
            
            # 3. Verify Data
            model = view.table.model()
            assert model.rowCount() == 1
            
            item = view.table.data_map[0]
            assert item.object.name == "Obj 1"
            assert item.foreman.full_name == "Petrov"
            assert item.is_posted == True
            
            # Test Filter Options
            objects = view.controller.get_object_filter_options()
            assert len(objects) == 1
            assert objects[0]['name'] == "Obj 1"

            foremen = view.controller.get_foreman_filter_options()
            assert len(foremen) == 1
            assert foremen[0]['name'] == "Petrov"

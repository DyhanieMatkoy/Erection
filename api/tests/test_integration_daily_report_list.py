import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.sqlalchemy_models import Base, DailyReport, Estimate, Person, User
from src.views.daily_report_list_form_v2 import DailyReportListFormV2
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

def test_daily_report_list_integration(session):
    """
    Test the DailyReportListFormV2:
    1. Setup DB with report, estimate, foreman.
    2. Initialize view.
    3. Verify data loading and filtering.
    """
    # 1. Setup Data
    user = User(id=1, username="test", password_hash="hash", role="Администратор")
    session.add(user)

    est = Estimate(number="E-001", date=datetime.date(2023, 1, 1))
    session.add(est)
    session.flush()
    
    foreman = Person(full_name="Ivanov", is_group=False)
    session.add(foreman)
    session.flush()

    report = DailyReport(
        date=datetime.date(2023, 1, 2),
        estimate_id=est.id,
        foreman_id=foreman.id,
        is_posted=True
    )
    session.add(report)
    
    session.commit()

    # 2. Initialize View with Mocks
    with patch('src.controllers.list_form_controller.DatabaseManager') as MockDBManager:
        mock_db_instance = MockDBManager.return_value
        mock_db_instance.get_session.return_value = session
        
        # Also need to mock DocumentPostingService to avoid DB connection there if it creates one
        with patch('src.views.daily_report_list_form_v2.DocumentPostingService'):
            view = DailyReportListFormV2(user_id=1)
            view.load_data()
            
            # 3. Verify Data
            model = view.table.model()
            assert model.rowCount() == 1
            
            # Check columns (approximate indices)
            # Note: DocumentListTable stores data objects in data_map
            item = view.table.data_map[0]
            assert item.estimate.number == "E-001"
            assert item.foreman.full_name == "Ivanov"
            assert item.is_posted == True
            
            # Test Filter Options loading
            estimates = view.controller.get_estimate_filter_options()
            assert len(estimates) == 1
            assert estimates[0]['name'] == "E-001 от 2023-01-01"

            foremen = view.controller.get_foreman_filter_options()
            assert len(foremen) == 1
            assert foremen[0]['name'] == "Ivanov"

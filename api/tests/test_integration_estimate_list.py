import pytest
import sys
import os
from datetime import date
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.views.estimate_list_form_v2 import EstimateListFormV2
from src.data.models.sqlalchemy_models import User, Person, Counterparty, Object, Estimate, EstimateType
from src.data.database_manager import DatabaseManager

# Mock QApplication
try:
    from PyQt6.QtWidgets import QApplication
    if not QApplication.instance():
        qapp = QApplication([])
    else:
        qapp = QApplication.instance()
except ImportError:
    qapp = None

@pytest.mark.skipif(qapp is None, reason="PyQt6 not available")
class TestIntegrationEstimateList:
    
    def test_estimate_list_integration(self, setup_database):
        """
        Test that EstimateListFormV2 loads data correctly from the database
        using ListFormController and DataService.
        """
        db_manager = setup_database
        
        with db_manager.session_scope() as db_session:
            # 1. Setup Data
            # Create user
            user = db_session.query(User).filter_by(username="admin").first()
            if not user:
                user = User(username="admin", password_hash="hash", role="admin", is_active=True)
                db_session.add(user)
                db_session.flush()
                
            # Create references
            customer = Counterparty(name="Test Customer")
            obj = Object(name="Test Object")
            person = Person(full_name="Test Person", user_id=user.id)
            
            db_session.add_all([customer, obj, person])
            db_session.flush()
            
            # Create estimates
            est1 = Estimate(
                number="EST-001",
                date=date.today(),
                customer_id=customer.id,
                object_id=obj.id,
                responsible_id=person.id,
                estimate_type=EstimateType.GENERAL.value,
                total_sum=1000.0,
                is_posted=True
            )
            
            est2 = Estimate(
                number="EST-002",
                date=date.today(),
                customer_id=customer.id,
                object_id=obj.id,
                responsible_id=person.id,
                estimate_type=EstimateType.PLAN.value,
                total_sum=500.0,
                is_posted=False
            )
            
            db_session.add_all([est1, est2])
            db_session.commit()
            
            user_id = user.id
            est1_id = est1.id
        
        # 2. Initialize Form
        # We need to ensure ListFormController uses the SAME session or same DB.
        # ListFormController creates a new session via DatabaseManager().get_session().
        # Since setup_database initializes DatabaseManager with a temp path, 
        # new sessions should connect to the same temp DB.
        
        form = EstimateListFormV2(user_id=user_id)
        
        # 3. Verify Data Load
        # Wait for data load? load_data() is synchronous in this implementation.
        
        # Check table row count
        assert form.table.rowCount() >= 2 # Might have other tests data
        
        # Check content
        found_001 = False
        found_002 = False
        
        for i in range(form.table.rowCount()):
            number_item = form.table.item(i, 1) # Column 1 is Number
            if number_item.text() == "EST-001":
                found_001 = True
                
                # Check customer name (nested property)
                customer_item = form.table.item(i, 3)
                assert customer_item.text() == "Test Customer"
                
            elif number_item.text() == "EST-002":
                found_002 = True
                
        assert found_001
        assert found_002
        
        # 4. Test Filtering
        # Filter by Posted
        form.on_filter("is_posted", True)
        
        # Verify filtered
        has_unposted = False
        for i in range(form.table.rowCount()):
            number_item = form.table.item(i, 1)
            if number_item.text() == "EST-002":
                has_unposted = True
                break
        assert not has_unposted
        
        # 5. Test Command (Delete)
        # Reset filters to find EST-001
        form.on_filter("is_posted", None) # Clear filter
        
        # Find row for EST-001
        row_to_delete = -1
        for i in range(form.table.rowCount()):
            if form.table.item(i, 1).text() == "EST-001":
                row_to_delete = i
                break
                
        assert row_to_delete >= 0
        
        # Select the row
        form.table.selectRow(row_to_delete)
        # Manually trigger selection change signal as UI interaction is mocked
        form.table.on_selection_changed()
        
        # Trigger delete command
        form.on_command('delete')
        
        # Verify deletion in DB
        with db_manager.session_scope() as session:
            est1_db = session.query(Estimate).filter_by(id=est1_id).first()
            # Soft delete check
            assert est1_db.marked_for_deletion is True

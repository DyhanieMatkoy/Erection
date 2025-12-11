"""Integration test for EstimateService with migrated EstimateRepository

This test verifies that the EstimateService works correctly with the
SQLAlchemy-migrated EstimateRepository.
"""
import os
import sys
import tempfile
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.services.estimate_service import EstimateService
from src.data.models.estimate import Estimate, EstimateLine


def test_estimate_service_integration():
    """Test EstimateService with SQLAlchemy-migrated repository"""
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize(db_path)
        
        # Create reference data
        print("Setting up reference data...")
        from src.data.models.sqlalchemy_models import Person, Counterparty, Object, Organization, Work
        
        with db_manager.session_scope() as session:
            person = Person(id=1, full_name="Test Person", position="Manager")
            counterparty = Counterparty(id=1, name="Test Customer")
            obj = Object(id=1, name="Test Object", owner_id=1)
            org = Organization(id=1, name="Test Contractor")
            work1 = Work(id=1, name="Work 1", unit="м²", price=500.0, labor_rate=5.0)
            
            session.add(person)
            session.add(counterparty)
            session.add(obj)
            session.add(org)
            session.add(work1)
        
        print("✓ Reference data created")
        
        # Create service
        service = EstimateService()
        
        # Test 1: Create new estimate through service
        print("\nTest 1: Creating estimate through service...")
        estimate = service.create()
        estimate.number = "SVC-001"
        estimate.date = date(2024, 1, 15)
        estimate.customer_id = 1
        estimate.object_id = 1
        estimate.contractor_id = 1
        estimate.responsible_id = 1
        estimate.total_sum = 5000.0
        estimate.total_labor = 50.0
        
        estimate.lines = [
            EstimateLine(
                line_number=1,
                work_id=1,
                quantity=10.0,
                unit="м²",
                price=500.0,
                labor_rate=5.0,
                sum=5000.0,
                planned_labor=50.0
            )
        ]
        
        result = service.save(estimate)
        assert result is True, "Failed to save estimate through service"
        assert estimate.id > 0, "Estimate ID should be set"
        print(f"✓ Created estimate with ID: {estimate.id}")
        
        # Test 2: Load estimate through service
        print("\nTest 2: Loading estimate through service...")
        loaded = service.load(estimate.id)
        assert loaded is not None, "Failed to load estimate"
        assert loaded.number == "SVC-001", "Estimate number should match"
        assert len(loaded.lines) == 1, "Should have 1 line"
        print(f"✓ Loaded estimate: {loaded.number}")
        
        # Test 3: Update estimate through service
        print("\nTest 3: Updating estimate through service...")
        loaded.number = "SVC-001-UPDATED"
        loaded.lines.append(
            EstimateLine(
                line_number=2,
                work_id=1,
                quantity=5.0,
                unit="м²",
                price=500.0,
                labor_rate=5.0,
                sum=2500.0,
                planned_labor=25.0
            )
        )
        loaded.total_sum = 7500.0
        loaded.total_labor = 75.0
        
        result = service.save(loaded)
        assert result is True, "Failed to update estimate"
        
        # Verify update
        updated = service.load(estimate.id)
        assert updated.number == "SVC-001-UPDATED", "Number should be updated"
        assert len(updated.lines) == 2, "Should have 2 lines"
        print(f"✓ Updated estimate: {updated.number}, {len(updated.lines)} lines")
        
        print("\n" + "="*50)
        print("Integration test passed! ✓")
        print("="*50)
        
    finally:
        # Clean up
        try:
            if db_manager._engine:
                db_manager._engine.dispose()
            if db_manager._connection:
                db_manager._connection.close()
        except:
            pass
        
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except PermissionError:
            print(f"Warning: Could not delete temporary database file: {db_path}")


if __name__ == "__main__":
    test_estimate_service_integration()

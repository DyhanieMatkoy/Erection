"""Test cascade operations for EstimateLine

This test verifies that EstimateLine cascade operations work correctly
with the SQLAlchemy migration, specifically testing the cascade delete
behavior defined in the relationship.
"""
import os
import sys
import tempfile
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.repositories.estimate_repository import EstimateRepository
from src.data.models.estimate import Estimate, EstimateLine
from src.data.models.sqlalchemy_models import Estimate as EstimateModel, EstimateLine as EstimateLineModel


def test_cascade_delete():
    """Test that deleting an estimate cascades to delete its lines"""
    
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
            person = Person(id=1, full_name="Test Person")
            counterparty = Counterparty(id=1, name="Test Customer")
            obj = Object(id=1, name="Test Object", owner_id=1)
            org = Organization(id=1, name="Test Contractor")
            work1 = Work(id=1, name="Work 1", unit="м²")
            
            session.add_all([person, counterparty, obj, org, work1])
        
        print("✓ Reference data created")
        
        # Create repository
        repo = EstimateRepository()
        
        # Test 1: Create estimate with lines
        print("\nTest 1: Creating estimate with lines...")
        estimate = Estimate(
            number="CASCADE-001",
            date=date(2024, 1, 15),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=10000.0,
            total_labor=100.0
        )
        
        estimate.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=10.0, sum=5000.0),
            EstimateLine(line_number=2, work_id=1, quantity=10.0, sum=5000.0)
        ]
        
        result = repo.save(estimate)
        assert result is True, "Failed to save estimate"
        estimate_id = estimate.id
        print(f"✓ Created estimate with ID: {estimate_id}")
        
        # Verify lines exist
        with db_manager.session_scope() as session:
            line_count = session.query(EstimateLineModel)\
                .filter(EstimateLineModel.estimate_id == estimate_id)\
                .count()
            assert line_count == 2, f"Expected 2 lines, found {line_count}"
            print(f"✓ Verified 2 lines exist in database")
        
        # Test 2: Delete estimate and verify cascade
        print("\nTest 2: Testing cascade delete...")
        with db_manager.session_scope() as session:
            estimate_model = session.query(EstimateModel)\
                .filter(EstimateModel.id == estimate_id)\
                .first()
            
            assert estimate_model is not None, "Estimate should exist"
            session.delete(estimate_model)
        
        # Verify estimate is deleted
        with db_manager.session_scope() as session:
            estimate_model = session.query(EstimateModel)\
                .filter(EstimateModel.id == estimate_id)\
                .first()
            assert estimate_model is None, "Estimate should be deleted"
            print(f"✓ Estimate deleted")
            
            # Verify lines are also deleted (cascade)
            line_count = session.query(EstimateLineModel)\
                .filter(EstimateLineModel.estimate_id == estimate_id)\
                .count()
            assert line_count == 0, f"Lines should be cascade deleted, but found {line_count}"
            print(f"✓ Lines cascade deleted successfully")
        
        # Test 3: Test update with line replacement
        print("\nTest 3: Testing line replacement on update...")
        estimate2 = Estimate(
            number="CASCADE-002",
            date=date(2024, 1, 16),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=5000.0,
            total_labor=50.0
        )
        
        estimate2.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=10.0, sum=5000.0)
        ]
        
        result = repo.save(estimate2)
        assert result is True, "Failed to save second estimate"
        print(f"✓ Created estimate with 1 line")
        
        # Update with different lines
        estimate2.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=5.0, sum=2500.0),
            EstimateLine(line_number=2, work_id=1, quantity=5.0, sum=2500.0),
            EstimateLine(line_number=3, work_id=1, quantity=5.0, sum=2500.0)
        ]
        
        result = repo.save(estimate2)
        assert result is True, "Failed to update estimate"
        
        # Verify old lines are replaced
        loaded = repo.find_by_id(estimate2.id)
        assert loaded is not None, "Estimate should be found"
        assert len(loaded.lines) == 3, f"Expected 3 lines, found {len(loaded.lines)}"
        print(f"✓ Lines replaced successfully (1 → 3 lines)")
        
        print("\n" + "="*50)
        print("Cascade operations test passed! ✓")
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
    test_cascade_delete()

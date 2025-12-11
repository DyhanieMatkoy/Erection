"""Test EstimateRepository against task requirements

This test verifies that all requirements from task 6 are met:
- Update find_by_id() to use SQLAlchemy session ✓
- Update save() to use SQLAlchemy session with transaction handling ✓
- Update find_by_responsible() to use SQLAlchemy query API ✓
- Ensure EstimateLine cascade operations work correctly ✓
- Test with SQLite backend first ✓
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


def test_all_requirements():
    """Test all requirements from task 6"""
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with SQLite backend
        print("="*60)
        print("Testing EstimateRepository Migration - Task 6 Requirements")
        print("="*60)
        
        db_manager = DatabaseManager()
        db_manager.initialize(db_path)
        
        # Verify we're using SQLite
        assert db_manager._config is None or db_manager._config.is_sqlite(), \
            "Should be using SQLite backend"
        print("\n✓ Requirement: Test with SQLite backend first")
        
        # Create reference data
        from src.data.models.sqlalchemy_models import Person, Counterparty, Object, Organization, Work
        
        with db_manager.session_scope() as session:
            person = Person(id=1, full_name="Test Person")
            counterparty = Counterparty(id=1, name="Test Customer")
            obj = Object(id=1, name="Test Object", owner_id=1)
            org = Organization(id=1, name="Test Contractor")
            work1 = Work(id=1, name="Work 1", unit="м²")
            
            session.add_all([person, counterparty, obj, org, work1])
        
        # Create repository
        repo = EstimateRepository()
        
        # Requirement 1: find_by_id() uses SQLAlchemy session
        print("\n" + "-"*60)
        print("Requirement 1: find_by_id() uses SQLAlchemy session")
        print("-"*60)
        
        estimate = Estimate(
            number="REQ-001",
            date=date(2024, 1, 15),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=5000.0,
            total_labor=50.0
        )
        estimate.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=10.0, sum=5000.0)
        ]
        
        repo.save(estimate)
        
        # Test find_by_id with SQLAlchemy session
        found = repo.find_by_id(estimate.id)
        assert found is not None, "find_by_id should return estimate"
        assert found.number == "REQ-001", "Data should match"
        assert len(found.lines) == 1, "Lines should be loaded"
        print("✓ find_by_id() successfully uses SQLAlchemy session")
        print(f"  - Retrieved estimate ID {found.id} with {len(found.lines)} line(s)")
        
        # Requirement 2: save() uses SQLAlchemy session with transaction handling
        print("\n" + "-"*60)
        print("Requirement 2: save() uses SQLAlchemy session with transactions")
        print("-"*60)
        
        # Test insert
        estimate2 = Estimate(
            number="REQ-002",
            date=date(2024, 1, 16),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=10000.0,
            total_labor=100.0
        )
        estimate2.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=20.0, sum=10000.0)
        ]
        
        result = repo.save(estimate2)
        assert result is True, "save() should succeed for insert"
        assert estimate2.id > 0, "ID should be assigned"
        print("✓ save() successfully inserts with transaction handling")
        print(f"  - Created estimate ID {estimate2.id}")
        
        # Test update
        estimate2.number = "REQ-002-UPDATED"
        estimate2.lines.append(
            EstimateLine(line_number=2, work_id=1, quantity=10.0, sum=5000.0)
        )
        
        result = repo.save(estimate2)
        assert result is True, "save() should succeed for update"
        
        updated = repo.find_by_id(estimate2.id)
        assert updated.number == "REQ-002-UPDATED", "Update should persist"
        assert len(updated.lines) == 2, "Lines should be updated"
        print("✓ save() successfully updates with transaction handling")
        print(f"  - Updated estimate with {len(updated.lines)} line(s)")
        
        # Requirement 3: find_by_responsible() uses SQLAlchemy query API
        print("\n" + "-"*60)
        print("Requirement 3: find_by_responsible() uses SQLAlchemy query API")
        print("-"*60)
        
        # Create multiple estimates for same responsible person
        for i in range(3):
            est = Estimate(
                number=f"RESP-{i+1}",
                date=date(2024, 1, 17 + i),
                customer_id=1,
                object_id=1,
                contractor_id=1,
                responsible_id=1,
                total_sum=1000.0 * (i + 1),
                total_labor=10.0 * (i + 1)
            )
            repo.save(est)
        
        # Test find_by_responsible
        estimates = repo.find_by_responsible(1)
        assert len(estimates) >= 3, "Should find at least 3 estimates"
        
        # Verify ordering (should be by date DESC)
        dates = [e.date for e in estimates]
        assert dates == sorted(dates, reverse=True), "Should be ordered by date DESC"
        
        print("✓ find_by_responsible() successfully uses SQLAlchemy query API")
        print(f"  - Found {len(estimates)} estimate(s) for responsible person 1")
        print(f"  - Correctly ordered by date (DESC): {dates[:3]}")
        
        # Requirement 4: EstimateLine cascade operations work correctly
        print("\n" + "-"*60)
        print("Requirement 4: EstimateLine cascade operations work correctly")
        print("-"*60)
        
        # Create estimate with lines
        cascade_est = Estimate(
            number="CASCADE-001",
            date=date(2024, 1, 20),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=15000.0,
            total_labor=150.0
        )
        cascade_est.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=10.0, sum=5000.0),
            EstimateLine(line_number=2, work_id=1, quantity=10.0, sum=5000.0),
            EstimateLine(line_number=3, work_id=1, quantity=10.0, sum=5000.0)
        ]
        
        repo.save(cascade_est)
        cascade_id = cascade_est.id
        
        # Verify lines exist
        loaded = repo.find_by_id(cascade_id)
        assert len(loaded.lines) == 3, "Should have 3 lines"
        print("✓ Lines are saved correctly")
        
        # Update with fewer lines (should delete old ones)
        loaded.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=20.0, sum=10000.0)
        ]
        repo.save(loaded)
        
        reloaded = repo.find_by_id(cascade_id)
        assert len(reloaded.lines) == 1, "Old lines should be deleted"
        print("✓ Cascade delete works when updating lines")
        
        # Delete estimate (should cascade to lines)
        from src.data.models.sqlalchemy_models import Estimate as EstimateModel, EstimateLine as EstimateLineModel
        
        with db_manager.session_scope() as session:
            est_model = session.query(EstimateModel).filter(EstimateModel.id == cascade_id).first()
            session.delete(est_model)
        
        # Verify cascade delete
        with db_manager.session_scope() as session:
            line_count = session.query(EstimateLineModel)\
                .filter(EstimateLineModel.estimate_id == cascade_id)\
                .count()
            assert line_count == 0, "Lines should be cascade deleted"
        
        print("✓ Cascade delete works when deleting estimate")
        
        # Summary
        print("\n" + "="*60)
        print("ALL REQUIREMENTS VERIFIED ✓")
        print("="*60)
        print("\nTask 6 Requirements:")
        print("  ✓ find_by_id() uses SQLAlchemy session")
        print("  ✓ save() uses SQLAlchemy session with transaction handling")
        print("  ✓ find_by_responsible() uses SQLAlchemy query API")
        print("  ✓ EstimateLine cascade operations work correctly")
        print("  ✓ Tested with SQLite backend")
        print("\n" + "="*60)
        
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
            pass


if __name__ == "__main__":
    test_all_requirements()

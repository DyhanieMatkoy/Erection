"""Test EstimateRepository with SQLAlchemy migration

This test verifies that the EstimateRepository works correctly with SQLAlchemy
after migration from raw SQL queries.
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


def test_estimate_repository_crud():
    """Test CRUD operations on EstimateRepository with SQLAlchemy"""
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize(db_path)
        
        # Create reference data first
        print("Setting up reference data...")
        from src.data.models.sqlalchemy_models import Person, Counterparty, Object, Organization, Work
        
        with db_manager.session_scope() as session:
            # Create a person
            person = Person(
                id=1,
                full_name="Test Person",
                position="Manager"
            )
            session.add(person)
            
            # Create a counterparty
            counterparty = Counterparty(
                id=1,
                name="Test Customer"
            )
            session.add(counterparty)
            
            # Create an object
            obj = Object(
                id=1,
                name="Test Object",
                owner_id=1
            )
            session.add(obj)
            
            # Create an organization
            org = Organization(
                id=1,
                name="Test Contractor"
            )
            session.add(org)
            
            # Create works
            work1 = Work(id=1, name="Work 1", unit="м²", price=500.0, labor_rate=5.0)
            work2 = Work(id=2, name="Work 2", unit="шт", price=1000.0, labor_rate=10.0)
            work3 = Work(id=3, name="Work 3", unit="м", price=500.0, labor_rate=5.0)
            session.add(work1)
            session.add(work2)
            session.add(work3)
        
        print("✓ Reference data created")
        
        # Create repository
        repo = EstimateRepository()
        
        # Test 1: Create a new estimate
        print("Test 1: Creating new estimate...")
        estimate = Estimate(
            number="EST-001",
            date=date(2024, 1, 15),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=10000.0,
            total_labor=100.0
        )
        
        # Add some lines
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
            ),
            EstimateLine(
                line_number=2,
                work_id=2,
                quantity=5.0,
                unit="шт",
                price=1000.0,
                labor_rate=10.0,
                sum=5000.0,
                planned_labor=50.0
            )
        ]
        
        result = repo.save(estimate)
        assert result is True, "Failed to save estimate"
        assert estimate.id > 0, "Estimate ID should be set after save"
        print(f"✓ Created estimate with ID: {estimate.id}")
        
        # Test 2: Find by ID
        print("\nTest 2: Finding estimate by ID...")
        found_estimate = repo.find_by_id(estimate.id)
        assert found_estimate is not None, "Estimate should be found"
        assert found_estimate.number == "EST-001", "Estimate number should match"
        assert found_estimate.total_sum == 10000.0, "Total sum should match"
        assert len(found_estimate.lines) == 2, "Should have 2 lines"
        print(f"✓ Found estimate: {found_estimate.number}")
        print(f"  Lines: {len(found_estimate.lines)}")
        
        # Test 3: Update estimate
        print("\nTest 3: Updating estimate...")
        found_estimate.number = "EST-001-UPDATED"
        found_estimate.total_sum = 15000.0
        
        # Add a new line
        found_estimate.lines.append(
            EstimateLine(
                line_number=3,
                work_id=3,
                quantity=10.0,
                unit="м",
                price=500.0,
                labor_rate=5.0,
                sum=5000.0,
                planned_labor=50.0
            )
        )
        
        result = repo.save(found_estimate)
        assert result is True, "Failed to update estimate"
        print(f"✓ Updated estimate")
        
        # Verify update
        updated_estimate = repo.find_by_id(estimate.id)
        assert updated_estimate is not None, "Updated estimate should be found"
        assert updated_estimate.number == "EST-001-UPDATED", "Number should be updated"
        assert updated_estimate.total_sum == 15000.0, "Total sum should be updated"
        assert len(updated_estimate.lines) == 3, "Should have 3 lines after update"
        print(f"  Verified: {updated_estimate.number}, {len(updated_estimate.lines)} lines")
        
        # Test 4: Find by responsible
        print("\nTest 4: Finding estimates by responsible person...")
        estimates = repo.find_by_responsible(1)
        assert len(estimates) > 0, "Should find at least one estimate"
        assert estimates[0].responsible_id == 1, "Responsible ID should match"
        print(f"✓ Found {len(estimates)} estimate(s) for responsible person 1")
        
        # Test 5: Test cascade delete of lines
        print("\nTest 5: Testing cascade operations...")
        # Remove all lines
        found_estimate.lines = []
        result = repo.save(found_estimate)
        assert result is True, "Failed to save estimate with no lines"
        
        # Verify lines were deleted
        estimate_no_lines = repo.find_by_id(estimate.id)
        assert estimate_no_lines is not None, "Estimate should still exist"
        assert len(estimate_no_lines.lines) == 0, "Lines should be deleted"
        print(f"✓ Cascade delete works correctly")
        
        # Test 6: Test with group lines
        print("\nTest 6: Testing group lines...")
        estimate_with_groups = Estimate(
            number="EST-002",
            date=date(2024, 1, 16),
            customer_id=1,
            object_id=1,
            contractor_id=1,
            responsible_id=1,
            total_sum=20000.0,
            total_labor=200.0
        )
        
        # Note: parent_group_id should be 0 or None for now since we don't have the ID yet
        # In real usage, parent_group_id would be set after the parent line is saved
        estimate_with_groups.lines = [
            EstimateLine(
                line_number=1,
                is_group=True,
                group_name="Group 1",
                is_collapsed=False,
                parent_group_id=0
            ),
            EstimateLine(
                line_number=2,
                work_id=1,
                quantity=10.0,
                unit="м²",
                price=1000.0,
                labor_rate=10.0,
                sum=10000.0,
                planned_labor=100.0,
                parent_group_id=0  # Set to 0 for now
            )
        ]
        
        result = repo.save(estimate_with_groups)
        assert result is True, "Failed to save estimate with groups"
        
        found_groups = repo.find_by_id(estimate_with_groups.id)
        assert found_groups is not None, "Estimate with groups should be found"
        assert len(found_groups.lines) == 2, "Should have 2 lines"
        assert found_groups.lines[0].is_group is True, "First line should be a group"
        assert found_groups.lines[0].group_name == "Group 1", "Group name should match"
        print(f"✓ Group lines work correctly")
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("="*50)
        
    finally:
        # Clean up - close database connections first
        try:
            if db_manager._engine:
                db_manager._engine.dispose()
            if db_manager._connection:
                db_manager._connection.close()
        except:
            pass
        
        # Remove temporary file
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except PermissionError:
            print(f"Warning: Could not delete temporary database file: {db_path}")


if __name__ == "__main__":
    test_estimate_repository_crud()

"""Test SQLAlchemy table creation

This test verifies that the SQLAlchemy models can create tables
in an actual database (using SQLite for testing).
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, inspect
from src.data.models.sqlalchemy_models import Base


def test_create_tables_in_sqlite():
    """Test that all tables can be created in SQLite"""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create engine
        engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Inspect the database
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Created {len(tables)} tables in test database:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Verify all expected tables exist
        expected_tables = {
            'users', 'persons', 'organizations', 'counterparties', 'objects', 'works',
            'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
            'daily_report_executors', 'timesheets', 'timesheet_lines',
            'work_execution_register', 'payroll_register', 'user_settings', 'constants'
        }
        
        actual_tables = set(tables)
        missing = expected_tables - actual_tables
        
        if missing:
            print(f"\n✗ Missing tables: {missing}")
            assert False, f"Missing tables: {missing}"
        
        print(f"\n✓ All {len(expected_tables)} expected tables were created")
        
        # Test that we can inspect table columns
        print("\nSample table structure (estimates):")
        columns = inspector.get_columns('estimates')
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Test foreign keys
        print("\nForeign keys in estimates table:")
        fks = inspector.get_foreign_keys('estimates')
        for fk in fks:
            print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # Test indices
        print("\nIndices in estimates table:")
        indices = inspector.get_indexes('estimates')
        for idx in indices:
            print(f"  - {idx['name']}: {idx['column_names']}")
        
        print("\n✓ Table structure is correct")
        
        # Clean up
        engine.dispose()
        
    finally:
        # Remove temporary database
        if os.path.exists(db_path):
            os.remove(db_path)


def test_table_creation_is_idempotent():
    """Test that creating tables multiple times doesn't cause errors"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Create tables first time
        Base.metadata.create_all(engine)
        
        # Create tables second time (should not error)
        Base.metadata.create_all(engine)
        
        # Verify tables still exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert len(tables) == 17
        print("\n✓ Table creation is idempotent (can be called multiple times)")
        
        engine.dispose()
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == '__main__':
    print("=" * 70)
    print("Testing SQLAlchemy Table Creation")
    print("=" * 70)
    
    try:
        test_create_tables_in_sqlite()
        test_table_creation_is_idempotent()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

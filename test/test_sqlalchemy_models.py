"""Test SQLAlchemy models definition

This test verifies that all SQLAlchemy models are correctly defined
and can be imported without errors.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.models.sqlalchemy_models import (
    Base,
    User,
    Person,
    Organization,
    Counterparty,
    Object,
    Work,
    Estimate,
    EstimateLine,
    DailyReport,
    DailyReportLine,
    DailyReportExecutor,
    Timesheet,
    TimesheetLine,
    WorkExecutionRegister,
    PayrollRegister,
    UserSetting,
    Constant
)


def test_all_models_defined():
    """Test that all models are defined and accessible"""
    models = [
        User,
        Person,
        Organization,
        Counterparty,
        Object,
        Work,
        Estimate,
        EstimateLine,
        DailyReport,
        DailyReportLine,
        DailyReportExecutor,
        Timesheet,
        TimesheetLine,
        WorkExecutionRegister,
        PayrollRegister,
        UserSetting,
        Constant
    ]
    
    for model in models:
        assert model is not None
        assert hasattr(model, '__tablename__')
        print(f"✓ Model {model.__name__} defined with table '{model.__tablename__}'")
    
    print(f"\n✓ All {len(models)} models are correctly defined")


def test_base_metadata_contains_all_tables():
    """Test that Base metadata contains all expected tables"""
    expected_tables = {
        'users',
        'persons',
        'organizations',
        'counterparties',
        'objects',
        'works',
        'estimates',
        'estimate_lines',
        'daily_reports',
        'daily_report_lines',
        'daily_report_executors',
        'timesheets',
        'timesheet_lines',
        'work_execution_register',
        'payroll_register',
        'user_settings',
        'constants'
    }
    
    actual_tables = set(Base.metadata.tables.keys())
    
    print(f"\nExpected tables: {len(expected_tables)}")
    print(f"Actual tables: {len(actual_tables)}")
    
    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables
    
    if missing_tables:
        print(f"\n✗ Missing tables: {missing_tables}")
        assert False, f"Missing tables: {missing_tables}"
    
    if extra_tables:
        print(f"\n⚠ Extra tables: {extra_tables}")
    
    print(f"\n✓ All expected tables are present in Base metadata")
    print(f"\nTables in metadata:")
    for table_name in sorted(actual_tables):
        print(f"  - {table_name}")


def test_model_relationships():
    """Test that key relationships are defined"""
    # Test User relationships
    assert hasattr(User, 'person')
    assert hasattr(User, 'settings')
    
    # Test Person relationships
    assert hasattr(Person, 'user')
    assert hasattr(Person, 'parent')
    assert hasattr(Person, 'estimates_responsible')
    
    # Test Estimate relationships
    assert hasattr(Estimate, 'customer')
    assert hasattr(Estimate, 'object')
    assert hasattr(Estimate, 'contractor')
    assert hasattr(Estimate, 'responsible')
    assert hasattr(Estimate, 'lines')
    
    # Test EstimateLine relationships
    assert hasattr(EstimateLine, 'estimate')
    assert hasattr(EstimateLine, 'work')
    
    # Test DailyReport relationships
    assert hasattr(DailyReport, 'estimate')
    assert hasattr(DailyReport, 'foreman')
    assert hasattr(DailyReport, 'lines')
    
    # Test Timesheet relationships
    assert hasattr(Timesheet, 'object')
    assert hasattr(Timesheet, 'estimate')
    assert hasattr(Timesheet, 'foreman')
    assert hasattr(Timesheet, 'lines')
    
    print("\n✓ All key relationships are defined")


def test_model_primary_keys():
    """Test that all models have primary keys defined"""
    models = [
        User, Person, Organization, Counterparty, Object, Work,
        Estimate, EstimateLine, DailyReport, DailyReportLine,
        Timesheet, TimesheetLine, WorkExecutionRegister, PayrollRegister,
        Constant
    ]
    
    for model in models:
        table = model.__table__
        primary_keys = [col.name for col in table.primary_key.columns]
        assert len(primary_keys) > 0, f"Model {model.__name__} has no primary key"
        print(f"✓ {model.__name__}: primary key = {primary_keys}")
    
    # Test composite primary keys
    assert len(list(DailyReportExecutor.__table__.primary_key.columns)) == 2
    assert len(list(UserSetting.__table__.primary_key.columns)) == 3
    
    print("\n✓ All models have primary keys defined")


def test_model_foreign_keys():
    """Test that key foreign keys are defined"""
    # Test Estimate foreign keys
    estimate_fks = [fk.parent.name for fk in Estimate.__table__.foreign_keys]
    assert 'customer_id' in estimate_fks
    assert 'object_id' in estimate_fks
    assert 'contractor_id' in estimate_fks
    assert 'responsible_id' in estimate_fks
    
    # Test EstimateLine foreign keys
    estimate_line_fks = [fk.parent.name for fk in EstimateLine.__table__.foreign_keys]
    assert 'estimate_id' in estimate_line_fks
    assert 'work_id' in estimate_line_fks
    
    # Test Person foreign keys
    person_fks = [fk.parent.name for fk in Person.__table__.foreign_keys]
    assert 'user_id' in person_fks
    assert 'parent_id' in person_fks
    
    print("\n✓ Key foreign keys are defined")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing SQLAlchemy Models Definition")
    print("=" * 70)
    
    try:
        test_all_models_defined()
        test_base_metadata_contains_all_tables()
        test_model_relationships()
        test_model_primary_keys()
        test_model_foreign_keys()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

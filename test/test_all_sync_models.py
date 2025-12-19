"""Verification test for all synchronized models

This test verifies that all models listed in migration 20251217_000001
have synchronization fields properly configured.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import (
    Estimate, EstimateLine, DailyReport, DailyReportLine,
    Timesheet, TimesheetLine, Work, Material, CostItem,
    Unit, Person, Organization, Counterparty, Object
)


def test_all_synchronized_models():
    """Verify all models from migration have synchronization fields"""
    
    # Models that should have sync fields according to migration 20251217_000001
    models_to_check = {
        'estimates': Estimate,
        'estimate_lines': EstimateLine,
        'daily_reports': DailyReport,
        'daily_report_lines': DailyReportLine,
        'timesheets': Timesheet,
        'timesheet_lines': TimesheetLine,
        'works': Work,
        'materials': Material,
        'cost_items': CostItem,
        'units': Unit,
        'persons': Person,
        'organizations': Organization,
        'counterparties': Counterparty,
        'objects': Object,
    }
    
    required_fields = ['uuid', 'updated_at', 'is_deleted']
    
    print("Checking synchronization fields in all models...")
    print("=" * 70)
    
    all_passed = True
    
    for table_name, model_class in models_to_check.items():
        print(f"\n{table_name} ({model_class.__name__}):")
        
        # Get table columns
        columns = [col.name for col in model_class.__table__.columns]
        
        # Check for required fields
        missing_fields = [field for field in required_fields if field not in columns]
        
        if missing_fields:
            print(f"  ❌ MISSING: {missing_fields}")
            all_passed = False
        else:
            print(f"  ✓ All synchronization fields present")
            
            # Check field configurations
            uuid_col = model_class.__table__.columns['uuid']
            updated_at_col = model_class.__table__.columns['updated_at']
            is_deleted_col = model_class.__table__.columns['is_deleted']
            
            # Verify constraints
            checks = []
            if uuid_col.nullable:
                checks.append("uuid should be NOT NULL")
            if updated_at_col.nullable:
                checks.append("updated_at should be NOT NULL")
            if is_deleted_col.nullable:
                checks.append("is_deleted should be NOT NULL")
            if uuid_col.default is None:
                checks.append("uuid should have default")
            if updated_at_col.default is None:
                checks.append("updated_at should have default")
            if is_deleted_col.default is None:
                checks.append("is_deleted should have default")
            
            if checks:
                print(f"  ⚠ Configuration issues: {', '.join(checks)}")
                all_passed = False
            else:
                print(f"  ✓ All constraints correct")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("\n✅ ALL MODELS VERIFIED SUCCESSFULLY!")
        print("\nAll models have:")
        print("  ✓ uuid field with automatic generation")
        print("  ✓ updated_at field with automatic timestamps")
        print("  ✓ is_deleted field with default False")
        print("  ✓ Correct constraints (NOT NULL)")
        print("  ✓ Default value generators configured")
        return True
    else:
        print("\n❌ SOME MODELS HAVE ISSUES")
        print("Please review the output above for details.")
        return False


if __name__ == "__main__":
    success = test_all_synchronized_models()
    sys.exit(0 if success else 1)

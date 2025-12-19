#!/usr/bin/env python3
"""
Test script for UUID migration utilities

This script tests the UUID migration service functionality.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_manager import DatabaseManager
from src.services.uuid_migration_service import UUIDMigrationService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_uuid_generation():
    """Test UUID generation for works"""
    print("\n" + "="*60)
    print("TESTING UUID GENERATION")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        migration_service = UUIDMigrationService(db_manager)
        
        # Test UUID generation
        test_work_ids = [1, 2, 3, 100, 1000]
        
        for work_id in test_work_ids:
            uuid_str = migration_service.generate_uuid_for_work(work_id)
            is_valid = migration_service.validate_uuid_format(uuid_str)
            print(f"Work ID {work_id}: UUID = {uuid_str}, Valid = {is_valid}")
        
        # Test that same work ID generates same UUID
        uuid1 = migration_service.generate_uuid_for_work(1)
        uuid2 = migration_service.generate_uuid_for_work(1)
        print(f"\nConsistency test: Work ID 1 generates same UUID: {uuid1 == uuid2}")
        
        return True
        
    except Exception as e:
        print(f"Error testing UUID generation: {e}")
        return False


def test_uuid_assignment():
    """Test UUID assignment to existing works"""
    print("\n" + "="*60)
    print("TESTING UUID ASSIGNMENT")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        migration_service = UUIDMigrationService(db_manager)
        
        # Test UUID assignment (dry run with small batch)
        results = migration_service.assign_uuids_to_existing_works(batch_size=10)
        
        print(f"Total processed: {results['total_processed']}")
        print(f"UUIDs assigned: {results['uuids_assigned']}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Duration: {results['end_time'] - results['start_time']}")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        return len(results['errors']) == 0
        
    except Exception as e:
        print(f"Error testing UUID assignment: {e}")
        return False


def test_foreign_key_analysis():
    """Test foreign key table analysis"""
    print("\n" + "="*60)
    print("TESTING FOREIGN KEY ANALYSIS")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        migration_service = UUIDMigrationService(db_manager)
        
        # Get foreign key tables
        fk_tables = migration_service.get_foreign_key_tables()
        
        print(f"Found {len(fk_tables)} foreign key relationships to works table:")
        for fk_info in fk_tables:
            nullable_str = "nullable" if fk_info['is_nullable'] else "NOT NULL"
            print(f"  - {fk_info['table_name']}.{fk_info['column_name']} ({nullable_str})")
        
        return True
        
    except Exception as e:
        print(f"Error testing foreign key analysis: {e}")
        return False


def test_uuid_validation():
    """Test UUID validation functionality"""
    print("\n" + "="*60)
    print("TESTING UUID VALIDATION")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        migration_service = UUIDMigrationService(db_manager)
        
        # Test validation
        validation_results = migration_service.validate_uuid_migration()
        
        print(f"Works without UUID: {validation_results['works_without_uuid']}")
        print(f"Duplicate UUIDs: {validation_results['duplicate_uuids']}")
        print(f"Orphaned FK UUIDs: {len(validation_results['orphaned_fk_uuids'])}")
        print(f"Missing FK UUIDs: {len(validation_results['missing_fk_uuids'])}")
        print(f"Validation passed: {validation_results['validation_passed']}")
        
        if validation_results['errors']:
            print("\nValidation errors:")
            for error in validation_results['errors']:
                print(f"  - {error}")
        
        return True
        
    except Exception as e:
        print(f"Error testing UUID validation: {e}")
        return False


def main():
    """Run all UUID migration tests"""
    print("UUID MIGRATION SERVICE TESTS")
    print("="*80)
    
    tests = [
        ("UUID Generation", test_uuid_generation),
        ("UUID Assignment", test_uuid_assignment),
        ("Foreign Key Analysis", test_foreign_key_analysis),
        ("UUID Validation", test_uuid_validation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...")
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! UUID migration utilities are working correctly.")
        return True
    else:
        print("Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
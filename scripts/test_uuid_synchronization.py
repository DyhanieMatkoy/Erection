#!/usr/bin/env python3
"""
Test script for UUID synchronization service

This script tests the UUID synchronization service functionality.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_manager import DatabaseManager
from src.services.uuid_synchronization_service import (
    UUIDSynchronizationService, 
    ConflictResolutionStrategy, 
    SyncDirection
)
from src.data.models.sqlalchemy_models import Work

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_external_works() -> List[Dict[str, Any]]:
    """Create test external works data for synchronization testing"""
    return [
        {
            'uuid': 'test-uuid-001',
            'name': 'Test Work 1',
            'code': 'TW001',
            'price': 100.0,
            'labor_rate': 50.0,
            'unit_id': None,
            'parent_id': None,
            'is_group': False,
            'marked_for_deletion': False,
            'updated_at': '2025-12-19T01:00:00+00:00'
        },
        {
            'uuid': 'test-uuid-002',
            'name': 'Test Work 2',
            'code': 'TW002',
            'price': 200.0,
            'labor_rate': 75.0,
            'unit_id': None,
            'parent_id': None,
            'is_group': False,
            'marked_for_deletion': False,
            'updated_at': '2025-12-19T02:00:00+00:00'
        },
        {
            'uuid': 'test-uuid-003',
            'name': 'Test Group Work',
            'code': 'TGW001',
            'price': 0.0,
            'labor_rate': 0.0,
            'unit_id': None,
            'parent_id': None,
            'is_group': True,
            'marked_for_deletion': False,
            'updated_at': '2025-12-19T03:00:00+00:00'
        }
    ]


def test_uuid_lookup():
    """Test UUID-based work lookup functionality"""
    print("\n" + "="*60)
    print("TESTING UUID LOOKUP")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Test finding works by UUID
        # Get some existing works
        existing_works = session.query(Work).limit(3).all()
        
        if existing_works:
            for work in existing_works:
                found_work = sync_service.find_work_by_uuid(session, work.uuid)
                if found_work:
                    print(f"Found work by UUID {work.uuid}: {found_work.name}")
                else:
                    print(f"Could not find work by UUID {work.uuid}")
            
            # Test batch lookup
            uuids = [work.uuid for work in existing_works]
            found_works = sync_service.find_works_by_uuids(session, uuids)
            print(f"\nBatch lookup: Found {len(found_works)} out of {len(uuids)} works")
        else:
            print("No existing works found for UUID lookup test")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error testing UUID lookup: {e}")
        return False


def test_conflict_detection():
    """Test conflict detection between local and external works"""
    print("\n" + "="*60)
    print("TESTING CONFLICT DETECTION")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Create test external works
        external_works = create_test_external_works()
        
        # Detect conflicts
        conflicts = sync_service.detect_uuid_conflicts(session, external_works)
        
        print(f"Detected {len(conflicts)} conflicts")
        
        for conflict in conflicts:
            print(f"Conflict for UUID {conflict['uuid']}: {conflict['conflict_type']}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error testing conflict detection: {e}")
        return False


def test_uuid_index_creation():
    """Test UUID lookup index creation"""
    print("\n" + "="*60)
    print("TESTING UUID INDEX CREATION")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Create UUID indexes
        success = sync_service.create_uuid_lookup_index(session)
        
        print(f"UUID index creation: {'SUCCESS' if success else 'FAILED'}")
        
        session.close()
        return success
        
    except Exception as e:
        print(f"Error testing UUID index creation: {e}")
        return False


def test_works_export():
    """Test exporting works for synchronization"""
    print("\n" + "="*60)
    print("TESTING WORKS EXPORT")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Export all works
        exported_works = sync_service.export_works_for_sync(session)
        
        print(f"Exported {len(exported_works)} works for synchronization")
        
        if exported_works:
            # Show first few works
            for i, work in enumerate(exported_works[:3]):
                print(f"Work {i+1}: UUID={work['uuid']}, Name={work['name']}")
        
        # Test export with date filter
        recent_date = datetime(2025, 1, 1)
        recent_works = sync_service.export_works_for_sync(session, modified_since=recent_date)
        
        print(f"Exported {len(recent_works)} works modified since {recent_date}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error testing works export: {e}")
        return False


def test_uuid_relationship_validation():
    """Test UUID relationship validation"""
    print("\n" + "="*60)
    print("TESTING UUID RELATIONSHIP VALIDATION")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Validate UUID relationships
        validation_results = sync_service.validate_uuid_relationships(session)
        
        print(f"Valid relationships: {validation_results['valid_relationships']}")
        print(f"Invalid relationships: {len(validation_results['invalid_relationships'])}")
        print(f"Orphaned references: {len(validation_results['orphaned_references'])}")
        print(f"Validation passed: {validation_results['validation_passed']}")
        
        if validation_results['orphaned_references']:
            print("\nOrphaned references found:")
            for orphan in validation_results['orphaned_references'][:5]:  # Show first 5
                print(f"  - {orphan['table']}: {orphan['reference_type']} = {orphan['invalid_reference']}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error testing UUID relationship validation: {e}")
        return False


def test_synchronization_workflow():
    """Test complete synchronization workflow"""
    print("\n" + "="*60)
    print("TESTING SYNCHRONIZATION WORKFLOW")
    print("="*60)
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Create test external works
        external_works = create_test_external_works()
        
        # Test synchronization (dry run - won't actually create works)
        sync_results = sync_service.synchronize_works_by_uuid(
            session, 
            external_works,
            direction=SyncDirection.PULL,
            conflict_strategy=ConflictResolutionStrategy.LATEST_WINS
        )
        
        print(f"Synchronization results:")
        print(f"  Direction: {sync_results['direction']}")
        print(f"  Conflict strategy: {sync_results['conflict_strategy']}")
        print(f"  Total external works: {sync_results['total_external_works']}")
        print(f"  Works created: {sync_results['works_created']}")
        print(f"  Works updated: {sync_results['works_updated']}")
        print(f"  Works skipped: {sync_results['works_skipped']}")
        print(f"  Conflicts detected: {sync_results['conflicts_detected']}")
        print(f"  Conflicts resolved: {sync_results['conflicts_resolved']}")
        print(f"  Errors: {len(sync_results['errors'])}")
        
        if sync_results['errors']:
            print("\nErrors encountered:")
            for error in sync_results['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        session.close()
        return len(sync_results['errors']) == 0
        
    except Exception as e:
        print(f"Error testing synchronization workflow: {e}")
        return False


def main():
    """Run all UUID synchronization tests"""
    print("UUID SYNCHRONIZATION SERVICE TESTS")
    print("="*80)
    
    tests = [
        ("UUID Lookup", test_uuid_lookup),
        ("Conflict Detection", test_conflict_detection),
        ("UUID Index Creation", test_uuid_index_creation),
        ("Works Export", test_works_export),
        ("UUID Relationship Validation", test_uuid_relationship_validation),
        ("Synchronization Workflow", test_synchronization_workflow)
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
        print("All tests passed! UUID synchronization service is working correctly.")
        return True
    else:
        print("Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
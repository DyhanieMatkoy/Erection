#!/usr/bin/env python3
"""
UUID Migration and Synchronization Demo

This script demonstrates the complete UUID migration and synchronization workflow
for the works reference refactoring project.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_manager import DatabaseManager
from src.services.uuid_migration_service import UUIDMigrationService
from src.services.uuid_synchronization_service import (
    UUIDSynchronizationService, 
    ConflictResolutionStrategy, 
    SyncDirection
)
from scripts.utils.uuid_impact_assessment import UUIDImpactAssessment

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_subsection_header(title: str):
    """Print a formatted subsection header"""
    print("\n" + "-"*60)
    print(f" {title}")
    print("-"*60)


def demo_impact_assessment():
    """Demonstrate UUID impact assessment"""
    print_section_header("UUID IMPACT ASSESSMENT")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Create assessment tool
        assessment = UUIDImpactAssessment(db_manager)
        
        # Generate report
        print("Analyzing UUID migration impact...")
        report = assessment.generate_impact_report()
        
        # Print summary
        print(f"\nAssessment Results:")
        print(f"  Database Type: {report.database_type}")
        print(f"  Works Records: {report.works_table_record_count:,}")
        print(f"  Tables Affected: {report.migration_complexity.total_tables_affected}")
        print(f"  Foreign Keys: {report.migration_complexity.total_foreign_keys}")
        print(f"  Records to Update: {report.migration_complexity.total_records_to_update:,}")
        print(f"  Risk Level: {report.migration_complexity.risk_level.upper()}")
        print(f"  Estimated Time: {report.migration_complexity.estimated_migration_time_minutes} minutes")
        print(f"  Strategy: {report.migration_strategy}")
        
        # Save report
        filepath = assessment.save_report_to_file(report)
        print(f"\nDetailed report saved to: {filepath}")
        
        return report
        
    except Exception as e:
        print(f"Error during impact assessment: {e}")
        return None


def demo_uuid_migration():
    """Demonstrate UUID migration utilities"""
    print_section_header("UUID MIGRATION UTILITIES")
    
    try:
        # Initialize services
        db_manager = DatabaseManager()
        db_manager.initialize()
        migration_service = UUIDMigrationService(db_manager)
        
        print_subsection_header("UUID Generation Testing")
        
        # Test UUID generation
        test_ids = [1, 100, 1000]
        for work_id in test_ids:
            uuid_str = migration_service.generate_uuid_for_work(work_id)
            is_valid = migration_service.validate_uuid_format(uuid_str)
            print(f"  Work ID {work_id}: {uuid_str} (Valid: {is_valid})")
        
        print_subsection_header("Foreign Key Analysis")
        
        # Analyze foreign key relationships
        fk_tables = migration_service.get_foreign_key_tables()
        print(f"  Found {len(fk_tables)} foreign key relationships:")
        for fk_info in fk_tables:
            nullable_str = "nullable" if fk_info['is_nullable'] else "NOT NULL"
            print(f"    - {fk_info['table_name']}.{fk_info['column_name']} ({nullable_str})")
        
        print_subsection_header("Migration Validation")
        
        # Validate current state
        validation_results = migration_service.validate_uuid_migration()
        print(f"  Works without UUID: {validation_results['works_without_uuid']}")
        print(f"  Duplicate UUIDs: {validation_results['duplicate_uuids']}")
        print(f"  Validation passed: {validation_results['validation_passed']}")
        
        return True
        
    except Exception as e:
        print(f"Error during UUID migration demo: {e}")
        return False


def demo_uuid_synchronization():
    """Demonstrate UUID synchronization capabilities"""
    print_section_header("UUID SYNCHRONIZATION")
    
    try:
        # Initialize services
        db_manager = DatabaseManager()
        db_manager.initialize()
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        print_subsection_header("UUID Lookup Performance")
        
        # Test UUID lookup
        from src.data.models.sqlalchemy_models import Work
        sample_works = session.query(Work).limit(5).all()
        
        if sample_works:
            print(f"  Testing lookup for {len(sample_works)} works:")
            
            # Single lookups
            for work in sample_works[:3]:
                found = sync_service.find_work_by_uuid(session, work.uuid)
                status = "Found" if found else "Not Found"
                print(f"    UUID {work.uuid[:8]}...: {status}")
            
            # Batch lookup
            uuids = [work.uuid for work in sample_works]
            found_works = sync_service.find_works_by_uuids(session, uuids)
            print(f"    Batch lookup: {len(found_works)}/{len(uuids)} works found")
        
        print_subsection_header("Index Creation")
        
        # Create UUID indexes
        index_success = sync_service.create_uuid_lookup_index(session)
        print(f"  UUID index creation: {'SUCCESS' if index_success else 'FAILED'}")
        
        print_subsection_header("Works Export")
        
        # Export works for sync
        exported_works = sync_service.export_works_for_sync(session)
        print(f"  Exported {len(exported_works)} works for synchronization")
        
        if exported_works:
            print(f"  Sample exported work:")
            sample = exported_works[0]
            print(f"    UUID: {sample['uuid']}")
            print(f"    Name: {sample['name'][:50]}...")
            print(f"    Updated: {sample['updated_at']}")
        
        print_subsection_header("Relationship Validation")
        
        # Validate UUID relationships
        validation = sync_service.validate_uuid_relationships(session)
        print(f"  Valid relationships: {validation['valid_relationships']}")
        print(f"  Orphaned references: {len(validation['orphaned_references'])}")
        print(f"  Validation passed: {validation['validation_passed']}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error during UUID synchronization demo: {e}")
        return False


def demo_conflict_resolution():
    """Demonstrate conflict resolution strategies"""
    print_section_header("CONFLICT RESOLUTION STRATEGIES")
    
    try:
        # Initialize services
        db_manager = DatabaseManager()
        db_manager.initialize()
        sync_service = UUIDSynchronizationService(db_manager)
        
        session = db_manager.get_session()
        
        # Create sample external works for testing
        external_works = [
            {
                'uuid': 'demo-uuid-001',
                'name': 'Demo Work 1',
                'code': 'DW001',
                'price': 150.0,
                'labor_rate': 60.0,
                'unit_id': None,
                'parent_id': None,
                'is_group': False,
                'marked_for_deletion': False,
                'updated_at': '2025-12-19T10:00:00+00:00'
            },
            {
                'uuid': 'demo-uuid-002',
                'name': 'Demo Work 2',
                'code': 'DW002',
                'price': 250.0,
                'labor_rate': 80.0,
                'unit_id': None,
                'parent_id': None,
                'is_group': False,
                'marked_for_deletion': False,
                'updated_at': '2025-12-19T11:00:00+00:00'
            }
        ]
        
        print_subsection_header("Conflict Detection")
        
        # Detect conflicts
        conflicts = sync_service.detect_uuid_conflicts(session, external_works)
        print(f"  Detected {len(conflicts)} conflicts with external works")
        
        print_subsection_header("Synchronization Strategies")
        
        strategies = [
            (ConflictResolutionStrategy.LATEST_WINS, "Latest Wins"),
            (ConflictResolutionStrategy.SKIP_CONFLICT, "Skip Conflicts"),
        ]
        
        for strategy, name in strategies:
            print(f"\n  Testing {name} strategy:")
            
            # Test synchronization with this strategy
            sync_results = sync_service.synchronize_works_by_uuid(
                session,
                external_works,
                direction=SyncDirection.PULL,
                conflict_strategy=strategy
            )
            
            print(f"    Works created: {sync_results['works_created']}")
            print(f"    Works updated: {sync_results['works_updated']}")
            print(f"    Works skipped: {sync_results['works_skipped']}")
            print(f"    Conflicts resolved: {sync_results['conflicts_resolved']}")
            print(f"    Errors: {len(sync_results['errors'])}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error during conflict resolution demo: {e}")
        return False


def demo_performance_considerations():
    """Demonstrate performance considerations for UUID migration"""
    print_section_header("PERFORMANCE CONSIDERATIONS")
    
    try:
        # Initialize services
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        session = db_manager.get_session()
        
        print_subsection_header("Database Statistics")
        
        # Get database statistics
        from sqlalchemy import text
        
        # Count records in key tables
        tables = ['works', 'estimate_lines', 'daily_report_lines', 'cost_item_materials']
        
        for table in tables:
            try:
                count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: {count:,} records")
            except Exception as e:
                print(f"  {table}: Error counting records - {e}")
        
        print_subsection_header("Index Analysis")
        
        # Check existing indexes on works table
        try:
            indexes = session.execute(text("""
                SELECT name, sql 
                FROM sqlite_master 
                WHERE type='index' AND tbl_name='works'
                AND name NOT LIKE 'sqlite_%'
            """)).fetchall()
            
            print(f"  Existing indexes on works table: {len(indexes)}")
            for idx in indexes:
                print(f"    - {idx.name}")
        except Exception as e:
            print(f"  Error analyzing indexes: {e}")
        
        print_subsection_header("Migration Time Estimates")
        
        # Estimate migration times based on record counts
        from src.data.models.sqlalchemy_models import Work
        works_count = session.query(Work).count()
        
        # Simple time estimates (very rough)
        uuid_generation_time = max(1, works_count // 1000)  # 1 min per 1000 works
        fk_update_time = max(2, works_count // 500)  # 2 min per 500 works
        index_creation_time = 1  # 1 min for index creation
        
        total_time = uuid_generation_time + fk_update_time + index_creation_time
        
        print(f"  Estimated migration times:")
        print(f"    UUID generation: ~{uuid_generation_time} minutes")
        print(f"    FK updates: ~{fk_update_time} minutes")
        print(f"    Index creation: ~{index_creation_time} minutes")
        print(f"    Total estimated time: ~{total_time} minutes")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error during performance analysis: {e}")
        return False


def main():
    """Run the complete UUID workflow demonstration"""
    print("UUID MIGRATION AND SYNCHRONIZATION WORKFLOW DEMO")
    print("="*80)
    print("This demo showcases the complete UUID migration and synchronization")
    print("capabilities for the works reference refactoring project.")
    
    demos = [
        ("Impact Assessment", demo_impact_assessment),
        ("UUID Migration", demo_uuid_migration),
        ("UUID Synchronization", demo_uuid_synchronization),
        ("Conflict Resolution", demo_conflict_resolution),
        ("Performance Considerations", demo_performance_considerations)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} Running {demo_name} {'='*20}")
            results[demo_name] = demo_func()
        except Exception as e:
            print(f"Demo {demo_name} failed with exception: {e}")
            results[demo_name] = False
    
    # Summary
    print_section_header("DEMO RESULTS SUMMARY")
    
    passed = 0
    total = len(demos)
    
    for demo_name, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        print(f"  {demo_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} demos completed successfully")
    
    if passed == total:
        print("\n✅ All demos completed successfully!")
        print("The UUID migration and synchronization system is ready for use.")
    else:
        print("\n❌ Some demos failed. Please review the output above.")
    
    print("\nNext Steps:")
    print("1. Review the impact assessment report for migration planning")
    print("2. Test the migration utilities in a staging environment")
    print("3. Implement UUID-based synchronization in your application")
    print("4. Update API endpoints to support UUID lookups")
    print("5. Consider implementing the full migration workflow")


if __name__ == "__main__":
    main()
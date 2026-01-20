#!/usr/bin/env python3
"""
Simple Integration Test for Sync End-to-End Testing System

This script performs a basic integration test to verify that all components
of the sync end-to-end testing system work together correctly.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_sync_end_to_end import SyncEndToEndTestController
from test_config_manager import TestConfiguration
from test_logging_system import setup_test_logging
from test_report_generator import TestReportGenerator


def test_basic_initialization():
    """Test basic initialization of all components"""
    print("Testing basic initialization...")
    
    # Create test configuration
    config = TestConfiguration(
        client_count=1,
        server_port=8001,  # Use different port to avoid conflicts
        sync_timeout=10,
        verbose=True,
        cleanup=True
    )
    
    # Test controller initialization
    controller = SyncEndToEndTestController(config.to_dict())
    assert controller.test_id is not None
    assert controller.config['client_count'] == 1
    
    print(f"✓ Test controller initialized with ID: {controller.test_id}")
    
    # Test logging system
    logging_system = setup_test_logging(controller.test_id, config.to_dict())
    logger = logging_system.get_logger()
    logger.info("Test logging message")
    
    print("✓ Logging system initialized")
    
    # Test report generator
    report_generator = TestReportGenerator(controller.test_id, config.to_dict())
    report_generator.add_phase_result("test_phase", "PASSED", 1.5, controller.start_time)
    
    print("✓ Report generator initialized")
    
    # Cleanup
    logging_system.finalize_logging()
    
    print("✓ Basic initialization test completed successfully")


def test_configuration_management():
    """Test configuration management"""
    print("\nTesting configuration management...")
    
    # Test default configuration
    default_config = TestConfiguration()
    assert default_config.client_count == 3
    assert default_config.server_port == 8000
    
    print("✓ Default configuration created")
    
    # Test custom configuration
    custom_config = TestConfiguration(
        client_count=5,
        server_port=9000,
        sync_timeout=60,
        verbose=True
    )
    
    config_dict = custom_config.to_dict()
    assert config_dict['client_count'] == 5
    assert config_dict['server_port'] == 9000
    assert config_dict['sync_timeout'] == 60
    
    print("✓ Custom configuration created and validated")
    
    # Test configuration from dictionary
    restored_config = TestConfiguration.from_dict(config_dict)
    assert restored_config.client_count == 5
    assert restored_config.server_port == 9000
    
    print("✓ Configuration serialization/deserialization works")
    
    print("✓ Configuration management test completed successfully")


def test_document_templates():
    """Test document template generation"""
    print("\nTesting document templates...")
    
    from document_creation_engine import DocumentDataGenerator
    
    # Create logger
    logger = logging.getLogger("test_templates")
    logger.setLevel(logging.INFO)
    
    # Create data generator
    data_generator = DocumentDataGenerator(logger)
    
    # Test estimate data generation
    estimate_data = data_generator.generate_estimate_data("test_client")
    assert 'number' in estimate_data
    assert 'date' in estimate_data
    assert 'lines' in estimate_data
    assert len(estimate_data['lines']) > 0
    
    print(f"✓ Estimate template generated: {estimate_data['number']}")
    
    # Test daily report data generation
    daily_report_data = data_generator.generate_daily_report_data("test_client")
    assert 'number' in daily_report_data
    assert 'date' in daily_report_data
    assert 'lines' in daily_report_data
    
    print(f"✓ Daily report template generated: {daily_report_data['number']}")
    
    # Test timesheet data generation
    timesheet_data = data_generator.generate_timesheet_data("test_client")
    assert 'number' in timesheet_data
    assert 'month_year' in timesheet_data
    assert 'lines' in timesheet_data
    
    print(f"✓ Timesheet template generated: {timesheet_data['number']}")
    
    print("✓ Document template test completed successfully")


def test_report_generation():
    """Test report generation"""
    print("\nTesting report generation...")
    
    # Create test report generator
    test_id = "test_report_123"
    config = TestConfiguration().to_dict()
    
    report_generator = TestReportGenerator(test_id, config)
    
    # Add test data
    report_generator.add_phase_result(
        "setup", "PASSED", 2.5, 
        report_generator.start_time
    )
    
    report_generator.add_phase_result(
        "execution", "PASSED", 15.3,
        report_generator.start_time
    )
    
    report_generator.add_document(
        "estimate", "client_1", "EST-001", 
        report_generator.start_time.isoformat(),
        "synced", "verified"
    )
    
    report_generator.add_sync_operation({
        'client_id': 'client_1',
        'status': 'success',
        'duration': 12.5,
        'data_size': 1024
    })
    
    # Generate reports
    generated_files = report_generator.generate_report(
        formats=['json', 'html', 'txt']
    )
    
    assert 'json' in generated_files
    assert 'html' in generated_files
    assert 'txt' in generated_files
    
    # Verify files exist
    for format_type, file_path in generated_files.items():
        assert os.path.exists(file_path), f"Report file not found: {file_path}"
        print(f"✓ {format_type.upper()} report generated: {file_path}")
    
    # Test summary report
    summary = report_generator.generate_summary_report()
    assert "Test Summary" in summary
    assert test_id in summary
    
    print(f"✓ Summary report: {summary}")
    
    print("✓ Report generation test completed successfully")


def test_verification_engine():
    """Test data verification engine components"""
    print("\nTesting verification engine...")
    
    from data_verification_engine import ContentComparisonEngine, DatabaseQueryUtilities
    
    # Create logger
    logger = logging.getLogger("test_verification")
    logger.setLevel(logging.INFO)
    
    # Test content comparison
    content_engine = ContentComparisonEngine(logger)
    
    # Test content hashing
    test_content1 = {
        'id': 1,
        'number': 'TEST-001',
        'date': '2024-01-20',
        'total_sum': 1000.50,
        'created_at': '2024-01-20T10:00:00Z'
    }
    
    test_content2 = {
        'id': 2,  # Different ID (should be ignored)
        'number': 'TEST-001',
        'date': '2024-01-20',
        'total_sum': 1000.50,
        'created_at': '2024-01-20T11:00:00Z'  # Different timestamp (should be ignored)
    }
    
    hash1 = content_engine.calculate_content_hash(test_content1)
    hash2 = content_engine.calculate_content_hash(test_content2)
    
    # Hashes should be the same because ID and timestamps are ignored
    assert hash1 == hash2, f"Content hashes should match: {hash1} != {hash2}"
    
    print("✓ Content hashing works correctly")
    
    # Test document comparison
    comparison = content_engine.compare_documents(test_content1, test_content2)
    assert comparison['identical'] == True
    
    print("✓ Document comparison works correctly")
    
    # Test with different content
    test_content3 = test_content1.copy()
    test_content3['total_sum'] = 2000.00
    
    comparison2 = content_engine.compare_documents(test_content1, test_content3)
    assert comparison2['identical'] == False
    assert len(comparison2['differences']) > 0
    
    print("✓ Document difference detection works correctly")
    
    print("✓ Verification engine test completed successfully")


def cleanup_test_files():
    """Clean up test files"""
    print("\nCleaning up test files...")
    
    # Remove test directories
    test_dirs = ['test_logs', 'test_reports', 'test_databases', 'test_configs']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            import shutil
            try:
                shutil.rmtree(test_dir)
                print(f"✓ Removed {test_dir}")
            except Exception as e:
                print(f"⚠ Could not remove {test_dir}: {e}")


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("SYNC END-TO-END TESTING SYSTEM - INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Run all tests
        test_basic_initialization()
        test_configuration_management()
        test_document_templates()
        test_report_generation()
        test_verification_engine()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe sync end-to-end testing system is ready for use.")
        print("You can now run the full test with:")
        print("  python test_sync_end_to_end.py --verbose --client-count 3")
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Always cleanup
        cleanup_test_files()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
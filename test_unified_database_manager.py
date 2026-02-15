#!/usr/bin/env python3
"""Test script for Unified Database Manager"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_database_manager import UnifiedDatabaseManager

def test_document_creation():
    """Test document creation with unified database manager"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        logger.info(f"Testing unified database manager with: {db_path}")
        
        # Initialize database manager
        manager = UnifiedDatabaseManager(logger=logger, use_docker=False)
        success = manager.initialize(db_path)
        
        if not success:
            logger.error("Failed to initialize database manager")
            return False
        
        logger.info("Database manager initialized successfully")
        
        # Test document creation
        logger.info("Testing document creation...")
        
        # Test estimate creation
        try:
            estimate_id = manager.execute_update(
                "INSERT INTO estimates (number, date) VALUES (?, ?)",
                ("TEST-EST-001", "2026-01-28")
            )
            logger.info(f"✅ Estimate created successfully with ID: {estimate_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create estimate: {e}")
            return False
        
        # Test daily report creation
        try:
            report_id = manager.execute_update(
                "INSERT INTO daily_reports (date) VALUES (?)",
                ("2026-01-28",)
            )
            logger.info(f"✅ Daily report created successfully with ID: {report_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create daily report: {e}")
            return False
        
        # Test timesheet creation
        try:
            timesheet_id = manager.execute_update(
                "INSERT INTO timesheets (number, date, month_year) VALUES (?, ?, ?)",
                ("TEST-TS-001", "2026-01-28", "2026-01")
            )
            logger.info(f"✅ Timesheet created successfully with ID: {timesheet_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create timesheet: {e}")
            return False
        
        # Verify documents exist
        logger.info("Verifying documents exist...")
        
        estimates = manager.execute_query("SELECT * FROM estimates")
        daily_reports = manager.execute_query("SELECT * FROM daily_reports")
        timesheets = manager.execute_query("SELECT * FROM timesheets")
        
        logger.info(f"Found {len(estimates)} estimates, {len(daily_reports)} daily reports, {len(timesheets)} timesheets")
        
        if len(estimates) > 0 and len(daily_reports) > 0 and len(timesheets) > 0:
            logger.info("✅ All documents verified successfully")
            return True
        else:
            logger.error("❌ Document verification failed")
            return False
        
    finally:
        # Cleanup
        try:
            manager.close_connection()
            os.unlink(db_path)
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


def test_schema_info():
    """Test schema information"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        manager = UnifiedDatabaseManager(logger=logger, use_docker=False)
        success = manager.initialize(db_path)
        
        if not success:
            logger.error("Failed to initialize database manager")
            return False
        
        # Check table schemas
        logger.info("Checking table schemas...")
        
        # Check estimates table schema
        estimates_schema = manager.execute_query("PRAGMA table_info(estimates)")
        logger.info("Estimates table schema:")
        for column in estimates_schema:
            logger.info(f"  {column['name']}: {column['type']} (NOT NULL: {column['notnull']}, DEFAULT: {column['dflt_value']})")
        
        # Check daily_reports table schema
        daily_reports_schema = manager.execute_query("PRAGMA table_info(daily_reports)")
        logger.info("Daily reports table schema:")
        for column in daily_reports_schema:
            logger.info(f"  {column['name']}: {column['type']} (NOT NULL: {column['notnull']}, DEFAULT: {column['dflt_value']})")
        
        # Check timesheets table schema
        timesheets_schema = manager.execute_query("PRAGMA table_info(timesheets)")
        logger.info("Timesheets table schema:")
        for column in timesheets_schema:
            logger.info(f"  {column['name']}: {column['type']} (NOT NULL: {column['notnull']}, DEFAULT: {column['dflt_value']})")
        
        return True
        
    finally:
        try:
            manager.close_connection()
            os.unlink(db_path)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


if __name__ == '__main__':
    print("Testing Unified Database Manager...")
    print("=" * 50)
    
    print("\n1. Testing schema information...")
    schema_success = test_schema_info()
    
    print("\n2. Testing document creation...")
    creation_success = test_document_creation()
    
    print("\n" + "=" * 50)
    if schema_success and creation_success:
        print("✅ All tests PASSED")
        sys.exit(0)
    else:
        print("❌ Some tests FAILED")
        sys.exit(1)
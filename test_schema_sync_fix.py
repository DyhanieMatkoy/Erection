#!/usr/bin/env python3
"""Test Schema Synchronization Fix

This script tests the schema synchronization fix for document creation.
"""

import os
import sys
import logging
import tempfile
import uuid
import sqlite3
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.schema_synchronizer import SchemaSynchronizer
from src.data.database_manager import DatabaseManager


def test_document_creation_with_schema_sync():
    """Test document creation after schema synchronization"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        logger.info(f"Testing schema sync and document creation with: {db_path}")
        
        # Step 1: Apply schema synchronization (this will also initialize the database)
        synchronizer = SchemaSynchronizer(logger)
        sync_success = synchronizer.synchronize_schema(db_path, force=True)
        
        if not sync_success:
            logger.error("Schema synchronization failed")
            return False
        
        logger.info("✅ Schema synchronization completed")
        
        # Step 2: Initialize database manager WITHOUT reinitializing the database
        # The schema synchronizer already initialized it properly
        db_manager = DatabaseManager()
        # Don't call initialize() again as it would recreate tables
        # Just set up the connection to the existing database
        db_manager._connection = sqlite3.connect(db_path)
        db_manager._connection.row_factory = sqlite3.Row
        
        logger.info("✅ Database manager connected to existing database")
        
        # Step 3: Test document creation
        logger.info("Testing document creation...")
        
        # Test estimate creation
        try:
            estimate_id = db_manager.execute_update(
                """INSERT INTO estimates (uuid, number, date, estimate_type, marked_for_deletion) 
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), "TEST-EST-001", date.today(), "General", 0)
            )
            logger.info(f"✅ Estimate created successfully with ID: {estimate_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create estimate: {e}")
            return False
        
        # Test daily report creation
        try:
            report_id = db_manager.execute_update(
                """INSERT INTO daily_reports (uuid, date, marked_for_deletion) 
                   VALUES (?, ?, ?)""",
                (str(uuid.uuid4()), date.today(), 0)
            )
            logger.info(f"✅ Daily report created successfully with ID: {report_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create daily report: {e}")
            return False
        
        # Test timesheet creation
        try:
            timesheet_id = db_manager.execute_update(
                """INSERT INTO timesheets (uuid, number, date, month_year, marked_for_deletion) 
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), "TEST-TS-001", date.today(), "2026-01", 0)
            )
            logger.info(f"✅ Timesheet created successfully with ID: {timesheet_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create timesheet: {e}")
            return False
        
        # Step 4: Verify documents exist
        logger.info("Verifying documents exist...")
        
        estimates = db_manager.execute_query("SELECT * FROM estimates")
        daily_reports = db_manager.execute_query("SELECT * FROM daily_reports")
        timesheets = db_manager.execute_query("SELECT * FROM timesheets")
        
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
            if 'db_manager' in locals():
                db_manager.close_connection()
            os.unlink(db_path)
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


def test_schema_check():
    """Test schema checking functionality"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        logger.info("Testing schema check functionality...")
        
        synchronizer = SchemaSynchronizer(logger)
        
        # Check schema on non-existent database
        schema_info = synchronizer.check_schema_version(db_path)
        logger.info(f"Schema info for new database: needs_update={schema_info.get('needs_update', True)}")
        
        # Synchronize schema
        sync_success = synchronizer.synchronize_schema(db_path)
        if not sync_success:
            logger.error("Schema synchronization failed")
            return False
        
        # Check schema after synchronization
        schema_info = synchronizer.check_schema_version(db_path)
        logger.info(f"Schema info after sync: needs_update={schema_info.get('needs_update', True)}")
        logger.info(f"Schema version: {schema_info.get('schema_version', 'unknown')}")
        logger.info(f"Tables count: {schema_info.get('tables_count', 0)}")
        
        if not schema_info.get('needs_update', True):
            logger.info("✅ Schema check passed")
            return True
        else:
            logger.error("❌ Schema still needs update after synchronization")
            return False
        
    finally:
        try:
            os.unlink(db_path)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


if __name__ == '__main__':
    print("Testing Schema Synchronization Fix...")
    print("=" * 50)
    
    print("\n1. Testing schema check functionality...")
    schema_check_success = test_schema_check()
    
    print("\n2. Testing document creation with schema sync...")
    creation_success = test_document_creation_with_schema_sync()
    
    print("\n" + "=" * 50)
    if schema_check_success and creation_success:
        print("✅ All tests PASSED")
        sys.exit(0)
    else:
        print("❌ Some tests FAILED")
        sys.exit(1)
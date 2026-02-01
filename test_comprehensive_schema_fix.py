#!/usr/bin/env python3
"""Test Comprehensive Schema Fix

This script tests that ALL required fields (UUID, updated_at, is_deleted) are properly added
to ALL tables and that document creation works correctly.
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

from unified_database_manager import UnifiedDatabaseManager


def test_comprehensive_document_creation():
    """Test document creation with comprehensive schema including ALL required fields"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        logger.info(f"Testing comprehensive schema with: {db_path}")
        
        # Step 1: Initialize database with Unified Database Manager
        db_manager = UnifiedDatabaseManager(logger)
        success = db_manager.initialize(db_path)
        
        if not success:
            logger.error("Database initialization failed")
            return False
        
        logger.info("✅ Database initialized with Unified Database Manager")
        
        # Step 2: Verify that ALL tables have required fields
        logger.info("Verifying ALL tables have UUID, updated_at, is_deleted fields...")
        
        required_fields = ['uuid', 'updated_at', 'is_deleted']
        tables_to_check = [
            'users', 'persons', 'organizations', 'counterparties', 'objects', 'works',
            'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines', 
            'timesheets', 'timesheet_lines', 'materials', 'units', 'cost_items',
            'work_execution_register', 'payroll_register', 'cost_item_materials',
            'work_specifications', 'audit_logs'
        ]
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        missing_fields_report = {}
        
        for table_name in tables_to_check:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor.fetchone():
                    logger.warning(f"Table {table_name} does not exist")
                    continue
                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                missing_fields = []
                for field in required_fields:
                    if field not in columns:
                        missing_fields.append(field)
                
                if missing_fields:
                    missing_fields_report[table_name] = missing_fields
                    logger.warning(f"❌ Table {table_name} missing fields: {missing_fields}")
                else:
                    logger.info(f"✅ Table {table_name} has all required fields")
                    
            except Exception as e:
                logger.error(f"Failed to check table {table_name}: {e}")
        
        conn.close()
        
        if missing_fields_report:
            logger.error(f"❌ {len(missing_fields_report)} tables missing required fields")
            for table, fields in missing_fields_report.items():
                logger.error(f"  {table}: {fields}")
            return False
        else:
            logger.info(f"✅ All {len(tables_to_check)} tables have required synchronization fields")
        
        # Step 3: Test document creation with ALL required fields
        logger.info("Testing document creation with ALL required fields...")
        
        # Test estimate creation
        try:
            estimate_id = db_manager.execute_update(
                """INSERT INTO estimates (uuid, number, date, estimate_type, marked_for_deletion, updated_at, is_deleted) 
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (str(uuid.uuid4()), "TEST-EST-001", date.today(), "General", 0, 0)
            )
            logger.info(f"✅ Estimate created successfully with ID: {estimate_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create estimate: {e}")
            return False
        
        # Test daily report creation
        try:
            report_id = db_manager.execute_update(
                """INSERT INTO daily_reports (uuid, date, marked_for_deletion, updated_at, is_deleted) 
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (str(uuid.uuid4()), date.today(), 0, 0)
            )
            logger.info(f"✅ Daily report created successfully with ID: {report_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create daily report: {e}")
            return False
        
        # Test timesheet creation
        try:
            timesheet_id = db_manager.execute_update(
                """INSERT INTO timesheets (uuid, number, date, month_year, marked_for_deletion, updated_at, is_deleted) 
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (str(uuid.uuid4()), "TEST-TS-001", date.today(), "2026-01", 0, 0)
            )
            logger.info(f"✅ Timesheet created successfully with ID: {timesheet_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create timesheet: {e}")
            return False
        
        # Test reference data creation
        try:
            person_id = db_manager.execute_update(
                """INSERT INTO persons (uuid, full_name, marked_for_deletion, updated_at, is_deleted) 
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (str(uuid.uuid4()), "Test Person", 0, 0)
            )
            logger.info(f"✅ Person created successfully with ID: {person_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create person: {e}")
            return False
        
        # Step 4: Verify documents exist and have correct fields
        logger.info("Verifying created documents...")
        
        estimates = db_manager.execute_query("SELECT id, uuid, updated_at, is_deleted FROM estimates")
        daily_reports = db_manager.execute_query("SELECT id, uuid, updated_at, is_deleted FROM daily_reports")
        timesheets = db_manager.execute_query("SELECT id, uuid, updated_at, is_deleted FROM timesheets")
        persons = db_manager.execute_query("SELECT id, uuid, updated_at, is_deleted FROM persons WHERE full_name = 'Test Person'")
        
        logger.info(f"Found {len(estimates)} estimates, {len(daily_reports)} daily reports, {len(timesheets)} timesheets, {len(persons)} persons")
        
        # Verify all documents have UUIDs and sync fields
        all_docs = [
            ("estimates", estimates),
            ("daily_reports", daily_reports), 
            ("timesheets", timesheets),
            ("persons", persons)
        ]
        
        for doc_type, docs in all_docs:
            for doc in docs:
                if not doc[1]:  # uuid
                    logger.error(f"❌ {doc_type} document {doc[0]} missing UUID")
                    return False
                if not doc[2]:  # updated_at
                    logger.error(f"❌ {doc_type} document {doc[0]} missing updated_at")
                    return False
                if doc[3] is None:  # is_deleted
                    logger.error(f"❌ {doc_type} document {doc[0]} missing is_deleted")
                    return False
        
        logger.info("✅ All documents have required synchronization fields")
        
        if len(estimates) > 0 and len(daily_reports) > 0 and len(timesheets) > 0 and len(persons) > 0:
            logger.info("✅ ALL document types created and verified successfully")
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


if __name__ == '__main__':
    print("Testing Comprehensive Schema Fix...")
    print("=" * 60)
    
    success = test_comprehensive_document_creation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Comprehensive schema fix successful!")
        print("✅ ALL tables have UUID, updated_at, is_deleted fields")
        print("✅ ALL document types create successfully")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Schema fix incomplete")
        sys.exit(1)
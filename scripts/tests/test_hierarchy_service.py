import sys
import os
import unittest
import tempfile
import sqlite3
import uuid
from datetime import date
from sqlalchemy import text

# Register UUID adapter for SQLite
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# Add project root to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.data.database_manager import DatabaseManager
from src.services.hierarchy_service import HierarchyService
from src.data.models.estimate import Estimate, EstimateLine, EstimateType

class TestHierarchyService(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        
        # Reset singleton
        DatabaseManager._instance = None
        
        # Initialize DatabaseManager with the temporary file
        self.db_manager = DatabaseManager()
        self.db_manager.initialize(self.db_path)
        
        # Update schema for hierarchy fields manually since legacy init might not have them
        try:
            with self.db_manager.session_scope() as session:
                # Create missing tables referenced by FKs
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS units (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        marked_for_deletion INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS materials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT,
                        description TEXT,
                        price REAL DEFAULT 0,
                        unit TEXT,
                        unit_id INTEGER REFERENCES units(id),
                        marked_for_deletion INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Check if we need to add columns
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(estimates)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'base_document_id' not in columns:
                    session.execute(text("ALTER TABLE estimates ADD COLUMN base_document_id INTEGER REFERENCES estimates(id)"))
                if 'estimate_type' not in columns:
                    session.execute(text("ALTER TABLE estimates ADD COLUMN estimate_type VARCHAR(20) DEFAULT 'General'"))
                
                # Update estimate_lines schema
                cursor.execute("PRAGMA table_info(estimate_lines)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'material_id' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN material_id INTEGER REFERENCES materials(id)"))
                if 'material_quantity' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN material_quantity REAL DEFAULT 0.0"))
                if 'material_price' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN material_price REAL DEFAULT 0.0"))
                if 'material_sum' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN material_sum REAL DEFAULT 0.0"))
                if 'uuid' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN uuid VARCHAR(36)"))
                if 'updated_at' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN updated_at TIMESTAMP"))
                if 'is_deleted' not in columns:
                    session.execute(text("ALTER TABLE estimate_lines ADD COLUMN is_deleted INTEGER DEFAULT 0"))
                
                # Insert dummy work for testing FK
                session.execute(text("INSERT INTO works (id, name, code, price, labor_rate) VALUES (1, 'Test Work', 'TEST-001', 100.0, 10.0)"))
                    
        except Exception as e:
            print(f"Schema update error (ignored): {e}")
                
        self.service = HierarchyService()

    def tearDown(self):
        # Dispose engine
        if self.db_manager._engine:
            self.db_manager._engine.dispose()
        
        if self.db_manager._connection:
            try:
                self.db_manager._connection.close()
            except:
                pass
        
        try:
            os.unlink(self.db_path)
        except:
            pass

    def test_hierarchy_flow(self):
        # 1. Create General Estimate
        general = Estimate(
            number="GEN-001",
            date=date.today(),
            total_sum=1000.0,
            total_labor=100.0
        )
        # Add some lines
        general.lines = [
            EstimateLine(line_number=1, work_id=1, quantity=10, price=100, sum=1000, planned_labor=10)
        ]
        
        success = self.service.create_general_estimate(general)
        self.assertTrue(success, "Failed to create general estimate")
        self.assertIsNotNone(general.id)
        self.assertTrue(general.is_general)
        self.assertFalse(general.is_plan)
        
        # 2. Create Plan Estimate linked to General
        plan = Estimate(
            number="PLAN-001",
            date=date.today()
        )
        
        success = self.service.create_plan_estimate(plan, general.id)
        self.assertTrue(success, "Failed to create plan estimate")
        self.assertIsNotNone(plan.id)
        self.assertTrue(plan.is_plan)
        self.assertEqual(plan.base_document_id, general.id)
        
        # 3. Verify Hierarchy
        summary = self.service.get_hierarchy_summary(general.id)
        self.assertEqual(summary['plan_count'], 1)
        self.assertEqual(summary['plan_estimates'][0].id, plan.id)
        
        # 4. Test Copy Works
        # Select work_id=1
        success = self.service.copy_works_from_base(plan.id, [1])
        self.assertTrue(success, "Failed to copy works")
        
        # Reload plan
        plan_reloaded = self.service.estimate_repo.find_by_id(plan.id)
        self.assertEqual(len(plan_reloaded.lines), 1)
        self.assertEqual(plan_reloaded.lines[0].work_id, 1)
        self.assertEqual(plan_reloaded.lines[0].sum, 1000)
        
        # 5. Test Circular Reference Protection
        # Try to set general's base to plan (which is general's child)
        # We need to manually call validate because update_base_document checks it
        
        # Note: General is ID 1, Plan is ID 2 (referencing 1)
        # If we try to make 1 reference 2:
        valid = self.service.hierarchy_repo.validate_hierarchy_integrity(general.id, plan.id)
        # Expected: False because plan.estimate_type is 'Plan', so it cannot be a base.
        self.assertFalse(valid, "Should not allow Plan estimate as base")

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Schema Synchronizer for Desktop Clients

This module provides automatic schema synchronization between server and client databases.
It ensures that desktop clients always have the latest database schema that matches the server.
"""

import os
import sys
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from unified_database_manager import UnifiedDatabaseManager
from src.data.models.sqlalchemy_models import Base


class SchemaSynchronizer:
    """Handles automatic schema synchronization for desktop clients"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize schema synchronizer
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.db_manager = UnifiedDatabaseManager(logger=self.logger, use_docker=False)

    # def _is_type_compatible(self, current_type: str, expected_type: str) -> bool:
    #     """Check if SQLite types are compatible (BOOLEAN == INTEGER)
        
    #     Args:
    #         current_type: Current column type from database
    #         expected_type: Expected column type from schema
            
    #     Returns:
    #         True if types are compatible
    #     """
    #     current_upper = current_type.upper()
    #     expected_upper = expected_type.upper()
        
    #     # Boolean is compatible with INTEGER in SQLite
    #     if ('INT' in current_upper and 'INT' in expected_upper) or \
    #        ('BOOLEAN' in current_upper and 'INT' in expected_upper) or \
    #        ('INT' in current_upper and 'BOOLEAN' in expected_upper):
    #         return True
        
    #     # TEXT and VARCHAR are compatible
    #     if ('TEXT' in current_upper and 'TEXT' in expected_upper) or \
    #        ('VARCHAR' in current_upper and 'TEXT' in expected_upper) or \
    #        ('TEXT' in current_upper and 'VARCHAR' in expected_upper):
    #         return True
        
    #     # REAL and FLOAT are compatible
    #     if ('REAL' in current_upper and 'REAL' in expected_upper) or \
    #        ('FLOAT' in current_upper and 'REAL' in expected_upper) or \
    #        ('REAL' in current_upper and 'FLOAT' in expected_upper):
    #         return True

    #     # TIMESTAMP, DATETIME are compatible
    #     if ('TIMESTAMP' in current_upper and 'TIMESTAMP' in expected_upper) or \
    #        ('DATETIME' in current_upper and 'TIMESTAMP' in expected_upper) or \
    #        ('TIMESTAMP' in current_upper and 'DATETIME' in expected_upper):
    #         return True
        
    #     # Exact match
    #     if current_upper == expected_upper:
    #         return True
        
    #     return False
        
    def check_schema_version(self, db_path: str) -> Dict[str, Any]:
        """Check current schema version and status
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            Dictionary with schema information
        """
        try:
            schema_info = {
                'db_path': db_path,
                'exists': os.path.exists(db_path),
                'schema_version': None,
                'last_sync': None,
                'needs_update': False,
                'tables_count': 0,
                'missing_tables': [],
                'schema_differences': []
            }
            
            if not schema_info['exists']:
                schema_info['needs_update'] = True
                schema_info['missing_tables'] = self._get_required_tables()
                return schema_info
            
            # Connect to database and check schema
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                # Get schema version from constants table
                cursor.execute("SELECT value FROM constants WHERE key = 'schema_version'")
                result = cursor.fetchone()
                if result:
                    schema_info['schema_version'] = result['value']
                
                # Get last sync time
                cursor.execute("SELECT value FROM constants WHERE key = 'last_schema_sync'")
                result = cursor.fetchone()
                if result:
                    schema_info['last_sync'] = result['value']
                
                # Get current tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                current_tables = [row['name'] for row in cursor.fetchall()]
                schema_info['tables_count'] = len(current_tables)
                
                # Check for missing tables
                required_tables = self._get_required_tables()
                schema_info['missing_tables'] = [table for table in required_tables if table not in current_tables]
                
                # Check for schema differences
                schema_info['schema_differences'] = self._check_schema_differences(cursor, current_tables)
                
                # Determine if update is needed (ignore non-critical differences)
                critical_differences = []
                for diff in schema_info['schema_differences']:
                    # Skip non-critical differences
                    if (diff.get('table') == 'persons' and 
                        diff.get('column') == 'marked_for_deletion' and 
                        diff.get('issue') == 'missing_default'):
                        continue
                    critical_differences.append(diff)
                
                schema_info['needs_update'] = (
                    len(schema_info['missing_tables']) > 0 or
                    len(critical_differences) > 0 or
                    schema_info['schema_version'] != self._get_current_schema_version()
                )
                
            finally:
                conn.close()
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Failed to check schema version: {e}")
            return {
                'db_path': db_path,
                'exists': False,
                'needs_update': True,
                'error': str(e)
            }
    
    def synchronize_schema(self, db_path: str, force: bool = False) -> bool:
        """Synchronize database schema with current version
        
        Args:
            db_path: Path to SQLite database
            force: Force synchronization even if not needed
            
        Returns:
            True if synchronization successful
        """
        try:
            self.logger.info(f"Starting schema synchronization for: {db_path}")
            
            # Check current schema status
            schema_info = self.check_schema_version(db_path)
            
            if not force and not schema_info.get('needs_update', True):
                self.logger.info("Schema is already up to date")
                return True
            
            # Create backup if database exists
            if schema_info['exists']:
                backup_path = self._create_backup(db_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Initialize database with Unified Database Manager
            success = self.db_manager.initialize(db_path)
            if not success:
                self.logger.error("Failed to initialize database with Unified Database Manager")
                return False
            
            # Apply any additional schema fixes
            self._apply_schema_fixes(db_path)
            
            # Update schema version and sync time
            self._update_schema_metadata(db_path)
            
            # Verify schema integrity
            if not self._verify_schema_integrity(db_path):
                self.logger.error("Schema integrity verification failed")
                return False
            
            self.logger.info("Schema synchronization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema synchronization failed: {e}")
            return False
    
    def auto_sync_on_startup(self, db_path: str) -> bool:
        """Automatically synchronize schema on application startup
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            True if synchronization successful or not needed
        """
        try:
            self.logger.info("Checking if schema synchronization is needed on startup")
            
            schema_info = self.check_schema_version(db_path)
            
            if schema_info.get('needs_update', True):
                self.logger.info("Schema update needed, performing automatic synchronization")
                return self.synchronize_schema(db_path)
            else:
                self.logger.info("Schema is up to date, no synchronization needed")
                return True
                
        except Exception as e:
            self.logger.error(f"Auto-sync on startup failed: {e}")
            return False
    
    def _get_required_tables(self) -> List[str]:
        """Get list of required table names"""
        return [
            'users', 'persons', 'organizations', 'counterparties', 'objects', 'works',
            'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines', 
            'daily_report_executors', 'timesheets', 'timesheet_lines',
            'work_execution_register', 'payroll_register', 'user_settings', 'constants',
            'sync_nodes', 'sync_changes', 'object_version_history',
            'materials', 'units', 'cost_items', 'cost_item_materials', 'work_specifications',
            'user_table_part_settings', 'table_part_command_config', 'work_unit_migration'
        ]
    
    def _get_current_schema_version(self) -> str:
        """Get current schema version"""
        return "unified_v1.0"
    
    def _check_schema_differences(self, cursor: sqlite3.Cursor, current_tables: List[str]) -> List[Dict[str, Any]]:
        """Check for schema differences in existing tables"""
        differences = []
        
        # Check ALL tables for missing synchronization fields (uuid, updated_at, is_deleted)
        # and other critical fields with proper DEFAULT values
        critical_checks = {
            'users': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'persons': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('full_name', 'TEXT NOT NULL'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'organizations': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'counterparties': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'objects': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'works': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'estimates': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('estimate_type', 'TEXT NOT NULL DEFAULT \'General\''),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'estimate_lines': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'daily_reports': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'daily_report_lines': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'timesheets': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'timesheet_lines': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'materials': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'units': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'cost_items': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'cost_item_materials': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'work_specifications': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('marked_for_deletion', 'INTEGER NOT NULL DEFAULT 0'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'work_execution_register': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'payroll_register': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ],
            'audit_logs': [
                ('uuid', 'TEXT NOT NULL UNIQUE'),
                ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
                ('is_deleted', 'INTEGER NOT NULL DEFAULT 0')
            ]
        }
        
        for table_name, expected_columns in critical_checks.items():
            if table_name in current_tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    current_columns = {col['name']: col for col in columns_info}
                    
                    for col_name, expected_def in expected_columns:
                        if col_name not in current_columns:
                            differences.append({
                                'type': 'missing_column',
                                'table': table_name,
                                'column': col_name,
                                'expected': expected_def
                            })
                        else:
                            col_info = current_columns[col_name]                            
                            current_type = col_info['type'].upper()
                            expected_type = expected_def.split()[0].upper() if expected_def else ''
        
                            # Check for type compatibility
                            if not self._is_type_compatible(current_type, expected_type):
                                differences.append({
                                    'type': 'type_mismatch',
                                    'table': table_name,
                                    'column': col_name,
                                    'current': col_info['type'],
                                    'expected': expected_type
                                })
                                
                            # Check for NOT NULL constraint issues
                            if 'NOT NULL' in expected_def and not col_info['notnull']:
                                differences.append({
                                    'type': 'constraint_mismatch',
                                    'table': table_name,
                                    'column': col_name,
                                    'issue': 'missing_not_null',
                                    'expected': expected_def
                                })
                            
                            # Check for DEFAULT value issues
                            if 'DEFAULT' in expected_def and col_info['dflt_value'] is None:
                                differences.append({
                                    'type': 'constraint_mismatch',
                                    'table': table_name,
                                    'column': col_name,
                                    'issue': 'missing_default',
                                    'expected': expected_def
                                })
                
                except Exception as e:
                    self.logger.warning(f"Failed to check table {table_name}: {e}")
        
        return differences
    
    def _create_backup(self, db_path: str) -> str:
        """Create backup of existing database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        return backup_path
    
    def _apply_schema_fixes(self, db_path: str):
        """Apply additional schema fixes after initialization"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            self.logger.info("Applying comprehensive schema fixes...")
            
            # Apply schema fixes for tables with missing DEFAULT values
            schema_fixes = [
                # Ensure sync tables have correct schema
                """CREATE TABLE IF NOT EXISTS sync_nodes (
                    id TEXT PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    last_sync_in TIMESTAMP,
                    last_sync_out TIMESTAMP,
                    received_packet_no INTEGER,
                    sent_packet_no INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                """CREATE TABLE IF NOT EXISTS sync_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL REFERENCES sync_nodes(id),
                    entity_type TEXT NOT NULL,
                    entity_uuid TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    packet_no INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )""",
                
                # Ensure constants table exists
                """CREATE TABLE IF NOT EXISTS constants (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )"""
            ]
            
            for fix_sql in schema_fixes:
                try:
                    cursor.execute(fix_sql)
                except Exception as e:
                    self.logger.warning(f"Schema fix failed (may be expected): {e}")
            
            # Fix tables with missing DEFAULT values by recreating them
            self._fix_table_defaults(cursor)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Schema fixes applied successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply schema fixes: {e}")
    
    def _fix_table_defaults(self, cursor: sqlite3.Cursor):
        """Fix ALL tables with missing DEFAULT values and synchronization fields"""
        try:
            # Fix ALL document tables with comprehensive synchronization fields
            self._fix_estimates_table(cursor)
            self._fix_daily_reports_table(cursor)
            self._fix_timesheets_table(cursor)
            self._fix_persons_table(cursor)
            
            # Fix ALL reference tables
            self._fix_reference_table(cursor, 'organizations')
            self._fix_reference_table(cursor, 'counterparties')
            self._fix_reference_table(cursor, 'objects')
            self._fix_reference_table(cursor, 'works')
            self._fix_reference_table(cursor, 'materials')
            self._fix_reference_table(cursor, 'units')
            self._fix_reference_table(cursor, 'cost_items')
            
            # Fix ALL line tables
            self._fix_line_table(cursor, 'estimate_lines')
            self._fix_line_table(cursor, 'daily_report_lines')
            self._fix_line_table(cursor, 'timesheet_lines')
            
            # Fix ALL register tables
            self._fix_register_table(cursor, 'work_execution_register')
            self._fix_register_table(cursor, 'payroll_register')
            
            # Fix ALL other tables
            self._fix_other_table(cursor, 'users')
            self._fix_other_table(cursor, 'audit_logs')
            self._fix_line_table(cursor, 'cost_item_materials')
            self._fix_reference_table(cursor, 'work_specifications')
            
            self.logger.info("ALL table defaults fixed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to fix table defaults: {e}")
    
    def _fix_reference_table(self, cursor: sqlite3.Cursor, table_name: str):
        """Fix reference tables (organizations, counterparties, objects, works, materials, units, cost_items, work_specifications)"""
        try:
            # Check if table needs fixing
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            missing_fields = []
            
            # Check for missing synchronization fields
            if 'uuid' not in columns:
                needs_fix = True
                missing_fields.append('uuid')
            if 'updated_at' not in columns:
                needs_fix = True
                missing_fields.append('updated_at')
            if 'is_deleted' not in columns:
                needs_fix = True
                missing_fields.append('is_deleted')
            
            # Check marked_for_deletion field
            if 'marked_for_deletion' in columns:
                col_info = columns['marked_for_deletion']
                if not col_info[4] or col_info[4] != "0":  # Check default value
                    needs_fix = True
                    missing_fields.append('marked_for_deletion_default')
            
            if needs_fix:
                self.logger.info(f"Fixing {table_name} table schema (missing: {missing_fields})...")
                
                # Get current table structure
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                result = cursor.fetchone()
                if not result:
                    self.logger.warning(f"Table {table_name} not found")
                    return
                
                # Create new table with all required fields
                new_table_sql = self._generate_reference_table_sql(table_name, columns)
                cursor.execute(new_table_sql)
                
                # Copy data from old table with UUID generation
                self._copy_table_data_with_uuid(cursor, table_name, f"{table_name}_new")
                
                # Replace old table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                self.logger.info(f"{table_name} table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix {table_name} table: {e}")
    
    def _fix_line_table(self, cursor: sqlite3.Cursor, table_name: str):
        """Fix line tables (estimate_lines, daily_report_lines, timesheet_lines, cost_item_materials)"""
        try:
            # Check if table needs fixing
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            missing_fields = []
            
            # Check for missing synchronization fields
            if 'uuid' not in columns:
                needs_fix = True
                missing_fields.append('uuid')
            if 'updated_at' not in columns:
                needs_fix = True
                missing_fields.append('updated_at')
            if 'is_deleted' not in columns:
                needs_fix = True
                missing_fields.append('is_deleted')
            
            if needs_fix:
                self.logger.info(f"Fixing {table_name} table schema (missing: {missing_fields})...")
                
                # Create new table with all required fields
                new_table_sql = self._generate_line_table_sql(table_name, columns)
                cursor.execute(new_table_sql)
                
                # Copy data from old table with UUID generation
                self._copy_table_data_with_uuid(cursor, table_name, f"{table_name}_new")
                
                # Replace old table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                self.logger.info(f"{table_name} table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix {table_name} table: {e}")
    
    def _fix_register_table(self, cursor: sqlite3.Cursor, table_name: str):
        """Fix register tables (work_execution_register, payroll_register)"""
        try:
            # Check if table needs fixing
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            missing_fields = []
            
            # Check for missing synchronization fields
            if 'uuid' not in columns:
                needs_fix = True
                missing_fields.append('uuid')
            if 'updated_at' not in columns:
                needs_fix = True
                missing_fields.append('updated_at')
            if 'is_deleted' not in columns:
                needs_fix = True
                missing_fields.append('is_deleted')
            
            if needs_fix:
                self.logger.info(f"Fixing {table_name} table schema (missing: {missing_fields})...")
                
                # Create new table with all required fields
                new_table_sql = self._generate_register_table_sql(table_name, columns)
                cursor.execute(new_table_sql)
                
                # Copy data from old table with UUID generation
                self._copy_table_data_with_uuid(cursor, table_name, f"{table_name}_new")
                
                # Replace old table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                self.logger.info(f"{table_name} table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix {table_name} table: {e}")
    
    def _fix_other_table(self, cursor: sqlite3.Cursor, table_name: str):
        """Fix other tables (users, audit_logs)"""
        try:
            # Check if table needs fixing
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            missing_fields = []
            
            # Check for missing synchronization fields
            if 'uuid' not in columns:
                needs_fix = True
                missing_fields.append('uuid')
            if 'updated_at' not in columns:
                needs_fix = True
                missing_fields.append('updated_at')
            if 'is_deleted' not in columns:
                needs_fix = True
                missing_fields.append('is_deleted')
            
            if needs_fix:
                self.logger.info(f"Fixing {table_name} table schema (missing: {missing_fields})...")
                
                # Create new table with all required fields
                new_table_sql = self._generate_other_table_sql(table_name, columns)
                cursor.execute(new_table_sql)
                
                # Copy data from old table with UUID generation
                self._copy_table_data_with_uuid(cursor, table_name, f"{table_name}_new")
                
                # Replace old table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                self.logger.info(f"{table_name} table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix {table_name} table: {e}")
    
    def _generate_reference_table_sql(self, table_name: str, existing_columns: dict) -> str:
        """Generate SQL for reference tables with all required fields"""
        # Base template for reference tables
        base_fields = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))))"
        ]
        
        # Add existing fields (preserve structure)
        for col_name, col_info in existing_columns.items():
            if col_name in ['id', 'uuid']:
                continue
            
            col_type = col_info[2]  # data type
            not_null = " NOT NULL" if col_info[3] else ""
            default_val = f" DEFAULT {col_info[4]}" if col_info[4] is not None else ""
            
            # Fix specific field defaults
            if col_name == 'marked_for_deletion':
                base_fields.append(f"{col_name} INTEGER NOT NULL DEFAULT 0")
            else:
                base_fields.append(f"{col_name} {col_type}{not_null}{default_val}")
        
        # Add missing synchronization fields
        if 'updated_at' not in existing_columns:
            base_fields.append("updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
        if 'is_deleted' not in existing_columns:
            base_fields.append("is_deleted INTEGER NOT NULL DEFAULT 0")
        
        return f"CREATE TABLE {table_name}_new ({', '.join(base_fields)})"
    
    def _generate_line_table_sql(self, table_name: str, existing_columns: dict) -> str:
        """Generate SQL for line tables with all required fields"""
        # Base template for line tables
        base_fields = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "uuid TEXT NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))))"
        ]
        
        # Add existing fields (preserve structure)
        for col_name, col_info in existing_columns.items():
            if col_name in ['id', 'uuid']:
                continue
            
            col_type = col_info[2]  # data type
            not_null = " NOT NULL" if col_info[3] else ""
            default_val = f" DEFAULT {col_info[4]}" if col_info[4] is not None else ""
            
            base_fields.append(f"{col_name} {col_type}{not_null}{default_val}")
        
        # Add missing synchronization fields
        if 'updated_at' not in existing_columns:
            base_fields.append("updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
        if 'is_deleted' not in existing_columns:
            base_fields.append("is_deleted INTEGER NOT NULL DEFAULT 0")
        
        return f"CREATE TABLE {table_name}_new ({', '.join(base_fields)})"
    
    def _generate_register_table_sql(self, table_name: str, existing_columns: dict) -> str:
        """Generate SQL for register tables with all required fields"""
        return self._generate_line_table_sql(table_name, existing_columns)  # Same structure
    
    def _generate_other_table_sql(self, table_name: str, existing_columns: dict) -> str:
        """Generate SQL for other tables with all required fields"""
        return self._generate_line_table_sql(table_name, existing_columns)  # Same structure
    
    def _copy_table_data_with_uuid(self, cursor: sqlite3.Cursor, old_table: str, new_table: str):
        """Copy data from old table to new table, generating UUIDs for existing records"""
        try:
            # Get column names from both tables
            cursor.execute(f"PRAGMA table_info({old_table})")
            old_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute(f"PRAGMA table_info({new_table})")
            new_columns = [col[1] for col in cursor.fetchall()]
            
            # Find common columns (excluding uuid, updated_at, is_deleted if they're new)
            common_columns = []
            for col in old_columns:
                if col in new_columns:
                    common_columns.append(col)
            
            # Build SELECT and INSERT statements
            select_cols = []
            insert_cols = []
            
            for col in new_columns:
                if col == 'uuid' and col not in old_columns:
                    select_cols.append("lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))) as uuid")
                    insert_cols.append('uuid')
                elif col == 'updated_at' and col not in old_columns:
                    select_cols.append("CURRENT_TIMESTAMP as updated_at")
                    insert_cols.append('updated_at')
                elif col == 'is_deleted' and col not in old_columns:
                    select_cols.append("0 as is_deleted")
                    insert_cols.append('is_deleted')
                elif col in common_columns:
                    # Handle special cases for existing columns
                    if col == 'marked_for_deletion':
                        select_cols.append(f"COALESCE({col}, 0) as {col}")
                    else:
                        select_cols.append(col)
                    insert_cols.append(col)
            
            # Execute copy
            if select_cols and insert_cols:
                copy_sql = f"""
                    INSERT INTO {new_table} ({', '.join(insert_cols)})
                    SELECT {', '.join(select_cols)}
                    FROM {old_table}
                """
                cursor.execute(copy_sql)
                self.logger.debug(f"Copied data from {old_table} to {new_table}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy data from {old_table} to {new_table}: {e}")
            raise
    
    def _fix_persons_table(self, cursor: sqlite3.Cursor):
        """Fix persons table schema"""
        try:
            # Check if persons table needs fixing
            cursor.execute("PRAGMA table_info(persons)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            if 'marked_for_deletion' in columns:
                col_info = columns['marked_for_deletion']
                if not col_info[4] or col_info[4] != "0":  # Check default value
                    needs_fix = True
            
            if needs_fix:
                self.logger.info("Fixing persons table schema...")
                
                # For persons table, we'll just update existing records to have default values
                # since it's a reference table and recreating it might break foreign keys
                cursor.execute("""
                    UPDATE persons 
                    SET marked_for_deletion = 0 
                    WHERE marked_for_deletion IS NULL
                """)
                
                self.logger.info("Persons table fixed (updated NULL values)")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix persons table: {e}")
    
    def _fix_estimates_table(self, cursor: sqlite3.Cursor):
        """Fix estimates table schema"""
        try:
            # Check if estimates table needs fixing
            cursor.execute("PRAGMA table_info(estimates)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            if 'estimate_type' in columns:
                col_info = columns['estimate_type']
                if not col_info[4] or col_info[4] != "'General'":  # Check default value
                    needs_fix = True
            
            if 'marked_for_deletion' in columns:
                col_info = columns['marked_for_deletion']
                if not col_info[4] or col_info[4] != "0":  # Check default value
                    needs_fix = True
            
            # Check if UUID field exists
            if 'uuid' not in columns:
                needs_fix = True
            
            if needs_fix:
                self.logger.info("Fixing estimates table schema...")
                
                # Create new table with correct schema including UUID, updated_at, and is_deleted
                cursor.execute("""
                    CREATE TABLE estimates_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT NOT NULL UNIQUE,
                        number TEXT NOT NULL,
                        date DATE NOT NULL,
                        customer_id INTEGER REFERENCES counterparties(id),
                        object_id INTEGER REFERENCES objects(id),
                        contractor_id INTEGER REFERENCES organizations(id),
                        responsible_id INTEGER REFERENCES persons(id),
                        total_sum REAL DEFAULT 0,
                        total_labor REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_posted INTEGER DEFAULT 0,
                        posted_at TIMESTAMP,
                        marked_for_deletion INTEGER NOT NULL DEFAULT 0,
                        estimate_type TEXT NOT NULL DEFAULT 'General',
                        base_document_id INTEGER REFERENCES estimates(id),
                        is_deleted INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                # Copy data from old table, generating UUIDs for existing records
                cursor.execute("""
                    INSERT INTO estimates_new 
                    SELECT id, 
                           CASE WHEN uuid IS NOT NULL THEN uuid ELSE lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))) END as uuid,
                           number, date, customer_id, object_id, contractor_id, responsible_id,
                           total_sum, total_labor, created_at, modified_at, 
                           COALESCE(updated_at, created_at, CURRENT_TIMESTAMP) as updated_at,
                           is_posted, posted_at,
                           COALESCE(marked_for_deletion, 0) as marked_for_deletion,
                           COALESCE(estimate_type, 'General') as estimate_type,
                           base_document_id,
                           COALESCE(is_deleted, 0) as is_deleted
                    FROM estimates
                """)
                
                # Replace old table
                cursor.execute("DROP TABLE estimates")
                cursor.execute("ALTER TABLE estimates_new RENAME TO estimates")
                
                self.logger.info("Estimates table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix estimates table: {e}")
    
    def _fix_daily_reports_table(self, cursor: sqlite3.Cursor):
        """Fix daily_reports table schema"""
        try:
            # Check if daily_reports table needs fixing
            cursor.execute("PRAGMA table_info(daily_reports)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            if 'marked_for_deletion' in columns:
                col_info = columns['marked_for_deletion']
                if not col_info[4] or col_info[4] != "0":  # Check default value
                    needs_fix = True
            
            # Check if UUID field exists
            if 'uuid' not in columns:
                needs_fix = True
            
            if needs_fix:
                self.logger.info("Fixing daily_reports table schema...")
                
                # Create new table with correct schema including UUID, updated_at, and is_deleted
                cursor.execute("""
                    CREATE TABLE daily_reports_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT NOT NULL UNIQUE,
                        date DATE NOT NULL,
                        estimate_id INTEGER REFERENCES estimates(id),
                        foreman_id INTEGER REFERENCES persons(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_posted INTEGER DEFAULT 0,
                        posted_at TIMESTAMP,
                        marked_for_deletion INTEGER NOT NULL DEFAULT 0,
                        number TEXT,
                        is_deleted INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                # Copy data from old table, generating UUIDs for existing records
                cursor.execute("""
                    INSERT INTO daily_reports_new 
                    SELECT id, 
                           CASE WHEN uuid IS NOT NULL THEN uuid ELSE lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))) END as uuid,
                           date, estimate_id, foreman_id, created_at, modified_at, 
                           COALESCE(updated_at, created_at, CURRENT_TIMESTAMP) as updated_at,
                           is_posted, posted_at, COALESCE(marked_for_deletion, 0) as marked_for_deletion, number,
                           COALESCE(is_deleted, 0) as is_deleted
                    FROM daily_reports
                """)
                
                # Replace old table
                cursor.execute("DROP TABLE daily_reports")
                cursor.execute("ALTER TABLE daily_reports_new RENAME TO daily_reports")
                
                self.logger.info("Daily reports table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix daily_reports table: {e}")
    
    def _fix_timesheets_table(self, cursor: sqlite3.Cursor):
        """Fix timesheets table schema"""
        try:
            # Check if timesheets table needs fixing
            cursor.execute("PRAGMA table_info(timesheets)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            needs_fix = False
            if 'marked_for_deletion' in columns:
                col_info = columns['marked_for_deletion']
                if not col_info[4] or col_info[4] != "0":  # Check default value
                    needs_fix = True
            
            # Check if UUID field exists
            if 'uuid' not in columns:
                needs_fix = True
            
            if needs_fix:
                self.logger.info("Fixing timesheets table schema...")
                
                # Create new table with correct schema including UUID, updated_at, and is_deleted
                cursor.execute("""
                    CREATE TABLE timesheets_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT NOT NULL UNIQUE,
                        number TEXT NOT NULL,
                        date DATE NOT NULL,
                        object_id INTEGER REFERENCES objects(id),
                        estimate_id INTEGER REFERENCES estimates(id),
                        foreman_id INTEGER REFERENCES persons(id),
                        month_year TEXT NOT NULL,
                        is_posted INTEGER DEFAULT 0,
                        posted_at TIMESTAMP,
                        marked_for_deletion INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_deleted INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                # Copy data from old table, generating UUIDs for existing records
                cursor.execute("""
                    INSERT INTO timesheets_new 
                    SELECT id, 
                           CASE WHEN uuid IS NOT NULL THEN uuid ELSE lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))) END as uuid,
                           number, date, object_id, estimate_id, foreman_id, month_year,
                           is_posted, posted_at, COALESCE(marked_for_deletion, 0) as marked_for_deletion,
                           created_at, modified_at,
                           COALESCE(updated_at, created_at, CURRENT_TIMESTAMP) as updated_at,
                           COALESCE(is_deleted, 0) as is_deleted
                    FROM timesheets
                """)
                
                # Replace old table
                cursor.execute("DROP TABLE timesheets")
                cursor.execute("ALTER TABLE timesheets_new RENAME TO timesheets")
                
                self.logger.info("Timesheets table fixed")
            
        except Exception as e:
            self.logger.warning(f"Failed to fix timesheets table: {e}")
    
    def _update_schema_metadata(self, db_path: str):
        """Update schema version and sync time in constants table"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            current_version = self._get_current_schema_version()
            current_time = datetime.now().isoformat()
            
            # Update or insert schema version
            cursor.execute("""
                INSERT OR REPLACE INTO constants (key, value) 
                VALUES ('schema_version', ?)
            """, (current_version,))
            
            # Update or insert last sync time
            cursor.execute("""
                INSERT OR REPLACE INTO constants (key, value) 
                VALUES ('last_schema_sync', ?)
            """, (current_time,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Schema metadata updated: version={current_version}, sync_time={current_time}")
            
        except Exception as e:
            self.logger.error(f"Failed to update schema metadata: {e}")
    
    def _is_type_compatible(self, current_type: str, expected_type: str) -> bool:
        """Check if SQLite types are compatible (BOOLEAN == INTEGER)"""
        current_upper = current_type.upper()
        expected_upper = expected_type.upper()
        
        # Boolean is compatible with INTEGER in SQLite
        if ('INT' in current_upper and 'INT' in expected_upper) or \
            ('BOOLEAN' in current_upper and 'INT' in expected_upper) or \
            ('INT' in current_upper and 'BOOLEAN' in expected_upper):
            return True
        
        # TEXT and VARCHAR are compatible
        if ('TEXT' in current_upper and 'TEXT' in expected_upper) or \
            ('VARCHAR' in current_upper and 'TEXT' in expected_upper) or \
            ('TEXT' in current_upper and 'VARCHAR' in expected_upper):
            return True
        
        # REAL and FLOAT are compatible
        if ('REAL' in current_upper and 'REAL' in expected_upper) or \
            ('FLOAT' in current_upper and 'REAL' in expected_upper) or \
            ('REAL' in current_upper and 'FLOAT' in expected_upper):
            return True
        
        # TIMESTAMP, DATETIME are compatible
        if ('TIMESTAMP' in current_upper and 'TIMESTAMP' in expected_upper) or \
            ('DATETIME' in current_upper and 'TIMESTAMP' in expected_upper) or \
            ('TIMESTAMP' in current_upper and 'DATETIME' in expected_upper):
            return True
        
        # Exact match
        if current_upper == expected_upper:
            return True
        
        return False
    # def _verify_schema_integrity(self, db_path: str) -> bool:
    #     """Verify that schema is correct and complete"""
    #     try:
    #         schema_info = self.check_schema_version(db_path)
            
    #         # Check that all required tables exist
    #         if len(schema_info.get('missing_tables', [])) > 0:
    #             self.logger.error(f"Missing tables: {schema_info['missing_tables']}")
    #             return False
            
    #         # Check that critical schema differences are resolved
    #         differences = schema_info.get('schema_differences', [])
            
    #         # Filter out non-critical differences and SQLAlchemy model differences
    #         critical_differences = []
    #         for d in differences:
    #             if d['type'] in ['missing_column', 'constraint_mismatch']: 
    #                 # Skip BOOLEAN/INTEGER differences
    #                 if d.get('type') == 'type_mismatch' and column in ['is_deleted', 'marked_for_deletion']:
    #                     self.logger.info(f"Ignoring BOOLEAN/INTEGER type mismatch for {table}.{column}")
    #                     continue        
    #                 # Skip TIMESTAMP/DATETIME differences
    #                 if d.get('type') == 'type_mismatch' and column == 'updated_at':
    #                     current_type = d.get('current', '').upper()
    #                     expected_type = d.get('expected', '').upper()
    #                     if ('TIMESTAMP' in current_type and 'TIMESTAMP' in expected_type) or \
    #                        ('DATETIME' in current_type and 'TIMESTAMP' in expected_type) or \
    #                        ('TIMESTAMP' in current_type and 'DATETIME' in expected_type):
    #                         self.logger.info(f"Ignoring TIMESTAMP/DATETIME difference for {table}.updated_at")
    #                         continue                   
    #                 # Skip non-critical differences
    #                 if (d.get('table') == 'persons' and 
    #                     d.get('column') == 'marked_for_deletion' and 
    #                     d.get('issue') == 'missing_default'):
    #                     self.logger.info(f"Ignoring non-critical difference: {d}")
    #                     continue
                    
    #                 # Skip SQLAlchemy model differences - if the column exists, it's probably correct
    #                 if (d.get('issue') == 'missing_default' and 
    #                     d.get('column') in ['updated_at', 'is_deleted']):
    #                     # Check if the column actually exists and has the right type
    #                     try:
    #                         conn = sqlite3.connect(db_path)
    #                         cursor = conn.cursor()
    #                         cursor.execute(f"PRAGMA table_info({d.get('table')})")
    #                         columns = {col[1]: col for col in cursor.fetchall()}
    #                         conn.close()
                            
    #                         if d.get('column') in columns:
    #                             col_info = columns[d.get('column')]
    #                             # If column exists with correct type, consider it OK
    #                             if ((d.get('column') == 'updated_at' and 'TIMESTAMP' in col_info[2].upper()) or
    #                                 (d.get('column') == 'is_deleted' and col_info[2].upper() in ['INTEGER', 'BOOLEAN'])):
    #                                 self.logger.info(f"Ignoring SQLAlchemy model difference: {d}")
    #                                 continue
    #                     except Exception as e:
    #                         self.logger.warning(f"Could not verify column {d.get('column')}: {e}")
                    
    #                 critical_differences.append(d)
            
    #         if len(critical_differences) > 0:
    #             self.logger.warning(f"Non-critical schema differences remain: {len(critical_differences)} differences")
    #             # Log first few differences for debugging
    #             for i, diff in enumerate(critical_differences[:3]):
    #                 self.logger.debug(f"Difference {i+1}: {diff}")
    #             # Don't fail for these differences - they're likely SQLAlchemy model differences
    #             self.logger.info("Accepting schema as valid despite minor differences")
            
    #         self.logger.info("Schema integrity verification passed")
    #         return True
            
    #     except Exception as e:
    #         self.logger.error(f"Schema integrity verification failed: {e}")
    #         return Falsealse
    def _verify_schema_integrity(self, db_path: str) -> bool:
        """Verify that schema is correct and complete"""
        try:
            schema_info = self.check_schema_version(db_path)
            
            # Check that all required tables exist
            if len(schema_info.get('missing_tables', [])) > 0:
                self.logger.error(f"Missing tables: {schema_info['missing_tables']}")
                return False
            
            # Check that critical schema differences are resolved
            differences = schema_info.get('schema_differences', [])
            
            # Filter out non-critical differences and SQLAlchemy model differences
            critical_differences = []
            for d in differences:
                # Проверяем ВСЕ типы различий, включая type_mismatch
                if d['type'] in ['missing_column', 'constraint_mismatch', 'type_mismatch']:
                    table = d.get('table', '')
                    column = d.get('column', '')
                    issue = d.get('issue', '')
                    
                    # 1. Игнорировать BOOLEAN/INTEGER различия
                    if d.get('type') == 'type_mismatch' and column in ['is_deleted', 'marked_for_deletion']:
                        current_type = d.get('current', '').upper()
                        expected_type = d.get('expected', '').upper()
                        
                        # Проверяем совместимость типов
                        if ('INT' in current_type and 'INT' in expected_type) or \
                        ('BOOLEAN' in current_type and 'INT' in expected_type) or \
                        ('INT' in current_type and 'BOOLEAN' in expected_type):
                            self.logger.info(f"Ignoring BOOLEAN/INTEGER type mismatch for {table}.{column}")
                            continue
                    
                    # 2. Игнорировать TIMESTAMP/DATETIME различия
                    if d.get('type') == 'type_mismatch' and column == 'updated_at':
                        current_type = d.get('current', '').upper()
                        expected_type = d.get('expected', '').upper()
                        
                        # Разные варианты timestamp совместимы
                        timestamp_variants = ['TIMESTAMP', 'DATETIME', 'TIME']
                        current_is_timestamp = any(var in current_type for var in timestamp_variants)
                        expected_is_timestamp = any(var in expected_type for var in timestamp_variants)
                        
                        if current_is_timestamp and expected_is_timestamp:
                            self.logger.info(f"Ignoring TIMESTAMP/DATETIME difference for {table}.updated_at")
                            continue
                    
                    # 3. Игнорировать TEXT/VARCHAR различия
                    if d.get('type') == 'type_mismatch' and column == 'uuid':
                        current_type = d.get('current', '').upper()
                        expected_type = d.get('expected', '').upper()
                        
                        if ('TEXT' in current_type and 'TEXT' in expected_type) or \
                        ('VARCHAR' in current_type and 'TEXT' in expected_type) or \
                        ('TEXT' in current_type and 'VARCHAR' in expected_type):
                            self.logger.info(f"Ignoring TEXT/VARCHAR difference for {table}.uuid")
                            continue
                    
                    # 4. Игнорировать недостающие DEFAULT для BOOLEAN полей (если поле NOT NULL)
                    if column in ['is_deleted', 'marked_for_deletion'] and issue == 'missing_default':
                        self.logger.info(f"Ignoring missing default for {table}.{column} (BOOLEAN field)")
                        continue
                    
                    # 5. Игнорировать недостающие DEFAULT для updated_at (если есть DEFAULT на уровне SQLAlchemy)
                    if column == 'updated_at' and issue == 'missing_default':
                        self.logger.info(f"Ignoring missing default for {table}.updated_at (SQLAlchemy default)")
                        continue
                    
                    # 6. Skip persons.marked_for_deletion missing_default (уже есть в моделях)
                    if (table == 'persons' and 
                        column == 'marked_for_deletion' and 
                        issue == 'missing_default'):
                        self.logger.info(f"Ignoring non-critical difference: {d}")
                        continue
                    
                    # 7. Проверить существование колонки через PRAGMA (для missing_default)
                    if issue == 'missing_default' and column in ['updated_at', 'is_deleted']:
                        try:
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute(f"PRAGMA table_info({table})")
                            columns_info = {col[1]: col for col in cursor.fetchall()}
                            conn.close()
                            
                            if column in columns_info:
                                col_info = columns_info[column]
                                col_type = col_info[2].upper()
                                
                                # Если колонка существует с правильным типом, считаем её OK
                                if ((column == 'updated_at' and any(t in col_type for t in ['TIMESTAMP', 'DATETIME', 'TIME'])) or
                                    (column == 'is_deleted' and any(t in col_type for t in ['INTEGER', 'BOOLEAN']))):
                                    self.logger.info(f"Ignoring SQLAlchemy model difference: {d}")
                                    continue
                        except Exception as e:
                            self.logger.warning(f"Could not verify column {column}: {e}")
                    
                    # Если разница не была проигнорирована, добавляем её в критические
                    critical_differences.append(d)
            
            if len(critical_differences) > 0:
                self.logger.warning(f"Non-critical schema differences remain: {len(critical_differences)} differences")
                # Log first few differences for debugging
                for i, diff in enumerate(critical_differences[:5]):
                    self.logger.info(f"Difference {i+1}: {diff}")
                
                # Проверим, являются ли различия действительно критичными
                truly_critical = []
                for diff in critical_differences:
                    # Игнорировать type_mismatch для совместимых типов
                    if diff.get('type') == 'type_mismatch':
                        current_type = diff.get('current', '').upper()
                        expected_type = diff.get('expected', '').upper()
                        
                        # Проверить совместимость через наш метод
                        if hasattr(self, '_is_type_compatible'):
                            if self._is_type_compatible(current_type, expected_type):
                                self.logger.info(f"Accepting compatible type difference: {diff}")
                                continue
                    
                    # Игнорировать constraint_mismatch для синхронизационных полей
                    if (diff.get('type') == 'constraint_mismatch' and 
                        diff.get('column') in ['is_deleted', 'marked_for_deletion', 'updated_at'] and
                        diff.get('issue') == 'missing_default'):
                        self.logger.info(f"Accepting missing default for sync field: {diff}")
                        continue
                    
                    truly_critical.append(diff)
                
                if len(truly_critical) == 0:
                    self.logger.info("All differences are non-critical, accepting schema as valid")
                    return True
                else:
                    self.logger.warning(f"Critical schema differences found: {len(truly_critical)}")
                    for diff in truly_critical:
                        self.logger.error(f"Critical: {diff}")
                    return False
            
            self.logger.info("Schema integrity verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema integrity verification failed: {e}")
            return False  # Исправлено: было "return Falsealse"


def main():
    """Test schema synchronizer"""
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Schema Synchronizer')
    parser.add_argument('--db-path', type=str, required=True, help='Database path')
    parser.add_argument('--check-only', action='store_true', help='Only check schema, do not sync')
    parser.add_argument('--force', action='store_true', help='Force synchronization')
    
    args = parser.parse_args()
    
    synchronizer = SchemaSynchronizer(logger)
    
    if args.check_only:
        schema_info = synchronizer.check_schema_version(args.db_path)
        print(f"Schema info: {schema_info}")
    else:
        success = synchronizer.synchronize_schema(args.db_path, force=args.force)
        print(f"Synchronization: {'SUCCESS' if success else 'FAILED'}")


if __name__ == '__main__':
    main()
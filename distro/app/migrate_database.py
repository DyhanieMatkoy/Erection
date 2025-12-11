#!/usr/bin/env python3
"""
Database Migration Tool

This tool migrates data from SQLite to PostgreSQL or MSSQL.
It handles schema creation and data transfer automatically.

Usage:
    python migrate_database.py --source construction.db --target-config env.ini
    python migrate_database.py --source construction.db --target-config env_postgresql.ini --verify
    python migrate_database.py --help
"""

import sqlite3
import argparse
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import sys

from src.data.database_manager import DatabaseManager
from src.data.database_config import DatabaseConfig
from src.data.models.sqlalchemy_models import (
    User, Person, Organization, Counterparty, Object, Work,
    Estimate, EstimateLine, DailyReport, DailyReportLine, DailyReportExecutor,
    Timesheet, TimesheetLine, WorkExecutionRegister, PayrollRegister,
    UserSetting, Constant
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles database migration from SQLite to PostgreSQL/MSSQL"""
    
    # Define migration order (respecting foreign key dependencies)
    MIGRATION_ORDER = [
        ('users', User),
        ('persons', Person),
        ('organizations', Organization),
        ('counterparties', Counterparty),
        ('objects', Object),
        ('works', Work),
        ('estimates', Estimate),
        ('estimate_lines', EstimateLine),
        ('daily_reports', DailyReport),
        ('daily_report_lines', DailyReportLine),
        ('daily_report_executors', DailyReportExecutor),
        ('timesheets', Timesheet),
        ('timesheet_lines', TimesheetLine),
        ('work_execution_register', WorkExecutionRegister),
        ('payroll_register', PayrollRegister),
        ('user_settings', UserSetting),
        ('constants', Constant),
    ]
    
    def __init__(self, source_db: str, target_config: str):
        """
        Initialize migrator
        
        Args:
            source_db: Path to source SQLite database
            target_config: Path to target database configuration file
        """
        self.source_db = source_db
        self.target_config = target_config
        self.source_conn = None
        self.target_manager = None
        self.stats = {}
        
    def connect_source(self) -> bool:
        """Connect to source SQLite database"""
        try:
            logger.info(f"Connecting to source database: {self.source_db}")
            self.source_conn = sqlite3.connect(self.source_db)
            self.source_conn.row_factory = sqlite3.Row
            logger.info("✓ Connected to source database")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to source database: {e}")
            return False
    
    def connect_target(self) -> bool:
        """Connect to target database"""
        try:
            logger.info(f"Connecting to target database using config: {self.target_config}")
            self.target_manager = DatabaseManager()
            success = self.target_manager.initialize(self.target_config)
            
            if success:
                config = DatabaseConfig(self.target_config)
                logger.info(f"✓ Connected to target database ({config.db_type})")
                return True
            else:
                logger.error("✗ Failed to connect to target database")
                return False
        except Exception as e:
            logger.error(f"✗ Failed to connect to target database: {e}")
            return False
    
    def get_table_count(self, table_name: str) -> int:
        """Get record count from source table"""
        try:
            cursor = self.source_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Table doesn't exist in source
            return 0
    
    def migrate_table(self, table_name: str, model_class) -> Tuple[int, int]:
        """
        Migrate a single table
        
        Returns:
            Tuple of (records_migrated, records_failed)
        """
        logger.info(f"Migrating table: {table_name}")
        
        # Check if table exists in source
        source_count = self.get_table_count(table_name)
        if source_count == 0:
            logger.info(f"  ⊘ Table {table_name} is empty or doesn't exist, skipping")
            return (0, 0)
        
        logger.info(f"  Found {source_count} records to migrate")
        
        migrated = 0
        failed = 0
        
        try:
            # Fetch all records from source
            cursor = self.source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Migrate in batches
            batch_size = 100
            with self.target_manager.session_scope() as session:
                for i, row in enumerate(rows):
                    try:
                        # Convert row to dict
                        row_dict = dict(row)
                        
                        # Convert boolean values (SQLite stores as 0/1)
                        for key, value in row_dict.items():
                            if isinstance(value, int) and key in [
                                'is_active', 'marked_for_deletion', 'is_posted'
                            ]:
                                row_dict[key] = bool(value)
                        
                        # Create model instance
                        instance = model_class(**row_dict)
                        session.add(instance)
                        
                        migrated += 1
                        
                        # Commit in batches
                        if (i + 1) % batch_size == 0:
                            session.flush()
                            logger.info(f"  Migrated {i + 1}/{source_count} records")
                    
                    except Exception as e:
                        logger.warning(f"  Failed to migrate record {row_dict.get('id', '?')}: {e}")
                        failed += 1
                        continue
                
                # Final commit
                session.commit()
            
            logger.info(f"  ✓ Migrated {migrated} records ({failed} failed)")
            
        except Exception as e:
            logger.error(f"  ✗ Failed to migrate table {table_name}: {e}")
            return (0, source_count)
        
        return (migrated, failed)
    
    def migrate_all(self) -> bool:
        """Migrate all tables"""
        logger.info("=" * 60)
        logger.info("Starting database migration")
        logger.info("=" * 60)
        
        total_migrated = 0
        total_failed = 0
        
        for table_name, model_class in self.MIGRATION_ORDER:
            migrated, failed = self.migrate_table(table_name, model_class)
            total_migrated += migrated
            total_failed += failed
            self.stats[table_name] = {'migrated': migrated, 'failed': failed}
        
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        
        for table_name, stats in self.stats.items():
            if stats['migrated'] > 0 or stats['failed'] > 0:
                status = "✓" if stats['failed'] == 0 else "⚠"
                logger.info(f"{status} {table_name}: {stats['migrated']} migrated, {stats['failed']} failed")
        
        logger.info("-" * 60)
        logger.info(f"Total: {total_migrated} records migrated, {total_failed} failed")
        logger.info("=" * 60)
        
        return total_failed == 0
    
    def verify_migration(self) -> bool:
        """Verify migration by comparing record counts"""
        logger.info("=" * 60)
        logger.info("Verifying migration")
        logger.info("=" * 60)
        
        all_match = True
        
        for table_name, model_class in self.MIGRATION_ORDER:
            source_count = self.get_table_count(table_name)
            
            if source_count == 0:
                continue
            
            try:
                with self.target_manager.session_scope() as session:
                    target_count = session.query(model_class).count()
                
                match = source_count == target_count
                status = "✓" if match else "✗"
                
                logger.info(f"{status} {table_name}: Source={source_count}, Target={target_count}")
                
                if not match:
                    all_match = False
            
            except Exception as e:
                logger.error(f"✗ Failed to verify {table_name}: {e}")
                all_match = False
        
        logger.info("=" * 60)
        if all_match:
            logger.info("✓ Verification successful! All counts match.")
        else:
            logger.warning("⚠ Verification found mismatches!")
        logger.info("=" * 60)
        
        return all_match
    
    def close(self):
        """Close database connections"""
        if self.source_conn:
            self.source_conn.close()
            logger.info("Closed source database connection")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate database from SQLite to PostgreSQL/MSSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate to PostgreSQL
  python migrate_database.py --source construction.db --target-config env_postgresql.ini
  
  # Migrate to MSSQL with verification
  python migrate_database.py --source construction.db --target-config env_mssql.ini --verify
  
  # Verify existing migration
  python migrate_database.py --source construction.db --target-config env.ini --verify-only
        """
    )
    
    parser.add_argument(
        '--source',
        required=True,
        help='Path to source SQLite database file'
    )
    
    parser.add_argument(
        '--target-config',
        required=True,
        help='Path to target database configuration file (env.ini)'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration after completion'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing migration (do not migrate)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create migrator
    migrator = DatabaseMigrator(args.source, args.target_config)
    
    try:
        # Connect to databases
        if not migrator.connect_source():
            logger.error("Failed to connect to source database")
            return 1
        
        if not migrator.connect_target():
            logger.error("Failed to connect to target database")
            return 1
        
        # Perform migration or verification
        if args.verify_only:
            # Only verify
            success = migrator.verify_migration()
        else:
            # Migrate
            success = migrator.migrate_all()
            
            # Verify if requested
            if args.verify and success:
                success = migrator.verify_migration()
        
        # Close connections
        migrator.close()
        
        if success:
            logger.info("✓ Migration completed successfully!")
            return 0
        else:
            logger.warning("⚠ Migration completed with warnings")
            return 1
    
    except KeyboardInterrupt:
        logger.warning("\nMigration interrupted by user")
        migrator.close()
        return 1
    
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        migrator.close()
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""Migration backup and rollback utilities

This module provides utilities for creating backups and rollback procedures
for safe work unit migration.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work, WorkUnitMigration
from sqlalchemy import text


class MigrationBackupManager:
    """Manager for migration backup and rollback operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.backup_dir = "migration_backups"
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_pre_migration_backup(self) -> Dict[str, Any]:
        """Create a complete backup before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_info = {
            'timestamp': timestamp,
            'backup_type': 'pre_migration',
            'files': {},
            'metadata': {}
        }
        
        # Backup database file (SQLite only)
        if hasattr(self.db_manager, '_config') and self.db_manager._config and self.db_manager._config.is_sqlite():
            config_data = self.db_manager._config.get_config_data()
            db_path = config_data.get('db_path')
            if db_path and os.path.exists(db_path):
                backup_db_path = os.path.join(
                    self.backup_dir, 
                    f"database_backup_{timestamp}.db"
                )
                shutil.copy2(db_path, backup_db_path)
                backup_info['files']['database'] = backup_db_path
                backup_info['metadata']['original_db_path'] = db_path
        
        # Export works table data as JSON
        works_backup_path = os.path.join(
            self.backup_dir,
            f"works_data_{timestamp}.json"
        )
        self.export_works_data(works_backup_path)
        backup_info['files']['works_data'] = works_backup_path
        
        # Save backup info
        backup_info_path = os.path.join(
            self.backup_dir,
            f"backup_info_{timestamp}.json"
        )
        with open(backup_info_path, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, default=str)
        backup_info['files']['backup_info'] = backup_info_path
        
        print(f"Pre-migration backup created: {timestamp}")
        return backup_info
    
    def export_works_data(self, output_path: str):
        """Export works table data to JSON"""
        with self.db_manager.get_session() as session:
            works = session.query(Work).all()
            works_data = []
            
            for work in works:
                work_dict = {
                    'id': work.id,
                    'name': work.name,
                    'code': work.code,
                    'unit': work.unit,
                    'unit_id': work.unit_id,
                    'price': work.price,
                    'labor_rate': work.labor_rate,
                    'parent_id': work.parent_id,
                    'is_group': work.is_group,
                    'marked_for_deletion': work.marked_for_deletion,
                    'uuid': work.uuid,
                    'created_at': work.created_at.isoformat() if work.created_at else None,
                    'modified_at': work.modified_at.isoformat() if work.modified_at else None,
                    'updated_at': work.updated_at.isoformat() if work.updated_at else None,
                    'is_deleted': work.is_deleted
                }
                works_data.append(work_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(works_data, f, indent=2, ensure_ascii=False)
    
    def create_migration_checkpoint(self, checkpoint_name: str) -> Dict[str, Any]:
        """Create a checkpoint during migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_info = {
            'timestamp': timestamp,
            'checkpoint_name': checkpoint_name,
            'backup_type': 'checkpoint',
            'files': {}
        }
        
        # Export current migration state
        migration_state_path = os.path.join(
            self.backup_dir,
            f"migration_state_{checkpoint_name}_{timestamp}.json"
        )
        self.export_migration_state(migration_state_path)
        checkpoint_info['files']['migration_state'] = migration_state_path
        
        # Save checkpoint info
        checkpoint_info_path = os.path.join(
            self.backup_dir,
            f"checkpoint_{checkpoint_name}_{timestamp}.json"
        )
        with open(checkpoint_info_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_info, f, indent=2, default=str)
        checkpoint_info['files']['checkpoint_info'] = checkpoint_info_path
        
        print(f"Migration checkpoint created: {checkpoint_name} at {timestamp}")
        return checkpoint_info
    
    def export_migration_state(self, output_path: str):
        """Export current migration tracking state"""
        with self.db_manager.get_session() as session:
            migrations = session.query(WorkUnitMigration).all()
            migration_data = []
            
            for migration in migrations:
                migration_dict = {
                    'work_id': migration.work_id,
                    'legacy_unit': migration.legacy_unit,
                    'matched_unit_id': migration.matched_unit_id,
                    'migration_status': migration.migration_status,
                    'confidence_score': migration.confidence_score,
                    'manual_review_reason': migration.manual_review_reason,
                    'created_at': migration.created_at.isoformat() if migration.created_at else None,
                    'updated_at': migration.updated_at.isoformat() if migration.updated_at else None
                }
                migration_data.append(migration_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(migration_data, f, indent=2, ensure_ascii=False)
    
    def rollback_to_backup(self, backup_timestamp: str) -> bool:
        """Rollback to a specific backup"""
        backup_info_path = os.path.join(
            self.backup_dir,
            f"backup_info_{backup_timestamp}.json"
        )
        
        if not os.path.exists(backup_info_path):
            print(f"Backup info not found: {backup_info_path}")
            return False
        
        with open(backup_info_path, 'r', encoding='utf-8') as f:
            backup_info = json.load(f)
        
        # Restore database
        if 'database' in backup_info['files']:
            backup_db_path = backup_info['files']['database']
            original_db_path = backup_info['metadata']['original_db_path']
            
            if os.path.exists(backup_db_path):
                # Create current backup before rollback
                current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup = f"pre_rollback_{current_timestamp}.db"
                current_backup_path = os.path.join(self.backup_dir, current_backup)
                shutil.copy2(original_db_path, current_backup_path)
                
                # Restore from backup
                shutil.copy2(backup_db_path, original_db_path)
                print(f"Database restored from backup: {backup_timestamp}")
                print(f"Current state backed up to: {current_backup}")
                return True
            else:
                print(f"Backup database file not found: {backup_db_path}")
                return False
        
        return False
    
    def verify_backup_integrity(self, backup_timestamp: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        backup_info_path = os.path.join(
            self.backup_dir,
            f"backup_info_{backup_timestamp}.json"
        )
        
        if not os.path.exists(backup_info_path):
            return {'valid': False, 'error': 'Backup info file not found'}
        
        with open(backup_info_path, 'r', encoding='utf-8') as f:
            backup_info = json.load(f)
        
        verification = {
            'valid': True,
            'files_checked': {},
            'errors': []
        }
        
        # Check all backup files exist
        for file_type, file_path in backup_info['files'].items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                verification['files_checked'][file_type] = {
                    'exists': True,
                    'size': file_size,
                    'path': file_path
                }
            else:
                verification['valid'] = False
                verification['files_checked'][file_type] = {
                    'exists': False,
                    'path': file_path
                }
                verification['errors'].append(f"Missing file: {file_path}")
        
        # Verify database backup if it exists
        if 'database' in backup_info['files']:
            db_path = backup_info['files']['database']
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM works")
                    works_count = cursor.fetchone()[0]
                    conn.close()
                    verification['files_checked']['database']['works_count'] = works_count
                except Exception as e:
                    verification['valid'] = False
                    verification['errors'].append(f"Database verification failed: {str(e)}")
        
        return verification
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_info_') and filename.endswith('.json'):
                backup_path = os.path.join(self.backup_dir, filename)
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                    backups.append(backup_info)
                except Exception as e:
                    print(f"Error reading backup info {filename}: {e}")
        
        # Sort by timestamp
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """Clean up old backups, keeping only the most recent ones"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        backups_to_remove = backups[keep_count:]
        removed_count = 0
        
        for backup in backups_to_remove:
            try:
                # Remove all files associated with this backup
                for file_path in backup['files'].values():
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        removed_count += 1
            except Exception as e:
                print(f"Error removing backup files: {e}")
        
        return removed_count


def main():
    """Main entry point for backup utilities"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration backup utilities')
    parser.add_argument('action', choices=['backup', 'rollback', 'verify', 'list', 'cleanup'],
                       help='Action to perform')
    parser.add_argument('--timestamp', '-t', help='Backup timestamp for rollback/verify')
    parser.add_argument('--keep', '-k', type=int, default=5,
                       help='Number of backups to keep during cleanup')
    
    args = parser.parse_args()
    
    # Initialize database manager and backup manager
    db_manager = DatabaseManager()
    db_manager.initialize()
    backup_manager = MigrationBackupManager(db_manager)
    
    if args.action == 'backup':
        backup_info = backup_manager.create_pre_migration_backup()
        print(f"Backup created with timestamp: {backup_info['timestamp']}")
    
    elif args.action == 'rollback':
        if not args.timestamp:
            print("Error: --timestamp required for rollback")
            sys.exit(1)
        success = backup_manager.rollback_to_backup(args.timestamp)
        if success:
            print("Rollback completed successfully")
        else:
            print("Rollback failed")
            sys.exit(1)
    
    elif args.action == 'verify':
        if not args.timestamp:
            print("Error: --timestamp required for verify")
            sys.exit(1)
        verification = backup_manager.verify_backup_integrity(args.timestamp)
        if verification['valid']:
            print("Backup verification passed")
        else:
            print("Backup verification failed:")
            for error in verification['errors']:
                print(f"  - {error}")
    
    elif args.action == 'list':
        backups = backup_manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  {backup['timestamp']} - {backup['backup_type']}")
        else:
            print("No backups found")
    
    elif args.action == 'cleanup':
        removed = backup_manager.cleanup_old_backups(args.keep)
        print(f"Cleaned up {removed} old backup files")


if __name__ == '__main__':
    main()
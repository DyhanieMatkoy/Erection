"""
Table Part Settings Migration Utilities

This module provides utilities for migrating table part settings
between different versions and managing settings data integrity.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..data.models.sqlalchemy_models import UserTablePartSettings, User
from .table_part_settings_service import TablePartSettingsService, CURRENT_SETTINGS_VERSION

logger = logging.getLogger(__name__)


class TablePartSettingsMigrator:
    """Utility class for migrating table part settings"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.settings_service = TablePartSettingsService(db_session)
    
    def migrate_all_user_settings(
        self,
        target_version: str = CURRENT_SETTINGS_VERSION,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate all user settings to target version.
        
        Args:
            target_version: Version to migrate to
            dry_run: If True, only analyze what would be migrated
            
        Returns:
            Migration report dictionary
        """
        try:
            # Get all settings records
            all_settings = self.db_session.query(UserTablePartSettings).all()
            
            migration_report = {
                'total_records': len(all_settings),
                'migrated_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'errors': [],
                'dry_run': dry_run,
                'target_version': target_version,
                'migration_date': datetime.now().isoformat()
            }
            
            for settings_record in all_settings:
                try:
                    # Check if migration is needed
                    settings_dict = json.loads(settings_record.settings_data)
                    current_version = settings_dict.get('version', '0.9')
                    
                    if current_version == target_version:
                        migration_report['skipped_count'] += 1
                        continue
                    
                    if not dry_run:
                        # Perform migration
                        migrated_data, was_migrated = self.settings_service.migrate_settings_if_needed(
                            settings_record.settings_data, target_version
                        )
                        
                        if was_migrated:
                            settings_record.settings_data = migrated_data
                            migration_report['migrated_count'] += 1
                        else:
                            migration_report['skipped_count'] += 1
                    else:
                        # Dry run - just count what would be migrated
                        migration_report['migrated_count'] += 1
                    
                except Exception as e:
                    error_msg = f"Error migrating settings for record {settings_record.id}: {e}"
                    logger.error(error_msg)
                    migration_report['errors'].append(error_msg)
                    migration_report['error_count'] += 1
            
            if not dry_run and migration_report['migrated_count'] > 0:
                self.db_session.commit()
                logger.info(f"Successfully migrated {migration_report['migrated_count']} settings records")
            
            return migration_report
            
        except Exception as e:
            logger.error(f"Error during bulk migration: {e}")
            if not dry_run:
                self.db_session.rollback()
            return {
                'error': str(e),
                'total_records': 0,
                'migrated_count': 0,
                'skipped_count': 0,
                'error_count': 1
            }
    
    def migrate_user_settings(
        self,
        user_id: int,
        target_version: str = CURRENT_SETTINGS_VERSION,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate settings for a specific user.
        
        Args:
            user_id: User ID to migrate settings for
            target_version: Version to migrate to
            dry_run: If True, only analyze what would be migrated
            
        Returns:
            Migration report dictionary
        """
        try:
            user_settings = self.db_session.query(UserTablePartSettings).filter(
                UserTablePartSettings.user_id == user_id
            ).all()
            
            migration_report = {
                'user_id': user_id,
                'total_records': len(user_settings),
                'migrated_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'errors': [],
                'dry_run': dry_run,
                'target_version': target_version,
                'migration_date': datetime.now().isoformat()
            }
            
            for settings_record in user_settings:
                try:
                    settings_dict = json.loads(settings_record.settings_data)
                    current_version = settings_dict.get('version', '0.9')
                    
                    if current_version == target_version:
                        migration_report['skipped_count'] += 1
                        continue
                    
                    if not dry_run:
                        migrated_data, was_migrated = self.settings_service.migrate_settings_if_needed(
                            settings_record.settings_data, target_version
                        )
                        
                        if was_migrated:
                            settings_record.settings_data = migrated_data
                            migration_report['migrated_count'] += 1
                        else:
                            migration_report['skipped_count'] += 1
                    else:
                        migration_report['migrated_count'] += 1
                    
                except Exception as e:
                    error_msg = f"Error migrating settings for {settings_record.document_type}/{settings_record.table_part_id}: {e}"
                    logger.error(error_msg)
                    migration_report['errors'].append(error_msg)
                    migration_report['error_count'] += 1
            
            if not dry_run and migration_report['migrated_count'] > 0:
                self.db_session.commit()
            
            return migration_report
            
        except Exception as e:
            logger.error(f"Error migrating user {user_id} settings: {e}")
            if not dry_run:
                self.db_session.rollback()
            return {
                'error': str(e),
                'user_id': user_id,
                'migrated_count': 0,
                'skipped_count': 0,
                'error_count': 1
            }
    
    def validate_all_settings(self) -> Dict[str, Any]:
        """
        Validate all settings records in the database.
        
        Returns:
            Validation report dictionary
        """
        try:
            all_settings = self.db_session.query(UserTablePartSettings).all()
            
            validation_report = {
                'total_records': len(all_settings),
                'valid_count': 0,
                'invalid_count': 0,
                'validation_errors': [],
                'validation_date': datetime.now().isoformat()
            }
            
            for settings_record in all_settings:
                try:
                    is_valid, errors = self.settings_service.validate_settings_data(
                        settings_record.settings_data
                    )
                    
                    if is_valid:
                        validation_report['valid_count'] += 1
                    else:
                        validation_report['invalid_count'] += 1
                        validation_report['validation_errors'].append({
                            'record_id': settings_record.id,
                            'user_id': settings_record.user_id,
                            'document_type': settings_record.document_type,
                            'table_part_id': settings_record.table_part_id,
                            'errors': errors
                        })
                
                except Exception as e:
                    validation_report['invalid_count'] += 1
                    validation_report['validation_errors'].append({
                        'record_id': settings_record.id,
                        'user_id': settings_record.user_id,
                        'document_type': settings_record.document_type,
                        'table_part_id': settings_record.table_part_id,
                        'errors': [f"Validation exception: {e}"]
                    })
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error during settings validation: {e}")
            return {
                'error': str(e),
                'total_records': 0,
                'valid_count': 0,
                'invalid_count': 0
            }
    
    def backup_settings(
        self,
        backup_path: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a backup of settings data.
        
        Args:
            backup_path: Path to save backup file
            user_id: Optional user ID to backup specific user settings
            
        Returns:
            Backup operation result
        """
        try:
            query = self.db_session.query(UserTablePartSettings)
            
            if user_id:
                query = query.filter(UserTablePartSettings.user_id == user_id)
            
            settings_records = query.all()
            
            backup_data = {
                'backup_version': CURRENT_SETTINGS_VERSION,
                'backup_date': datetime.now().isoformat(),
                'total_records': len(settings_records),
                'user_filter': user_id,
                'settings': []
            }
            
            for record in settings_records:
                backup_data['settings'].append({
                    'id': record.id,
                    'user_id': record.user_id,
                    'document_type': record.document_type,
                    'table_part_id': record.table_part_id,
                    'settings_data': json.loads(record.settings_data),
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Created settings backup with {len(settings_records)} records at {backup_path}")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'records_backed_up': len(settings_records),
                'backup_date': backup_data['backup_date']
            }
            
        except Exception as e:
            logger.error(f"Error creating settings backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'backup_path': backup_path
            }
    
    def restore_settings(
        self,
        backup_path: str,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Restore settings from backup file.
        
        Args:
            backup_path: Path to backup file
            overwrite_existing: Whether to overwrite existing settings
            
        Returns:
            Restore operation result
        """
        try:
            # Load backup data
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            settings_list = backup_data.get('settings', [])
            
            for setting_data in settings_list:
                try:
                    user_id = setting_data['user_id']
                    document_type = setting_data['document_type']
                    table_part_id = setting_data['table_part_id']
                    settings_json = json.dumps(setting_data['settings_data'])
                    
                    # Check if settings already exist
                    existing = self.db_session.query(UserTablePartSettings).filter(
                        and_(
                            UserTablePartSettings.user_id == user_id,
                            UserTablePartSettings.document_type == document_type,
                            UserTablePartSettings.table_part_id == table_part_id
                        )
                    ).first()
                    
                    if existing and not overwrite_existing:
                        skipped_count += 1
                        continue
                    
                    # Migrate settings to current version
                    migrated_json, _ = self.settings_service.migrate_settings_if_needed(settings_json)
                    
                    if existing:
                        existing.settings_data = migrated_json
                    else:
                        new_settings = UserTablePartSettings(
                            user_id=user_id,
                            document_type=document_type,
                            table_part_id=table_part_id,
                            settings_data=migrated_json
                        )
                        self.db_session.add(new_settings)
                    
                    restored_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error restoring setting: {e}")
            
            self.db_session.commit()
            
            return {
                'success': True,
                'restored_count': restored_count,
                'skipped_count': skipped_count,
                'error_count': error_count,
                'errors': errors,
                'backup_path': backup_path
            }
            
        except Exception as e:
            logger.error(f"Error restoring settings backup: {e}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': str(e),
                'backup_path': backup_path,
                'restored_count': 0
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status for all settings.
        
        Returns:
            Migration status report
        """
        try:
            all_settings = self.db_session.query(UserTablePartSettings).all()
            
            version_counts = {}
            total_records = len(all_settings)
            
            for settings_record in all_settings:
                try:
                    settings_dict = json.loads(settings_record.settings_data)
                    version = settings_dict.get('version', '0.9')
                    version_counts[version] = version_counts.get(version, 0) + 1
                except Exception:
                    version_counts['invalid'] = version_counts.get('invalid', 0) + 1
            
            needs_migration = sum(
                count for version, count in version_counts.items()
                if version != CURRENT_SETTINGS_VERSION and version != 'invalid'
            )
            
            return {
                'total_records': total_records,
                'current_version': CURRENT_SETTINGS_VERSION,
                'version_distribution': version_counts,
                'needs_migration': needs_migration,
                'migration_percentage': (needs_migration / total_records * 100) if total_records > 0 else 0,
                'status_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {
                'error': str(e),
                'total_records': 0,
                'needs_migration': 0
            }
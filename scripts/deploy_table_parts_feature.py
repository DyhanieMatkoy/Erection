#!/usr/bin/env python3
"""
Deployment script for Document Table Parts feature.

This script handles the deployment of the Document Table Parts feature,
including database migrations, configuration updates, and validation.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('table_parts_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TablePartsDeployment:
    """Handles deployment of Document Table Parts feature"""
    
    def __init__(self, database_url: str, dry_run: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def deploy(self) -> bool:
        """
        Execute complete deployment process.
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            logger.info("Starting Document Table Parts deployment...")
            
            # Pre-deployment checks
            if not self._pre_deployment_checks():
                logger.error("Pre-deployment checks failed")
                return False
            
            # Database migrations
            if not self._run_database_migrations():
                logger.error("Database migrations failed")
                return False
            
            # Configuration updates
            if not self._update_configurations():
                logger.error("Configuration updates failed")
                return False
            
            # Feature validation
            if not self._validate_deployment():
                logger.error("Deployment validation failed")
                return False
            
            # Post-deployment tasks
            if not self._post_deployment_tasks():
                logger.error("Post-deployment tasks failed")
                return False
            
            logger.info("Document Table Parts deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed with error: {e}")
            return False
    
    def _pre_deployment_checks(self) -> bool:
        """Perform pre-deployment validation checks"""
        logger.info("Performing pre-deployment checks...")
        
        checks = [
            self._check_database_connectivity,
            self._check_required_files,
            self._check_dependencies,
            self._check_permissions,
            self._backup_existing_data
        ]
        
        for check in checks:
            if not check():
                return False
        
        logger.info("Pre-deployment checks passed")
        return True
    
    def _check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Database connectivity verified")
            return True
        except Exception as e:
            logger.error(f"✗ Database connectivity failed: {e}")
            return False
    
    def _check_required_files(self) -> bool:
        """Check that all required files exist"""
        required_files = [
            'alembic/versions/20251219_140000_add_table_part_settings.py',
            'src/views/widgets/base_table_part.py',
            'web-client/src/components/common/BaseTablePart.vue',
            'src/services/table_part_settings_service.py',
            'src/services/table_part_keyboard_handler.py',
            'src/services/table_part_calculation_engine.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"✗ Missing required files: {missing_files}")
            return False
        
        logger.info("✓ All required files present")
        return True
    
    def _check_dependencies(self) -> bool:
        """Check that all dependencies are installed"""
        try:
            # Check Python dependencies
            import PyQt6
            import sqlalchemy
            import alembic
            
            # Check if web client is built
            web_dist = project_root / 'web-client' / 'dist'
            if not web_dist.exists():
                logger.warning("Web client not built - run 'npm run build' in web-client directory")
            
            logger.info("✓ Dependencies verified")
            return True
        except ImportError as e:
            logger.error(f"✗ Missing dependency: {e}")
            return False
    
    def _check_permissions(self) -> bool:
        """Check file and database permissions"""
        try:
            # Check database write permissions
            with self.engine.connect() as conn:
                conn.execute(text("CREATE TEMP TABLE test_permissions (id INTEGER)"))
                conn.execute(text("DROP TABLE test_permissions"))
            
            # Check file write permissions
            test_file = project_root / 'test_permissions.tmp'
            test_file.write_text('test')
            test_file.unlink()
            
            logger.info("✓ Permissions verified")
            return True
        except Exception as e:
            logger.error(f"✗ Permission check failed: {e}")
            return False
    
    def _backup_existing_data(self) -> bool:
        """Backup existing user settings if any"""
        try:
            backup_dir = project_root / 'backups' / f'table_parts_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if user settings table exists
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_table_part_settings'
                    )
                """))
                
                if result.scalar():
                    # Backup existing settings
                    settings_result = conn.execute(text("SELECT * FROM user_table_part_settings"))
                    settings_data = [dict(row._mapping) for row in settings_result]
                    
                    backup_file = backup_dir / 'user_table_part_settings.json'
                    backup_file.write_text(json.dumps(settings_data, default=str, indent=2))
                    logger.info(f"✓ Backed up existing settings to {backup_file}")
            
            return True
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
            return False
    
    def _run_database_migrations(self) -> bool:
        """Run database migrations"""
        logger.info("Running database migrations...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would run database migrations")
            return True
        
        try:
            # Run Alembic migrations
            alembic_cfg = Config(str(project_root / 'alembic.ini'))
            alembic_cfg.set_main_option('sqlalchemy.url', self.database_url)
            
            # Run migrations
            command.upgrade(alembic_cfg, 'head')
            
            logger.info("✓ Database migrations completed")
            return True
        except Exception as e:
            logger.error(f"✗ Database migration failed: {e}")
            return False
    
    def _update_configurations(self) -> bool:
        """Update application configurations"""
        logger.info("Updating configurations...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would update configurations")
            return True
        
        try:
            # Update desktop configuration
            self._update_desktop_config()
            
            # Update web client configuration
            self._update_web_config()
            
            logger.info("✓ Configurations updated")
            return True
        except Exception as e:
            logger.error(f"✗ Configuration update failed: {e}")
            return False
    
    def _update_desktop_config(self):
        """Update desktop application configuration"""
        config_file = project_root / 'src' / 'config.py'
        
        # Add table parts configuration if not present
        config_additions = '''
# Table Parts Configuration
TABLE_PART_SETTINGS = {
    'CALCULATION_TIMEOUT_MS': 100,
    'TOTAL_CALCULATION_TIMEOUT_MS': 200,
    'PERFORMANCE_MONITORING_ENABLED': True,
    'DEFAULT_VISIBLE_COMMANDS': [
        'add_row', 'delete_row', 'move_up', 'move_down'
    ],
    'KEYBOARD_SHORTCUTS_ENABLED': True,
    'AUTO_CALCULATION_ENABLED': True,
    'DRAG_DROP_ENABLED': True
}
'''
        
        if config_file.exists():
            content = config_file.read_text()
            if 'TABLE_PART_SETTINGS' not in content:
                config_file.write_text(content + config_additions)
                logger.info("✓ Desktop configuration updated")
        else:
            logger.warning("Desktop config file not found, skipping")
    
    def _update_web_config(self):
        """Update web client configuration"""
        config_file = project_root / 'web-client' / 'src' / 'config' / 'tableparts.ts'
        
        config_content = '''// Table Parts Configuration
export const TABLE_PART_CONFIG = {
  calculationTimeoutMs: 100,
  totalCalculationTimeoutMs: 200,
  performanceMonitoringEnabled: true,
  defaultVisibleCommands: [
    'add_row', 'delete_row', 'move_up', 'move_down'
  ],
  keyboardShortcutsEnabled: true,
  autoCalculationEnabled: true,
  dragDropEnabled: true
}

export default TABLE_PART_CONFIG
'''
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(config_content)
        logger.info("✓ Web client configuration updated")
    
    def _validate_deployment(self) -> bool:
        """Validate that deployment was successful"""
        logger.info("Validating deployment...")
        
        validations = [
            self._validate_database_schema,
            self._validate_services,
            self._validate_components
        ]
        
        for validation in validations:
            if not validation():
                return False
        
        logger.info("✓ Deployment validation passed")
        return True
    
    def _validate_database_schema(self) -> bool:
        """Validate database schema"""
        try:
            with self.engine.connect() as conn:
                # Check user_table_part_settings table
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user_table_part_settings'
                """))
                columns = [row[0] for row in result]
                
                required_columns = ['id', 'user_id', 'document_type', 'table_part_id', 'settings_data']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    logger.error(f"✗ Missing columns in user_table_part_settings: {missing_columns}")
                    return False
                
                # Check table_part_command_config table
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'table_part_command_config'
                """))
                columns = [row[0] for row in result]
                
                required_columns = ['id', 'document_type', 'table_part_id', 'command_id', 'is_visible']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    logger.error(f"✗ Missing columns in table_part_command_config: {missing_columns}")
                    return False
            
            logger.info("✓ Database schema validated")
            return True
        except Exception as e:
            logger.error(f"✗ Database schema validation failed: {e}")
            return False
    
    def _validate_services(self) -> bool:
        """Validate that services can be imported and initialized"""
        try:
            # Test service imports
            from src.services.table_part_settings_service import TablePartSettingsService
            from src.services.table_part_keyboard_handler import TablePartKeyboardHandler
            from src.services.table_part_calculation_engine import TablePartCalculationEngine
            
            # Test service initialization
            session = self.Session()
            try:
                settings_service = TablePartSettingsService(session)
                # Test basic functionality
                default_settings = settings_service.get_default_settings('test', 'test')
                assert default_settings is not None
            finally:
                session.close()
            
            logger.info("✓ Services validated")
            return True
        except Exception as e:
            logger.error(f"✗ Service validation failed: {e}")
            return False
    
    def _validate_components(self) -> bool:
        """Validate that components exist and are properly structured"""
        try:
            # Check desktop component
            desktop_component = project_root / 'src' / 'views' / 'widgets' / 'base_table_part.py'
            if not desktop_component.exists():
                logger.error("✗ Desktop BaseTablePart component not found")
                return False
            
            # Check web component
            web_component = project_root / 'web-client' / 'src' / 'components' / 'common' / 'BaseTablePart.vue'
            if not web_component.exists():
                logger.error("✗ Web BaseTablePart component not found")
                return False
            
            logger.info("✓ Components validated")
            return True
        except Exception as e:
            logger.error(f"✗ Component validation failed: {e}")
            return False
    
    def _post_deployment_tasks(self) -> bool:
        """Perform post-deployment tasks"""
        logger.info("Performing post-deployment tasks...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would perform post-deployment tasks")
            return True
        
        try:
            # Create default settings for existing users
            self._create_default_user_settings()
            
            # Update documentation
            self._update_documentation_index()
            
            # Generate deployment report
            self._generate_deployment_report()
            
            logger.info("✓ Post-deployment tasks completed")
            return True
        except Exception as e:
            logger.error(f"✗ Post-deployment tasks failed: {e}")
            return False
    
    def _create_default_user_settings(self):
        """Create default settings for existing users"""
        session = self.Session()
        try:
            from src.services.table_part_settings_service import TablePartSettingsService
            
            settings_service = TablePartSettingsService(session)
            
            # Get all users
            result = session.execute(text("SELECT id FROM users WHERE is_active = true"))
            user_ids = [row[0] for row in result]
            
            # Create default settings for common document types
            document_types = ['estimate', 'daily_report', 'timesheet']
            table_parts = ['lines', 'materials', 'works']
            
            created_count = 0
            for user_id in user_ids:
                for doc_type in document_types:
                    for table_part in table_parts:
                        # Check if settings already exist
                        existing = settings_service.get_user_settings(user_id, doc_type, table_part)
                        if not existing:
                            # Create default settings
                            default_settings = settings_service.get_default_settings(doc_type, table_part)
                            settings_service.save_user_settings(user_id, doc_type, table_part, default_settings)
                            created_count += 1
            
            session.commit()
            logger.info(f"✓ Created {created_count} default user settings")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create default user settings: {e}")
            raise
        finally:
            session.close()
    
    def _update_documentation_index(self):
        """Update documentation index"""
        index_file = project_root / 'docs' / 'INDEX.md'
        
        if index_file.exists():
            content = index_file.read_text()
            
            # Add table parts documentation if not present
            table_parts_docs = '''
## Document Table Parts
- [User Guide](features/DOCUMENT_TABLE_PARTS_USER_GUIDE.md)
- [Technical Guide](features/DOCUMENT_TABLE_PARTS_TECHNICAL_GUIDE.md)
- [Release Notes](features/DOCUMENT_TABLE_PARTS_RELEASE_NOTES.md)
'''
            
            if 'Document Table Parts' not in content:
                content += table_parts_docs
                index_file.write_text(content)
                logger.info("✓ Documentation index updated")
    
    def _generate_deployment_report(self):
        """Generate deployment report"""
        report = {
            'deployment_date': datetime.now().isoformat(),
            'feature': 'Document Table Parts v1.0',
            'status': 'SUCCESS',
            'database_migrations': 'COMPLETED',
            'configuration_updates': 'COMPLETED',
            'validation': 'PASSED',
            'components': {
                'desktop': 'BaseTablePart (PyQt6)',
                'web': 'BaseTablePart.vue (Vue.js)',
                'services': [
                    'TablePartSettingsService',
                    'TablePartKeyboardHandler', 
                    'TablePartCalculationEngine',
                    'TablePartCommandManager'
                ]
            },
            'new_database_tables': [
                'user_table_part_settings',
                'table_part_command_config'
            ]
        }
        
        report_file = project_root / 'deployment_reports' / f'table_parts_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))
        
        logger.info(f"✓ Deployment report generated: {report_file}")


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Document Table Parts feature')
    parser.add_argument('--database-url', required=True, help='Database connection URL')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create deployment instance
    deployment = TablePartsDeployment(args.database_url, args.dry_run)
    
    # Execute deployment
    success = deployment.deploy()
    
    if success:
        print("\n🎉 Document Table Parts deployment completed successfully!")
        print("📚 See documentation in docs/features/ for user and technical guides")
        sys.exit(0)
    else:
        print("\n❌ Document Table Parts deployment failed!")
        print("📋 Check table_parts_deployment.log for details")
        sys.exit(1)


if __name__ == '__main__':
    main()
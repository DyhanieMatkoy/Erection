#!/usr/bin/env python3
"""Multi-Dialect Migration Manager

Manages Alembic migrations for multiple SQL dialects (SQLite, PostgreSQL, MySQL).
Automatically creates dialect-specific migrations from base SQLite migrations.
"""

import os
import sys
import shutil
import logging
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sql_dialect_translator import SQLDialectTranslator, SQLDialect


class MultiDialectMigrationManager:
    """Manages migrations for multiple SQL dialects"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize multi-dialect migration manager
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.translator = SQLDialectTranslator(logger)
        
        # Migration directories for each dialect
        self.migration_dirs = {
            SQLDialect.SQLITE: Path("alembic/versions"),
            SQLDialect.POSTGRESQL: Path("alembic/versions_postgresql"), 
            SQLDialect.MYSQL: Path("alembic/versions_mysql")
        }
        
        # Alembic config files for each dialect
        self.alembic_configs = {
            SQLDialect.SQLITE: Path("alembic.ini"),
            SQLDialect.POSTGRESQL: Path("alembic_postgresql.ini"),
            SQLDialect.MYSQL: Path("alembic_mysql.ini")
        }
        
        # Ensure directories exist
        for migration_dir in self.migration_dirs.values():
            migration_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Multi-dialect migration manager initialized")
    
    def create_migration_for_all_dialects(self, message: str, base_dialect: SQLDialect = SQLDialect.SQLITE) -> Dict[SQLDialect, str]:
        """Create migration for all supported dialects
        
        Args:
            message: Migration message
            base_dialect: Base dialect to create migration from
            
        Returns:
            Dictionary mapping dialects to migration file paths
        """
        try:
            self.logger.info(f"Creating migration for all dialects: {message}")
            
            results = {}
            
            # Create base migration (usually SQLite)
            base_migration_path = self._create_base_migration(message, base_dialect)
            if not base_migration_path:
                raise Exception(f"Failed to create base migration for {base_dialect.value}")
            
            results[base_dialect] = base_migration_path
            
            # Create translations for other dialects
            for dialect in [SQLDialect.POSTGRESQL, SQLDialect.MYSQL]:
                if dialect != base_dialect:
                    translated_path = self._create_translated_migration(
                        base_migration_path, base_dialect, dialect, message
                    )
                    if translated_path:
                        results[dialect] = translated_path
                    else:
                        self.logger.warning(f"Failed to create migration for {dialect.value}")
            
            self.logger.info(f"Created migrations for {len(results)} dialects")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to create migrations for all dialects: {e}")
            return {}
    
    def _create_base_migration(self, message: str, dialect: SQLDialect) -> Optional[str]:
        """Create base migration using Alembic
        
        Args:
            message: Migration message
            dialect: SQL dialect
            
        Returns:
            Path to created migration file
        """
        try:
            config_file = self.alembic_configs[dialect]
            
            # Run alembic revision
            cmd = ['alembic', '-c', str(config_file), 'revision', '--autogenerate', '-m', message]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                self.logger.error(f"Alembic revision failed: {result.stderr}")
                return None
            
            # Find the created migration file
            migration_dir = self.migration_dirs[dialect]
            migration_files = list(migration_dir.glob("*.py"))
            
            if migration_files:
                # Get the most recent migration file
                latest_migration = max(migration_files, key=lambda f: f.stat().st_mtime)
                self.logger.info(f"Created base migration: {latest_migration}")
                return str(latest_migration)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to create base migration: {e}")
            return None
    
    def _create_translated_migration(self, base_migration_path: str, source_dialect: SQLDialect,
                                   target_dialect: SQLDialect, message: str) -> Optional[str]:
        """Create translated migration from base migration
        
        Args:
            base_migration_path: Path to base migration file
            source_dialect: Source SQL dialect
            target_dialect: Target SQL dialect
            message: Migration message
            
        Returns:
            Path to created translated migration file
        """
        try:
            self.logger.info(f"Creating {target_dialect.value} migration from {source_dialect.value}")
            
            # Read base migration content
            with open(base_migration_path, 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            # Translate migration content
            translated_content = self.translator.create_dialect_specific_migration(
                base_content, target_dialect, source_dialect
            )
            
            # Generate migration filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = Path(base_migration_path).stem
            
            # Extract revision ID from base filename
            revision_parts = base_filename.split('_')
            if len(revision_parts) >= 2:
                base_revision = revision_parts[0]
                # Create new revision ID for target dialect
                target_revision = f"{base_revision}_{target_dialect.value[:2]}"
            else:
                target_revision = f"{timestamp}_{target_dialect.value}"
            
            # Create target migration filename
            target_filename = f"{target_revision}_{message.replace(' ', '_').lower()}.py"
            target_path = self.migration_dirs[target_dialect] / target_filename
            
            # Update revision IDs in translated content
            translated_content = self._update_revision_ids(
                translated_content, target_revision, base_revision
            )
            
            # Write translated migration
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            self.logger.info(f"Created translated migration: {target_path}")
            return str(target_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create translated migration: {e}")
            return None
    
    def _update_revision_ids(self, migration_content: str, new_revision: str, old_revision: str) -> str:
        """Update revision IDs in migration content"""
        # Update revision ID
        migration_content = migration_content.replace(
            f'revision = "{old_revision}"',
            f'revision = "{new_revision}"'
        )
        
        # Update down_revision if it references the old revision
        migration_content = migration_content.replace(
            f'down_revision = "{old_revision}"',
            f'down_revision = None'  # First migration in this dialect chain
        )
        
        return migration_content
    
    def create_alembic_configs_for_all_dialects(self) -> bool:
        """Create Alembic configuration files for all dialects
        
        Returns:
            True if all configs created successfully
        """
        try:
            self.logger.info("Creating Alembic configs for all dialects")
            
            # Base config template
            base_config_path = self.alembic_configs[SQLDialect.SQLITE]
            
            if not base_config_path.exists():
                self.logger.error(f"Base Alembic config not found: {base_config_path}")
                return False
            
            # Read base config
            with open(base_config_path, 'r') as f:
                base_config = f.read()
            
            # Create configs for other dialects
            for dialect in [SQLDialect.POSTGRESQL, SQLDialect.MYSQL]:
                config_path = self.alembic_configs[dialect]
                
                # Modify config for this dialect
                dialect_config = self._customize_alembic_config(base_config, dialect)
                
                # Write dialect-specific config
                with open(config_path, 'w') as f:
                    f.write(dialect_config)
                
                self.logger.info(f"Created Alembic config: {config_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Alembic configs: {e}")
            return False
    
    def _customize_alembic_config(self, base_config: str, dialect: SQLDialect) -> str:
        """Customize Alembic config for specific dialect
        
        Args:
            base_config: Base configuration content
            dialect: Target SQL dialect
            
        Returns:
            Customized configuration content
        """
        config = base_config
        
        # Update version locations
        version_dir = str(self.migration_dirs[dialect])
        config = config.replace(
            'version_locations = alembic/versions',
            f'version_locations = {version_dir}'
        )
        
        # Update script location if needed
        if dialect != SQLDialect.SQLITE:
            config = config.replace(
                'script_location = alembic',
                f'script_location = alembic_{dialect.value}'
            )
        
        # Add dialect-specific connection string placeholder
        if dialect == SQLDialect.POSTGRESQL:
            config = config.replace(
                'sqlalchemy.url = sqlite:///construction.db',
                'sqlalchemy.url = postgresql://user:password@localhost/dbname'
            )
        elif dialect == SQLDialect.MYSQL:
            config = config.replace(
                'sqlalchemy.url = sqlite:///construction.db',
                'sqlalchemy.url = mysql+pymysql://user:password@localhost/dbname'
            )
        
        return config
    
    def upgrade_database(self, dialect: SQLDialect, connection_string: str, 
                        target_revision: str = "head") -> bool:
        """Upgrade database to target revision
        
        Args:
            dialect: SQL dialect
            connection_string: Database connection string
            target_revision: Target revision (default: head)
            
        Returns:
            True if upgrade successful
        """
        try:
            self.logger.info(f"Upgrading {dialect.value} database to {target_revision}")
            
            # Get config file for this dialect
            config_file = self.alembic_configs[dialect]
            
            # Temporarily update connection string in config
            original_config = None
            if config_file.exists():
                with open(config_file, 'r') as f:
                    original_config = f.read()
                
                # Update connection string
                updated_config = self._update_connection_string(original_config, connection_string)
                with open(config_file, 'w') as f:
                    f.write(updated_config)
            
            try:
                # Run alembic upgrade
                cmd = ['alembic', '-c', str(config_file), 'upgrade', target_revision]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Alembic upgrade failed: {result.stderr}")
                    return False
                
                self.logger.info(f"Database upgrade completed: {dialect.value}")
                return True
                
            finally:
                # Restore original config
                if original_config and config_file.exists():
                    with open(config_file, 'w') as f:
                        f.write(original_config)
            
        except Exception as e:
            self.logger.error(f"Database upgrade failed: {e}")
            return False
    
    def _update_connection_string(self, config_content: str, connection_string: str) -> str:
        """Update connection string in Alembic config"""
        import re
        
        # Escape backslashes in Windows paths for regex
        escaped_connection_string = connection_string.replace('\\', '\\\\')
        
        pattern = r'sqlalchemy\.url\s*=\s*.*'
        replacement = f'sqlalchemy.url = {escaped_connection_string}'
        
        return re.sub(pattern, replacement, config_content)
    
    def get_migration_status(self, dialect: SQLDialect, connection_string: str) -> Dict[str, any]:
        """Get migration status for database
        
        Args:
            dialect: SQL dialect
            connection_string: Database connection string
            
        Returns:
            Migration status information
        """
        try:
            config_file = self.alembic_configs[dialect]
            
            # Temporarily update connection string
            original_config = None
            if config_file.exists():
                with open(config_file, 'r') as f:
                    original_config = f.read()
                
                updated_config = self._update_connection_string(original_config, connection_string)
                with open(config_file, 'w') as f:
                    f.write(updated_config)
            
            try:
                # Get current revision
                cmd = ['alembic', '-c', str(config_file), 'current']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                current_revision = result.stdout.strip() if result.returncode == 0 else None
                
                # Get head revision
                cmd = ['alembic', '-c', str(config_file), 'heads']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                head_revision = result.stdout.strip() if result.returncode == 0 else None
                
                return {
                    'dialect': dialect.value,
                    'current_revision': current_revision,
                    'head_revision': head_revision,
                    'up_to_date': current_revision == head_revision,
                    'connection_string': connection_string
                }
                
            finally:
                # Restore original config
                if original_config and config_file.exists():
                    with open(config_file, 'w') as f:
                        f.write(original_config)
            
        except Exception as e:
            self.logger.error(f"Failed to get migration status: {e}")
            return {
                'dialect': dialect.value,
                'error': str(e),
                'connection_string': connection_string
            }
    
    def sync_migrations_across_dialects(self) -> bool:
        """Synchronize migrations across all dialects
        
        Ensures all dialects have equivalent migrations
        
        Returns:
            True if synchronization successful
        """
        try:
            self.logger.info("Synchronizing migrations across dialects")
            
            # Get all SQLite migrations (base dialect)
            sqlite_migrations = self._get_migration_files(SQLDialect.SQLITE)
            
            for migration_file in sqlite_migrations:
                # Check if equivalent migrations exist for other dialects
                for dialect in [SQLDialect.POSTGRESQL, SQLDialect.MYSQL]:
                    if not self._has_equivalent_migration(migration_file, SQLDialect.SQLITE, dialect):
                        # Create equivalent migration
                        self.logger.info(f"Creating equivalent {dialect.value} migration for {migration_file.name}")
                        
                        message = self._extract_migration_message(migration_file)
                        self._create_translated_migration(
                            str(migration_file), SQLDialect.SQLITE, dialect, message
                        )
            
            self.logger.info("Migration synchronization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration synchronization failed: {e}")
            return False
    
    def _get_migration_files(self, dialect: SQLDialect) -> List[Path]:
        """Get all migration files for dialect"""
        migration_dir = self.migration_dirs[dialect]
        return sorted([f for f in migration_dir.glob("*.py") if f.name != "__init__.py"])
    
    def _has_equivalent_migration(self, base_migration: Path, base_dialect: SQLDialect, 
                                target_dialect: SQLDialect) -> bool:
        """Check if equivalent migration exists for target dialect"""
        # Extract message from base migration filename
        message = self._extract_migration_message(base_migration)
        
        # Look for migration with same message in target dialect
        target_migrations = self._get_migration_files(target_dialect)
        
        for migration in target_migrations:
            if message.lower() in migration.name.lower():
                return True
        
        return False
    
    def _extract_migration_message(self, migration_file: Path) -> str:
        """Extract migration message from filename"""
        # Remove revision ID and extension
        name_parts = migration_file.stem.split('_')[1:]  # Skip revision ID
        return '_'.join(name_parts) if name_parts else "migration"


def main():
    """Test multi-dialect migration manager"""
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Multi-Dialect Migration Manager')
    parser.add_argument('--create-configs', action='store_true',
                       help='Create Alembic configs for all dialects')
    parser.add_argument('--sync-migrations', action='store_true',
                       help='Synchronize migrations across dialects')
    parser.add_argument('--create-migration', type=str,
                       help='Create migration for all dialects')
    
    args = parser.parse_args()
    
    manager = MultiDialectMigrationManager(logger)
    
    if args.create_configs:
        success = manager.create_alembic_configs_for_all_dialects()
        print("✅ Configs created" if success else "❌ Config creation failed")
    
    elif args.sync_migrations:
        success = manager.sync_migrations_across_dialects()
        print("✅ Migrations synchronized" if success else "❌ Synchronization failed")
    
    elif args.create_migration:
        results = manager.create_migration_for_all_dialects(args.create_migration)
        print(f"✅ Created migrations for {len(results)} dialects: {list(results.keys())}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
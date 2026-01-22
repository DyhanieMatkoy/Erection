"""Alembic Migration Manager

This module manages Alembic schema migrations for multi-database testing,
including migration execution, monitoring, and cross-database synchronization.
"""

import os
import sys
import time
import logging
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_configuration_manager import DatabaseConfig, DatabaseType


@dataclass
class MigrationInfo:
    """Migration information data class"""
    migration_id: str
    name: str
    description: str
    operations: List[Dict[str, Any]]
    created_at: datetime
    executed_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None
    status: str = "pending"  # pending, executed, failed, rolled_back


class AlembicMigrationManager:
    """Manages Alembic migrations for multi-database testing"""
    
    def __init__(self, server_db_config: DatabaseConfig, client_db_configs: Dict[str, DatabaseConfig], logger: logging.Logger):
        """Initialize Alembic migration manager
        
        Args:
            server_db_config: Server database configuration
            client_db_configs: Dictionary of client database configurations
            logger: Logger instance
        """
        self.server_config = server_db_config
        self.client_configs = client_db_configs
        self.logger = logger
        
        # Migration tracking
        self.migration_history: List[MigrationInfo] = []
        self.current_migration: Optional[MigrationInfo] = None
        
        # Alembic configuration
        self.alembic_config_path = "test_alembic.ini"  # Use test configuration
        self.migrations_dir = "test_migrations/versions"
        
        # Test migration templates
        self.test_migrations = self._initialize_test_migrations()
        
        self.logger.info("Alembic migration manager initialized")
    
    def _initialize_test_migrations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize test migration templates
        
        Returns:
            Dictionary of test migration templates
        """
        return {
            'add_project_phases_table': {
                'name': 'add_project_phases_table',
                'description': 'Add project phases table for testing',
                'operations': [
                    {
                        'type': 'create_table',
                        'table_name': 'project_phases',
                        'columns': [
                            {'name': 'id', 'type': 'Integer', 'primary_key': True},
                            {'name': 'name', 'type': 'String(100)', 'nullable': False},
                            {'name': 'start_date', 'type': 'Date'},
                            {'name': 'end_date', 'type': 'Date'},
                            {'name': 'project_id', 'type': 'Integer', 'foreign_key': 'projects.id'},
                            {'name': 'created_at', 'type': 'DateTime', 'default': 'func.now()'},
                            {'name': 'updated_at', 'type': 'DateTime', 'default': 'func.now()'}
                        ]
                    }
                ]
            },
            'add_priority_to_estimates': {
                'name': 'add_priority_to_estimates',
                'description': 'Add priority column to estimates table',
                'operations': [
                    {
                        'type': 'add_column',
                        'table_name': 'estimates',
                        'column': {'name': 'priority', 'type': 'Integer', 'default': 1}
                    }
                ]
            },
            'extend_description_length': {
                'name': 'extend_description_length',
                'description': 'Extend description field length in daily reports',
                'operations': [
                    {
                        'type': 'alter_column',
                        'table_name': 'daily_reports',
                        'column_name': 'description',
                        'new_type': 'String(500)'  # Extended from String(255)
                    }
                ]
            },
            'add_indexes_for_performance': {
                'name': 'add_indexes_for_performance',
                'description': 'Add database indexes for performance optimization',
                'operations': [
                    {
                        'type': 'create_index',
                        'table_name': 'estimates',
                        'columns': ['created_at', 'status'],
                        'index_name': 'idx_estimates_created_status'
                    },
                    {
                        'type': 'create_index',
                        'table_name': 'daily_reports',
                        'columns': ['date', 'project_id'],
                        'index_name': 'idx_daily_reports_date_project'
                    }
                ]
            },
            'add_foreign_key_constraints': {
                'name': 'add_foreign_key_constraints',
                'description': 'Add foreign key constraints for data integrity',
                'operations': [
                    {
                        'type': 'create_foreign_key',
                        'table_name': 'estimate_items',
                        'column_name': 'estimate_id',
                        'referenced_table': 'estimates',
                        'referenced_column': 'id',
                        'constraint_name': 'fk_estimate_items_estimate_id'
                    }
                ]
            }
        }
    
    def create_test_migration(self, migration_name: str, schema_changes: Optional[Dict[str, Any]] = None) -> MigrationInfo:
        """Create a test migration script
        
        Args:
            migration_name: Name of the migration (must be in test_migrations)
            schema_changes: Optional custom schema changes
            
        Returns:
            MigrationInfo instance
        """
        try:
            self.logger.info(f"Creating test migration: {migration_name}")
            
            # Get migration template
            if schema_changes:
                migration_template = schema_changes
            elif migration_name in self.test_migrations:
                migration_template = self.test_migrations[migration_name]
            else:
                raise ValueError(f"Unknown migration template: {migration_name}")
            
            # Generate migration ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            migration_id = f"{timestamp}_{migration_name}"
            
            # Create migration info
            migration_info = MigrationInfo(
                migration_id=migration_id,
                name=migration_template['name'],
                description=migration_template['description'],
                operations=migration_template['operations'],
                created_at=datetime.now()
            )
            
            # Generate Alembic migration file
            self._generate_alembic_migration_file(migration_info)
            
            # Add to history
            self.migration_history.append(migration_info)
            
            self.logger.info(f"Test migration created: {migration_id}")
            return migration_info
            
        except Exception as e:
            self.logger.error(f"Failed to create test migration {migration_name}: {e}")
            raise
    
    def _generate_alembic_migration_file(self, migration_info: MigrationInfo) -> None:
        """Generate Alembic migration file from migration info
        
        Args:
            migration_info: Migration information
        """
        try:
            # Ensure migrations directory exists
            Path(self.migrations_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate migration file content
            migration_content = self._generate_migration_content(migration_info)
            
            # Write migration file
            migration_file_path = Path(self.migrations_dir) / f"{migration_info.migration_id}.py"
            
            with open(migration_file_path, 'w') as f:
                f.write(migration_content)
            
            self.logger.debug(f"Generated migration file: {migration_file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate migration file for {migration_info.migration_id}: {e}")
            raise
    
    def _get_last_migration_revision(self) -> Optional[str]:
        """Get the last migration revision ID
        
        Returns:
            Last migration revision ID or None if no migrations exist
        """
        try:
            # Check existing migration files
            migrations_path = Path(self.migrations_dir)
            if not migrations_path.exists():
                return None
            
            migration_files = list(migrations_path.glob("*.py"))
            if not migration_files:
                return None
            
            # Sort by filename (timestamp-based) and get the last one
            migration_files.sort()
            
            # If we have the initial schema migration, use it
            for migration_file in migration_files:
                if "initial_test_schema" in migration_file.name:
                    return "20260122_000000_initial_test_schema"
            
            # Otherwise, use the last migration from history
            if self.migration_history:
                return self.migration_history[-1].migration_id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get last migration revision: {e}")
            return None
    
    def _generate_migration_content(self, migration_info: MigrationInfo) -> str:
        """Generate Alembic migration file content
        
        Args:
            migration_info: Migration information
            
        Returns:
            Migration file content as string
        """
        # Find the last migration to chain properly
        down_revision = self._get_last_migration_revision()
        
        # Migration file template
        template = f'''"""Test migration: {migration_info.name}

{migration_info.description}

Revision ID: {migration_info.migration_id}
Revises: {down_revision}
Create Date: {migration_info.created_at.isoformat()}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '{migration_info.migration_id}'
down_revision = {repr(down_revision)}
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    # Check if we're in test mode - create tables if they don't exist
    try:
        # Create basic tables if they don't exist (for test isolation)
        _ensure_basic_tables_exist()
    except Exception:
        pass  # Continue with migration even if table creation fails
'''
        
        # Generate upgrade operations
        for operation in migration_info.operations:
            template += self._generate_operation_code(operation, 'upgrade')
        
        template += '''

def downgrade():
    """Downgrade database schema"""
'''
        
        # Generate downgrade operations (reverse order)
        for operation in reversed(migration_info.operations):
            template += self._generate_operation_code(operation, 'downgrade')
        
        template += '''

def _ensure_basic_tables_exist():
    """Ensure basic tables exist for test migrations"""
    # This function creates basic tables if they don't exist
    # to support isolated test migrations
    
    # Check if estimates table exists, if not create basic structure
    try:
        op.get_bind().execute(sa.text("SELECT 1 FROM estimates LIMIT 1"))
    except Exception:
        # Create basic estimates table
        op.create_table('estimates',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(255)),
            sa.Column('description', sa.Text),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
        )
    
    # Check if daily_reports table exists
    try:
        op.get_bind().execute(sa.text("SELECT 1 FROM daily_reports LIMIT 1"))
    except Exception:
        # Create basic daily_reports table
        op.create_table('daily_reports',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('date', sa.Date),
            sa.Column('description', sa.String(255)),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
        )
'''
        
        return template
    
    def _generate_operation_code(self, operation: Dict[str, Any], direction: str) -> str:
        """Generate operation code for migration
        
        Args:
            operation: Operation definition
            direction: 'upgrade' or 'downgrade'
            
        Returns:
            Generated operation code
        """
        op_type = operation['type']
        
        if op_type == 'create_table' and direction == 'upgrade':
            return self._generate_create_table_code(operation)
        elif op_type == 'create_table' and direction == 'downgrade':
            return f"    op.drop_table('{operation['table_name']}')\n"
        
        elif op_type == 'add_column' and direction == 'upgrade':
            return self._generate_add_column_code(operation)
        elif op_type == 'add_column' and direction == 'downgrade':
            return f"    op.drop_column('{operation['table_name']}', '{operation['column']['name']}')\n"
        
        elif op_type == 'alter_column' and direction == 'upgrade':
            return self._generate_alter_column_code(operation)
        elif op_type == 'alter_column' and direction == 'downgrade':
            return f"    # Note: Column type rollback may require manual intervention\n    pass\n"
        
        elif op_type == 'create_index' and direction == 'upgrade':
            return self._generate_create_index_code(operation)
        elif op_type == 'create_index' and direction == 'downgrade':
            return f"    op.drop_index('{operation['index_name']}', table_name='{operation['table_name']}')\n"
        
        elif op_type == 'create_foreign_key' and direction == 'upgrade':
            return self._generate_create_foreign_key_code(operation)
        elif op_type == 'create_foreign_key' and direction == 'downgrade':
            return f"    op.drop_constraint('{operation['constraint_name']}', '{operation['table_name']}', type_='foreignkey')\n"
        
        else:
            return f"    # TODO: Implement {op_type} operation for {direction}\n    pass\n"
    
    def _generate_create_table_code(self, operation: Dict[str, Any]) -> str:
        """Generate create table operation code"""
        table_name = operation['table_name']
        columns = operation['columns']
        
        code = f"    op.create_table('{table_name}',\n"
        
        for column in columns:
            col_def = self._generate_column_definition(column)
            code += f"        {col_def},\n"
        
        code += "    )\n"
        return code
    
    def _generate_column_definition(self, column: Dict[str, Any]) -> str:
        """Generate column definition code"""
        name = column['name']
        col_type = column['type']
        
        # Convert type string to SQLAlchemy type
        if col_type == 'Integer':
            sa_type = 'sa.Integer'
        elif col_type.startswith('String'):
            length = col_type.replace('String(', '').replace(')', '')
            sa_type = f'sa.String({length})'
        elif col_type == 'Date':
            sa_type = 'sa.Date'
        elif col_type == 'DateTime':
            sa_type = 'sa.DateTime'
        elif col_type == 'Boolean':
            sa_type = 'sa.Boolean'
        elif col_type == 'Text':
            sa_type = 'sa.Text'
        else:
            sa_type = f'sa.{col_type}'
        
        col_def = f"sa.Column('{name}', {sa_type}"
        
        # Add constraints
        if column.get('primary_key'):
            col_def += ", primary_key=True"
        
        if column.get('nullable') is False:
            col_def += ", nullable=False"
        
        if column.get('default'):
            default_val = column['default']
            if default_val == 'func.now()':
                col_def += ", server_default=func.now()"
            else:
                col_def += f", default={default_val}"
        
        col_def += ")"
        
        # Add foreign key if specified
        if column.get('foreign_key'):
            fk_ref = column['foreign_key']
            col_def += f", sa.ForeignKey('{fk_ref}')"
        
        return col_def
    
    def _generate_add_column_code(self, operation: Dict[str, Any]) -> str:
        """Generate add column operation code"""
        table_name = operation['table_name']
        column = operation['column']
        col_def = self._generate_column_definition(column)
        
        return f"    op.add_column('{table_name}', {col_def})\n"
    
    def _generate_alter_column_code(self, operation: Dict[str, Any]) -> str:
        """Generate alter column operation code"""
        table_name = operation['table_name']
        column_name = operation['column_name']
        new_type = operation['new_type']
        
        # Convert type string to SQLAlchemy type
        if new_type.startswith('String'):
            length = new_type.replace('String(', '').replace(')', '')
            sa_type = f'sa.String({length})'
        else:
            sa_type = f'sa.{new_type}'
        
        return f"    op.alter_column('{table_name}', '{column_name}', type_={sa_type})\n"
    
    def _generate_create_index_code(self, operation: Dict[str, Any]) -> str:
        """Generate create index operation code"""
        table_name = operation['table_name']
        columns = operation['columns']
        index_name = operation['index_name']
        
        columns_str = ', '.join([f"'{col}'" for col in columns])
        return f"    op.create_index('{index_name}', '{table_name}', [{columns_str}])\n"
    
    def _generate_create_foreign_key_code(self, operation: Dict[str, Any]) -> str:
        """Generate create foreign key operation code"""
        table_name = operation['table_name']
        column_name = operation['column_name']
        referenced_table = operation['referenced_table']
        referenced_column = operation['referenced_column']
        constraint_name = operation['constraint_name']
        
        return f"    op.create_foreign_key('{constraint_name}', '{table_name}', '{referenced_table}', ['{column_name}'], ['{referenced_column}'])\n"
    
    def execute_server_migration(self, migration_id: str) -> Tuple[bool, Optional[str]]:
        """Execute migration on server database
        
        Args:
            migration_id: Migration identifier to execute
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.info(f"Executing migration on server: {migration_id}")
            
            # Find migration info
            migration_info = self._find_migration_by_id(migration_id)
            if not migration_info:
                raise ValueError(f"Migration not found: {migration_id}")
            
            self.current_migration = migration_info
            
            # Update database connection in alembic.ini for server
            self._update_alembic_config_for_database(self.server_config)
            
            # Execute Alembic upgrade with test configuration
            start_time = time.time()
            
            result = subprocess.run(
                ['alembic', '-c', self.alembic_config_path, 'upgrade', 'head'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Migration successful
                migration_info.status = "executed"
                migration_info.executed_at = datetime.now()
                
                self.logger.info(f"Server migration executed successfully: {migration_id} ({duration:.2f}s)")
                return True, None
            else:
                # Migration failed
                migration_info.status = "failed"
                error_msg = result.stderr or result.stdout
                
                self.logger.error(f"Server migration failed: {migration_id} - {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Migration execution failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def trigger_client_sync(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """Trigger synchronization on specific client to propagate schema changes
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.info(f"Triggering schema sync on client: {client_id}")
            
            # Get client configuration
            client_config = self.client_configs.get(client_id)
            if not client_config:
                raise ValueError(f"Client configuration not found: {client_id}")
            
            # Update alembic config for client database
            self._update_alembic_config_for_database(client_config)
            
            # Execute migration on client database with test configuration
            start_time = time.time()
            
            result = subprocess.run(
                ['alembic', '-c', self.alembic_config_path, 'upgrade', 'head'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"Client schema sync completed: {client_id} ({duration:.2f}s)")
                return True, None
            else:
                error_msg = result.stderr or result.stdout
                self.logger.error(f"Client schema sync failed: {client_id} - {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Client sync failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def verify_schema_consistency(self) -> Dict[str, Any]:
        """Verify schema consistency across all databases
        
        Returns:
            Schema consistency verification results
        """
        try:
            self.logger.info("Verifying schema consistency across databases")
            
            results = {
                'consistent': True,
                'server_schema': None,
                'client_schemas': {},
                'inconsistencies': [],
                'verification_time': datetime.now().isoformat()
            }
            
            # Get server schema version
            server_version = self._get_database_schema_version(self.server_config)
            results['server_schema'] = {
                'version': server_version,
                'database_type': self.server_config.db_type.value
            }
            
            # Get client schema versions
            for client_id, client_config in self.client_configs.items():
                client_version = self._get_database_schema_version(client_config)
                results['client_schemas'][client_id] = {
                    'version': client_version,
                    'database_type': client_config.db_type.value
                }
                
                # Check consistency
                if client_version != server_version:
                    results['consistent'] = False
                    results['inconsistencies'].append({
                        'client_id': client_id,
                        'server_version': server_version,
                        'client_version': client_version,
                        'issue': 'version_mismatch'
                    })
            
            if results['consistent']:
                self.logger.info("Schema consistency verification passed")
            else:
                self.logger.warning(f"Schema inconsistencies found: {len(results['inconsistencies'])}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Schema consistency verification failed: {e}")
            return {
                'consistent': False,
                'error': str(e),
                'verification_time': datetime.now().isoformat()
            }
    
    def _get_database_schema_version(self, db_config: DatabaseConfig) -> Optional[str]:
        """Get current schema version from database
        
        Args:
            db_config: Database configuration
            
        Returns:
            Current schema version or None if not found
        """
        try:
            # Update alembic config for this database
            self._update_alembic_config_for_database(db_config)
            
            # Get current revision
            result = subprocess.run(
                ['alembic', 'current'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Parse version from output
                output = result.stdout.strip()
                if output and 'head' not in output.lower():
                    return output.split()[0] if output.split() else None
                return 'head'
            else:
                self.logger.warning(f"Failed to get schema version for {db_config.db_type.value}: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting schema version for {db_config.db_type.value}: {e}")
            return None
    
    def _update_alembic_config_for_database(self, db_config: DatabaseConfig) -> None:
        """Update alembic.ini configuration for specific database
        
        Args:
            db_config: Database configuration to use
        """
        try:
            # Read current alembic.ini
            config_path = Path(self.alembic_config_path)
            if not config_path.exists():
                raise FileNotFoundError(f"Alembic config not found: {self.alembic_config_path}")
            
            # Update connection string
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Replace sqlalchemy.url line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('sqlalchemy.url'):
                    lines[i] = f"sqlalchemy.url = {db_config.connection_string}"
                    break
            
            # Write updated config
            with open(config_path, 'w') as f:
                f.write('\n'.join(lines))
            
            self.logger.debug(f"Updated alembic config for {db_config.db_type.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update alembic config: {e}")
            raise
    
    def rollback_migration(self, migration_id: str) -> Tuple[bool, Optional[str]]:
        """Rollback migration for testing purposes
        
        Args:
            migration_id: Migration identifier to rollback
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.info(f"Rolling back migration: {migration_id}")
            
            # Find migration info
            migration_info = self._find_migration_by_id(migration_id)
            if not migration_info:
                raise ValueError(f"Migration not found: {migration_id}")
            
            # Execute rollback on server
            self._update_alembic_config_for_database(self.server_config)
            
            # Get previous revision
            result = subprocess.run(
                ['alembic', 'downgrade', '-1'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                migration_info.status = "rolled_back"
                migration_info.rollback_at = datetime.now()
                
                self.logger.info(f"Migration rolled back successfully: {migration_id}")
                return True, None
            else:
                error_msg = result.stderr or result.stdout
                self.logger.error(f"Migration rollback failed: {migration_id} - {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Migration rollback failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _find_migration_by_id(self, migration_id: str) -> Optional[MigrationInfo]:
        """Find migration info by ID
        
        Args:
            migration_id: Migration identifier
            
        Returns:
            MigrationInfo or None if not found
        """
        for migration in self.migration_history:
            if migration.migration_id == migration_id:
                return migration
        return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history
        
        Returns:
            List of migration information dictionaries
        """
        return [
            {
                'migration_id': migration.migration_id,
                'name': migration.name,
                'description': migration.description,
                'status': migration.status,
                'created_at': migration.created_at.isoformat(),
                'executed_at': migration.executed_at.isoformat() if migration.executed_at else None,
                'rollback_at': migration.rollback_at.isoformat() if migration.rollback_at else None
            }
            for migration in self.migration_history
        ]
    
    def get_migration_performance_metrics(self) -> Dict[str, Any]:
        """Get migration performance metrics
        
        Returns:
            Performance metrics dictionary
        """
        executed_migrations = [m for m in self.migration_history if m.executed_at]
        
        if not executed_migrations:
            return {'total_migrations': 0, 'avg_execution_time': 0}
        
        # Calculate execution times (this would need to be tracked during execution)
        # For now, return basic metrics
        return {
            'total_migrations': len(executed_migrations),
            'successful_migrations': len([m for m in executed_migrations if m.status == 'executed']),
            'failed_migrations': len([m for m in executed_migrations if m.status == 'failed']),
            'rolled_back_migrations': len([m for m in executed_migrations if m.status == 'rolled_back'])
        }
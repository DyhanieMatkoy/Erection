"""Multi-Database Test Environment Manager

This module extends the test environment manager to support multiple database types
and provides comprehensive testing capabilities for cross-database synchronization.
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

from test_environment_manager import TestEnvironmentManager, TestDesktopClient
from database_configuration_manager import DatabaseConfigurationManager, DatabaseConfig, DatabaseType
from alembic_migration_manager import AlembicMigrationManager
from schema_synchronization_validator import SchemaSynchronizationValidator


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    description: str
    server_db_type: DatabaseType
    client_db_types: Dict[str, DatabaseType]
    migration_tests: List[str]
    expected_duration: int  # seconds


class MultiDatabaseTestEnvironmentManager(TestEnvironmentManager):
    """Extended test environment manager for multi-database testing"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize multi-database test environment manager
        
        Args:
            config: Test configuration
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Multi-database components
        self.db_config_manager = DatabaseConfigurationManager(logger)
        self.migration_manager: Optional[AlembicMigrationManager] = None
        self.schema_validator: Optional[SchemaSynchronizationValidator] = None
        
        # Test scenarios
        self.test_scenarios = self._initialize_test_scenarios()
        self.current_scenario: Optional[TestScenario] = None
        
        # Multi-database state
        self.server_db_config: Optional[DatabaseConfig] = None
        self.client_db_configs: Dict[str, DatabaseConfig] = {}
        
        self.logger.info("Multi-database test environment manager initialized")
    
    def _initialize_test_scenarios(self) -> Dict[str, TestScenario]:
        """Initialize predefined test scenarios
        
        Returns:
            Dictionary of test scenarios
        """
        return {
            'sqlite_only': TestScenario(
                name='SQLite Only Testing',
                description='SQLite server with SQLite clients (no external DB required)',
                server_db_type=DatabaseType.SQLITE,
                client_db_types={
                    'client_1': DatabaseType.SQLITE,
                    'client_2': DatabaseType.SQLITE,
                    'client_3': DatabaseType.SQLITE
                },
                migration_tests=['add_project_phases_table', 'add_priority_to_estimates'],
                expected_duration=180  # 3 minutes
            ),
            'postgresql_mixed': TestScenario(
                name='PostgreSQL Server with Mixed Desktop Clients',
                description='PostgreSQL server with SQLite + MySQL clients',
                server_db_type=DatabaseType.POSTGRESQL,
                client_db_types={
                    'client_1': DatabaseType.SQLITE,
                    'client_2': DatabaseType.MYSQL,
                    'client_3': DatabaseType.MYSQL
                },
                migration_tests=['add_project_phases_table', 'add_priority_to_estimates'],
                expected_duration=300  # 5 minutes
            ),
            'mysql_mixed': TestScenario(
                name='MySQL Server with Mixed Desktop Clients',
                description='MySQL server with SQLite + MySQL clients',
                server_db_type=DatabaseType.MYSQL,
                client_db_types={
                    'client_1': DatabaseType.SQLITE,
                    'client_2': DatabaseType.SQLITE,
                    'client_3': DatabaseType.MYSQL
                },
                migration_tests=['extend_description_length', 'add_indexes_for_performance'],
                expected_duration=280  # 4.5 minutes
            ),
            'sqlite_mysql': TestScenario(
                name='SQLite Server with MySQL Desktop Clients',
                description='SQLite server with MySQL clients',
                server_db_type=DatabaseType.SQLITE,
                client_db_types={
                    'client_1': DatabaseType.MYSQL,
                    'client_2': DatabaseType.MYSQL,
                    'client_3': DatabaseType.MYSQL
                },
                migration_tests=['add_foreign_key_constraints'],
                expected_duration=240  # 4 minutes
            )
        }
    
    def setup_multi_database_environment(self, scenario_name: str) -> bool:
        """Setup multi-database test environment for specific scenario
        
        Args:
            scenario_name: Name of the test scenario to setup
            
        Returns:
            True if setup successful
        """
        try:
            self.logger.info(f"Setting up multi-database environment: {scenario_name}")
            
            # Get scenario configuration
            if scenario_name not in self.test_scenarios:
                raise ValueError(f"Unknown test scenario: {scenario_name}")
            
            scenario = self.test_scenarios[scenario_name]
            self.current_scenario = scenario
            
            # Setup server database configuration
            self.logger.info(f"Configuring server database: {scenario.server_db_type.value}")
            self.server_db_config = self.db_config_manager.create_server_config(scenario.server_db_type)
            
            # Setup server database
            if not self.db_config_manager.setup_database_for_testing(self.server_db_config):
                raise Exception("Failed to setup server database")
            
            # Validate server database connectivity
            success, error = self.db_config_manager.validate_database_connectivity(self.server_db_config)
            if not success:
                raise Exception(f"Server database connectivity failed: {error}")
            
            # Setup client database configurations
            for client_id, db_type in scenario.client_db_types.items():
                self.logger.info(f"Configuring client database: {client_id} ({db_type.value})")
                
                client_config = self.db_config_manager.create_client_config(client_id, db_type)
                self.client_db_configs[client_id] = client_config
                
                # Setup client database
                if not self.db_config_manager.setup_database_for_testing(client_config):
                    raise Exception(f"Failed to setup client database: {client_id}")
                
                # Validate client database connectivity
                success, error = self.db_config_manager.validate_database_connectivity(client_config)
                if not success:
                    raise Exception(f"Client database connectivity failed ({client_id}): {error}")
            
            # Initialize migration manager
            self.migration_manager = AlembicMigrationManager(
                server_db_config=self.server_db_config,
                client_db_configs=self.client_db_configs,
                logger=self.logger
            )
            
            # Initialize schema validator
            all_db_configs = {'server': self.server_db_config}
            all_db_configs.update(self.client_db_configs)
            
            self.schema_validator = SchemaSynchronizationValidator(
                database_configs=all_db_configs,
                logger=self.logger
            )
            
            # Start server with appropriate database configuration
            self._update_server_database_config()
            self.start_server()
            
            # Create desktop clients with appropriate database configurations
            for client_id in scenario.client_db_types.keys():
                client = self.create_multi_database_desktop_client(client_id)
                if not client:
                    raise Exception(f"Failed to create desktop client: {client_id}")
            
            # Verify all client connections
            self.verify_client_connections(self.desktop_clients)
            
            self.logger.info(f"Multi-database environment setup completed: {scenario_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup multi-database environment: {e}")
            return False
    
    def create_multi_database_desktop_client(self, client_id: str) -> Optional[TestDesktopClient]:
        """Create desktop client with specific database configuration
        
        Args:
            client_id: Client identifier
            
        Returns:
            TestDesktopClient instance or None if failed
        """
        try:
            self.logger.info(f"Creating multi-database desktop client: {client_id}")
            
            # Get client database configuration
            client_config = self.client_db_configs.get(client_id)
            if not client_config:
                raise ValueError(f"Client configuration not found: {client_id}")
            
            # Determine database path based on configuration
            if client_config.db_type == DatabaseType.SQLITE:
                db_path = client_config.additional_params['database_path']
            else:
                # For MySQL/PostgreSQL, we'll use the connection string
                db_path = client_config.connection_string
            
            # Create client instance
            client = TestDesktopClient(
                client_id=client_id,
                database_path=db_path,
                server_url=self.config['server_url'],
                logger=self.logger
            )
            
            # Set database configuration for this client
            client.db_config = client_config
            
            # Start the client with multi-database support
            if not self._start_multi_database_client(client):
                raise Exception(f"Failed to start multi-database client: {client_id}")
            
            self.desktop_clients.append(client)
            
            self.logger.info(f"Multi-database desktop client created: {client_id} ({client_config.db_type.value})")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to create multi-database desktop client {client_id}: {e}")
            return None
    
    def _start_multi_database_client(self, client: TestDesktopClient) -> bool:
        """Start desktop client with multi-database configuration
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            True if started successfully
        """
        try:
            # Initialize database manager with specific configuration
            from src.data.database_manager import DatabaseManager
            
            client.db_manager = DatabaseManager()
            
            # Configure database manager for specific database type
            if hasattr(client, 'db_config'):
                success = self._configure_database_manager(client.db_manager, client.db_config)
                if not success:
                    raise Exception("Failed to configure database manager")
            else:
                # Fallback to original initialization
                success = client.db_manager.initialize(client.database_path)
                if not success:
                    raise Exception(f"Failed to initialize database: {client.database_path}")
            
            # Initialize sync schema
            client._initialize_sync_schema()
            
            # Create sync configuration
            client._create_sync_config()
            
            # Initialize sync service
            from src.services.sync_service import SyncService
            
            client.sync_service = SyncService(
                db_manager=client.db_manager,
                server_url=client.server_url,
                node_code=client.node_code
            )
            
            # Register with server
            client._register_with_server()
            
            client.is_running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start multi-database client {client.client_id}: {e}")
            return False
    
    def _configure_database_manager(self, db_manager, db_config: DatabaseConfig) -> bool:
        """Configure database manager for specific database type
        
        Args:
            db_manager: DatabaseManager instance
            db_config: Database configuration
            
        Returns:
            True if configured successfully
        """
        try:
            # Set connection string based on database type
            if db_config.db_type == DatabaseType.SQLITE:
                return db_manager.initialize(db_config.additional_params['database_path'])
            else:
                # For PostgreSQL/MySQL, we need to configure the connection string
                # This would require modifications to DatabaseManager to support different DB types
                # For now, we'll use a simplified approach
                return db_manager.initialize_with_connection_string(db_config.connection_string)
                
        except Exception as e:
            self.logger.error(f"Failed to configure database manager: {e}")
            return False
    
    def _update_server_database_config(self) -> None:
        """Update server configuration to use the specified database type"""
        try:
            if not self.server_db_config:
                raise Exception("Server database configuration not set")
            
            # Initialize server database with proper schema
            self._initialize_server_database_schema()
            
            # Update environment configuration file
            config_path = Path("env.ini")
            
            if config_path.exists():
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Update database configuration
                if 'Database' not in config:
                    config.add_section('Database')
                
                config['Database']['connection_string'] = self.server_db_config.connection_string
                config['Database']['type'] = self.server_db_config.db_type.value
                
                with open(config_path, 'w') as f:
                    config.write(f)
                
                self.logger.debug(f"Updated server database configuration: {self.server_db_config.db_type.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update server database config: {e}")
            raise
    
    def _initialize_server_database_schema(self) -> None:
        """Initialize server database with proper schema"""
        try:
            self.logger.info("Initializing server database schema")
            
            # Import database manager to initialize schema
            from src.data.database_manager import DatabaseManager
            
            # Create database manager for server
            server_db_manager = DatabaseManager()
            
            if self.server_db_config.db_type == DatabaseType.SQLITE:
                # For SQLite, use the database path
                database_path = self.server_db_config.additional_params['database_path']
                success = server_db_manager.initialize(database_path)
            else:
                # For PostgreSQL/MySQL, use connection string
                success = server_db_manager.initialize_with_connection_string(self.server_db_config.connection_string)
            
            if not success:
                raise Exception("Failed to initialize server database manager")
            
            # Initialize all required tables
            self._create_server_database_tables(server_db_manager)
            
            self.logger.info("Server database schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize server database schema: {e}")
            # Don't raise - continue with empty schema for testing
    
    def _create_server_database_tables(self, db_manager) -> None:
        """Create all required tables in server database"""
        try:
            # Import all model classes from existing files
            from src.data.models.estimate import Estimate, EstimateLine
            from src.data.models.daily_report import DailyReport, DailyReportLine
            from src.data.models.references import Work, Organization, Counterparty, Person, Object
            from src.data.models.user import User
            from src.data.models.audit import AuditLog
            from src.data.models.sync_models import SyncNode, SyncChange
            
            # Note: Some models may not exist yet, so we'll use what's available
            
            # Get database engine
            engine = db_manager.get_engine()
            
            # Create all tables
            model_classes = [
                # Core models that exist
                Organization, Counterparty, Person, Object, User,
                # Work and estimation models
                Work, Estimate, EstimateLine,
                # Daily report models
                DailyReport, DailyReportLine,
                # System models
                AuditLog,
                # Sync models
                SyncNode, SyncChange
            ]
            
            for model_class in model_classes:
                try:
                    if hasattr(model_class, '__table__'):
                        model_class.__table__.create(engine, checkfirst=True)
                        self.logger.debug(f"Created table for {model_class.__name__}")
                except Exception as e:
                    self.logger.warning(f"Failed to create table for {model_class.__name__}: {e}")
            
            self.logger.info(f"Created {len(model_classes)} tables in server database")
            
        except Exception as e:
            self.logger.error(f"Failed to create server database tables: {e}")
            # Continue without full schema
    
    def execute_migration_test_scenario(self, migration_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute migration testing scenario
        
        Args:
            migration_names: List of migration names to test (uses scenario default if None)
            
        Returns:
            Migration test results
        """
        try:
            self.logger.info("Executing migration test scenario")
            
            if not self.migration_manager:
                raise Exception("Migration manager not initialized")
            
            if not self.current_scenario:
                raise Exception("No test scenario active")
            
            # Use provided migrations or scenario defaults
            migrations_to_test = migration_names or self.current_scenario.migration_tests
            
            results = {
                'scenario': self.current_scenario.name,
                'migrations_tested': [],
                'migration_results': {},
                'schema_consistency_checks': [],
                'overall_success': True,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration': 0
            }
            
            start_time = time.time()
            
            # Execute each migration
            for migration_name in migrations_to_test:
                self.logger.info(f"Testing migration: {migration_name}")
                
                migration_result = {
                    'migration_name': migration_name,
                    'server_execution': None,
                    'client_propagation': {},
                    'schema_consistency': None,
                    'success': True
                }
                
                try:
                    # Create and execute migration on server
                    migration_info = self.migration_manager.create_test_migration(migration_name)
                    
                    server_success, server_error = self.migration_manager.execute_server_migration(migration_info.migration_id)
                    migration_result['server_execution'] = {
                        'success': server_success,
                        'error': server_error,
                        'migration_id': migration_info.migration_id
                    }
                    
                    if not server_success:
                        migration_result['success'] = False
                        results['overall_success'] = False
                        self.logger.error(f"Server migration failed: {migration_name} - {server_error}")
                        continue
                    
                    # Trigger synchronization on all clients
                    for client_id in self.client_db_configs.keys():
                        self.logger.info(f"Propagating migration to client: {client_id}")
                        
                        client_success, client_error = self.migration_manager.trigger_client_sync(client_id)
                        migration_result['client_propagation'][client_id] = {
                            'success': client_success,
                            'error': client_error
                        }
                        
                        if not client_success:
                            migration_result['success'] = False
                            results['overall_success'] = False
                            self.logger.error(f"Client migration failed: {client_id} - {client_error}")
                    
                    # Verify schema consistency
                    if migration_result['success']:
                        consistency_results = self.migration_manager.verify_schema_consistency()
                        migration_result['schema_consistency'] = consistency_results
                        
                        if not consistency_results['consistent']:
                            migration_result['success'] = False
                            results['overall_success'] = False
                            self.logger.error(f"Schema consistency check failed for migration: {migration_name}")
                    
                except Exception as e:
                    migration_result['success'] = False
                    migration_result['error'] = str(e)
                    results['overall_success'] = False
                    self.logger.error(f"Migration test failed: {migration_name} - {e}")
                
                results['migration_results'][migration_name] = migration_result
                results['migrations_tested'].append(migration_name)
            
            # Final schema consistency validation
            if self.schema_validator:
                self.logger.info("Performing final schema consistency validation")
                
                final_validation = self.schema_validator.validate_cross_database_sync()
                results['schema_consistency_checks'].append(final_validation)
                
                if not final_validation['overall_consistent']:
                    results['overall_success'] = False
                    self.logger.warning("Final schema consistency validation failed")
            
            # Calculate duration
            end_time = time.time()
            results['duration'] = round(end_time - start_time, 2)
            results['end_time'] = datetime.now().isoformat()
            
            status = "SUCCESS" if results['overall_success'] else "FAILED"
            self.logger.info(f"Migration test scenario completed: {status} ({results['duration']}s)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Migration test scenario failed: {e}")
            return {
                'scenario': self.current_scenario.name if self.current_scenario else 'Unknown',
                'overall_success': False,
                'error': str(e),
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 0
            }
    
    def execute_full_sync_workflow_test(self) -> Dict[str, Any]:
        """Execute full synchronization workflow test with document creation
        
        Returns:
            Sync workflow test results
        """
        try:
            self.logger.info("Executing full sync workflow test")
            
            results = {
                'scenario': self.current_scenario.name if self.current_scenario else 'Unknown',
                'document_creation': {},
                'synchronization_results': {},
                'data_verification': {},
                'overall_success': True,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration': 0
            }
            
            start_time = time.time()
            
            # Document creation phase
            self.logger.info("Phase 1: Document creation")
            
            document_templates = {
                'client_1': {'type': 'estimate', 'name': 'Test Estimate Multi-DB'},
                'client_2': {'type': 'daily_report', 'date': datetime.now().strftime('%Y-%m-%d')},
                'client_3': {'type': 'timesheet', 'period': 'Week 1'}
            }
            
            created_documents = []
            
            for client in self.desktop_clients:
                if client.client_id in document_templates:
                    doc_template = document_templates[client.client_id]
                    
                    try:
                        doc_info = client.create_document(doc_template['type'], doc_template)
                        created_documents.append({
                            'client_id': client.client_id,
                            'document_type': doc_template['type'],
                            'document_id': doc_info.get('id'),
                            'success': True
                        })
                        
                        results['document_creation'][client.client_id] = {
                            'success': True,
                            'document_info': doc_info
                        }
                        
                    except Exception as e:
                        self.logger.error(f"Document creation failed on {client.client_id}: {e}")
                        results['document_creation'][client.client_id] = {
                            'success': False,
                            'error': str(e)
                        }
                        results['overall_success'] = False
            
            # Synchronization phase
            self.logger.info("Phase 2: Synchronization")
            
            for client in self.desktop_clients:
                try:
                    sync_result = client.trigger_sync()
                    results['synchronization_results'][client.client_id] = sync_result
                    
                    if sync_result['status'] != 'success':
                        results['overall_success'] = False
                        
                except Exception as e:
                    self.logger.error(f"Synchronization failed on {client.client_id}: {e}")
                    results['synchronization_results'][client.client_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    results['overall_success'] = False
            
            # Data verification phase
            self.logger.info("Phase 3: Data verification")
            
            for client in self.desktop_clients:
                try:
                    verification_result = client.verify_documents(created_documents)
                    results['data_verification'][client.client_id] = verification_result
                    
                    if not verification_result['success']:
                        results['overall_success'] = False
                        
                except Exception as e:
                    self.logger.error(f"Data verification failed on {client.client_id}: {e}")
                    results['data_verification'][client.client_id] = {
                        'success': False,
                        'error': str(e)
                    }
                    results['overall_success'] = False
            
            # Calculate duration
            end_time = time.time()
            results['duration'] = round(end_time - start_time, 2)
            results['end_time'] = datetime.now().isoformat()
            
            status = "SUCCESS" if results['overall_success'] else "FAILED"
            self.logger.info(f"Full sync workflow test completed: {status} ({results['duration']}s)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Full sync workflow test failed: {e}")
            return {
                'scenario': self.current_scenario.name if self.current_scenario else 'Unknown',
                'overall_success': False,
                'error': str(e),
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 0
            }
    
    def execute_all_test_scenarios(self) -> Dict[str, Any]:
        """Execute all predefined test scenarios
        
        Returns:
            Results from all test scenarios
        """
        try:
            self.logger.info("Executing all multi-database test scenarios")
            
            all_results = {
                'total_scenarios': len(self.test_scenarios),
                'successful_scenarios': 0,
                'failed_scenarios': 0,
                'scenario_results': {},
                'overall_success': True,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_duration': 0
            }
            
            start_time = time.time()
            
            for scenario_name in self.test_scenarios.keys():
                self.logger.info(f"Executing scenario: {scenario_name}")
                
                scenario_result = {
                    'setup_success': False,
                    'sync_workflow_results': None,
                    'migration_test_results': None,
                    'cleanup_success': False,
                    'overall_success': False
                }
                
                try:
                    # Setup environment for this scenario
                    setup_success = self.setup_multi_database_environment(scenario_name)
                    scenario_result['setup_success'] = setup_success
                    
                    if setup_success:
                        # Execute sync workflow test
                        sync_results = self.execute_full_sync_workflow_test()
                        scenario_result['sync_workflow_results'] = sync_results
                        
                        # Execute migration tests
                        migration_results = self.execute_migration_test_scenario()
                        scenario_result['migration_test_results'] = migration_results
                        
                        # Determine overall success
                        scenario_result['overall_success'] = (
                            sync_results['overall_success'] and 
                            migration_results['overall_success']
                        )
                        
                        if scenario_result['overall_success']:
                            all_results['successful_scenarios'] += 1
                        else:
                            all_results['failed_scenarios'] += 1
                            all_results['overall_success'] = False
                    else:
                        all_results['failed_scenarios'] += 1
                        all_results['overall_success'] = False
                    
                    # Cleanup environment
                    self.cleanup_multi_database_environment()
                    scenario_result['cleanup_success'] = True
                    
                except Exception as e:
                    self.logger.error(f"Scenario execution failed: {scenario_name} - {e}")
                    scenario_result['error'] = str(e)
                    all_results['failed_scenarios'] += 1
                    all_results['overall_success'] = False
                    
                    # Attempt cleanup even if scenario failed
                    try:
                        self.cleanup_multi_database_environment()
                        scenario_result['cleanup_success'] = True
                    except Exception as cleanup_error:
                        self.logger.error(f"Cleanup failed for scenario {scenario_name}: {cleanup_error}")
                        scenario_result['cleanup_success'] = False
                
                all_results['scenario_results'][scenario_name] = scenario_result
            
            # Calculate total duration
            end_time = time.time()
            all_results['total_duration'] = round(end_time - start_time, 2)
            all_results['end_time'] = datetime.now().isoformat()
            
            status = "SUCCESS" if all_results['overall_success'] else "FAILED"
            self.logger.info(f"All scenarios completed: {status} ({all_results['total_duration']}s)")
            self.logger.info(f"Results: {all_results['successful_scenarios']} successful, {all_results['failed_scenarios']} failed")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Failed to execute all test scenarios: {e}")
            return {
                'total_scenarios': len(self.test_scenarios),
                'successful_scenarios': 0,
                'failed_scenarios': len(self.test_scenarios),
                'overall_success': False,
                'error': str(e),
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration': 0
            }
    
    def cleanup_multi_database_environment(self) -> None:
        """Clean up multi-database test environment"""
        try:
            self.logger.info("Cleaning up multi-database test environment")
            
            # Stop all desktop clients
            for client in self.desktop_clients:
                try:
                    client.stop()
                except Exception as e:
                    self.logger.warning(f"Error stopping client {client.client_id}: {e}")
            
            # Stop server
            if self.server_process:
                try:
                    self.server_process.terminate()
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                except Exception as e:
                    self.logger.error(f"Error stopping server: {e}")
            
            # Clean up databases
            if self.server_db_config:
                self.db_config_manager.cleanup_database(self.server_db_config)
            
            for client_id, client_config in self.client_db_configs.items():
                self.db_config_manager.cleanup_database(client_config)
            
            # Reset state
            self.desktop_clients.clear()
            self.test_databases.clear()
            self.server_db_config = None
            self.client_db_configs.clear()
            self.current_scenario = None
            self.migration_manager = None
            self.schema_validator = None
            
            self.logger.info("Multi-database test environment cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during multi-database environment cleanup: {e}")
    
    def get_test_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get available test scenarios
        
        Returns:
            Dictionary of test scenario information
        """
        return {
            name: {
                'name': scenario.name,
                'description': scenario.description,
                'server_db_type': scenario.server_db_type.value,
                'client_db_types': {k: v.value for k, v in scenario.client_db_types.items()},
                'migration_tests': scenario.migration_tests,
                'expected_duration': scenario.expected_duration
            }
            for name, scenario in self.test_scenarios.items()
        }
    
    def generate_multi_database_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate comprehensive test report for multi-database testing
        
        Args:
            test_results: Test results from execute_all_test_scenarios
            
        Returns:
            Formatted test report as string
        """
        try:
            report_lines = []
            report_lines.append("=" * 100)
            report_lines.append("MULTI-DATABASE SYNCHRONIZATION TEST REPORT")
            report_lines.append("=" * 100)
            report_lines.append("")
            
            # Executive summary
            report_lines.append("EXECUTIVE SUMMARY")
            report_lines.append("-" * 50)
            report_lines.append(f"Overall Result: {'PASS' if test_results['overall_success'] else 'FAIL'}")
            report_lines.append(f"Total Scenarios: {test_results['total_scenarios']}")
            report_lines.append(f"Successful Scenarios: {test_results['successful_scenarios']}")
            report_lines.append(f"Failed Scenarios: {test_results['failed_scenarios']}")
            report_lines.append(f"Total Duration: {test_results['total_duration']} seconds")
            report_lines.append(f"Test Execution Time: {test_results['start_time']} - {test_results['end_time']}")
            report_lines.append("")
            
            # Detailed scenario results
            report_lines.append("DETAILED SCENARIO RESULTS")
            report_lines.append("-" * 50)
            
            for scenario_name, scenario_result in test_results['scenario_results'].items():
                scenario_info = self.test_scenarios.get(scenario_name)
                
                report_lines.append(f"Scenario: {scenario_name}")
                if scenario_info:
                    report_lines.append(f"  Description: {scenario_info.description}")
                    report_lines.append(f"  Server DB: {scenario_info.server_db_type.value}")
                    report_lines.append(f"  Client DBs: {', '.join([f'{k}={v.value}' for k, v in scenario_info.client_db_types.items()])}")
                
                report_lines.append(f"  Overall Result: {'PASS' if scenario_result['overall_success'] else 'FAIL'}")
                report_lines.append(f"  Setup: {'SUCCESS' if scenario_result['setup_success'] else 'FAILED'}")
                report_lines.append(f"  Cleanup: {'SUCCESS' if scenario_result['cleanup_success'] else 'FAILED'}")
                
                # Sync workflow results
                if scenario_result['sync_workflow_results']:
                    sync_results = scenario_result['sync_workflow_results']
                    report_lines.append(f"  Sync Workflow: {'PASS' if sync_results['overall_success'] else 'FAIL'}")
                    report_lines.append(f"    Duration: {sync_results['duration']} seconds")
                    
                    # Document creation summary
                    doc_success = sum(1 for r in sync_results['document_creation'].values() if r['success'])
                    doc_total = len(sync_results['document_creation'])
                    report_lines.append(f"    Document Creation: {doc_success}/{doc_total} successful")
                    
                    # Synchronization summary
                    sync_success = sum(1 for r in sync_results['synchronization_results'].values() if r['status'] == 'success')
                    sync_total = len(sync_results['synchronization_results'])
                    report_lines.append(f"    Synchronization: {sync_success}/{sync_total} successful")
                    
                    # Verification summary
                    verify_success = sum(1 for r in sync_results['data_verification'].values() if r['success'])
                    verify_total = len(sync_results['data_verification'])
                    report_lines.append(f"    Data Verification: {verify_success}/{verify_total} successful")
                
                # Migration test results
                if scenario_result['migration_test_results']:
                    migration_results = scenario_result['migration_test_results']
                    report_lines.append(f"  Migration Tests: {'PASS' if migration_results['overall_success'] else 'FAIL'}")
                    report_lines.append(f"    Duration: {migration_results['duration']} seconds")
                    report_lines.append(f"    Migrations Tested: {len(migration_results['migrations_tested'])}")
                    
                    # Migration success summary
                    migration_success = sum(1 for r in migration_results['migration_results'].values() if r['success'])
                    migration_total = len(migration_results['migration_results'])
                    report_lines.append(f"    Migration Success Rate: {migration_success}/{migration_total}")
                
                if 'error' in scenario_result:
                    report_lines.append(f"  Error: {scenario_result['error']}")
                
                report_lines.append("")
            
            report_lines.append("=" * 100)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            self.logger.error(f"Failed to generate multi-database test report: {e}")
            return f"Error generating test report: {e}"
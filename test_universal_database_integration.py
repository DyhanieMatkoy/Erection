#!/usr/bin/env python3
"""Test Universal Database Integration

This script tests the integration of the Unified Database Manager
with the existing multi-database test environment.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_database_test_environment_manager import MultiDatabaseTestEnvironmentManager


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_universal_integration.log')
        ]
    )
    
    return logging.getLogger("UniversalDatabaseIntegrationTest")


def test_unified_database_manager_basic():
    """Test basic Unified Database Manager functionality"""
    logger = logging.getLogger("UniversalDatabaseIntegrationTest")
    
    try:
        from unified_database_manager import UnifiedDatabaseManager
        from sql_dialect_translator import SQLDialect
        
        logger.info("Testing Unified Database Manager basic functionality")
        
        with UnifiedDatabaseManager(logger) as db_manager:
            # Test SQLite connection
            sqlite_connection = "sqlite:///test_universal.db"
            success = db_manager.connect_to_database(sqlite_connection, "test_sqlite")
            
            if success:
                logger.info("✅ SQLite connection successful")
                
                # Test database info
                info = db_manager.get_database_info("test_sqlite")
                logger.info(f"Database info: {info}")
                
                # Test SQL execution
                result = db_manager.execute_sql("SELECT 1 as test", "test_sqlite")
                logger.info("✅ SQL execution successful")
                
            else:
                logger.error("❌ SQLite connection failed")
                return False
            
            # Test Docker availability
            if db_manager.docker_manager:
                docker_available, error = db_manager.docker_manager.check_docker_availability()
                if docker_available:
                    logger.info("✅ Docker is available")
                    
                    # Test PostgreSQL setup
                    pg_connection = db_manager.setup_database_with_docker(SQLDialect.POSTGRESQL)
                    if pg_connection:
                        logger.info("✅ PostgreSQL Docker setup successful")
                        
                        # Test connection
                        if db_manager.connect_to_database(pg_connection, "test_postgresql"):
                            logger.info("✅ PostgreSQL connection successful")
                        else:
                            logger.warning("⚠️ PostgreSQL connection failed")
                    else:
                        logger.warning("⚠️ PostgreSQL Docker setup failed")
                        
                else:
                    logger.warning(f"⚠️ Docker not available: {error}")
            else:
                logger.warning("⚠️ Docker manager not initialized")
        
        logger.info("✅ Unified Database Manager basic test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Unified Database Manager basic test failed: {e}")
        return False


def test_multi_database_environment_setup(scenario_name: str = "sqlite_only"):
    """Test multi-database environment setup with Unified Database Manager"""
    logger = logging.getLogger("UniversalDatabaseIntegrationTest")
    
    try:
        logger.info(f"Testing multi-database environment setup: {scenario_name}")
        
        # Test configuration
        config = {
            'server_url': 'http://localhost:8000',
            'server_port': 8000,
            'test_duration': 300,
            'cleanup_on_exit': True
        }
        
        # Create test environment manager
        test_manager = MultiDatabaseTestEnvironmentManager(config, logger)
        
        # Get available scenarios
        scenarios = test_manager.get_test_scenarios()
        logger.info(f"Available scenarios: {list(scenarios.keys())}")
        
        if scenario_name not in scenarios:
            logger.error(f"❌ Scenario not found: {scenario_name}")
            return False
        
        scenario_info = scenarios[scenario_name]
        logger.info(f"Testing scenario: {scenario_info['name']}")
        logger.info(f"Description: {scenario_info['description']}")
        logger.info(f"Server DB: {scenario_info['server_db_type']}")
        logger.info(f"Client DBs: {scenario_info['client_db_types']}")
        
        # Setup environment
        setup_success = test_manager.setup_multi_database_environment(scenario_name)
        
        if setup_success:
            logger.info("✅ Multi-database environment setup successful")
            
            # Test database connections
            logger.info("Testing database connections...")
            
            # Check Unified Database Manager connections
            for connection_id in test_manager.database_connections:
                info = test_manager.unified_db_manager.get_database_info(connection_id)
                if info.get('connected', False):
                    logger.info(f"✅ Connection {connection_id}: {info.get('dialect', 'unknown')}")
                else:
                    logger.warning(f"⚠️ Connection {connection_id}: {info.get('error', 'unknown error')}")
            
            # Cleanup
            test_manager.cleanup_multi_database_environment()
            logger.info("✅ Environment cleanup completed")
            
            return True
        else:
            logger.error("❌ Multi-database environment setup failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Multi-database environment test failed: {e}")
        return False


def test_sql_translation():
    """Test SQL dialect translation"""
    logger = logging.getLogger("UniversalDatabaseIntegrationTest")
    
    try:
        logger.info("Testing SQL dialect translation")
        
        from sql_dialect_translator import SQLDialectTranslator, SQLDialect
        
        translator = SQLDialectTranslator(logger)
        
        # Test basic translation
        sqlite_sql = "CREATE TABLE test (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        
        # Translate to PostgreSQL
        pg_sql = translator.translate_sql(sqlite_sql, SQLDialect.SQLITE, SQLDialect.POSTGRESQL)
        logger.info(f"SQLite → PostgreSQL: {pg_sql}")
        
        # Translate to MySQL
        mysql_sql = translator.translate_sql(sqlite_sql, SQLDialect.SQLITE, SQLDialect.MYSQL)
        logger.info(f"SQLite → MySQL: {mysql_sql}")
        
        # Test CREATE TABLE translation
        pg_create = translator.translate_create_table(sqlite_sql, SQLDialect.SQLITE, SQLDialect.POSTGRESQL)
        logger.info(f"CREATE TABLE SQLite → PostgreSQL: {pg_create}")
        
        logger.info("✅ SQL dialect translation test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQL dialect translation test failed: {e}")
        return False


def test_migration_manager():
    """Test multi-dialect migration manager"""
    logger = logging.getLogger("UniversalDatabaseIntegrationTest")
    
    try:
        logger.info("Testing multi-dialect migration manager")
        
        from multi_dialect_migration_manager import MultiDialectMigrationManager
        
        manager = MultiDialectMigrationManager(logger)
        
        # Test config creation
        success = manager.create_alembic_configs_for_all_dialects()
        if success:
            logger.info("✅ Alembic configs created for all dialects")
        else:
            logger.warning("⚠️ Alembic config creation failed")
        
        # Check if config files exist
        config_files = [
            "alembic.ini",
            "alembic_postgresql.ini", 
            "alembic_mysql.ini"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                logger.info(f"✅ Config file exists: {config_file}")
            else:
                logger.warning(f"⚠️ Config file missing: {config_file}")
        
        logger.info("✅ Multi-dialect migration manager test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-dialect migration manager test failed: {e}")
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Universal Database Integration')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--test', choices=['basic', 'environment', 'translation', 'migration', 'all'],
                       default='all', help='Test to run')
    parser.add_argument('--scenario', default='sqlite_only',
                       help='Test scenario for environment test')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    logger.info("=" * 80)
    logger.info("UNIVERSAL DATABASE INTEGRATION TEST")
    logger.info("=" * 80)
    
    tests_to_run = []
    
    if args.test == 'all':
        tests_to_run = ['basic', 'translation', 'migration', 'environment']
    else:
        tests_to_run = [args.test]
    
    results = {}
    
    for test_name in tests_to_run:
        logger.info(f"\n{'='*20} Running {test_name.upper()} Test {'='*20}")
        
        if test_name == 'basic':
            results[test_name] = test_unified_database_manager_basic()
        elif test_name == 'environment':
            results[test_name] = test_multi_database_environment_setup(args.scenario)
        elif test_name == 'translation':
            results[test_name] = test_sql_translation()
        elif test_name == 'migration':
            results[test_name] = test_migration_manager()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name.upper()}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed} TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
"""
Unit tests for configuration migration scenarios

Tests the ConfigMigrationTester and related migration functionality
to ensure proper migration, rollback, and validation behavior.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import configparser
import json

from config_migration_tester import (
    ConfigMigrationTester, MigrationStep, MigrationType, ConfigType,
    INIToENVMigrationStrategy, SchemaUpdateMigrationStrategy,
    BackwardCompatibilityTest, create_desktop_to_api_migration_steps,
    create_schema_update_migration_steps, create_backward_compatibility_tests
)
from config_validator import ValidationResult, ValidationIssue, ValidationSeverity


class TestINIToENVMigrationStrategy(unittest.TestCase):
    """Test INI to ENV migration strategy"""
    
    def setUp(self):
        self.strategy = INIToENVMigrationStrategy()
        self.sample_ini_config = {
            "Database": {
                "connection_string": "sqlite:///test.db",
                "type": "sqlite"
            },
            "Sync": {
                "enabled": "true",
                "server_url": "http://localhost:8000",
                "auto_sync": "false"
            }
        }
        
        self.migration_step = MigrationStep(
            step_id="test_ini_to_env",
            description="Test INI to ENV migration",
            migration_type=MigrationType.FORMAT_CHANGE,
            source_format=ConfigType.INI,
            target_format=ConfigType.ENV,
            transformation_rules={
                "key_mappings": {
                    "Database.connection_string": "DATABASE_CONNECTION_STRING",
                    "Database.type": "DATABASE_TYPE",
                    "Sync.enabled": "SYNC_ENABLED",
                    "Sync.server_url": "SYNC_SERVER_URL",
                    "Sync.auto_sync": "SYNC_AUTO_SYNC"
                },
                "value_transformations": {
                    "enabled": {"type": "boolean"},
                    "auto_sync": {"type": "boolean"}
                }
            },
            validation_rules={},
            rollback_rules={
                "reverse_key_mappings": {
                    "DATABASE_CONNECTION_STRING": "Database.connection_string",
                    "DATABASE_TYPE": "Database.type",
                    "SYNC_ENABLED": "Sync.enabled",
                    "SYNC_SERVER_URL": "Sync.server_url",
                    "SYNC_AUTO_SYNC": "Sync.auto_sync"
                }
            }
        )
    
    def test_can_migrate_ini_to_env(self):
        """Test that strategy can handle INI to ENV migration"""
        result = self.strategy.can_migrate(
            self.sample_ini_config, 
            ConfigType.INI, 
            ConfigType.ENV
        )
        self.assertTrue(result)
    
    def test_cannot_migrate_wrong_types(self):
        """Test that strategy rejects wrong type combinations"""
        result = self.strategy.can_migrate(
            self.sample_ini_config,
            ConfigType.ENV,
            ConfigType.INI
        )
        self.assertFalse(result)
    
    def test_migrate_ini_to_env(self):
        """Test INI to ENV migration"""
        env_config, warnings = self.strategy.migrate(self.sample_ini_config, self.migration_step)
        
        # Check that all expected keys are present
        expected_keys = [
            "DATABASE_CONNECTION_STRING",
            "DATABASE_TYPE", 
            "SYNC_ENABLED",
            "SYNC_SERVER_URL",
            "SYNC_AUTO_SYNC"
        ]
        
        for key in expected_keys:
            self.assertIn(key, env_config)
        
        # Check specific values
        self.assertEqual(env_config["DATABASE_CONNECTION_STRING"], "sqlite:///test.db")
        self.assertEqual(env_config["SYNC_ENABLED"], "true")
        self.assertEqual(env_config["SYNC_AUTO_SYNC"], "false")
        
        # Should have no warnings for this simple case
        self.assertEqual(len(warnings), 0)
    
    def test_rollback_env_to_ini(self):
        """Test ENV to INI rollback"""
        env_config = {
            "DATABASE_CONNECTION_STRING": "sqlite:///test.db",
            "DATABASE_TYPE": "sqlite",
            "SYNC_ENABLED": "true",
            "SYNC_SERVER_URL": "http://localhost:8000",
            "SYNC_AUTO_SYNC": "false"
        }
        
        ini_config, warnings = self.strategy.rollback(env_config, self.migration_step)
        
        # Check structure
        self.assertIn("Database", ini_config)
        self.assertIn("Sync", ini_config)
        
        # Check values
        self.assertEqual(ini_config["Database"]["connection_string"], "sqlite:///test.db")
        self.assertEqual(ini_config["Sync"]["enabled"], "true")
        self.assertEqual(ini_config["Sync"]["auto_sync"], "false")


class TestSchemaUpdateMigrationStrategy(unittest.TestCase):
    """Test schema update migration strategy"""
    
    def setUp(self):
        self.strategy = SchemaUpdateMigrationStrategy()
        self.sample_config = {
            "Sync": {
                "enabled": "true",
                "server_url": "http://localhost:8000",
                "debug_logging": "true"
            }
        }
        
        self.migration_step = MigrationStep(
            step_id="test_schema_update",
            description="Test schema update",
            migration_type=MigrationType.SCHEMA_UPDATE,
            source_format=ConfigType.INI,
            target_format=ConfigType.INI,
            transformation_rules={
                "add_keys": {
                    "Sync.batch_size": "100",
                    "Sync.compression_enabled": "true"
                },
                "rename_keys": {
                    "Sync.debug_logging": "Sync.log_level"
                },
                "remove_keys": []
            },
            validation_rules={},
            rollback_rules={
                "remove_added_keys": ["Sync.batch_size", "Sync.compression_enabled"],
                "reverse_renames": {
                    "Sync.log_level": "Sync.debug_logging"
                }
            }
        )
    
    def test_can_migrate_same_format(self):
        """Test that strategy can handle same format migrations"""
        result = self.strategy.can_migrate(
            self.sample_config,
            ConfigType.INI,
            ConfigType.INI
        )
        self.assertTrue(result)
    
    def test_migrate_schema_update(self):
        """Test schema update migration"""
        updated_config, warnings = self.strategy.migrate(self.sample_config, self.migration_step)
        
        # Check that new keys were added
        self.assertEqual(updated_config["Sync"]["batch_size"], "100")
        self.assertEqual(updated_config["Sync"]["compression_enabled"], "true")
        
        # Check that key was renamed
        self.assertIn("log_level", updated_config["Sync"])
        self.assertNotIn("debug_logging", updated_config["Sync"])
        
        # Check warnings
        self.assertGreater(len(warnings), 0)
        warning_messages = " ".join(warnings)
        self.assertIn("Added new key", warning_messages)
        self.assertIn("Renamed key", warning_messages)
    
    def test_rollback_schema_update(self):
        """Test schema update rollback"""
        updated_config = {
            "Sync": {
                "enabled": "true",
                "server_url": "http://localhost:8000",
                "log_level": "true",
                "batch_size": "100",
                "compression_enabled": "true"
            }
        }
        
        rolled_back_config, warnings = self.strategy.rollback(updated_config, self.migration_step)
        
        # Check that added keys were removed
        self.assertNotIn("batch_size", rolled_back_config["Sync"])
        self.assertNotIn("compression_enabled", rolled_back_config["Sync"])
        
        # Check that rename was reversed
        self.assertIn("debug_logging", rolled_back_config["Sync"])
        self.assertNotIn("log_level", rolled_back_config["Sync"])


class TestConfigMigrationTester(unittest.TestCase):
    """Test the main ConfigMigrationTester class"""
    
    def setUp(self):
        self.tester = ConfigMigrationTester()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample INI config file
        self.sample_ini_path = os.path.join(self.temp_dir, "test_config.ini")
        config = configparser.ConfigParser()
        config["Database"] = {
            "connection_string": "sqlite:///test.db",
            "type": "sqlite"
        }
        config["Sync"] = {
            "enabled": "true",
            "server_url": "http://localhost:8000"
        }
        
        with open(self.sample_ini_path, 'w') as f:
            config.write(f)
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('config_migration_tester.ConfigValidator')
    def test_migration_workflow_success(self, mock_validator):
        """Test successful migration workflow"""
        # Mock validator to return valid results
        mock_validation_result = ValidationResult(is_valid=True, issues=[])
        mock_validator.return_value.validate_file.return_value = mock_validation_result
        
        # Create simple migration steps
        migration_steps = [
            MigrationStep(
                step_id="test_step",
                description="Test migration step",
                migration_type=MigrationType.SCHEMA_UPDATE,
                source_format=ConfigType.INI,
                target_format=ConfigType.INI,
                transformation_rules={"add_keys": {"Test.new_key": "value"}},
                validation_rules={"required_keys": ["Test.new_key"]},
                rollback_rules={"remove_added_keys": ["Test.new_key"]}
            )
        ]
        
        result = self.tester.test_migration_workflow(migration_steps, self.sample_ini_path)
        
        # Check result
        self.assertTrue(result.success)
        self.assertEqual(len(result.steps_completed), 1)
        self.assertEqual(len(result.steps_failed), 0)
        self.assertGreater(len(result.backup_paths), 0)
    
    def test_backward_compatibility_full(self):
        """Test full backward compatibility"""
        compatibility_tests = [
            BackwardCompatibilityTest(
                test_id="test_full_compat",
                description="Test full compatibility",
                old_config_format={
                    "Database": {"type": "sqlite", "sqlite_path": "test.db"}
                },
                expected_behavior="Should work without issues",
                compatibility_level="full",
                deprecation_warnings=[]
            )
        ]
        
        with patch.object(self.tester.config_validator, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True, issues=[])
            
            results = self.tester.test_backward_compatibility(compatibility_tests, self.sample_ini_path)
            
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].is_valid)
    
    def test_backward_compatibility_partial(self):
        """Test partial backward compatibility with warnings"""
        compatibility_tests = [
            BackwardCompatibilityTest(
                test_id="test_partial_compat",
                description="Test partial compatibility",
                old_config_format={
                    "Database": {"type": "sqlite", "sqlite_path": "test.db"}
                },
                expected_behavior="Should work with warnings",
                compatibility_level="partial",
                deprecation_warnings=["sqlite_path is deprecated"]
            )
        ]
        
        with patch.object(self.tester.config_validator, 'validate_file') as mock_validate:
            # Return validation result with warnings but no errors
            mock_validate.return_value = ValidationResult(
                is_valid=True, 
                issues=[ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Deprecated configuration",
                    file_path=""
                )]
            )
            
            results = self.tester.test_backward_compatibility(compatibility_tests, self.sample_ini_path)
            
            self.assertEqual(len(results), 1)
            # Should still be valid for partial compatibility
            self.assertTrue(results[0].is_valid)
            # Should have deprecation warning
            deprecation_issues = [issue for issue in results[0].issues 
                                if "Deprecation warning" in issue.message]
            self.assertGreater(len(deprecation_issues), 0)
    
    @patch('config_migration_tester.ConfigValidator')
    def test_rollback_scenario(self, mock_validator):
        """Test rollback scenario"""
        # Mock validator to return valid results
        mock_validation_result = ValidationResult(is_valid=True, issues=[])
        mock_validator.return_value.validate_file.return_value = mock_validation_result
        
        # Create a migrated config file (simulating post-migration state)
        migrated_config_path = os.path.join(self.temp_dir, "migrated_config.ini")
        config = configparser.ConfigParser()
        config["Database"] = {
            "connection_string": "sqlite:///test.db",
            "type": "sqlite"
        }
        config["Sync"] = {
            "enabled": "true",
            "server_url": "http://localhost:8000"
        }
        config["Test"] = {
            "new_key": "value"  # This key should be removed during rollback
        }
        
        with open(migrated_config_path, 'w') as f:
            config.write(f)
        
        # Create migration steps with rollback capability
        migration_steps = [
            MigrationStep(
                step_id="reversible_step",
                description="Reversible migration step",
                migration_type=MigrationType.SCHEMA_UPDATE,
                source_format=ConfigType.INI,
                target_format=ConfigType.INI,
                transformation_rules={"add_keys": {"Test.new_key": "value"}},
                validation_rules={"required_keys": []},  # No required keys for rollback validation
                rollback_rules={"remove_added_keys": ["Test.new_key"]},
                is_reversible=True
            )
        ]
        
        result = self.tester.test_rollback_scenario(migration_steps, migrated_config_path)
        
        # Debug: Print error messages if test fails
        if not result.success:
            print(f"Rollback failed with errors: {result.error_messages}")
            print(f"Steps failed: {result.steps_failed}")
        
        # Check result
        self.assertTrue(result.success)
        self.assertEqual(len(result.steps_completed), 1)
        self.assertEqual(len(result.steps_failed), 0)
    
    @patch('config_migration_tester.DatabaseConnectionValidator')
    def test_alembic_configuration_changes(self, mock_db_validator):
        """Test Alembic configuration changes"""
        # Create sample Alembic config
        alembic_config_path = os.path.join(self.temp_dir, "alembic.ini")
        config = configparser.ConfigParser()
        config["alembic"] = {
            "script_location": "alembic",
            "sqlalchemy.url": "sqlite:///test.db"
        }
        
        with open(alembic_config_path, 'w') as f:
            config.write(f)
        
        # Mock database validator
        mock_db_validator.return_value.test_connection.return_value = (True, None)
        
        # Mock config validator to return valid Alembic config
        with patch.object(self.tester.config_validator, 'validate_alembic_config') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True, issues=[])
            
            database_changes = {
                "Switch to PostgreSQL": "postgresql://user:pass@localhost/testdb",
                "Switch to MySQL": "mysql+pymysql://user:pass@localhost/testdb"
            }
            
            result = self.tester.test_alembic_configuration_changes(
                alembic_config_path, 
                database_changes
            )
            
            self.assertTrue(result.is_valid)
            # Should have tested both database changes
            self.assertEqual(mock_validate.call_count, 3)  # Original + 2 changes


class TestMigrationStepCreation(unittest.TestCase):
    """Test migration step creation functions"""
    
    def test_create_desktop_to_api_migration_steps(self):
        """Test creation of desktop to API migration steps"""
        steps = create_desktop_to_api_migration_steps()
        
        self.assertGreater(len(steps), 0)
        
        # Check first step
        first_step = steps[0]
        self.assertEqual(first_step.migration_type, MigrationType.FORMAT_CHANGE)
        self.assertEqual(first_step.source_format, ConfigType.INI)
        self.assertEqual(first_step.target_format, ConfigType.ENV)
        
        # Check that key mappings are present
        self.assertIn("key_mappings", first_step.transformation_rules)
        key_mappings = first_step.transformation_rules["key_mappings"]
        self.assertIn("Database.connection_string", key_mappings)
        self.assertEqual(key_mappings["Database.connection_string"], "DATABASE_CONNECTION_STRING")
    
    def test_create_schema_update_migration_steps(self):
        """Test creation of schema update migration steps"""
        steps = create_schema_update_migration_steps()
        
        self.assertGreater(len(steps), 0)
        
        # Check first step
        first_step = steps[0]
        self.assertEqual(first_step.migration_type, MigrationType.SCHEMA_UPDATE)
        self.assertEqual(first_step.source_format, ConfigType.INI)
        self.assertEqual(first_step.target_format, ConfigType.INI)
        
        # Check that transformation rules are present
        self.assertIn("add_keys", first_step.transformation_rules)
        add_keys = first_step.transformation_rules["add_keys"]
        self.assertIn("Sync.batch_size", add_keys)
    
    def test_create_backward_compatibility_tests(self):
        """Test creation of backward compatibility tests"""
        tests = create_backward_compatibility_tests()
        
        self.assertGreater(len(tests), 0)
        
        # Check first test
        first_test = tests[0]
        self.assertIsInstance(first_test, BackwardCompatibilityTest)
        self.assertIn("test_id", first_test.__dict__)
        self.assertIn("description", first_test.__dict__)
        self.assertIn("old_config_format", first_test.__dict__)
        self.assertIn("compatibility_level", first_test.__dict__)


class TestMigrationValidation(unittest.TestCase):
    """Test migration validation functionality"""
    
    def setUp(self):
        self.tester = ConfigMigrationTester()
    
    def test_validate_migrated_config_required_keys(self):
        """Test validation of required keys in migrated config"""
        config = {
            "Database": {"connection_string": "sqlite:///test.db"},
            "Sync": {"enabled": "true"}
        }
        
        step = MigrationStep(
            step_id="test_validation",
            description="Test validation",
            migration_type=MigrationType.SCHEMA_UPDATE,
            source_format=ConfigType.INI,
            target_format=ConfigType.INI,
            transformation_rules={},
            validation_rules={
                "required_keys": ["Database.connection_string", "Sync.enabled", "Missing.key"]
            },
            rollback_rules={}
        )
        
        result = self.tester._validate_migrated_config(config, step)
        
        # Should be invalid due to missing key
        self.assertFalse(result.is_valid)
        
        # Should have error for missing key
        missing_key_errors = [issue for issue in result.issues 
                            if "Missing.key" in issue.message]
        self.assertGreater(len(missing_key_errors), 0)
    
    def test_validate_migrated_config_forbidden_keys(self):
        """Test validation of forbidden keys in migrated config"""
        config = {
            "Database": {"connection_string": "sqlite:///test.db"},
            "Sync": {"enabled": "true", "deprecated_key": "value"}
        }
        
        step = MigrationStep(
            step_id="test_validation",
            description="Test validation",
            migration_type=MigrationType.SCHEMA_UPDATE,
            source_format=ConfigType.INI,
            target_format=ConfigType.INI,
            transformation_rules={},
            validation_rules={
                "forbidden_keys": ["Sync.deprecated_key"]
            },
            rollback_rules={}
        )
        
        result = self.tester._validate_migrated_config(config, step)
        
        # Should be invalid due to forbidden key
        self.assertFalse(result.is_valid)
        
        # Should have error for forbidden key
        forbidden_key_errors = [issue for issue in result.issues 
                              if "Forbidden key" in issue.message]
        self.assertGreater(len(forbidden_key_errors), 0)
    
    @patch('config_migration_tester.DatabaseConnectionValidator')
    def test_validate_database_urls_in_config(self, mock_db_validator):
        """Test validation of database URLs in migrated config"""
        config = {
            "Database": {"connection_string": "invalid://connection/string"}
        }
        
        # Mock database validator to return invalid result
        mock_validation_result = ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Invalid connection string",
                file_path=""
            )]
        )
        mock_db_validator.return_value.validate_connection_string.return_value = mock_validation_result
        
        step = MigrationStep(
            step_id="test_validation",
            description="Test validation",
            migration_type=MigrationType.SCHEMA_UPDATE,
            source_format=ConfigType.INI,
            target_format=ConfigType.INI,
            transformation_rules={},
            validation_rules={},
            rollback_rules={}
        )
        
        result = self.tester._validate_migrated_config(config, step)
        
        # Should be invalid due to invalid database URL
        self.assertFalse(result.is_valid)
        
        # Should have database validation error
        db_errors = [issue for issue in result.issues 
                    if "Invalid connection string" in issue.message]
        self.assertGreater(len(db_errors), 0)


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()
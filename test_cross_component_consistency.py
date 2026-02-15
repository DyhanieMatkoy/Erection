"""
Unit tests for cross-component consistency checking

Tests the CrossComponentConsistencyChecker and related functionality
to ensure proper validation of configuration consistency across components.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import configparser
import json

from cross_component_consistency_checker import (
    CrossComponentConsistencyChecker, ComponentConfig, ComponentType,
    ConsistencyRule, ConsistencyLevel, create_component_config,
    check_desktop_api_consistency, check_all_components_consistency
)
from config_validator import ValidationResult, ValidationIssue, ValidationSeverity, ConfigType


class TestCrossComponentConsistencyChecker(unittest.TestCase):
    """Test the main CrossComponentConsistencyChecker class"""
    
    def setUp(self):
        self.checker = CrossComponentConsistencyChecker()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample configuration files
        self._create_sample_configs()
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_sample_configs(self):
        """Create sample configuration files for testing"""
        # Desktop client config (INI)
        self.desktop_config_path = os.path.join(self.temp_dir, "desktop_env.ini")
        desktop_config = configparser.ConfigParser()
        desktop_config["Database"] = {
            "connection_string": "sqlite:///test.db",
            "type": "sqlite"
        }
        desktop_config["Sync"] = {
            "enabled": "true",
            "server_url": "http://localhost:8000",
            "auto_sync": "false",
            "node_code": "NODE001"
        }
        
        with open(self.desktop_config_path, 'w') as f:
            desktop_config.write(f)
        
        # Web client config (JSON)
        self.web_config_path = os.path.join(self.temp_dir, "web_config.json")
        web_config = {
            "VITE_API_URL": "http://localhost:8000",
            "VITE_AUTH_ENABLED": "true",
            "build": {
                "outDir": "dist"
            }
        }
        
        with open(self.web_config_path, 'w') as f:
            json.dump(web_config, f)
        
        # API config (ENV) - Updated to allow web client origin
        self.api_config_path = os.path.join(self.temp_dir, "api.env")
        with open(self.api_config_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=sqlite:///test.db\n")
            f.write("DATABASE_TYPE=sqlite\n")
            f.write("SYNC_ENABLED=true\n")
            f.write("SYNC_SERVER_URL=http://localhost:8000\n")
            f.write("SYNC_AUTO_SYNC=false\n")
            f.write("SYNC_NODE_CODE=NODE001\n")
            f.write("JWT_SECRET_KEY=test_secret\n")
            f.write("CORS_ORIGINS=http://localhost:8000\n")  # Allow web client origin
        
        # Alembic config (INI)
        self.alembic_config_path = os.path.join(self.temp_dir, "alembic.ini")
        alembic_config = configparser.ConfigParser()
        alembic_config["alembic"] = {
            "script_location": "alembic",
            "sqlalchemy.url": "sqlite:///test.db"
        }
        
        with open(self.alembic_config_path, 'w') as f:
            alembic_config.write(f)
    
    def test_validate_env_ini_consistency_success(self):
        """Test successful env.ini and .env consistency validation"""
        result = self.checker.validate_env_ini_consistency(
            self.desktop_config_path, 
            self.api_config_path
        )
        
        # Should be valid since configurations are consistent
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
    
    def test_validate_env_ini_consistency_mismatch(self):
        """Test env.ini and .env consistency validation with mismatched values"""
        # Create mismatched API config
        mismatched_api_path = os.path.join(self.temp_dir, "mismatched_api.env")
        with open(mismatched_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost/testdb\n")
            f.write("SYNC_ENABLED=false\n")  # Different from desktop config
            f.write("SYNC_SERVER_URL=http://different-server:8000\n")  # Different URL
        
        result = self.checker.validate_env_ini_consistency(
            self.desktop_config_path, 
            mismatched_api_path
        )
        
        # Should be invalid due to mismatches
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)
        
        # Check for specific mismatch errors
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("Inconsistent values" in msg for msg in error_messages))
    
    def test_validate_env_ini_consistency_missing_keys(self):
        """Test env.ini and .env consistency validation with missing keys"""
        # Create API config with missing keys
        incomplete_api_path = os.path.join(self.temp_dir, "incomplete_api.env")
        with open(incomplete_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=sqlite:///test.db\n")
            # Missing SYNC_ENABLED and other sync keys
        
        result = self.checker.validate_env_ini_consistency(
            self.desktop_config_path, 
            incomplete_api_path
        )
        
        # Should have warnings about missing keys
        warning_issues = [issue for issue in result.issues 
                         if issue.severity == ValidationSeverity.WARNING]
        self.assertGreater(len(warning_issues), 0)
        
        # Check for missing key warnings
        warning_messages = [issue.message for issue in warning_issues]
        self.assertTrue(any("Missing .env key" in msg for msg in warning_messages))
    
    def test_validate_api_desktop_compatibility_success(self):
        """Test successful API and desktop compatibility validation"""
        result = self.checker.validate_api_desktop_compatibility(
            self.api_config_path,
            self.desktop_config_path
        )
        
        # Should be valid since configurations are compatible
        self.assertTrue(result.is_valid)
    
    def test_validate_api_desktop_compatibility_database_mismatch(self):
        """Test API and desktop compatibility with database type mismatch"""
        # Create API config with different database type
        different_db_api_path = os.path.join(self.temp_dir, "different_db_api.env")
        with open(different_db_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost/testdb\n")
            f.write("SYNC_ENABLED=true\n")
        
        result = self.checker.validate_api_desktop_compatibility(
            different_db_api_path,
            self.desktop_config_path
        )
        
        # Should have error about incompatible database types
        self.assertFalse(result.is_valid)
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("Incompatible database types" in msg for msg in error_messages))
    
    def test_validate_api_desktop_compatibility_sync_mismatch(self):
        """Test API and desktop compatibility with sync setting mismatch"""
        # Create API config with different sync settings
        different_sync_api_path = os.path.join(self.temp_dir, "different_sync_api.env")
        with open(different_sync_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=sqlite:///test.db\n")
            f.write("SYNC_ENABLED=false\n")  # Different from desktop
            f.write("SYNC_SERVER_URL=http://different-server:8000\n")  # Different URL
        
        result = self.checker.validate_api_desktop_compatibility(
            different_sync_api_path,
            self.desktop_config_path
        )
        
        # Should have errors about inconsistent sync settings
        self.assertFalse(result.is_valid)
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("Inconsistent sync settings" in msg for msg in error_messages))
        self.assertTrue(any("Different sync server URLs" in msg for msg in error_messages))
    
    def test_validate_web_client_compatibility_success(self):
        """Test successful web client compatibility validation"""
        result = self.checker.validate_web_client_compatibility(
            self.web_config_path,
            self.api_config_path
        )
        
        # Should be valid since web client origin is allowed by CORS
        self.assertTrue(result.is_valid)
    
    def test_validate_web_client_compatibility_cors_mismatch(self):
        """Test web client compatibility with CORS mismatch"""
        # Create API config with different CORS origins
        different_cors_api_path = os.path.join(self.temp_dir, "different_cors_api.env")
        with open(different_cors_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=sqlite:///test.db\n")
            f.write("CORS_ORIGINS=http://different-origin:3000\n")  # Different origin
            f.write("JWT_SECRET_KEY=test_secret\n")
        
        result = self.checker.validate_web_client_compatibility(
            self.web_config_path,
            different_cors_api_path
        )
        
        # Should have error about CORS origin not allowed
        self.assertFalse(result.is_valid)
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("not allowed by API CORS" in msg for msg in error_messages))
    
    def test_validate_web_client_compatibility_missing_jwt(self):
        """Test web client compatibility with missing JWT secret"""
        # Create API config without JWT secret
        no_jwt_api_path = os.path.join(self.temp_dir, "no_jwt_api.env")
        with open(no_jwt_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=sqlite:///test.db\n")
            f.write("CORS_ORIGINS=http://localhost:3000\n")
            # Missing JWT_SECRET_KEY
        
        result = self.checker.validate_web_client_compatibility(
            self.web_config_path,
            no_jwt_api_path
        )
        
        # Should have error about missing JWT secret
        self.assertFalse(result.is_valid)
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("no JWT secret" in msg for msg in error_messages))
    
    def test_validate_alembic_database_consistency_success(self):
        """Test successful Alembic database consistency validation"""
        database_configs = [
            ("API", self.api_config_path),
            ("Desktop", self.desktop_config_path)
        ]
        
        result = self.checker.validate_alembic_database_consistency(
            self.alembic_config_path,
            database_configs
        )
        
        # Should be valid since all use SQLite
        self.assertTrue(result.is_valid)
    
    def test_validate_alembic_database_consistency_type_mismatch(self):
        """Test Alembic database consistency with type mismatch"""
        # Create API config with different database type
        different_db_api_path = os.path.join(self.temp_dir, "different_db_api.env")
        with open(different_db_api_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost/testdb\n")
        
        database_configs = [
            ("API", different_db_api_path),
            ("Desktop", self.desktop_config_path)
        ]
        
        result = self.checker.validate_alembic_database_consistency(
            self.alembic_config_path,
            database_configs
        )
        
        # Should have error about database type mismatch
        self.assertFalse(result.is_valid)
        error_messages = [issue.message for issue in result.issues]
        self.assertTrue(any("Database type mismatch" in msg for msg in error_messages))
    
    def test_validate_multi_database_consistency_mixed_types(self):
        """Test multi-database consistency with mixed database types"""
        # Create configs with different database types
        postgres_config_path = os.path.join(self.temp_dir, "postgres.env")
        with open(postgres_config_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost/testdb\n")
        
        mysql_config_path = os.path.join(self.temp_dir, "mysql.env")
        with open(mysql_config_path, 'w') as f:
            f.write("DATABASE_CONNECTION_STRING=mysql+pymysql://user:pass@localhost/testdb\n")
        
        database_configs = [
            ("SQLite", self.api_config_path),
            ("PostgreSQL", postgres_config_path),
            ("MySQL", mysql_config_path)
        ]
        
        result = self.checker.validate_multi_database_consistency(database_configs)
        
        # Should have info message about mixed database types
        info_issues = [issue for issue in result.issues 
                      if issue.severity == ValidationSeverity.INFO]
        self.assertGreater(len(info_issues), 0)
        
        info_messages = [issue.message for issue in info_issues]
        self.assertTrue(any("Mixed database types detected" in msg for msg in info_messages))
    
    def test_check_consistency_with_components(self):
        """Test consistency checking with component configs"""
        components = [
            create_component_config(ComponentType.DESKTOP_CLIENT, self.desktop_config_path),
            create_component_config(ComponentType.API_SERVER, self.api_config_path)
        ]
        
        result = self.checker.check_consistency(components)
        
        # Should be valid since configurations are consistent
        self.assertTrue(result.is_valid)
    
    def test_check_consistency_with_inconsistent_components(self):
        """Test consistency checking with inconsistent components"""
        # Create inconsistent API config
        inconsistent_api_path = os.path.join(self.temp_dir, "inconsistent_api.env")
        with open(inconsistent_api_path, 'w') as f:
            f.write("DATABASE_TYPE=postgresql\n")  # Different from desktop
            f.write("SYNC_ENABLED=false\n")  # Different from desktop
            f.write("SYNC_SERVER_URL=http://different-server:8000\n")  # Different from desktop
        
        components = [
            create_component_config(ComponentType.DESKTOP_CLIENT, self.desktop_config_path),
            create_component_config(ComponentType.API_SERVER, inconsistent_api_path)
        ]
        
        result = self.checker.check_consistency(components)
        
        # Should be invalid due to inconsistencies
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)


class TestComponentConfig(unittest.TestCase):
    """Test ComponentConfig creation and handling"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_component_config_ini(self):
        """Test creating ComponentConfig from INI file"""
        config_path = os.path.join(self.temp_dir, "test.ini")
        config = configparser.ConfigParser()
        config["Section"] = {"key": "value"}
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        component = create_component_config(ComponentType.DESKTOP_CLIENT, config_path)
        
        self.assertEqual(component.component_type, ComponentType.DESKTOP_CLIENT)
        self.assertEqual(component.file_path, config_path)
        self.assertEqual(component.config_type, ConfigType.INI)
        self.assertIn("Section", component.config_data)
        self.assertEqual(component.config_data["Section"]["key"], "value")
    
    def test_create_component_config_env(self):
        """Test creating ComponentConfig from ENV file"""
        config_path = os.path.join(self.temp_dir, "test.env")
        with open(config_path, 'w') as f:
            f.write("TEST_KEY=test_value\n")
            f.write("ANOTHER_KEY=another_value\n")
        
        component = create_component_config(ComponentType.API_SERVER, config_path)
        
        self.assertEqual(component.component_type, ComponentType.API_SERVER)
        self.assertEqual(component.file_path, config_path)
        self.assertEqual(component.config_type, ConfigType.ENV)
        self.assertEqual(component.config_data["TEST_KEY"], "test_value")
        self.assertEqual(component.config_data["ANOTHER_KEY"], "another_value")
    
    def test_create_component_config_json(self):
        """Test creating ComponentConfig from JSON file"""
        config_path = os.path.join(self.temp_dir, "test.json")
        config_data = {"key": "value", "nested": {"inner_key": "inner_value"}}
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        component = create_component_config(ComponentType.WEB_CLIENT, config_path)
        
        self.assertEqual(component.component_type, ComponentType.WEB_CLIENT)
        self.assertEqual(component.file_path, config_path)
        self.assertEqual(component.config_type, ConfigType.JSON)
        self.assertEqual(component.config_data["key"], "value")
        self.assertEqual(component.config_data["nested"]["inner_key"], "inner_value")


class TestConsistencyHelperFunctions(unittest.TestCase):
    """Test helper functions for consistency checking"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample configs
        self.desktop_config_path = os.path.join(self.temp_dir, "desktop.ini")
        desktop_config = configparser.ConfigParser()
        desktop_config["Database"] = {"type": "sqlite"}
        desktop_config["Sync"] = {"enabled": "true"}
        
        with open(self.desktop_config_path, 'w') as f:
            desktop_config.write(f)
        
        self.api_config_path = os.path.join(self.temp_dir, "api.env")
        with open(self.api_config_path, 'w') as f:
            f.write("DATABASE_TYPE=sqlite\n")
            f.write("SYNC_ENABLED=true\n")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_desktop_api_consistency_success(self):
        """Test desktop-API consistency check helper function"""
        result = check_desktop_api_consistency(self.desktop_config_path, self.api_config_path)
        
        # Should be valid since configurations are consistent
        self.assertTrue(result.is_valid)
    
    def test_check_desktop_api_consistency_failure(self):
        """Test desktop-API consistency check with inconsistent configs"""
        # Create inconsistent API config
        inconsistent_api_path = os.path.join(self.temp_dir, "inconsistent_api.env")
        with open(inconsistent_api_path, 'w') as f:
            f.write("DATABASE_TYPE=postgresql\n")  # Different type
            f.write("SYNC_ENABLED=false\n")  # Different setting
        
        result = check_desktop_api_consistency(self.desktop_config_path, inconsistent_api_path)
        
        # Should be invalid due to inconsistencies
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)
    
    def test_check_all_components_consistency(self):
        """Test all components consistency check helper function"""
        config_paths = {
            ComponentType.DESKTOP_CLIENT: self.desktop_config_path,
            ComponentType.API_SERVER: self.api_config_path
        }
        
        result = check_all_components_consistency(config_paths)
        
        # Should be valid since configurations are consistent
        self.assertTrue(result.is_valid)
    
    def test_check_all_components_consistency_missing_file(self):
        """Test all components consistency check with missing file"""
        config_paths = {
            ComponentType.DESKTOP_CLIENT: self.desktop_config_path,
            ComponentType.API_SERVER: self.api_config_path,
            ComponentType.WEB_CLIENT: "/nonexistent/path.json"  # Missing file
        }
        
        # Should not crash and should only check existing files
        result = check_all_components_consistency(config_paths)
        
        # Should still be valid since existing configurations are consistent
        self.assertTrue(result.is_valid)


class TestConsistencyRules(unittest.TestCase):
    """Test consistency rule creation and application"""
    
    def setUp(self):
        self.checker = CrossComponentConsistencyChecker()
    
    def test_consistency_rules_creation(self):
        """Test that consistency rules are created properly"""
        rules = self.checker.consistency_rules
        
        # Should have some predefined rules
        self.assertGreater(len(rules), 0)
        
        # Check that rules have required fields
        for rule in rules:
            self.assertIsInstance(rule.rule_id, str)
            self.assertIsInstance(rule.description, str)
            self.assertIsInstance(rule.source_component, ComponentType)
            self.assertIsInstance(rule.target_component, ComponentType)
            self.assertIsInstance(rule.source_key, str)
            self.assertIsInstance(rule.target_key, str)
            self.assertIsInstance(rule.consistency_level, ConsistencyLevel)
    
    def test_normalize_boolean_function(self):
        """Test boolean normalization function"""
        # Test various boolean representations
        self.assertTrue(self.checker._normalize_boolean("true"))
        self.assertTrue(self.checker._normalize_boolean("True"))
        self.assertTrue(self.checker._normalize_boolean("1"))
        self.assertTrue(self.checker._normalize_boolean("yes"))
        self.assertTrue(self.checker._normalize_boolean("on"))
        self.assertTrue(self.checker._normalize_boolean("enabled"))
        self.assertTrue(self.checker._normalize_boolean(True))
        
        self.assertFalse(self.checker._normalize_boolean("false"))
        self.assertFalse(self.checker._normalize_boolean("False"))
        self.assertFalse(self.checker._normalize_boolean("0"))
        self.assertFalse(self.checker._normalize_boolean("no"))
        self.assertFalse(self.checker._normalize_boolean("off"))
        self.assertFalse(self.checker._normalize_boolean("disabled"))
        self.assertFalse(self.checker._normalize_boolean(False))
    
    def test_normalize_value_function(self):
        """Test value normalization function"""
        # Test string normalization
        self.assertEqual(self.checker._normalize_value("  Test Value  "), "test value")
        self.assertEqual(self.checker._normalize_value("UPPERCASE"), "uppercase")
        
        # Test boolean normalization
        self.assertEqual(self.checker._normalize_value(True), "true")
        self.assertEqual(self.checker._normalize_value(False), "false")
        
        # Test other types
        self.assertEqual(self.checker._normalize_value(123), "123")
        self.assertEqual(self.checker._normalize_value(None), "None")
    
    def test_get_nested_value_function(self):
        """Test nested value extraction function"""
        config = {
            "section1": {
                "key1": "value1",
                "nested": {
                    "deep_key": "deep_value"
                }
            },
            "flat_key": "flat_value"
        }
        
        # Test flat key access
        self.assertEqual(self.checker._get_nested_value(config, "flat_key"), "flat_value")
        
        # Test nested key access
        self.assertEqual(self.checker._get_nested_value(config, "section1.key1"), "value1")
        
        # Test deep nested access
        self.assertEqual(self.checker._get_nested_value(config, "section1.nested.deep_key"), "deep_value")
        
        # Test missing key with default
        self.assertEqual(self.checker._get_nested_value(config, "missing.key", "default"), "default")
        
        # Test missing key without default
        self.assertIsNone(self.checker._get_nested_value(config, "missing.key"))


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()
"""
Unit tests for Database-Specific Validator

Tests database-specific validation rules and best practices for SQLite, PostgreSQL, and MySQL.
"""

import unittest
from config_validator import (
    ConfigValidator, DatabaseSpecificValidator, DatabaseConnectionValidator,
    ValidationSeverity, ValidationResult, ValidationIssue, DatabaseConnectionInfo
)


class TestDatabaseSpecificValidator(unittest.TestCase):
    """Test database-specific validation rules"""
    
    def setUp(self):
        self.validator = DatabaseSpecificValidator()
        self.db_validator = DatabaseConnectionValidator()
        self.main_validator = ConfigValidator()
    
    def test_sqlite_specific_rules(self):
        """Test SQLite-specific validation rules"""
        # Test valid SQLite connection
        conn_str = "sqlite:///project_data.db"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_sqlite_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)
        # Should have minimal issues for good naming
        
        # Test SQLite without .db extension
        conn_str = "sqlite:///project_data"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_sqlite_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        extension_warnings = [issue for issue in result.issues 
                            if "extension" in issue.message.lower()]
        self.assertGreater(len(extension_warnings), 0)
        
        # Test generic database name
        conn_str = "sqlite:///test.db"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_sqlite_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        generic_warnings = [issue for issue in result.issues 
                          if "Generic database name" in issue.message]
        self.assertGreater(len(generic_warnings), 0)
    
    def test_postgresql_specific_rules(self):
        """Test PostgreSQL-specific validation rules"""
        # Test PostgreSQL with weak username
        conn_str = "postgresql://postgres:password@localhost:5432/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_postgresql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        weak_username_warnings = [issue for issue in result.issues 
                                if "Weak username" in issue.message]
        self.assertGreater(len(weak_username_warnings), 0)
        
        # Test PostgreSQL with default port
        conn_str = "postgresql://appuser:password@localhost:5432/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_postgresql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)
        default_port_info = [issue for issue in result.issues 
                           if "default PostgreSQL port" in issue.message]
        self.assertGreater(len(default_port_info), 0)
        
        # Test PostgreSQL with generic database name
        conn_str = "postgresql://appuser:password@localhost:5433/testdb"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_postgresql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        generic_db_warnings = [issue for issue in result.issues 
                             if "Generic database name" in issue.message]
        self.assertGreater(len(generic_db_warnings), 0)
    
    def test_mysql_specific_rules(self):
        """Test MySQL-specific validation rules"""
        # Test MySQL without pymysql driver
        conn_str = "mysql://user:password@localhost:3306/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_mysql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        driver_warnings = [issue for issue in result.issues 
                         if "PyMySQL driver" in issue.message]
        self.assertGreater(len(driver_warnings), 0)
        
        # Test MySQL with pymysql driver (should be better)
        conn_str = "mysql+pymysql://appuser:password@localhost:3307/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_mysql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)
        # Should have fewer warnings with proper driver
        
        # Test MySQL with weak username
        conn_str = "mysql+pymysql://root:password@localhost:3306/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_mysql_specific_rules(conn_info)
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        weak_username_warnings = [issue for issue in result.issues 
                                if "Weak username" in issue.message]
        self.assertGreater(len(weak_username_warnings), 0)
    
    def test_environment_specific_rules_production(self):
        """Test environment-specific rules for production"""
        # Test SQLite in production (should warn)
        conn_str = "sqlite:///production_data.db"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_environment_specific_rules(conn_info, 'production')
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        sqlite_prod_warnings = [issue for issue in result.issues 
                              if "SQLite not recommended for production" in issue.message]
        self.assertGreater(len(sqlite_prod_warnings), 0)
        
        # Test database with test-like name in production (should error)
        conn_str = "postgresql://user:pass@localhost:5432/test_database"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_environment_specific_rules(conn_info, 'production')
        
        self.assertFalse(result.is_valid)  # Should be invalid
        test_name_errors = [issue for issue in result.issues 
                          if issue.severity == ValidationSeverity.ERROR and "Test-like database name" in issue.message]
        self.assertGreater(len(test_name_errors), 0)
    
    def test_environment_specific_rules_development(self):
        """Test environment-specific rules for development"""
        # Test remote database in development (should inform)
        conn_str = "postgresql://user:pass@remote-server:5432/myapp_dev"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_environment_specific_rules(conn_info, 'development')
        
        self.assertTrue(result.is_valid)
        remote_db_info = [issue for issue in result.issues 
                        if "Using remote database for development" in issue.message]
        self.assertGreater(len(remote_db_info), 0)
    
    def test_environment_specific_rules_test(self):
        """Test environment-specific rules for test environment"""
        # Test database without 'test' in name for test environment
        conn_str = "postgresql://user:pass@localhost:5432/myapp"
        conn_info = self.db_validator.parse_connection_string(conn_str)
        result = self.validator.validate_environment_specific_rules(conn_info, 'test')
        
        self.assertTrue(result.is_valid)  # Valid but with warnings
        test_name_warnings = [issue for issue in result.issues 
                            if "should contain 'test'" in issue.message]
        self.assertGreater(len(test_name_warnings), 0)
    
    def test_cross_database_consistency(self):
        """Test cross-database consistency validation"""
        connections = [
            ("main_db", self.db_validator.parse_connection_string("postgresql://user:pass@localhost:5432/myapp")),
            ("cache_db", self.db_validator.parse_connection_string("postgresql://user:pass@localhost:5433/myapp_cache")),
            ("analytics_db", self.db_validator.parse_connection_string("mysql+pymysql://user:pass@localhost:3306/analytics"))
        ]
        
        result = self.validator.validate_cross_database_consistency(connections)
        
        self.assertTrue(result.is_valid)
        # Should have info about mixed database types
        mixed_type_info = [issue for issue in result.issues 
                         if "Mixed database types" in issue.message]
        self.assertGreater(len(mixed_type_info), 0)
        
        # Test consistent database types
        pg_connections = [
            ("main_db", self.db_validator.parse_connection_string("postgresql://user:pass@localhost:5432/myapp")),
            ("test_db", self.db_validator.parse_connection_string("postgresql://user:pass@localhost:5433/myapp_test"))
        ]
        
        result = self.validator.validate_cross_database_consistency(pg_connections)
        self.assertTrue(result.is_valid)
        # Should have warning about inconsistent ports
        port_warnings = [issue for issue in result.issues 
                       if "Inconsistent ports" in issue.message]
        self.assertGreater(len(port_warnings), 0)


class TestConfigValidatorDatabaseSpecificIntegration(unittest.TestCase):
    """Test integration of database-specific validation with main ConfigValidator"""
    
    def setUp(self):
        self.validator = ConfigValidator()
    
    def test_validate_database_specific_rules_sqlite(self):
        """Test database-specific validation through main validator - SQLite"""
        conn_str = "sqlite:///test.db"
        result = self.validator.validate_database_specific_rules(conn_str)
        
        self.assertTrue(result.is_valid)
        # Should have warnings about generic name
        generic_warnings = [issue for issue in result.issues 
                          if "Generic database name" in issue.message]
        self.assertGreater(len(generic_warnings), 0)
    
    def test_validate_database_specific_rules_postgresql(self):
        """Test database-specific validation through main validator - PostgreSQL"""
        conn_str = "postgresql://postgres:password@localhost:5432/testdb"
        result = self.validator.validate_database_specific_rules(conn_str)
        
        self.assertTrue(result.is_valid)
        # Should have warnings about weak username and generic database name
        weak_username_warnings = [issue for issue in result.issues 
                                if "Weak username" in issue.message]
        self.assertGreater(len(weak_username_warnings), 0)
    
    def test_validate_database_specific_rules_mysql(self):
        """Test database-specific validation through main validator - MySQL"""
        conn_str = "mysql://root:password@localhost:3306/test"
        result = self.validator.validate_database_specific_rules(conn_str)
        
        self.assertTrue(result.is_valid)
        # Should have warnings about driver, username, and database name
        issues_count = len(result.issues)
        self.assertGreater(issues_count, 0)
    
    def test_validate_database_specific_rules_with_environment(self):
        """Test database-specific validation with environment context"""
        # Test production environment
        conn_str = "sqlite:///test.db"
        result = self.validator.validate_database_specific_rules(conn_str, "production")
        
        self.assertFalse(result.is_valid)  # Should be invalid due to test name in production
        
        # Test development environment
        conn_str = "postgresql://user:pass@remote-host:5432/myapp_dev"
        result = self.validator.validate_database_specific_rules(conn_str, "development")
        
        self.assertTrue(result.is_valid)
        # Should have info about remote database
        remote_info = [issue for issue in result.issues 
                     if "remote database" in issue.message.lower()]
        self.assertGreater(len(remote_info), 0)
    
    def test_validate_cross_database_consistency_integration(self):
        """Test cross-database consistency validation through main validator"""
        connections = {
            "main": "postgresql://user:pass@localhost:5432/myapp",
            "cache": "postgresql://user:pass@localhost:5433/cache",
            "analytics": "mysql+pymysql://user:pass@localhost:3306/analytics"
        }
        
        result = self.validator.validate_cross_database_consistency(connections)
        
        self.assertTrue(result.is_valid)
        # Should have info about mixed types and inconsistent ports
        self.assertGreater(len(result.issues), 0)
    
    def test_validate_invalid_connection_string(self):
        """Test database-specific validation with invalid connection string"""
        conn_str = "invalid://connection/string"
        result = self.validator.validate_database_specific_rules(conn_str)
        
        self.assertFalse(result.is_valid)
        # Should have error about invalid connection string
        invalid_errors = [issue for issue in result.issues 
                        if "Invalid connection string" in issue.message]
        self.assertGreater(len(invalid_errors), 0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
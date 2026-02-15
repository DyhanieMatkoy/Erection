"""
Unit tests for Alembic Configuration Validator

Tests Alembic-specific configuration validation including database URL consistency,
script location validation, and comparison between main and test configurations.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from config_validator import (
    ConfigValidator, AlembicConfigValidator, ValidationSeverity,
    ValidationResult, ValidationIssue
)


class TestAlembicConfigValidator(unittest.TestCase):
    """Test Alembic configuration validator"""
    
    def setUp(self):
        self.validator = AlembicConfigValidator()
        self.main_validator = ConfigValidator()
    
    def test_validate_valid_alembic_config(self):
        """Test validation of valid Alembic configuration"""
        alembic_content = """[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///test.db
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertTrue(result.is_valid)
            
            # Should have some info messages but no errors
            error_issues = [issue for issue in result.issues 
                           if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
            self.assertEqual(len(error_issues), 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_missing_alembic_section(self):
        """Test validation with missing [alembic] section"""
        alembic_content = """[loggers]
keys = root,sqlalchemy,alembic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertFalse(result.is_valid)
            
            # Should have critical error for missing section
            critical_issues = [issue for issue in result.issues 
                             if issue.severity == ValidationSeverity.CRITICAL]
            self.assertGreater(len(critical_issues), 0)
            self.assertIn("Missing required [alembic] section", critical_issues[0].message)
        finally:
            os.unlink(temp_path)
    
    def test_validate_missing_script_location(self):
        """Test validation with missing script_location"""
        alembic_content = """[alembic]
sqlalchemy.url = sqlite:///test.db

[loggers]
keys = root,sqlalchemy,alembic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertFalse(result.is_valid)
            
            # Should have error for missing script_location
            error_issues = [issue for issue in result.issues 
                           if "script_location" in issue.message]
            self.assertGreater(len(error_issues), 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_invalid_database_url(self):
        """Test validation with invalid database URL"""
        alembic_content = """[alembic]
script_location = alembic
sqlalchemy.url = invalid://connection/string

[loggers]
keys = root,sqlalchemy,alembic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertFalse(result.is_valid)
            
            # Should have database validation errors
            db_errors = [issue for issue in result.issues 
                        if "database" in issue.message.lower() or "connection" in issue.message.lower()]
            self.assertGreater(len(db_errors), 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_missing_database_url(self):
        """Test validation with missing database URL"""
        alembic_content = """[alembic]
script_location = alembic

[loggers]
keys = root,sqlalchemy,alembic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertTrue(result.is_valid)  # Valid but with warnings
            
            # Should have warning for missing database URL
            warning_issues = [issue for issue in result.issues 
                            if issue.severity == ValidationSeverity.WARNING and "database URL" in issue.message]
            self.assertGreater(len(warning_issues), 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_nonexistent_script_location(self):
        """Test validation with non-existent script location"""
        alembic_content = """[alembic]
script_location = definitely_nonexistent_directory_12345
sqlalchemy.url = sqlite:///test.db
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            # Should be valid but with warnings about non-existent directory
            
            # Should have warning for non-existent script location
            warning_issues = [issue for issue in result.issues 
                            if "Script location does not exist" in issue.message]
            self.assertGreater(len(warning_issues), 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_missing_logging_sections(self):
        """Test validation with missing logging sections"""
        alembic_content = """[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///test.db
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = self.validator.validate_alembic_config(temp_path)
            self.assertTrue(result.is_valid)  # Valid but with warnings
            
            # Should have warnings for missing logging sections
            logging_warnings = [issue for issue in result.issues 
                              if "logging section" in issue.message]
            self.assertGreaterEqual(len(logging_warnings), 3)  # loggers, handlers, formatters
        finally:
            os.unlink(temp_path)
    
    def test_compare_alembic_configs_consistent(self):
        """Test comparison of consistent Alembic configurations"""
        main_content = """[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///main.db
prepend_sys_path = .
path_separator = os

[loggers]
keys = root,alembic
"""
        
        test_content = """[alembic]
script_location = test_migrations
sqlalchemy.url = sqlite:///test.db
prepend_sys_path = .
path_separator = os

[loggers]
keys = root,alembic
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as main_f:
            main_f.write(main_content)
            main_f.flush()
            main_path = main_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as test_f:
            test_f.write(test_content)
            test_f.flush()
            test_path = test_f.name
        
        try:
            result = self.validator.compare_alembic_configs(main_path, test_path)
            self.assertTrue(result.is_valid)
            
            # Should have minimal issues for consistent configs
            warning_issues = [issue for issue in result.issues 
                            if issue.severity == ValidationSeverity.WARNING]
            # May have warnings but no errors
            error_issues = [issue for issue in result.issues 
                           if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
            self.assertEqual(len(error_issues), 0)
        finally:
            os.unlink(main_path)
            os.unlink(test_path)
    
    def test_compare_alembic_configs_inconsistent(self):
        """Test comparison of inconsistent Alembic configurations"""
        main_content = """[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///main.db
prepend_sys_path = .
path_separator = os

[loggers]
keys = root,alembic
"""
        
        test_content = """[alembic]
script_location = test_migrations
sqlalchemy.url = postgresql://user:pass@localhost:5432/testdb
prepend_sys_path = .
path_separator = ;

[loggers]
keys = root,alembic
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as main_f:
            main_f.write(main_content)
            main_f.flush()
            main_path = main_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as test_f:
            test_f.write(test_content)
            test_f.flush()
            test_path = test_f.name
        
        try:
            result = self.validator.compare_alembic_configs(main_path, test_path)
            self.assertTrue(result.is_valid)  # Valid but with warnings
            
            # Should have warnings for inconsistencies
            inconsistency_warnings = [issue for issue in result.issues 
                                    if "Inconsistent" in issue.message or "Different" in issue.message]
            self.assertGreater(len(inconsistency_warnings), 0)
        finally:
            os.unlink(main_path)
            os.unlink(test_path)


class TestConfigValidatorAlembicIntegration(unittest.TestCase):
    """Test integration of Alembic validation with main ConfigValidator"""
    
    def setUp(self):
        self.validator = ConfigValidator()
    
    def test_validate_alembic_file_through_main_validator(self):
        """Test validating Alembic file through main ConfigValidator"""
        alembic_content = """[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///test.db

[loggers]
keys = root,alembic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(alembic_content)
            f.flush()
            temp_path = f.name
        
        try:
            # Test with explicit schema
            result = self.validator.validate_file(temp_path, "alembic")
            self.assertTrue(result.is_valid)
            
            # Test with filename detection
            alembic_path = temp_path.replace('.ini', '_alembic.ini')
            os.rename(temp_path, alembic_path)
            result = self.validator.validate_file(alembic_path)
            self.assertTrue(result.is_valid)
            
            temp_path = alembic_path  # Update for cleanup
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_existing_alembic_files(self):
        """Test validation of existing Alembic files in the project"""
        if os.path.exists("alembic.ini"):
            result = self.validator.validate_alembic_config("alembic.ini")
            self.assertIsNotNone(result)
            
            # Print results for debugging
            print(f"\nalembic.ini validation result: {result.is_valid}")
            for issue in result.issues:
                print(f"  {issue.severity.value}: {issue.message}")
        
        if os.path.exists("test_alembic.ini"):
            result = self.validator.validate_alembic_config("test_alembic.ini")
            self.assertIsNotNone(result)
            
            # Print results for debugging
            print(f"\ntest_alembic.ini validation result: {result.is_valid}")
            for issue in result.issues:
                print(f"  {issue.severity.value}: {issue.message}")
    
    def test_compare_existing_alembic_configs(self):
        """Test comparison of existing Alembic configurations"""
        if os.path.exists("alembic.ini") and os.path.exists("test_alembic.ini"):
            result = self.validator.compare_alembic_configs("alembic.ini", "test_alembic.ini")
            self.assertIsNotNone(result)
            
            # Print comparison results
            print(f"\nAlembic config comparison result: {result.is_valid}")
            for issue in result.issues:
                print(f"  {issue.severity.value}: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
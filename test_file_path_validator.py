"""
Unit tests for file path validation functionality in config_validator.py

Tests the FilePathValidator class and its integration with ConfigValidator.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from config_validator import (
    ConfigValidator, FilePathValidator, ValidationResult, ValidationSeverity,
    ValidationIssue
)


class TestFilePathValidator(unittest.TestCase):
    """Test cases for FilePathValidator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = FilePathValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.ini')
        
        # Create some test files and directories
        self.test_file = os.path.join(self.temp_dir, 'test_file.txt')
        self.test_dir = os.path.join(self.temp_dir, 'test_directory')
        
        with open(self.test_file, 'w') as f:
            f.write('test content')
        
        os.makedirs(self.test_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_is_path_key_detection(self):
        """Test detection of path-related configuration keys"""
        # Direct matches
        self.assertTrue(self.validator._is_path_key('sqlite_path'))
        self.assertTrue(self.validator._is_path_key('templates_path'))
        self.assertTrue(self.validator._is_path_key('script_location'))
        
        # Pattern matches
        self.assertTrue(self.validator._is_path_key('log_file'))
        self.assertTrue(self.validator._is_path_key('backup_directory'))
        self.assertTrue(self.validator._is_path_key('ssl_cert'))
        
        # Non-path keys
        self.assertFalse(self.validator._is_path_key('username'))
        self.assertFalse(self.validator._is_path_key('password'))
        self.assertFalse(self.validator._is_path_key('port'))
    
    def test_path_interpolation_resolution(self):
        """Test resolution of path interpolation variables"""
        base_dir = '/home/user/project'
        
        # Test %(here)s interpolation
        path_with_here = '%(here)s/migrations'
        resolved = self.validator._resolve_path_interpolation(path_with_here, base_dir)
        self.assertEqual(resolved, '/home/user/project/migrations')
        
        # Test environment variable interpolation
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            path_with_env = '${TEST_VAR}/subdir'
            resolved = self.validator._resolve_path_interpolation(path_with_env, base_dir)
            self.assertEqual(resolved, 'test_value/subdir')
            
            path_with_env2 = '$TEST_VAR/subdir'
            resolved2 = self.validator._resolve_path_interpolation(path_with_env2, base_dir)
            self.assertEqual(resolved2, 'test_value/subdir')
    
    def test_path_format_validation(self):
        """Test path format validation"""
        # Valid path
        result = self.validator._validate_path_format('sqlite_path', '/valid/path.db', self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
        
        # Empty path
        result = self.validator._validate_path_format('sqlite_path', '', self.config_file)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.ERROR)
        
        # Path with suspicious patterns
        result = self.validator._validate_path_format('sqlite_path', '../../../etc/passwd', self.config_file)
        self.assertTrue(result.is_valid)  # Format is valid, but should have warning
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.WARNING)
    
    @patch('os.name', 'nt')  # Mock Windows
    def test_path_format_validation_windows(self):
        """Test path format validation on Windows"""
        # Path with invalid Windows characters
        result = self.validator._validate_path_format('sqlite_path', 'C:\\invalid<path>.db', self.config_file)
        self.assertFalse(result.is_valid)  # Should be invalid due to invalid character
        self.assertGreater(len(result.issues), 0)  # At least one issue
        
        # Check that we have an invalid character error
        invalid_char_issues = [issue for issue in result.issues if 'Invalid character' in issue.message]
        self.assertGreater(len(invalid_char_issues), 0)
    
    def test_path_existence_validation(self):
        """Test path existence validation"""
        # Existing file
        result = self.validator._validate_path_existence('sqlite_path', self.test_file, self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
        
        # Existing directory
        result = self.validator._validate_path_existence('templates_path', self.test_dir, self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
        
        # Non-existent path
        non_existent = os.path.join(self.temp_dir, 'non_existent.db')
        result = self.validator._validate_path_existence('sqlite_path', non_existent, self.config_file)
        self.assertTrue(result.is_valid)  # SQLite paths can be created
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.WARNING)
        
        # Wrong type (file expected, directory found)
        result = self.validator._validate_path_existence('sqlite_path', self.test_dir, self.config_file)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('Expected file but found directory', result.issues[0].message)
    
    def test_path_permissions_validation(self):
        """Test path permissions validation"""
        # Test with existing readable file
        result = self.validator._validate_path_permissions('sqlite_path', self.test_file, self.config_file)
        self.assertTrue(result.is_valid)
        
        # Test with non-existent path (should not fail)
        non_existent = os.path.join(self.temp_dir, 'non_existent.db')
        result = self.validator._validate_path_permissions('sqlite_path', non_existent, self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
    
    @patch('os.name', 'nt')  # Mock Windows
    def test_path_platform_compatibility_windows(self):
        """Test path platform compatibility on Windows"""
        # Long path on Windows
        long_path = 'C:\\' + 'a' * 300 + '\\file.db'
        result = self.validator._validate_path_platform_compatibility('sqlite_path', long_path, self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.WARNING)
        self.assertIn('exceeds Windows limit', result.issues[0].message)
        
        # Mixed path separators
        mixed_path = 'C:\\path/to\\file.db'
        result = self.validator._validate_path_platform_compatibility('sqlite_path', mixed_path, self.config_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, ValidationSeverity.WARNING)
        self.assertIn('Mixed path separators', result.issues[0].message)
    
    def test_validate_file_paths_flat_config(self):
        """Test validation of file paths in flat configuration (ENV style)"""
        config_data = {
            'DATABASE_PATH': self.test_file,
            'TEMPLATES_PATH': self.test_dir,
            'LOG_FILE': os.path.join(self.temp_dir, 'non_existent.log'),
            'USERNAME': 'testuser',  # Not a path
        }
        
        result = self.validator.validate_file_paths(config_data, self.config_file)
        
        # Should validate 3 path keys, ignore USERNAME
        path_issues = [issue for issue in result.issues if issue.key in ['DATABASE_PATH', 'TEMPLATES_PATH', 'LOG_FILE']]
        # LOG_FILE should have issues (non-existent), and there might be multiple issues per path
        self.assertGreater(len(path_issues), 0)  # At least one issue
        
        # Check that LOG_FILE has issues
        log_issues = [issue for issue in result.issues if issue.key == 'LOG_FILE']
        self.assertGreater(len(log_issues), 0)
    
    def test_validate_file_paths_sectioned_config(self):
        """Test validation of file paths in sectioned configuration (INI style)"""
        config_data = {
            'Database': {
                'sqlite_path': self.test_file,
                'backup_path': self.test_dir,
            },
            'PrintForms': {
                'templates_path': os.path.join(self.temp_dir, 'non_existent_dir'),
            },
            'Auth': {
                'username': 'testuser',  # Not a path
                'password': 'testpass',  # Not a path
            }
        }
        
        result = self.validator.validate_file_paths(config_data, self.config_file)
        
        # Should find issues with non-existent templates_path
        template_issues = [issue for issue in result.issues if issue.key == 'templates_path']
        self.assertGreater(len(template_issues), 0)  # At least one issue
        # Check that at least one issue is an error
        error_issues = [issue for issue in template_issues if issue.severity == ValidationSeverity.ERROR]
        self.assertGreater(len(error_issues), 0)
    
    def test_validate_relative_path_resolution(self):
        """Test validation of relative path resolution"""
        config_data = {
            'Database': {
                'sqlite_path': './relative.db',  # Relative path
                'backup_path': '../backup',      # Parent directory
            }
        }
        
        result = self.validator.validate_relative_path_resolution(config_data, self.config_file)
        
        # Should not have critical issues for reasonable relative paths
        self.assertTrue(result.is_valid)
        
        # Test excessive parent directory traversal
        config_data_bad = {
            'Database': {
                'sqlite_path': '../../../../../../../../etc/passwd',
            }
        }
        
        result_bad = self.validator.validate_relative_path_resolution(config_data_bad, self.config_file)
        
        # Should have warning about excessive traversal
        traversal_issues = [issue for issue in result_bad.issues if 'traversal' in issue.message]
        self.assertEqual(len(traversal_issues), 1)
        self.assertEqual(traversal_issues[0].severity, ValidationSeverity.WARNING)


class TestConfigValidatorFilePathIntegration(unittest.TestCase):
    """Test integration of file path validation with ConfigValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_config = os.path.join(self.temp_dir, 'test.ini')
        self.test_db = os.path.join(self.temp_dir, 'test.db')
        self.test_templates = os.path.join(self.temp_dir, 'templates')
        
        os.makedirs(self.test_templates, exist_ok=True)
        
        # Create a test INI file with path configurations
        config_content = f"""[Database]
type = sqlite
sqlite_path = {self.test_db}
backup_path = {self.test_templates}

[PrintForms]
templates_path = {self.test_templates}
format = xlsx
estimate_variant = standard

[Features]
use_simplified_specifications = true

[Auth]
login = admin
password = admin

[Interface]
button_style = modern
button_position = top

[Sync]
enabled = false
server_url = http://localhost:8000
node_code = test
"""
        
        with open(self.test_config, 'w') as f:
            f.write(config_content)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_integrated_file_path_validation(self):
        """Test that file path validation is integrated into main validation"""
        result = self.validator.validate_file(self.test_config, 'desktop_client')
        
        # Should have issues for non-existent sqlite_path or other path-related issues
        path_issues = [issue for issue in result.issues if 'sqlite_path' in str(issue.key) or 'path' in issue.message.lower()]
        self.assertGreater(len(path_issues), 0)
        
        # Check that we get path-related validation messages
        path_messages = [issue.message for issue in result.issues if 'path' in issue.message.lower() or 'exist' in issue.message.lower()]
        self.assertGreater(len(path_messages), 0)
    
    def test_validate_file_paths_method(self):
        """Test the validate_file_paths method directly"""
        config_data = {
            'Database': {
                'sqlite_path': self.test_db,  # Non-existent
                'log_path': self.test_templates,  # Exists, should be directory
            }
        }
        
        result = self.validator.validate_file_paths(config_data, self.test_config)
        
        # Should have warning for non-existent sqlite_path
        sqlite_issues = [issue for issue in result.issues if issue.key == 'sqlite_path']
        self.assertGreater(len(sqlite_issues), 0)  # At least one issue
        
        # Check that at least one issue is a warning
        warning_issues = [issue for issue in sqlite_issues if issue.severity == ValidationSeverity.WARNING]
        self.assertGreater(len(warning_issues), 0)
        
        # log_path exists and is a directory, so should have no issues
        log_issues = [issue for issue in result.issues if issue.key == 'log_path']
        self.assertEqual(len(log_issues), 0)
    
    def test_validate_relative_path_resolution_method(self):
        """Test the validate_relative_path_resolution method directly"""
        config_data = {
            'Database': {
                'sqlite_path': './test.db',
                'backup_path': '../backup',
            }
        }
        
        result = self.validator.validate_relative_path_resolution(config_data, self.test_config)
        
        # Should complete without critical errors
        self.assertTrue(result.is_valid)
        
        # May have informational messages about relative paths
        info_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.INFO]
        # This is acceptable - relative paths may generate info messages


if __name__ == '__main__':
    unittest.main()
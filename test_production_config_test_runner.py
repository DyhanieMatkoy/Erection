"""
Unit tests for Production Configuration Test Runner

Tests the functionality of running tests with production-like configurations,
including configuration profile management and environment-specific testing scenarios.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from production_config_test_runner import (
    ProductionConfigTestRunner, ConfigurationProfileManager, ConfigProfile,
    TestEnvironment, ProductionConfigSettings, TestRunResult
)
from config_validator import ValidationResult, ValidationIssue, ValidationSeverity


class TestConfigurationProfileManager(unittest.TestCase):
    """Test configuration profile manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.profile_manager = ConfigurationProfileManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialize_default_profiles(self):
        """Test that default profiles are initialized correctly"""
        # Check that all profiles are present
        expected_profiles = {ConfigProfile.DEVELOPMENT, ConfigProfile.TESTING, 
                           ConfigProfile.STAGING, ConfigProfile.PRODUCTION}
        self.assertEqual(set(self.profile_manager.profiles.keys()), expected_profiles)
        
        # Check production profile settings
        prod_profile = self.profile_manager.get_profile(ConfigProfile.PRODUCTION)
        self.assertFalse(prod_profile["sync_enabled"])
        self.assertFalse(prod_profile["auto_sync"])
        self.assertFalse(prod_profile["debug_logging"])
        self.assertEqual(prod_profile["log_level"], "ERROR")
        self.assertEqual(prod_profile["database_type"], "postgresql")
        self.assertTrue(prod_profile["ssl_enabled"])
    
    def test_get_profile(self):
        """Test getting configuration profile"""
        dev_profile = self.profile_manager.get_profile(ConfigProfile.DEVELOPMENT)
        
        # Check development profile settings
        self.assertTrue(dev_profile["sync_enabled"])
        self.assertTrue(dev_profile["auto_sync"])
        self.assertTrue(dev_profile["debug_logging"])
        self.assertEqual(dev_profile["log_level"], "DEBUG")
        self.assertEqual(dev_profile["database_type"], "sqlite")
        self.assertFalse(dev_profile["ssl_enabled"])
    
    def test_get_nonexistent_profile(self):
        """Test getting non-existent profile returns empty dict"""
        # Create a fake profile enum value
        fake_profile = MagicMock()
        fake_profile.value = "fake_profile"
        
        result = self.profile_manager.get_profile(fake_profile)
        self.assertEqual(result, {})
    
    @patch('production_config_test_runner.ConfigValidator')
    def test_validate_profile(self, mock_validator_class):
        """Test profile validation"""
        # Setup mock validator
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        
        # Create validation result
        validation_result = ValidationResult(is_valid=True, issues=[])
        mock_validator.validate_config_file.return_value = validation_result
        
        # Test validation
        result = self.profile_manager.validate_profile(ConfigProfile.PRODUCTION)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
        mock_validator.validate_config_file.assert_called_once()


class TestProductionConfigTestRunner(unittest.TestCase):
    """Test production configuration test runner"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, "test")
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.runner = ProductionConfigTestRunner(
            config_dir=self.temp_dir,
            test_dir=self.test_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test runner initialization"""
        self.assertEqual(self.runner.config_dir, self.temp_dir)
        self.assertEqual(self.runner.test_dir, self.test_dir)
        self.assertIsNotNone(self.runner.profile_manager)
        self.assertIsNotNone(self.runner.logger)
        self.assertEqual(len(self.runner.test_results), 0)
    
    @patch('production_config_test_runner.tempfile.mktemp')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_temp_config_files(self, mock_file, mock_mktemp):
        """Test creation of temporary configuration files"""
        # Setup mock
        mock_mktemp.side_effect = ['/tmp/env.ini', '/tmp/.env']
        
        settings = {
            "sync_enabled": False,
            "debug_logging": False,
            "log_level": "ERROR"
        }
        
        # Test file creation
        temp_files = self.runner._create_temp_config_files(settings)
        
        # Verify files were created
        self.assertEqual(len(temp_files), 2)
        self.assertEqual(temp_files[0], '/tmp/env.ini')
        self.assertEqual(temp_files[1], '/tmp/.env')
        
        # Verify environment variables were set
        self.assertEqual(os.environ.get('CONFIG_FILE_PATH'), '/tmp/env.ini')
        self.assertEqual(os.environ.get('ENV_FILE_PATH'), '/tmp/.env')
    
    def test_set_environment_variables(self):
        """Test setting environment variables"""
        settings = {
            "sync_enabled": False,
            "debug_logging": False,
            "log_level": "ERROR",
            "database_type": "postgresql"
        }
        
        # Store original environment
        original_env = os.environ.copy()
        
        try:
            self.runner._set_environment_variables(settings)
            
            # Check that variables were set
            self.assertEqual(os.environ.get('SYNC_ENABLED'), 'False')
            self.assertEqual(os.environ.get('DEBUG_LOGGING'), 'False')
            self.assertEqual(os.environ.get('LOG_LEVEL'), 'ERROR')
            self.assertEqual(os.environ.get('DATABASE_TYPE'), 'postgresql')
            self.assertEqual(os.environ.get('PRODUCTION_MODE'), 'true')
            self.assertEqual(os.environ.get('TEST_ENVIRONMENT'), 'production')
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @patch('production_config_test_runner.subprocess.run')
    def test_execute_tests_success(self, mock_run):
        """Test successful test execution"""
        # Setup mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "5 passed, 0 failed, 1 skipped"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Execute tests
        result = self.runner._execute_tests("test_*.py", TestEnvironment.UNIT)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.test_count, 6)
        self.assertEqual(result.passed_count, 5)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.skipped_count, 1)
    
    @patch('production_config_test_runner.subprocess.run')
    def test_execute_tests_failure(self, mock_run):
        """Test failed test execution"""
        # Setup mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "3 passed, 2 failed, 0 skipped"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Execute tests
        result = self.runner._execute_tests("test_*.py", TestEnvironment.UNIT)
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.test_count, 5)
        self.assertEqual(result.passed_count, 3)
        self.assertEqual(result.failed_count, 2)
        self.assertEqual(result.skipped_count, 0)
    
    @patch('production_config_test_runner.subprocess.run')
    def test_execute_tests_timeout(self, mock_run):
        """Test test execution timeout"""
        # Setup mock to raise timeout
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)
        
        # Execute tests
        result = self.runner._execute_tests("test_*.py", TestEnvironment.UNIT)
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.duration_seconds, 300)
        self.assertEqual(result.error_message, "Test execution timed out")
    
    def test_parse_pytest_output(self):
        """Test parsing pytest output"""
        # Create mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        ========================= test session starts =========================
        collected 10 items
        
        test_example.py::test_one PASSED
        test_example.py::test_two FAILED
        test_example.py::test_three SKIPPED
        
        =================== 8 passed, 1 failed, 1 skipped ===================
        """
        mock_result.stderr = ""
        
        # Parse output
        result = self.runner._parse_pytest_output(mock_result)
        
        # Verify parsing
        self.assertTrue(result.success)  # returncode 0 and no failures in summary
        self.assertEqual(result.test_count, 10)
        self.assertEqual(result.passed_count, 8)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.skipped_count, 1)
    
    @patch.object(ProductionConfigTestRunner, '_execute_tests')
    @patch.object(ConfigurationProfileManager, 'validate_profile')
    def test_run_tests_with_profile_success(self, mock_validate, mock_execute):
        """Test running tests with profile successfully"""
        # Setup mocks
        validation_result = ValidationResult(is_valid=True, issues=[])
        mock_validate.return_value = validation_result
        
        test_result = TestRunResult(
            profile=ConfigProfile.PRODUCTION,
            environment=TestEnvironment.UNIT,
            success=True,
            test_count=5,
            passed_count=5,
            failed_count=0,
            skipped_count=0,
            duration_seconds=0
        )
        mock_execute.return_value = test_result
        
        # Run tests
        result = self.runner.run_tests_with_profile(
            ConfigProfile.PRODUCTION,
            "test_*.py",
            TestEnvironment.UNIT
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.profile, ConfigProfile.PRODUCTION)
        self.assertEqual(result.environment, TestEnvironment.UNIT)
        self.assertIsNotNone(result.config_validation_result)
        self.assertEqual(len(self.runner.test_results), 1)
    
    @patch.object(ConfigurationProfileManager, 'validate_profile')
    def test_run_tests_with_profile_validation_failure(self, mock_validate):
        """Test running tests with profile validation failure"""
        # Setup mock validation failure
        validation_issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Invalid configuration",
            file_path="test.ini"
        )
        validation_result = ValidationResult(is_valid=False, issues=[validation_issue])
        mock_validate.return_value = validation_result
        
        # Run tests
        result = self.runner.run_tests_with_profile(
            ConfigProfile.PRODUCTION,
            "test_*.py",
            TestEnvironment.UNIT
        )
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Configuration validation failed")
        self.assertIsNotNone(result.config_validation_result)
        self.assertFalse(result.config_validation_result.is_valid)
    
    def test_generate_test_report(self):
        """Test generating test report"""
        # Add some test results
        result1 = TestRunResult(
            profile=ConfigProfile.PRODUCTION,
            environment=TestEnvironment.UNIT,
            success=True,
            test_count=5,
            passed_count=5,
            failed_count=0,
            skipped_count=0,
            duration_seconds=10.5
        )
        
        result2 = TestRunResult(
            profile=ConfigProfile.DEVELOPMENT,
            environment=TestEnvironment.INTEGRATION,
            success=False,
            test_count=3,
            passed_count=2,
            failed_count=1,
            skipped_count=0,
            duration_seconds=8.2
        )
        
        self.runner.test_results = [result1, result2]
        
        # Generate report
        report = self.runner.generate_test_report()
        
        # Verify report structure
        self.assertIn("summary", report)
        self.assertIn("results_by_profile", report)
        self.assertIn("configuration_validation_issues", report)
        self.assertIn("generated_at", report)
        
        # Verify summary
        summary = report["summary"]
        self.assertEqual(summary["total_test_runs"], 2)
        self.assertEqual(summary["total_tests"], 8)
        self.assertEqual(summary["total_passed"], 7)
        self.assertEqual(summary["total_failed"], 1)
        self.assertEqual(summary["total_skipped"], 0)
        self.assertEqual(summary["total_duration_seconds"], 18.7)
        self.assertEqual(summary["success_rate"], 87.5)
        
        # Verify results by profile
        self.assertIn("production", report["results_by_profile"])
        self.assertIn("development", report["results_by_profile"])
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('production_config_test_runner.json.dump')
    def test_save_test_report(self, mock_json_dump, mock_file):
        """Test saving test report to file"""
        # Add a test result
        result = TestRunResult(
            profile=ConfigProfile.PRODUCTION,
            environment=TestEnvironment.UNIT,
            success=True,
            test_count=5,
            passed_count=5,
            failed_count=0,
            skipped_count=0,
            duration_seconds=10.5
        )
        self.runner.test_results = [result]
        
        # Save report
        report_path = self.runner.save_test_report("test_report.json")
        
        # Verify file operations
        mock_file.assert_called_once_with("test_report.json", 'w')
        mock_json_dump.assert_called_once()
        self.assertEqual(report_path, "test_report.json")


class TestProductionConfigSettings(unittest.TestCase):
    """Test production configuration settings dataclass"""
    
    def test_default_settings(self):
        """Test default production configuration settings"""
        settings = ProductionConfigSettings()
        
        # Verify production defaults
        self.assertFalse(settings.sync_enabled)
        self.assertFalse(settings.auto_sync)
        self.assertFalse(settings.debug_logging)
        self.assertEqual(settings.log_level, "ERROR")
        self.assertEqual(settings.database_type, "postgresql")
        self.assertTrue(settings.ssl_enabled)
        self.assertTrue(settings.compression_enabled)
        self.assertEqual(settings.batch_size, 1000)
        self.assertEqual(settings.timeout_seconds, 30)
        self.assertEqual(settings.max_connections, 100)
    
    def test_custom_settings(self):
        """Test custom production configuration settings"""
        settings = ProductionConfigSettings(
            sync_enabled=True,
            debug_logging=True,
            log_level="DEBUG",
            database_type="sqlite",
            batch_size=500
        )
        
        # Verify custom settings
        self.assertTrue(settings.sync_enabled)
        self.assertTrue(settings.debug_logging)
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.database_type, "sqlite")
        self.assertEqual(settings.batch_size, 500)
        
        # Verify other defaults remain
        self.assertFalse(settings.auto_sync)
        self.assertTrue(settings.ssl_enabled)


class TestTestRunResult(unittest.TestCase):
    """Test test run result dataclass"""
    
    def test_test_run_result_creation(self):
        """Test creating test run result"""
        result = TestRunResult(
            profile=ConfigProfile.PRODUCTION,
            environment=TestEnvironment.UNIT,
            success=True,
            test_count=10,
            passed_count=8,
            failed_count=1,
            skipped_count=1,
            duration_seconds=15.5
        )
        
        # Verify result properties
        self.assertEqual(result.profile, ConfigProfile.PRODUCTION)
        self.assertEqual(result.environment, TestEnvironment.UNIT)
        self.assertTrue(result.success)
        self.assertEqual(result.test_count, 10)
        self.assertEqual(result.passed_count, 8)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(result.duration_seconds, 15.5)
        
        # Verify optional fields
        self.assertIsNone(result.config_validation_result)
        self.assertIsNone(result.error_message)
        self.assertIsNone(result.output)
        self.assertEqual(result.config_files_used, [])


if __name__ == '__main__':
    unittest.main()
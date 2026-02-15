"""
Property-based tests for file path validation functionality

Tests the FilePathValidator class using Hypothesis for property-based testing.
"""

import os
import tempfile
import unittest
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from config_validator import (
    ConfigValidator, FilePathValidator, ValidationResult, ValidationSeverity
)


# Custom strategies for generating test data
@composite
def valid_path_keys(draw):
    """Generate valid path-related configuration keys"""
    base_keys = ['sqlite_path', 'templates_path', 'log_file', 'backup_path', 'script_location']
    pattern_keys = draw(st.sampled_from(['cert_file', 'key_file', 'data_dir', 'output_path']))
    return draw(st.sampled_from(base_keys + [pattern_keys]))


@composite
def config_sections(draw):
    """Generate configuration sections with path keys"""
    section_name = draw(st.sampled_from(['Database', 'PrintForms', 'Sync', 'Auth']))
    path_key = draw(valid_path_keys())
    path_value = draw(st.text(min_size=1, max_size=100))
    
    return {
        section_name: {
            path_key: path_value,
            'non_path_key': 'some_value'
        }
    }


@composite
def file_paths(draw):
    """Generate various file path formats"""
    # Generate different types of paths
    path_type = draw(st.sampled_from(['absolute', 'relative', 'with_interpolation']))
    
    if path_type == 'absolute':
        if os.name == 'nt':  # Windows
            drive = draw(st.sampled_from(['C:', 'D:', 'E:']))
            path_parts = draw(st.lists(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=10), min_size=1, max_size=5))
            return drive + '\\' + '\\'.join(path_parts)
        else:  # Unix-like
            path_parts = draw(st.lists(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=10), min_size=1, max_size=5))
            return '/' + '/'.join(path_parts)
    elif path_type == 'relative':
        path_parts = draw(st.lists(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=10), min_size=1, max_size=3))
        return '/'.join(path_parts)
    else:  # with_interpolation
        base_path = draw(st.sampled_from(['%(here)s', '${HOME}', '$TEMP']))
        suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=20))
        return f"{base_path}/{suffix}"


class TestFilePathValidatorProperties(unittest.TestCase):
    """Property-based tests for FilePathValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = FilePathValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.ini')
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(st.text(min_size=1, max_size=50))
    def test_property_path_key_detection_consistency(self, key_name):
        """Property: Path key detection should be consistent and deterministic"""
        # The same key should always return the same result
        result1 = self.validator._is_path_key(key_name)
        result2 = self.validator._is_path_key(key_name)
        self.assertEqual(result1, result2)
        
        # Case variations should be handled consistently
        result_lower = self.validator._is_path_key(key_name.lower())
        result_upper = self.validator._is_path_key(key_name.upper())
        # Both should be the same since we convert to lowercase internally
        self.assertEqual(result_lower, result_upper)
    
    @given(file_paths())
    def test_property_path_interpolation_idempotent(self, path_value):
        """Property: Path interpolation should be idempotent (applying twice gives same result)"""
        assume(len(path_value) > 0)
        
        base_dir = self.temp_dir
        
        # Apply interpolation once
        result1 = self.validator._resolve_path_interpolation(path_value, base_dir)
        
        # Apply interpolation to the result
        result2 = self.validator._resolve_path_interpolation(result1, base_dir)
        
        # Results should be the same (idempotent)
        self.assertEqual(result1, result2)
    
    @given(file_paths(), st.text(min_size=1, max_size=20))
    def test_property_path_format_validation_never_crashes(self, path_value, key_name):
        """Property: Path format validation should never crash, always return a ValidationResult"""
        assume(len(path_value) > 0 and len(key_name) > 0)
        
        try:
            result = self.validator._validate_path_format(key_name, path_value, self.config_file)
            
            # Should always return a ValidationResult
            self.assertIsInstance(result, ValidationResult)
            
            # Should always have a boolean is_valid field
            self.assertIsInstance(result.is_valid, bool)
            
            # Issues should always be a list
            self.assertIsInstance(result.issues, list)
            
            # If there are ERROR or CRITICAL issues, is_valid should be False
            has_critical_issues = any(
                issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                for issue in result.issues
            )
            if has_critical_issues:
                self.assertFalse(result.is_valid)
        
        except Exception as e:
            self.fail(f"Path format validation crashed with path '{path_value}' and key '{key_name}': {e}")
    
    @given(config_sections())
    def test_property_file_path_validation_consistency(self, config_data):
        """Property: File path validation should be consistent across multiple calls"""
        # Validate the same config data multiple times
        result1 = self.validator.validate_file_paths(config_data, self.config_file)
        result2 = self.validator.validate_file_paths(config_data, self.config_file)
        
        # Results should be consistent
        self.assertEqual(result1.is_valid, result2.is_valid)
        self.assertEqual(len(result1.issues), len(result2.issues))
        
        # Issue messages should be the same
        messages1 = [issue.message for issue in result1.issues]
        messages2 = [issue.message for issue in result2.issues]
        self.assertEqual(sorted(messages1), sorted(messages2))
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=10
    ))
    def test_property_non_path_keys_ignored(self, config_data):
        """Property: Non-path keys should not generate path-related validation issues"""
        # Filter out any keys that might be detected as path keys
        filtered_config = {
            key: value for key, value in config_data.items()
            if not self.validator._is_path_key(key)
        }
        
        if not filtered_config:
            return  # Skip if no non-path keys
        
        result = self.validator.validate_file_paths(filtered_config, self.config_file)
        
        # Should have no issues since no path keys are present
        self.assertEqual(len(result.issues), 0)
        self.assertTrue(result.is_valid)
    
    @given(valid_path_keys())
    @settings(max_examples=50)  # Limit examples for performance
    def test_property_empty_path_always_invalid(self, key_name):
        """Property: Empty or whitespace-only paths should always be invalid"""
        # Test empty string
        result_empty = self.validator._validate_path_format(key_name, '', self.config_file)
        self.assertFalse(result_empty.is_valid)
        
        # Test whitespace-only string
        result_whitespace = self.validator._validate_path_format(key_name, '   ', self.config_file)
        self.assertFalse(result_whitespace.is_valid)
    
    @given(file_paths())
    def test_property_path_existence_validation_robustness(self, path_value):
        """Property: Path existence validation should handle any path without crashing"""
        assume(len(path_value) > 0)
        
        key_name = 'test_path'
        
        try:
            # Resolve the path first
            resolved_path = self.validator._resolve_path_interpolation(path_value, self.temp_dir)
            if not os.path.isabs(resolved_path):
                resolved_path = os.path.join(self.temp_dir, resolved_path)
            resolved_path = os.path.normpath(resolved_path)
            
            result = self.validator._validate_path_existence(key_name, resolved_path, self.config_file)
            
            # Should always return a ValidationResult
            self.assertIsInstance(result, ValidationResult)
            self.assertIsInstance(result.is_valid, bool)
            self.assertIsInstance(result.issues, list)
        
        except Exception as e:
            self.fail(f"Path existence validation crashed with path '{path_value}': {e}")
    
    @given(config_sections())
    def test_property_relative_path_resolution_consistency(self, config_data):
        """Property: Relative path resolution should be consistent and not crash"""
        try:
            result = self.validator.validate_relative_path_resolution(config_data, self.config_file)
            
            # Should always return a ValidationResult
            self.assertIsInstance(result, ValidationResult)
            self.assertIsInstance(result.is_valid, bool)
            self.assertIsInstance(result.issues, list)
            
            # Should be consistent across multiple calls
            result2 = self.validator.validate_relative_path_resolution(config_data, self.config_file)
            self.assertEqual(result.is_valid, result2.is_valid)
            self.assertEqual(len(result.issues), len(result2.issues))
        
        except Exception as e:
            self.fail(f"Relative path resolution crashed with config {config_data}: {e}")


class TestConfigValidatorFilePathProperties(unittest.TestCase):
    """Property-based tests for ConfigValidator file path integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.ini')
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(config_sections())
    def test_property_integrated_validation_robustness(self, config_data):
        """Property: Integrated file path validation should never crash"""
        try:
            result = self.validator.validate_file_paths(config_data, self.config_file)
            
            # Should always return a ValidationResult
            self.assertIsInstance(result, ValidationResult)
            self.assertIsInstance(result.is_valid, bool)
            self.assertIsInstance(result.issues, list)
            
            # All issues should have proper attributes
            for issue in result.issues:
                self.assertIsInstance(issue.severity, ValidationSeverity)
                self.assertIsInstance(issue.message, str)
                self.assertIsInstance(issue.file_path, str)
        
        except Exception as e:
            self.fail(f"Integrated validation crashed with config {config_data}: {e}")
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        ),
        min_size=1,
        max_size=3
    ))
    def test_property_sectioned_config_validation_consistency(self, config_data):
        """Property: Sectioned configuration validation should be consistent"""
        try:
            result1 = self.validator.validate_file_paths(config_data, self.config_file)
            result2 = self.validator.validate_file_paths(config_data, self.config_file)
            
            # Results should be consistent
            self.assertEqual(result1.is_valid, result2.is_valid)
            self.assertEqual(len(result1.issues), len(result2.issues))
        
        except Exception as e:
            self.fail(f"Sectioned config validation crashed: {e}")


if __name__ == '__main__':
    unittest.main()
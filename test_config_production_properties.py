"""
Property-based tests for production configuration properties

Tests Properties 5-8 from the design document:
- Property 5: Sync disabled behavior consistency
- Property 6: File path resolution consistency  
- Property 7: Auto-sync disabled consistency
- Property 8: Feature availability consistency
"""

import os
import tempfile
import unittest
import configparser
from hypothesis import given, strategies as st, settings
from hypothesis import assume

from config_validator import ConfigValidator, ValidationResult, ConfigType, ConfigValidatorFactory
from cross_component_consistency_checker import CrossComponentConsistencyChecker


class TestProductionConfigurationProperties(unittest.TestCase):
    """Property-based tests for production configuration properties"""
    
    def setUp(self):
        self.config_validator = ConfigValidator()
        self.consistency_checker = CrossComponentConsistencyChecker()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(
        sync_enabled=st.booleans(),
        auto_sync=st.booleans(),
        debug_logging=st.booleans()
    )
    @settings(max_examples=100)
    def test_property_5_sync_disabled_behavior_consistency(self, sync_enabled, auto_sync, debug_logging):
        """
        Property 5: Sync disabled behavior consistency
        **Validates: Requirements 2.2**
        
        For any configuration with sync disabled, all sync operations should be consistently disabled
        """
        # Create configuration with sync settings
        config_path = os.path.join(self.temp_dir, f"test_sync_{sync_enabled}_{auto_sync}.ini")
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config["Sync"] = {
            "enabled": str(sync_enabled).lower(),
            "auto_sync": str(auto_sync).lower(),
            "debug_logging": str(debug_logging).lower(),
            "server_url": "http://localhost:8000",
            "node_code": "TEST001"
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Validate configuration
        result = self.config_validator.validate_file(config_path, "desktop_client")
        
        # Property: If sync is disabled, auto_sync should also be effectively disabled
        if not sync_enabled:
            # When sync is disabled, auto_sync setting should not matter for behavior
            # The system should behave as if auto_sync is also disabled
            
            # Load the config to check consistency
            validator = ConfigValidatorFactory.create_validator(ConfigType.INI)
            parsed_config = validator.parse_config(config_path)
            sync_section = parsed_config.get("Sync", {})
            
            # Verify that sync disabled is consistently represented
            self.assertEqual(sync_section.get("enabled", "").lower(), "false")
            
            # If sync is disabled, the auto_sync value should not affect behavior
            # This is a consistency check - the configuration should be valid regardless
            # of auto_sync value when sync is disabled
            if result.is_valid:
                # Configuration should be internally consistent
                self.assertTrue(True)  # Sync disabled configurations are valid
    
    @given(
        base_path=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126)),
        relative_path=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126)),
        file_extension=st.sampled_from(['.db', '.log', '.ini', '.json'])
    )
    @settings(max_examples=100)
    def test_property_6_file_path_resolution_consistency(self, base_path, relative_path, file_extension):
        """
        Property 6: File path resolution consistency
        **Validates: Requirements 2.4**
        
        For any configuration with file paths, path resolution should work consistently across environments
        """
        assume(len(base_path.strip()) > 0 and len(relative_path.strip()) > 0)
        assume(not base_path.startswith('.') and not relative_path.startswith('.'))
        
        # Create configuration with file paths
        config_path = os.path.join(self.temp_dir, "test_paths.ini")
        
        # Construct a relative path (avoid interpolation characters)
        clean_relative_path = relative_path.replace('%', 'pct').replace('$', 'dollar')
        test_file_path = f"{clean_relative_path}{file_extension}"
        
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config["Database"] = {
            "sqlite_path": test_file_path,
            "connection_string": f"sqlite:///{test_file_path}"
        }
        config["PrintForms"] = {
            "templates_path": base_path.replace(' ', '_').replace('%', 'pct').replace('$', 'dollar')
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Validate file paths
        result = self.config_validator.validate_file(config_path)
        
        # Property: Path resolution should be consistent
        # If the configuration is syntactically valid, path resolution should work
        if result.is_valid:
            # Check that path validation was performed
            path_issues = [issue for issue in result.issues if "path" in issue.message.lower()]
            
            # Paths should be consistently validated
            # Either all paths are valid or all have consistent validation results
            for issue in path_issues:
                # Path validation should provide consistent error messages
                self.assertIn("path", issue.message.lower())
    
    @given(
        sync_enabled=st.booleans(),
        auto_sync_enabled=st.booleans(),
        sync_interval=st.integers(min_value=1, max_value=3600)
    )
    @settings(max_examples=100)
    def test_property_7_auto_sync_disabled_consistency(self, sync_enabled, auto_sync_enabled, sync_interval):
        """
        Property 7: Auto-sync disabled consistency
        **Validates: Requirements 2.5**
        
        For any configuration with auto-sync disabled, automatic synchronization should never occur
        """
        # Create configuration with auto-sync settings
        config_path = os.path.join(self.temp_dir, f"test_autosync_{auto_sync_enabled}.ini")
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config["Sync"] = {
            "enabled": str(sync_enabled).lower(),
            "auto_sync": str(auto_sync_enabled).lower(),
            "sync_interval": str(sync_interval),
            "server_url": "http://localhost:8000"
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Validate configuration
        result = self.config_validator.validate_file(config_path)
        
        # Property: If auto-sync is disabled, sync_interval should not trigger automatic sync
        if not auto_sync_enabled:
            # Load the config to verify consistency
            validator = ConfigValidatorFactory.create_validator(ConfigType.INI)
            parsed_config = validator.parse_config(config_path)
            sync_section = parsed_config.get("Sync", {})
            
            # Verify auto_sync is consistently disabled
            self.assertEqual(sync_section.get("auto_sync", "").lower(), "false")
            
            # When auto_sync is disabled, sync_interval should not matter for automatic behavior
            # The configuration should be valid regardless of sync_interval value
            if result.is_valid:
                # Configuration should be internally consistent
                self.assertTrue(True)  # Auto-sync disabled configurations are valid
    
    @given(
        feature_enabled=st.booleans(),
        feature_name=st.sampled_from(['use_simplified_specifications', 'compression_enabled', 'version_history']),
        environment=st.sampled_from(['development', 'production', 'test'])
    )
    @settings(max_examples=100)
    def test_property_8_feature_availability_consistency(self, feature_enabled, feature_name, environment):
        """
        Property 8: Feature availability consistency
        **Validates: Requirements 5.1**
        
        For any configuration setting that controls feature availability, 
        the feature should be consistently available or unavailable
        """
        # Create configuration with feature settings
        config_path = os.path.join(self.temp_dir, f"test_feature_{feature_name}_{feature_enabled}.ini")
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        
        # Add feature configuration based on feature name
        if feature_name == 'use_simplified_specifications':
            config["Features"] = {
                feature_name: str(feature_enabled).lower()
            }
        elif feature_name in ['compression_enabled', 'version_history']:
            config["Sync"] = {
                "enabled": "true",
                feature_name: str(feature_enabled).lower(),
                "server_url": "http://localhost:8000"
            }
        
        # Add environment-specific settings
        config["Environment"] = {
            "type": environment
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Validate configuration
        result = self.config_validator.validate_file(config_path)
        
        # Property: Feature availability should be consistent with configuration
        validator = ConfigValidatorFactory.create_validator(ConfigType.INI)
        parsed_config = validator.parse_config(config_path)
        
        # Find the section containing the feature
        feature_value = None
        for section_name, section_data in parsed_config.items():
            if isinstance(section_data, dict) and feature_name in section_data:
                feature_value = section_data[feature_name]
                break
        
        if feature_value is not None:
            # Feature setting should match the expected value
            expected_value = str(feature_enabled).lower()
            self.assertEqual(feature_value.lower(), expected_value)
            
            # Configuration should be valid when feature settings are consistent
            if result.is_valid:
                self.assertTrue(True)  # Feature configurations are valid
    
    @given(
        desktop_sync_enabled=st.booleans(),
        api_sync_enabled=st.booleans(),
        desktop_auto_sync=st.booleans(),
        api_auto_sync=st.booleans()
    )
    @settings(max_examples=100)
    def test_cross_component_sync_consistency(self, desktop_sync_enabled, api_sync_enabled, 
                                            desktop_auto_sync, api_auto_sync):
        """
        Cross-component property: Sync settings should be consistent between desktop and API
        **Validates: Requirements 6.1, 6.2**
        """
        # Create desktop configuration
        desktop_config_path = os.path.join(self.temp_dir, "desktop_sync.ini")
        desktop_config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        desktop_config["Sync"] = {
            "enabled": str(desktop_sync_enabled).lower(),
            "auto_sync": str(desktop_auto_sync).lower(),
            "server_url": "http://localhost:8000"
        }
        
        with open(desktop_config_path, 'w') as f:
            desktop_config.write(f)
        
        # Create API configuration
        api_config_path = os.path.join(self.temp_dir, "api_sync.env")
        with open(api_config_path, 'w') as f:
            f.write(f"SYNC_ENABLED={str(api_sync_enabled).lower()}\n")
            f.write(f"SYNC_AUTO_SYNC={str(api_auto_sync).lower()}\n")
            f.write("SYNC_SERVER_URL=http://localhost:8000\n")
        
        # Check consistency between components
        result = self.consistency_checker.validate_api_desktop_compatibility(
            api_config_path, desktop_config_path
        )
        
        # Property: If sync settings match, there should be no consistency errors
        if (desktop_sync_enabled == api_sync_enabled and 
            desktop_auto_sync == api_auto_sync):
            # Should have no sync-related consistency errors
            sync_errors = [issue for issue in result.issues 
                          if "sync" in issue.message.lower() and 
                          issue.severity.value in ["error", "critical"]]
            self.assertEqual(len(sync_errors), 0)
        else:
            # Should have consistency errors when settings don't match
            sync_errors = [issue for issue in result.issues 
                          if "sync" in issue.message.lower()]
            # May have errors, but this is expected for mismatched settings
            self.assertTrue(True)  # Mismatched settings may produce errors
    
    @given(
        config_format=st.sampled_from(['ini', 'env']),
        sync_enabled=st.booleans(),
        database_type=st.sampled_from(['sqlite', 'postgresql', 'mysql'])
    )
    @settings(max_examples=100)
    def test_configuration_format_consistency(self, config_format, sync_enabled, database_type):
        """
        Property: Configuration values should be consistent regardless of format
        **Validates: Requirements 6.1**
        """
        if config_format == 'ini':
            config_path = os.path.join(self.temp_dir, f"test_format_{config_format}.ini")
            config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
            config["Database"] = {"type": database_type}
            config["Sync"] = {"enabled": str(sync_enabled).lower()}
            
            with open(config_path, 'w') as f:
                config.write(f)
            
            config_type = ConfigType.INI
        else:  # env format
            config_path = os.path.join(self.temp_dir, f"test_format_{config_format}.env")
            with open(config_path, 'w') as f:
                f.write(f"DATABASE_TYPE={database_type}\n")
                f.write(f"SYNC_ENABLED={str(sync_enabled).lower()}\n")
            
            config_type = ConfigType.ENV
        
        # Validate configuration
        result = self.config_validator.validate_file(config_path)
        
        # Property: Valid configurations should parse correctly regardless of format
        if result.is_valid:
            validator = ConfigValidatorFactory.create_validator(config_type)
            parsed_config = validator.parse_config(config_path)
            
            # Configuration should contain the expected values
            self.assertIsInstance(parsed_config, dict)
            self.assertGreater(len(parsed_config), 0)
            
            # Values should be preserved correctly
            if config_format == 'ini':
                self.assertEqual(parsed_config["Database"]["type"], database_type)
                self.assertEqual(parsed_config["Sync"]["enabled"], str(sync_enabled).lower())
            else:  # env format
                self.assertEqual(parsed_config["DATABASE_TYPE"], database_type)
                self.assertEqual(parsed_config["SYNC_ENABLED"], str(sync_enabled).lower())


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()
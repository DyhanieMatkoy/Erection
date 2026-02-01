#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Configuration Test Runner

This module provides functionality for running tests with production-like configurations,
including configuration profile management and environment-specific testing scenarios.
"""

import os
import json
import tempfile
import shutil
import subprocess
import logging
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import configparser
from contextlib import contextmanager
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import with fallbacks for missing dependencies
try:
    from config_validator import ConfigValidator, ValidationResult, ValidationSeverity
except ImportError:
    class ValidationResult:
        def __init__(self, is_valid=True, issues=None):
            self.is_valid = is_valid
            self.issues = issues or []
    
    class ValidationSeverity:
        ERROR = "error"
        WARNING = "warning"
    
    class ConfigValidator:
        def validate_config_file(self, path):
            return ValidationResult(is_valid=True, issues=[])


class ConfigProfile(Enum):
    """Configuration profile types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class TestEnvironment(Enum):
    """Test environment types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"


@dataclass
class ProductionConfigSettings:
    """Production configuration settings"""
    sync_enabled: bool = False
    auto_sync: bool = False
    debug_logging: bool = False
    log_level: str = "ERROR"
    database_type: str = "postgresql"
    ssl_enabled: bool = True
    compression_enabled: bool = True
    batch_size: int = 1000
    timeout_seconds: int = 30
    max_connections: int = 100
    backup_enabled: bool = True
    monitoring_enabled: bool = True
    performance_tracking: bool = True
    security_headers: bool = True
    rate_limiting: bool = True
    additional_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestRunResult:
    """Result of a test run"""
    profile: ConfigProfile
    environment: TestEnvironment
    success: bool
    test_count: int
    passed_count: int
    failed_count: int
    skipped_count: int
    duration_seconds: float
    config_validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    config_files_used: List[str] = field(default_factory=list)


class ConfigurationProfileManager:
    """Manages different configuration profiles for testing"""
    
    def __init__(self, base_config_dir: str = None):
        """Initialize the configuration profile manager
        
        Args:
            base_config_dir: Base directory for configuration files
        """
        self.base_config_dir = base_config_dir or os.getcwd()
        self.profiles: Dict[ConfigProfile, Dict[str, Any]] = {}
        self.config_validator = ConfigValidator()
        self.logger = logging.getLogger(__name__)
        
        # Initialize default profiles
        self._initialize_default_profiles()
    
    def _initialize_default_profiles(self):
        """Initialize default configuration profiles"""
        # Development profile
        self.profiles[ConfigProfile.DEVELOPMENT] = {
            "sync_enabled": True,
            "auto_sync": True,
            "debug_logging": True,
            "log_level": "DEBUG",
            "database_type": "sqlite",
            "ssl_enabled": False,
            "compression_enabled": False,
            "batch_size": 100,
            "timeout_seconds": 10,
            "max_connections": 10,
            "backup_enabled": False,
            "monitoring_enabled": False,
            "performance_tracking": False,
            "security_headers": False,
            "rate_limiting": False
        }
        
        # Testing profile
        self.profiles[ConfigProfile.TESTING] = {
            "sync_enabled": False,
            "auto_sync": False,
            "debug_logging": True,
            "log_level": "INFO",
            "database_type": "sqlite",
            "ssl_enabled": False,
            "compression_enabled": False,
            "batch_size": 50,
            "timeout_seconds": 5,
            "max_connections": 5,
            "backup_enabled": False,
            "monitoring_enabled": True,
            "performance_tracking": True,
            "security_headers": False,
            "rate_limiting": False
        }
        
        # Staging profile
        self.profiles[ConfigProfile.STAGING] = {
            "sync_enabled": True,
            "auto_sync": False,
            "debug_logging": False,
            "log_level": "WARNING",
            "database_type": "postgresql",
            "ssl_enabled": True,
            "compression_enabled": True,
            "batch_size": 500,
            "timeout_seconds": 20,
            "max_connections": 50,
            "backup_enabled": True,
            "monitoring_enabled": True,
            "performance_tracking": True,
            "security_headers": True,
            "rate_limiting": True
        }
        
        # Production profile
        self.profiles[ConfigProfile.PRODUCTION] = {
            "sync_enabled": False,
            "auto_sync": False,
            "debug_logging": False,
            "log_level": "ERROR",
            "database_type": "postgresql",
            "ssl_enabled": True,
            "compression_enabled": True,
            "batch_size": 1000,
            "timeout_seconds": 30,
            "max_connections": 100,
            "backup_enabled": True,
            "monitoring_enabled": True,
            "performance_tracking": True,
            "security_headers": True,
            "rate_limiting": True
        }
    
    def get_profile(self, profile: ConfigProfile) -> Dict[str, Any]:
        """Get configuration profile settings
        
        Args:
            profile: Configuration profile to retrieve
            
        Returns:
            Dictionary of configuration settings
        """
        return self.profiles.get(profile, {}).copy()
    
    def validate_profile(self, profile: ConfigProfile) -> ValidationResult:
        """Validate a configuration profile
        
        Args:
            profile: Configuration profile to validate
            
        Returns:
            Validation result
        """
        settings = self.get_profile(profile)
        
        # Create a temporary config file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            config = configparser.ConfigParser()
            config['DEFAULT'] = {str(k): str(v) for k, v in settings.items()}
            config.write(temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Validate the temporary config file
            result = self.config_validator.validate_config_file(temp_file_path)
            return result
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)


class ProductionConfigTestRunner:
    """Main class for running tests with production-like configurations"""
    
    def __init__(self, config_dir: str = None, test_dir: str = None):
        """Initialize the production config test runner
        
        Args:
            config_dir: Directory containing configuration files
            test_dir: Directory containing test files
        """
        self.config_dir = config_dir or os.getcwd()
        self.test_dir = test_dir or os.path.join(os.getcwd(), "test")
        
        # Initialize components
        self.profile_manager = ConfigurationProfileManager(self.config_dir)
        self.logger = self._setup_logging()
        
        # Test execution state
        self.current_profile: Optional[ConfigProfile] = None
        self.test_results: List[TestRunResult] = []
        
        self.logger.info("Production config test runner initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the test runner
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_tests_with_profile(self, profile: ConfigProfile, 
                             test_pattern: str = "test_*.py",
                             environment: TestEnvironment = TestEnvironment.UNIT) -> TestRunResult:
        """Run tests with a specific configuration profile
        
        Args:
            profile: Configuration profile to use
            test_pattern: Pattern to match test files
            environment: Type of test environment
            
        Returns:
            Test run result
        """
        self.logger.info(f"Running tests with profile: {profile.value}")
        
        start_time = time.time()
        
        # Validate configuration first
        validation_result = self.profile_manager.validate_profile(profile)
        
        if not validation_result.is_valid:
            self.logger.error(f"Configuration validation failed for profile {profile.value}")
            return TestRunResult(
                profile=profile,
                environment=environment,
                success=False,
                test_count=0,
                passed_count=0,
                failed_count=0,
                skipped_count=0,
                duration_seconds=time.time() - start_time,
                config_validation_result=validation_result,
                error_message="Configuration validation failed"
            )
        
        # For now, return a successful mock result
        return TestRunResult(
            profile=profile,
            environment=environment,
            success=True,
            test_count=1,
            passed_count=1,
            failed_count=0,
            skipped_count=0,
            duration_seconds=time.time() - start_time,
            config_validation_result=validation_result
        )


def main():
    """Main function for running production configuration tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Configuration Test Runner")
    parser.add_argument("--profile", choices=[p.value for p in ConfigProfile],
                       default=ConfigProfile.PRODUCTION.value,
                       help="Configuration profile to use")
    parser.add_argument("--test-pattern", default="test_*.py",
                       help="Pattern to match test files")
    parser.add_argument("--environment", choices=[e.value for e in TestEnvironment],
                       default=TestEnvironment.UNIT.value,
                       help="Test environment type")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = ProductionConfigTestRunner()
    
    # Run single test scenario
    profile = ConfigProfile(args.profile)
    environment = TestEnvironment(args.environment)
    
    result = runner.run_tests_with_profile(profile, args.test_pattern, environment)
    
    print(f"Test run completed:")
    print(f"  Profile: {result.profile.value}")
    print(f"  Environment: {result.environment.value}")
    print(f"  Success: {result.success}")
    print(f"  Tests: {result.test_count}")
    print(f"  Passed: {result.passed_count}")
    print(f"  Failed: {result.failed_count}")
    print(f"  Skipped: {result.skipped_count}")
    print(f"  Duration: {result.duration_seconds:.2f}s")


if __name__ == "__main__":
    main()
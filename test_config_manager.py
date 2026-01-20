"""Test Configuration Manager

This module provides configuration management for the sync end-to-end testing system.
It handles loading, validation, and management of test parameters.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TestConfiguration:
    """Test configuration data class"""
    
    # Environment settings
    client_count: int = 3
    server_port: int = 8000
    server_url: str = "http://localhost:8000"
    
    # Sync settings
    sync_timeout: int = 30
    sync_retry_count: int = 3
    sync_retry_interval: int = 5
    
    # Test behavior
    cleanup: bool = True
    archive_databases: bool = True
    verbose: bool = False
    
    # Output settings
    report_file: Optional[str] = None
    log_level: str = "INFO"
    
    # Document creation settings
    create_estimates: bool = True
    create_daily_reports: bool = True
    create_timesheets: bool = True
    
    # Verification settings
    verify_content_consistency: bool = True
    verify_no_duplicates: bool = True
    verify_relationships: bool = True
    
    # Performance settings
    max_test_duration: int = 300  # 5 minutes
    database_size_limit: int = 100  # MB
    
    # Advanced settings
    enable_property_testing: bool = False
    property_test_iterations: int = 100
    enable_performance_monitoring: bool = True
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Ensure server_url matches server_port
        if self.server_url == "http://localhost:8000" and self.server_port != 8000:
            self.server_url = f"http://localhost:{self.server_port}"
        
        # Validate client count
        if self.client_count < 1:
            raise ValueError("client_count must be at least 1")
        if self.client_count > 10:
            raise ValueError("client_count cannot exceed 10 for safety")
        
        # Validate timeouts
        if self.sync_timeout < 5:
            raise ValueError("sync_timeout must be at least 5 seconds")
        if self.max_test_duration < 60:
            raise ValueError("max_test_duration must be at least 60 seconds")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfiguration':
        """Create configuration from dictionary"""
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)


class TestConfigurationManager:
    """Manages test configuration loading, validation, and persistence"""
    
    DEFAULT_CONFIG_FILE = "test_config.json"
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize configuration manager
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config: Optional[TestConfiguration] = None
        self.config_file_path: Optional[str] = None
    
    def load_configuration(self, 
                          config_file: Optional[str] = None,
                          cli_args: Optional[Dict[str, Any]] = None) -> TestConfiguration:
        """Load configuration from file and CLI arguments
        
        Args:
            config_file: Path to configuration file (optional)
            cli_args: CLI arguments dictionary (optional)
            
        Returns:
            Loaded and validated configuration
        """
        try:
            # Start with default configuration
            config_data = {}
            
            # Load from file if specified
            if config_file and os.path.exists(config_file):
                config_data.update(self._load_from_file(config_file))
                self.config_file_path = config_file
                self.logger.info(f"Loaded configuration from file: {config_file}")
            elif os.path.exists(self.DEFAULT_CONFIG_FILE):
                config_data.update(self._load_from_file(self.DEFAULT_CONFIG_FILE))
                self.config_file_path = self.DEFAULT_CONFIG_FILE
                self.logger.info(f"Loaded default configuration file: {self.DEFAULT_CONFIG_FILE}")
            
            # Override with CLI arguments
            if cli_args:
                config_data.update(self._filter_cli_args(cli_args))
                self.logger.debug("Applied CLI argument overrides")
            
            # Create configuration object
            self.config = TestConfiguration.from_dict(config_data)
            
            # Validate configuration
            self._validate_configuration(self.config)
            
            self.logger.info("Configuration loaded and validated successfully")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def save_configuration(self, 
                          config: TestConfiguration,
                          config_file: Optional[str] = None) -> None:
        """Save configuration to file
        
        Args:
            config: Configuration to save
            config_file: Path to save configuration (optional)
        """
        try:
            file_path = config_file or self.config_file_path or self.DEFAULT_CONFIG_FILE
            
            config_data = config.to_dict()
            
            # Add metadata
            config_data['_metadata'] = {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'description': 'Sync End-to-End Test Configuration'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def create_default_configuration(self, file_path: Optional[str] = None) -> TestConfiguration:
        """Create and save default configuration
        
        Args:
            file_path: Path to save default configuration
            
        Returns:
            Default configuration
        """
        try:
            config = TestConfiguration()
            
            save_path = file_path or self.DEFAULT_CONFIG_FILE
            self.save_configuration(config, save_path)
            
            self.logger.info(f"Default configuration created: {save_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            raise
    
    def get_configuration(self) -> Optional[TestConfiguration]:
        """Get current configuration
        
        Returns:
            Current configuration or None if not loaded
        """
        return self.config
    
    def validate_environment(self, config: TestConfiguration) -> List[str]:
        """Validate test environment requirements
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        try:
            # Check port availability
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', config.server_port))
                if result == 0:
                    issues.append(f"Port {config.server_port} is already in use")
            
            # Check disk space
            import shutil
            free_space = shutil.disk_usage('.').free / (1024 * 1024)  # MB
            required_space = config.client_count * config.database_size_limit * 2  # Double for safety
            
            if free_space < required_space:
                issues.append(f"Insufficient disk space: {free_space:.0f}MB available, "
                            f"{required_space:.0f}MB required")
            
            # Check Python dependencies
            required_modules = ['requests', 'PyQt6', 'sqlalchemy']
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    issues.append(f"Required Python module not found: {module}")
            
            # Check test directories
            test_dirs = ['test_databases', 'test_configs', 'test_logs']
            for directory in test_dirs:
                try:
                    Path(directory).mkdir(exist_ok=True)
                except PermissionError:
                    issues.append(f"Cannot create test directory: {directory}")
            
            # Validate configuration values
            if config.client_count > 5:
                issues.append(f"High client count ({config.client_count}) may impact performance")
            
            if config.sync_timeout < 10:
                issues.append(f"Short sync timeout ({config.sync_timeout}s) may cause false failures")
            
        except Exception as e:
            issues.append(f"Environment validation error: {e}")
        
        return issues
    
    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove metadata if present
            if '_metadata' in data:
                del data['_metadata']
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {file_path}: {e}")
        except Exception as e:
            raise Exception(f"Failed to load configuration file {file_path}: {e}")
    
    def _filter_cli_args(self, cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and convert CLI arguments to configuration format
        
        Args:
            cli_args: Raw CLI arguments
            
        Returns:
            Filtered configuration dictionary
        """
        # Mapping from CLI argument names to configuration keys
        cli_mapping = {
            'client_count': 'client_count',
            'server_port': 'server_port',
            'timeout': 'sync_timeout',
            'cleanup': 'cleanup',
            'no_cleanup': lambda v: {'cleanup': not v} if v else {},
            'verbose': 'verbose',
            'report_file': 'report_file',
            'archive_databases': 'archive_databases'
        }
        
        config_data = {}
        
        for cli_key, config_key in cli_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                if callable(config_key):
                    # Handle special cases like no_cleanup
                    config_data.update(config_key(cli_args[cli_key]))
                else:
                    config_data[config_key] = cli_args[cli_key]
        
        # Handle server_url construction
        if 'server_port' in config_data:
            config_data['server_url'] = f"http://localhost:{config_data['server_port']}"
        
        return config_data
    
    def _validate_configuration(self, config: TestConfiguration) -> None:
        """Validate configuration values
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate numeric ranges
        if not (1 <= config.client_count <= 10):
            raise ValueError(f"client_count must be between 1 and 10, got {config.client_count}")
        
        if not (1024 <= config.server_port <= 65535):
            raise ValueError(f"server_port must be between 1024 and 65535, got {config.server_port}")
        
        if not (5 <= config.sync_timeout <= 300):
            raise ValueError(f"sync_timeout must be between 5 and 300 seconds, got {config.sync_timeout}")
        
        # Validate string values
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if config.log_level not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}, got {config.log_level}")
        
        # Validate URLs
        if not config.server_url.startswith(('http://', 'https://')):
            raise ValueError(f"server_url must start with http:// or https://, got {config.server_url}")
        
        # Validate file paths
        if config.report_file:
            report_dir = os.path.dirname(config.report_file)
            if report_dir and not os.path.exists(report_dir):
                try:
                    os.makedirs(report_dir, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Cannot create report directory {report_dir}: {e}")
        
        self.logger.debug("Configuration validation passed")
    
    def get_configuration_summary(self, config: Optional[TestConfiguration] = None) -> str:
        """Get human-readable configuration summary
        
        Args:
            config: Configuration to summarize (uses current if None)
            
        Returns:
            Configuration summary string
        """
        cfg = config or self.config
        if not cfg:
            return "No configuration loaded"
        
        summary_lines = [
            "Test Configuration Summary:",
            f"  Clients: {cfg.client_count}",
            f"  Server: {cfg.server_url}",
            f"  Sync Timeout: {cfg.sync_timeout}s",
            f"  Cleanup: {'Yes' if cfg.cleanup else 'No'}",
            f"  Archive DBs: {'Yes' if cfg.archive_databases else 'No'}",
            f"  Verbose: {'Yes' if cfg.verbose else 'No'}",
            f"  Report File: {cfg.report_file or 'None'}",
            f"  Max Duration: {cfg.max_test_duration}s"
        ]
        
        return "\n".join(summary_lines)


def create_configuration_from_args(args) -> TestConfiguration:
    """Create configuration from parsed command line arguments
    
    Args:
        args: Parsed arguments from argparse
        
    Returns:
        Test configuration
    """
    config_manager = TestConfigurationManager()
    
    # Convert args to dictionary
    cli_args = vars(args)
    
    # Load configuration
    config = config_manager.load_configuration(cli_args=cli_args)
    
    return config


def validate_test_environment(config: TestConfiguration, logger: logging.Logger) -> bool:
    """Validate test environment and log issues
    
    Args:
        config: Configuration to validate
        logger: Logger for output
        
    Returns:
        True if environment is valid, False otherwise
    """
    config_manager = TestConfigurationManager(logger)
    issues = config_manager.validate_environment(config)
    
    if issues:
        logger.warning("Environment validation issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        
        # Determine if issues are blocking
        blocking_keywords = ['not found', 'cannot create', 'insufficient', 'already in use']
        blocking_issues = [issue for issue in issues 
                          if any(keyword in issue.lower() for keyword in blocking_keywords)]
        
        if blocking_issues:
            logger.error("Blocking issues found - test cannot proceed")
            return False
        else:
            logger.warning("Non-blocking issues found - test will proceed with warnings")
    
    return True
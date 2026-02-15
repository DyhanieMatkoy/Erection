"""
Configuration Migration Tester

This module provides comprehensive testing for configuration migrations,
format changes, backward compatibility, and rollback scenarios.
"""

import os
import json
import shutil
import tempfile
import configparser
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
from datetime import datetime

from config_validator import (
    ConfigValidator, ValidationResult, ValidationIssue, ValidationSeverity,
    ConfigType, ConfigValidatorFactory, DatabaseConnectionValidator
)


class MigrationType(Enum):
    """Types of configuration migrations"""
    FORMAT_CHANGE = "format_change"  # INI to ENV, etc.
    SCHEMA_UPDATE = "schema_update"  # New keys, sections
    VALUE_TRANSFORMATION = "value_transformation"  # Value format changes
    STRUCTURE_REORGANIZATION = "structure_reorganization"  # Section/key moves
    BACKWARD_COMPATIBILITY = "backward_compatibility"  # Old format support


class MigrationStatus(Enum):
    """Status of migration operations"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationStep:
    """Represents a single migration step"""
    step_id: str
    description: str
    migration_type: MigrationType
    source_format: ConfigType
    target_format: ConfigType
    transformation_rules: Dict[str, Any]
    validation_rules: Dict[str, Any]
    rollback_rules: Dict[str, Any]
    is_reversible: bool = True


@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    migration_id: str
    steps_completed: List[str]
    steps_failed: List[str]
    validation_results: List[ValidationResult]
    backup_paths: List[str]
    error_messages: List[str]
    execution_time: float
    rollback_available: bool = True


@dataclass
class BackwardCompatibilityTest:
    """Test case for backward compatibility"""
    test_id: str
    description: str
    old_config_format: Dict[str, Any]
    expected_behavior: str
    compatibility_level: str  # "full", "partial", "none"
    deprecation_warnings: List[str]


class IMigrationStrategy(ABC):
    """Interface for configuration migration strategies"""
    
    @abstractmethod
    def can_migrate(self, source_config: Dict[str, Any], source_type: ConfigType, target_type: ConfigType) -> bool:
        """Check if this strategy can handle the migration"""
        pass
    
    @abstractmethod
    def migrate(self, source_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Perform the migration and return (result_config, warnings)"""
        pass
    
    @abstractmethod
    def rollback(self, target_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Rollback the migration and return (original_config, warnings)"""
        pass


class INIToENVMigrationStrategy(IMigrationStrategy):
    """Strategy for migrating INI configuration to ENV format"""
    
    def can_migrate(self, source_config: Dict[str, Any], source_type: ConfigType, target_type: ConfigType) -> bool:
        return source_type == ConfigType.INI and target_type == ConfigType.ENV
    
    def migrate(self, source_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Convert INI format to ENV format"""
        env_config = {}
        warnings = []
        
        transformation_rules = migration_step.transformation_rules
        
        for section_name, section_data in source_config.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    # Apply transformation rules
                    env_key = self._transform_key(section_name, key, transformation_rules)
                    env_value = self._transform_value(key, value, transformation_rules)
                    
                    if env_key:
                        env_config[env_key] = env_value
                    else:
                        warnings.append(f"Could not map {section_name}.{key} to ENV format")
        
        return env_config, warnings
    
    def rollback(self, target_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Convert ENV format back to INI format"""
        ini_config = {}
        warnings = []
        
        rollback_rules = migration_step.rollback_rules
        
        for env_key, env_value in target_config.items():
            section, key = self._reverse_transform_key(env_key, rollback_rules)
            
            if section and key:
                if section not in ini_config:
                    ini_config[section] = {}
                ini_config[section][key] = self._reverse_transform_value(key, env_value, rollback_rules)
            else:
                warnings.append(f"Could not map ENV key {env_key} back to INI format")
        
        return ini_config, warnings
    
    def _transform_key(self, section: str, key: str, rules: Dict[str, Any]) -> Optional[str]:
        """Transform INI section.key to ENV key"""
        key_mappings = rules.get("key_mappings", {})
        
        # Check for explicit mapping
        ini_key = f"{section}.{key}"
        if ini_key in key_mappings:
            return key_mappings[ini_key]
        
        # Apply default transformation rules
        default_format = rules.get("default_format", "{section}_{key}")
        env_key = default_format.format(section=section.upper(), key=key.upper())
        
        # Clean up the key
        env_key = env_key.replace(" ", "_").replace("-", "_")
        
        return env_key
    
    def _transform_value(self, key: str, value: str, rules: Dict[str, Any]) -> str:
        """Transform value format if needed"""
        value_transformations = rules.get("value_transformations", {})
        
        if key in value_transformations:
            transformation = value_transformations[key]
            if transformation["type"] == "boolean":
                return "true" if value.lower() in ["true", "1", "yes", "on"] else "false"
            elif transformation["type"] == "path":
                # Normalize path separators
                return value.replace("\\", "/")
        
        return str(value)
    
    def _reverse_transform_key(self, env_key: str, rules: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Reverse transform ENV key to INI section.key"""
        reverse_mappings = rules.get("reverse_key_mappings", {})
        
        if env_key in reverse_mappings:
            section_key = reverse_mappings[env_key]
            if "." in section_key:
                section, key = section_key.split(".", 1)
                return section, key
        
        # Try to reverse default transformation
        if "_" in env_key:
            parts = env_key.split("_", 1)
            if len(parts) == 2:
                return parts[0].title(), parts[1].lower()
        
        return None, None
    
    def _reverse_transform_value(self, key: str, value: str, rules: Dict[str, Any]) -> str:
        """Reverse transform value format"""
        reverse_transformations = rules.get("reverse_value_transformations", {})
        
        if key in reverse_transformations:
            transformation = reverse_transformations[key]
            if transformation["type"] == "boolean":
                return "true" if value.lower() == "true" else "false"
        
        return str(value)


class SchemaUpdateMigrationStrategy(IMigrationStrategy):
    """Strategy for updating configuration schema (adding/removing keys)"""
    
    def can_migrate(self, source_config: Dict[str, Any], source_type: ConfigType, target_type: ConfigType) -> bool:
        return source_type == target_type  # Same format, different schema
    
    def migrate(self, source_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Update configuration schema"""
        updated_config = source_config.copy()
        warnings = []
        
        transformation_rules = migration_step.transformation_rules
        
        # Add new keys with default values
        new_keys = transformation_rules.get("add_keys", {})
        for key_path, default_value in new_keys.items():
            self._add_nested_key(updated_config, key_path, default_value)
            warnings.append(f"Added new key: {key_path} = {default_value}")
        
        # Remove deprecated keys
        remove_keys = transformation_rules.get("remove_keys", [])
        for key_path in remove_keys:
            if self._remove_nested_key(updated_config, key_path):
                warnings.append(f"Removed deprecated key: {key_path}")
        
        # Rename keys
        rename_keys = transformation_rules.get("rename_keys", {})
        for old_key, new_key in rename_keys.items():
            value = self._get_nested_key(updated_config, old_key)
            if value is not None:
                self._add_nested_key(updated_config, new_key, value)
                self._remove_nested_key(updated_config, old_key)
                warnings.append(f"Renamed key: {old_key} -> {new_key}")
        
        return updated_config, warnings
    
    def rollback(self, target_config: Dict[str, Any], migration_step: MigrationStep) -> Tuple[Dict[str, Any], List[str]]:
        """Rollback schema changes"""
        rollback_config = target_config.copy()
        warnings = []
        
        rollback_rules = migration_step.rollback_rules
        
        # Remove keys that were added
        added_keys = rollback_rules.get("remove_added_keys", [])
        for key_path in added_keys:
            if self._remove_nested_key(rollback_config, key_path):
                warnings.append(f"Removed added key: {key_path}")
        
        # Restore removed keys
        restore_keys = rollback_rules.get("restore_keys", {})
        for key_path, default_value in restore_keys.items():
            self._add_nested_key(rollback_config, key_path, default_value)
            warnings.append(f"Restored removed key: {key_path}")
        
        # Reverse key renames
        reverse_renames = rollback_rules.get("reverse_renames", {})
        for new_key, old_key in reverse_renames.items():
            value = self._get_nested_key(rollback_config, new_key)
            if value is not None:
                self._add_nested_key(rollback_config, old_key, value)
                self._remove_nested_key(rollback_config, new_key)
                warnings.append(f"Reversed rename: {new_key} -> {old_key}")
        
        return rollback_config, warnings
    
    def _add_nested_key(self, config: Dict[str, Any], key_path: str, value: Any):
        """Add a nested key to configuration"""
        if "." in key_path:
            section, key = key_path.split(".", 1)
            if section not in config:
                config[section] = {}
            if isinstance(config[section], dict):
                self._add_nested_key(config[section], key, value)
        else:
            config[key_path] = value
    
    def _remove_nested_key(self, config: Dict[str, Any], key_path: str) -> bool:
        """Remove a nested key from configuration"""
        if "." in key_path:
            section, key = key_path.split(".", 1)
            if section in config and isinstance(config[section], dict):
                return self._remove_nested_key(config[section], key)
        else:
            if key_path in config:
                del config[key_path]
                return True
        return False
    
    def _get_nested_key(self, config: Dict[str, Any], key_path: str) -> Any:
        """Get a nested key value from configuration"""
        if "." in key_path:
            section, key = key_path.split(".", 1)
            if section in config and isinstance(config[section], dict):
                return self._get_nested_key(config[section], key)
        else:
            return config.get(key_path)
        return None


class ConfigMigrationTester:
    """Main class for testing configuration migrations"""
    
    def __init__(self):
        self.config_validator = ConfigValidator()
        self.db_validator = DatabaseConnectionValidator()
        self.migration_strategies = [
            INIToENVMigrationStrategy(),
            SchemaUpdateMigrationStrategy(),
        ]
        self.logger = logging.getLogger(__name__)
    
    def test_migration_workflow(self, migration_steps: List[MigrationStep], 
                              source_config_path: str) -> MigrationResult:
        """Test a complete migration workflow"""
        migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        result = MigrationResult(
            success=True,
            migration_id=migration_id,
            steps_completed=[],
            steps_failed=[],
            validation_results=[],
            backup_paths=[],
            error_messages=[],
            execution_time=0.0
        )
        
        # Create backup
        backup_path = self._create_backup(source_config_path, migration_id)
        result.backup_paths.append(backup_path)
        
        try:
            # Load source configuration
            source_config = self._load_config(source_config_path)
            current_config = source_config.copy()
            current_type = ConfigValidatorFactory.detect_config_type(source_config_path)
            
            # Execute migration steps
            for step in migration_steps:
                try:
                    self.logger.info(f"Executing migration step: {step.step_id}")
                    
                    # Find appropriate strategy
                    strategy = self._find_migration_strategy(current_config, current_type, step.target_format)
                    if not strategy:
                        raise ValueError(f"No migration strategy found for {current_type} -> {step.target_format}")
                    
                    # Perform migration
                    migrated_config, warnings = strategy.migrate(current_config, step)
                    
                    # Validate migrated configuration
                    validation_result = self._validate_migrated_config(migrated_config, step)
                    result.validation_results.append(validation_result)
                    
                    if not validation_result.is_valid:
                        result.steps_failed.append(step.step_id)
                        result.error_messages.extend([issue.message for issue in validation_result.issues])
                        result.success = False
                        break
                    
                    # Update current state
                    current_config = migrated_config
                    current_type = step.target_format
                    result.steps_completed.append(step.step_id)
                    
                    # Log warnings
                    for warning in warnings:
                        self.logger.warning(f"Migration step {step.step_id}: {warning}")
                
                except Exception as e:
                    self.logger.error(f"Migration step {step.step_id} failed: {str(e)}")
                    result.steps_failed.append(step.step_id)
                    result.error_messages.append(str(e))
                    result.success = False
                    break
            
            # Save final configuration if successful
            if result.success:
                final_config_path = self._save_migrated_config(current_config, current_type, migration_id)
                self.logger.info(f"Migration completed successfully. Final config: {final_config_path}")
        
        except Exception as e:
            self.logger.error(f"Migration workflow failed: {str(e)}")
            result.success = False
            result.error_messages.append(str(e))
        
        finally:
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
        
        return result
    
    def test_backward_compatibility(self, compatibility_tests: List[BackwardCompatibilityTest],
                                  current_config_path: str) -> List[ValidationResult]:
        """Test backward compatibility with old configuration formats"""
        results = []
        
        for test in compatibility_tests:
            self.logger.info(f"Testing backward compatibility: {test.test_id}")
            
            result = ValidationResult(is_valid=True, issues=[])
            
            try:
                # Create temporary config file with old format
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
                    self._write_config_to_file(test.old_config_format, temp_file.name, ConfigType.INI)
                    temp_config_path = temp_file.name
                
                try:
                    # Test if current system can handle old format
                    validation_result = self.config_validator.validate_file(temp_config_path)
                    
                    # Check compatibility level
                    if test.compatibility_level == "full":
                        if not validation_result.is_valid:
                            result.add_issue(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                message=f"Full compatibility test failed: {test.description}",
                                file_path=temp_config_path,
                                suggestion="Update configuration format or improve backward compatibility"
                            ))
                    elif test.compatibility_level == "partial":
                        # Allow some warnings but not errors
                        critical_issues = [issue for issue in validation_result.issues 
                                         if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
                        if critical_issues:
                            result.add_issue(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                message=f"Partial compatibility issues: {test.description}",
                                file_path=temp_config_path,
                                suggestion="Consider migration to newer format"
                            ))
                    
                    # Add deprecation warnings
                    for warning in test.deprecation_warnings:
                        result.add_issue(ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            message=f"Deprecation warning: {warning}",
                            file_path=temp_config_path,
                            suggestion="Plan migration to newer configuration format"
                        ))
                
                finally:
                    # Clean up temporary file
                    os.unlink(temp_config_path)
            
            except Exception as e:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Backward compatibility test failed: {str(e)}",
                    file_path=current_config_path,
                    suggestion="Review backward compatibility implementation"
                ))
            
            results.append(result)
        
        return results
    
    def test_rollback_scenario(self, migration_steps: List[MigrationStep],
                             migrated_config_path: str) -> MigrationResult:
        """Test rollback of a migration"""
        migration_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        result = MigrationResult(
            success=True,
            migration_id=migration_id,
            steps_completed=[],
            steps_failed=[],
            validation_results=[],
            backup_paths=[],
            error_messages=[],
            execution_time=0.0
        )
        
        # Create backup
        backup_path = self._create_backup(migrated_config_path, migration_id)
        result.backup_paths.append(backup_path)
        
        try:
            # Load migrated configuration
            current_config = self._load_config(migrated_config_path)
            current_type = ConfigValidatorFactory.detect_config_type(migrated_config_path)
            
            # Execute rollback steps in reverse order
            for step in reversed(migration_steps):
                if not step.is_reversible:
                    self.logger.warning(f"Step {step.step_id} is not reversible, skipping")
                    continue
                
                try:
                    self.logger.info(f"Rolling back migration step: {step.step_id}")
                    
                    # Find appropriate strategy
                    strategy = self._find_migration_strategy(current_config, current_type, step.source_format)
                    if not strategy:
                        raise ValueError(f"No rollback strategy found for {current_type} -> {step.source_format}")
                    
                    # Perform rollback
                    rolled_back_config, warnings = strategy.rollback(current_config, step)
                    
                    # Validate rolled back configuration
                    validation_result = self._validate_migrated_config(rolled_back_config, step)
                    result.validation_results.append(validation_result)
                    
                    if not validation_result.is_valid:
                        result.steps_failed.append(step.step_id)
                        result.error_messages.extend([issue.message for issue in validation_result.issues])
                        result.success = False
                        break
                    
                    # Update current state
                    current_config = rolled_back_config
                    current_type = step.source_format
                    result.steps_completed.append(step.step_id)
                    
                    # Log warnings
                    for warning in warnings:
                        self.logger.warning(f"Rollback step {step.step_id}: {warning}")
                
                except Exception as e:
                    self.logger.error(f"Rollback step {step.step_id} failed: {str(e)}")
                    result.steps_failed.append(step.step_id)
                    result.error_messages.append(str(e))
                    result.success = False
                    break
            
            # Save rolled back configuration if successful
            if result.success:
                rollback_config_path = self._save_migrated_config(current_config, current_type, migration_id)
                self.logger.info(f"Rollback completed successfully. Config: {rollback_config_path}")
        
        except Exception as e:
            self.logger.error(f"Rollback workflow failed: {str(e)}")
            result.success = False
            result.error_messages.append(str(e))
        
        finally:
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
        
        return result
    
    def test_alembic_configuration_changes(self, alembic_config_path: str,
                                         database_changes: Dict[str, str]) -> ValidationResult:
        """Test Alembic configuration changes and their impact"""
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            # Validate current Alembic configuration
            current_validation = self.config_validator.validate_alembic_config(alembic_config_path)
            if not current_validation.is_valid:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Current Alembic configuration is invalid",
                    file_path=alembic_config_path,
                    suggestion="Fix current configuration before testing changes"
                ))
                return result
            
            # Test each database change
            for change_description, new_db_url in database_changes.items():
                self.logger.info(f"Testing Alembic config change: {change_description}")
                
                # Create temporary config with new database URL
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
                    temp_config_path = temp_file.name
                
                try:
                    # Copy current config and modify database URL
                    config = configparser.ConfigParser()
                    config.read(alembic_config_path)
                    
                    if 'alembic' in config:
                        config['alembic']['sqlalchemy.url'] = new_db_url
                    
                    with open(temp_config_path, 'w') as f:
                        config.write(f)
                    
                    # Validate modified configuration
                    modified_validation = self.config_validator.validate_alembic_config(temp_config_path)
                    
                    if not modified_validation.is_valid:
                        for issue in modified_validation.issues:
                            issue.message = f"{change_description}: {issue.message}"
                            result.issues.append(issue)
                        result.is_valid = False
                    
                    # Test database connectivity if validation passes
                    if modified_validation.is_valid:
                        connection_test = self.db_validator.test_connection(new_db_url)
                        if not connection_test[0]:
                            result.add_issue(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                message=f"{change_description}: Database connection test failed: {connection_test[1]}",
                                file_path=alembic_config_path,
                                suggestion="Verify database connectivity and credentials"
                            ))
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_config_path):
                        os.unlink(temp_config_path)
        
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Alembic configuration change test failed: {str(e)}",
                file_path=alembic_config_path,
                suggestion="Review Alembic configuration change procedure"
            ))
        
        return result
    
    def _find_migration_strategy(self, config: Dict[str, Any], source_type: ConfigType, 
                               target_type: ConfigType) -> Optional[IMigrationStrategy]:
        """Find appropriate migration strategy"""
        for strategy in self.migration_strategies:
            if strategy.can_migrate(config, source_type, target_type):
                return strategy
        return None
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        config_type = ConfigValidatorFactory.detect_config_type(config_path)
        validator = ConfigValidatorFactory.create_validator(config_type)
        return validator.parse_config(config_path)
    
    def _validate_migrated_config(self, config: Dict[str, Any], step: MigrationStep) -> ValidationResult:
        """Validate migrated configuration"""
        result = ValidationResult(is_valid=True, issues=[])
        
        # Apply validation rules from migration step
        validation_rules = step.validation_rules
        
        # Check required keys
        required_keys = validation_rules.get("required_keys", [])
        for key_path in required_keys:
            if not self._has_nested_key(config, key_path):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required key after migration: {key_path}",
                    file_path="",
                    suggestion=f"Ensure migration includes required key: {key_path}"
                ))
        
        # Check forbidden keys
        forbidden_keys = validation_rules.get("forbidden_keys", [])
        for key_path in forbidden_keys:
            if self._has_nested_key(config, key_path):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Forbidden key present after migration: {key_path}",
                    file_path="",
                    suggestion=f"Remove forbidden key: {key_path}"
                ))
        
        # Validate database connections if present
        db_urls = self._extract_database_urls(config)
        for key, url in db_urls.items():
            db_result = self.db_validator.validate_connection_string(url)
            for issue in db_result.issues:
                issue.key = key
                result.issues.append(issue)
            if not db_result.is_valid:
                result.is_valid = False
        
        return result
    
    def _has_nested_key(self, config: Dict[str, Any], key_path: str) -> bool:
        """Check if nested key exists in configuration"""
        if "." in key_path:
            section, key = key_path.split(".", 1)
            if section in config and isinstance(config[section], dict):
                return self._has_nested_key(config[section], key)
        else:
            return key_path in config
        return False
    
    def _extract_database_urls(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Extract database URLs from configuration"""
        db_urls = {}
        
        # Check common database URL keys
        db_keys = ['connection_string', 'database_url', 'sqlalchemy.url', 'DATABASE_URL', 'CONNECTION_STRING']
        
        for key in db_keys:
            if key in config and config[key]:
                db_urls[key] = config[key]
        
        # Check in sections
        for section_name, section_data in config.items():
            if isinstance(section_data, dict):
                for key in db_keys:
                    if key in section_data and section_data[key]:
                        db_urls[f"{section_name}.{key}"] = section_data[key]
        
        return db_urls
    
    def _create_backup(self, config_path: str, migration_id: str) -> str:
        """Create backup of configuration file"""
        backup_dir = os.path.join(os.path.dirname(config_path), "migration_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(config_path)
        backup_filename = f"{migration_id}_{filename}.backup"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def _save_migrated_config(self, config: Dict[str, Any], config_type: ConfigType, migration_id: str) -> str:
        """Save migrated configuration to file"""
        output_dir = os.path.join(os.getcwd(), "migration_results")
        os.makedirs(output_dir, exist_ok=True)
        
        if config_type == ConfigType.INI:
            filename = f"{migration_id}_migrated.ini"
            output_path = os.path.join(output_dir, filename)
            self._write_config_to_file(config, output_path, config_type)
        elif config_type == ConfigType.ENV:
            filename = f"{migration_id}_migrated.env"
            output_path = os.path.join(output_dir, filename)
            self._write_config_to_file(config, output_path, config_type)
        else:
            filename = f"{migration_id}_migrated.json"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return output_path
    
    def _write_config_to_file(self, config: Dict[str, Any], file_path: str, config_type: ConfigType):
        """Write configuration to file in specified format"""
        if config_type == ConfigType.INI:
            config_parser = configparser.ConfigParser()
            for section_name, section_data in config.items():
                if isinstance(section_data, dict):
                    config_parser[section_name] = section_data
            
            with open(file_path, 'w') as f:
                config_parser.write(f)
        
        elif config_type == ConfigType.ENV:
            with open(file_path, 'w') as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")
        
        elif config_type == ConfigType.JSON:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)


# Example migration steps for common scenarios
def create_desktop_to_api_migration_steps() -> List[MigrationStep]:
    """Create migration steps for desktop client config to API config"""
    return [
        MigrationStep(
            step_id="desktop_to_api_format",
            description="Convert desktop client INI format to API ENV format",
            migration_type=MigrationType.FORMAT_CHANGE,
            source_format=ConfigType.INI,
            target_format=ConfigType.ENV,
            transformation_rules={
                "key_mappings": {
                    "Database.connection_string": "DATABASE_CONNECTION_STRING",
                    "Auth.login": "DEFAULT_USERNAME",
                    "Auth.password": "DEFAULT_PASSWORD",
                    "Sync.enabled": "SYNC_ENABLED",
                    "Sync.server_url": "SYNC_SERVER_URL",
                    "Sync.auto_sync": "SYNC_AUTO_SYNC",
                    "Sync.debug_logging": "SYNC_DEBUG_LOGGING"
                },
                "value_transformations": {
                    "enabled": {"type": "boolean"},
                    "auto_sync": {"type": "boolean"},
                    "debug_logging": {"type": "boolean"}
                }
            },
            validation_rules={
                "required_keys": ["DATABASE_CONNECTION_STRING", "SYNC_ENABLED"],
                "forbidden_keys": []
            },
            rollback_rules={
                "reverse_key_mappings": {
                    "DATABASE_CONNECTION_STRING": "Database.connection_string",
                    "DEFAULT_USERNAME": "Auth.login",
                    "DEFAULT_PASSWORD": "Auth.password",
                    "SYNC_ENABLED": "Sync.enabled",
                    "SYNC_SERVER_URL": "Sync.server_url",
                    "SYNC_AUTO_SYNC": "Sync.auto_sync",
                    "SYNC_DEBUG_LOGGING": "Sync.debug_logging"
                }
            }
        )
    ]


def create_schema_update_migration_steps() -> List[MigrationStep]:
    """Create migration steps for schema updates"""
    return [
        MigrationStep(
            step_id="add_new_sync_features",
            description="Add new synchronization configuration options",
            migration_type=MigrationType.SCHEMA_UPDATE,
            source_format=ConfigType.INI,
            target_format=ConfigType.INI,
            transformation_rules={
                "add_keys": {
                    "Sync.batch_size": "100",
                    "Sync.compression_enabled": "true",
                    "Sync.conflict_resolution": "server_wins",
                    "Sync.version_history": "false"
                },
                "rename_keys": {
                    "Sync.debug_logging": "Sync.log_level"
                }
            },
            validation_rules={
                "required_keys": ["Sync.batch_size", "Sync.compression_enabled"],
                "forbidden_keys": ["Sync.debug_logging"]
            },
            rollback_rules={
                "remove_added_keys": ["Sync.batch_size", "Sync.compression_enabled", 
                                    "Sync.conflict_resolution", "Sync.version_history"],
                "reverse_renames": {
                    "Sync.log_level": "Sync.debug_logging"
                }
            }
        )
    ]


def create_backward_compatibility_tests() -> List[BackwardCompatibilityTest]:
    """Create backward compatibility test cases"""
    return [
        BackwardCompatibilityTest(
            test_id="old_sync_config_format",
            description="Test compatibility with old sync configuration format",
            old_config_format={
                "Sync": {
                    "enabled": "true",
                    "server_url": "http://localhost:8000",
                    "debug_logging": "true"
                }
            },
            expected_behavior="Should work with deprecation warnings",
            compatibility_level="partial",
            deprecation_warnings=[
                "debug_logging is deprecated, use log_level instead",
                "Consider adding new sync configuration options"
            ]
        ),
        BackwardCompatibilityTest(
            test_id="old_database_config",
            description="Test compatibility with old database configuration",
            old_config_format={
                "Database": {
                    "type": "sqlite",
                    "sqlite_path": "database.db"
                }
            },
            expected_behavior="Should work but recommend connection_string format",
            compatibility_level="full",
            deprecation_warnings=[
                "sqlite_path is deprecated, use connection_string instead"
            ]
        )
    ]
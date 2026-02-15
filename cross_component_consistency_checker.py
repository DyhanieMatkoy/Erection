"""
Cross-Component Consistency Checker

This module validates consistency between different configuration components
including desktop client, API, web-client, and Alembic configurations.
"""

import os
import json
import configparser
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

from config_validator import (
    ConfigValidator, ValidationResult, ValidationIssue, ValidationSeverity,
    ConfigType, ConfigValidatorFactory, DatabaseConnectionValidator
)


class ComponentType(Enum):
    """Types of configuration components"""
    DESKTOP_CLIENT = "desktop_client"
    API_SERVER = "api_server"
    WEB_CLIENT = "web_client"
    ALEMBIC = "alembic"
    TEST_CONFIG = "test_config"


class ConsistencyLevel(Enum):
    """Levels of consistency checking"""
    STRICT = "strict"  # All values must match exactly
    COMPATIBLE = "compatible"  # Values must be compatible
    INFORMATIONAL = "informational"  # Report differences but don't fail


@dataclass
class ComponentConfig:
    """Represents a configuration component"""
    component_type: ComponentType
    file_path: str
    config_data: Dict[str, Any]
    config_type: ConfigType


@dataclass
class ConsistencyRule:
    """Rule for checking consistency between components"""
    rule_id: str
    description: str
    source_component: ComponentType
    target_component: ComponentType
    source_key: str
    target_key: str
    consistency_level: ConsistencyLevel
    value_transformer: Optional[callable] = None
    validation_function: Optional[callable] = None


@dataclass
class ConsistencyViolation:
    """Represents a consistency violation"""
    rule_id: str
    description: str
    source_component: ComponentType
    target_component: ComponentType
    source_value: Any
    target_value: Any
    severity: ValidationSeverity
    suggestion: str


class CrossComponentConsistencyChecker:
    """Main class for checking cross-component consistency"""
    
    def __init__(self):
        self.config_validator = ConfigValidator()
        self.db_validator = DatabaseConnectionValidator()
        self.logger = logging.getLogger(__name__)
        
        # Define consistency rules
        self.consistency_rules = self._create_consistency_rules()
    
    def check_consistency(self, component_configs: List[ComponentConfig]) -> ValidationResult:
        """Check consistency across all provided components"""
        result = ValidationResult(is_valid=True, issues=[])
        
        # Group components by type for easier access
        components_by_type = {}
        for component in component_configs:
            components_by_type[component.component_type] = component
        
        # Apply consistency rules
        violations = []
        for rule in self.consistency_rules:
            if (rule.source_component in components_by_type and 
                rule.target_component in components_by_type):
                
                source_component = components_by_type[rule.source_component]
                target_component = components_by_type[rule.target_component]
                
                violation = self._check_rule(rule, source_component, target_component)
                if violation:
                    violations.append(violation)
        
        # Convert violations to validation issues
        for violation in violations:
            result.add_issue(ValidationIssue(
                severity=violation.severity,
                message=f"{violation.description}: {violation.source_component.value} "
                       f"has '{violation.source_value}', {violation.target_component.value} "
                       f"has '{violation.target_value}'",
                file_path=f"{violation.source_component.value} vs {violation.target_component.value}",
                suggestion=violation.suggestion
            ))
        
        return result
    
    def validate_env_ini_consistency(self, env_ini_path: str, dot_env_path: str) -> ValidationResult:
        """Validate consistency between env.ini and .env files"""
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            # Load configurations
            env_ini_config = self._load_config(env_ini_path, ConfigType.INI)
            dot_env_config = self._load_config(dot_env_path, ConfigType.ENV)
            
            # Define key mappings between env.ini and .env
            key_mappings = {
                ("Database", "connection_string"): "DATABASE_CONNECTION_STRING",
                ("Database", "type"): "DATABASE_TYPE",
                ("Sync", "enabled"): "SYNC_ENABLED",
                ("Sync", "server_url"): "SYNC_SERVER_URL",
                ("Sync", "auto_sync"): "SYNC_AUTO_SYNC",
                ("Sync", "debug_logging"): "SYNC_DEBUG_LOGGING",
                ("Sync", "node_code"): "SYNC_NODE_CODE",
                ("Sync", "compression_enabled"): "SYNC_COMPRESSION_ENABLED",
                ("Sync", "conflict_resolution"): "SYNC_CONFLICT_RESOLUTION",
                ("Sync", "batch_size"): "SYNC_BATCH_SIZE",
                ("Sync", "log_level"): "SYNC_LOG_LEVEL"
            }
            
            # Check consistency for each mapping
            for (section, key), env_key in key_mappings.items():
                ini_value = self._get_nested_value(env_ini_config, f"{section}.{key}")
                env_value = dot_env_config.get(env_key)
                
                if ini_value is not None and env_value is not None:
                    # Normalize values for comparison
                    normalized_ini = self._normalize_value(ini_value)
                    normalized_env = self._normalize_value(env_value)
                    
                    if normalized_ini != normalized_env:
                        result.add_issue(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Inconsistent values: env.ini [{section}].{key}='{ini_value}' "
                                   f"vs .env {env_key}='{env_value}'",
                            file_path=f"{env_ini_path} vs {dot_env_path}",
                            section=section,
                            key=key,
                            suggestion=f"Ensure {section}.{key} and {env_key} have consistent values"
                        ))
                elif ini_value is not None and env_value is None:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Missing .env key: {env_key} (present in env.ini as [{section}].{key})",
                        file_path=dot_env_path,
                        key=env_key,
                        suggestion=f"Add {env_key}={ini_value} to .env file"
                    ))
                elif ini_value is None and env_value is not None:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Missing env.ini key: [{section}].{key} (present in .env as {env_key})",
                        file_path=env_ini_path,
                        section=section,
                        key=key,
                        suggestion=f"Add {key}={env_value} to [{section}] section in env.ini"
                    ))
        
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Failed to validate env.ini/.env consistency: {str(e)}",
                file_path=f"{env_ini_path} vs {dot_env_path}",
                suggestion="Check file paths and formats"
            ))
        
        return result
    
    def validate_api_desktop_compatibility(self, api_config_path: str, 
                                         desktop_config_path: str) -> ValidationResult:
        """Validate compatibility between API and desktop configurations"""
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            # Load configurations
            api_config = self._load_config(api_config_path, ConfigType.ENV)
            desktop_config = self._load_config(desktop_config_path, ConfigType.INI)
            
            # Check database compatibility
            api_db_url = api_config.get("DATABASE_CONNECTION_STRING") or api_config.get("DATABASE_URL")
            desktop_db_url = self._get_nested_value(desktop_config, "Database.connection_string")
            
            if api_db_url and desktop_db_url:
                api_db_info = self.db_validator.parse_connection_string(api_db_url)
                desktop_db_info = self.db_validator.parse_connection_string(desktop_db_url)
                
                if api_db_info.is_valid and desktop_db_info.is_valid:
                    # Check database type compatibility
                    if api_db_info.db_type != desktop_db_info.db_type:
                        result.add_issue(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Incompatible database types: API uses {api_db_info.db_type}, "
                                   f"desktop uses {desktop_db_info.db_type}",
                            file_path=f"{api_config_path} vs {desktop_config_path}",
                            suggestion="Use the same database type for API and desktop"
                        ))
                    
                    # For non-SQLite databases, check if they point to the same database
                    if (api_db_info.db_type != 'sqlite' and 
                        desktop_db_info.db_type != 'sqlite'):
                        if (api_db_info.host != desktop_db_info.host or
                            api_db_info.database != desktop_db_info.database):
                            result.add_issue(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                message=f"Different database instances: API connects to "
                                       f"{api_db_info.host}/{api_db_info.database}, desktop connects to "
                                       f"{desktop_db_info.host}/{desktop_db_info.database}",
                                file_path=f"{api_config_path} vs {desktop_config_path}",
                                suggestion="Consider using the same database instance for consistency"
                            ))
            
            # Check sync configuration compatibility
            api_sync_enabled = api_config.get("SYNC_ENABLED", "").lower()
            desktop_sync_enabled = self._get_nested_value(desktop_config, "Sync.enabled", "").lower()
            
            if api_sync_enabled and desktop_sync_enabled:
                if self._normalize_boolean(api_sync_enabled) != self._normalize_boolean(desktop_sync_enabled):
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Inconsistent sync settings: API sync_enabled={api_sync_enabled}, "
                               f"desktop sync enabled={desktop_sync_enabled}",
                        file_path=f"{api_config_path} vs {desktop_config_path}",
                        suggestion="Ensure sync is enabled/disabled consistently"
                    ))
            
            # Check sync server URL compatibility
            api_sync_url = api_config.get("SYNC_SERVER_URL")
            desktop_sync_url = self._get_nested_value(desktop_config, "Sync.server_url")
            
            if api_sync_url and desktop_sync_url and api_sync_url != desktop_sync_url:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Different sync server URLs: API={api_sync_url}, desktop={desktop_sync_url}",
                    file_path=f"{api_config_path} vs {desktop_config_path}",
                    suggestion="Use the same sync server URL for API and desktop"
                ))
        
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Failed to validate API/desktop compatibility: {str(e)}",
                file_path=f"{api_config_path} vs {desktop_config_path}",
                suggestion="Check file paths and formats"
            ))
        
        return result
    
    def validate_web_client_compatibility(self, web_client_config_path: str,
                                        api_config_path: str) -> ValidationResult:
        """Validate web-client configuration compatibility with API settings"""
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            # Load configurations
            if web_client_config_path.endswith('.json'):
                web_config = self._load_config(web_client_config_path, ConfigType.JSON)
            else:
                web_config = self._load_config(web_client_config_path, ConfigType.ENV)
            
            api_config = self._load_config(api_config_path, ConfigType.ENV)
            
            # Check API endpoint compatibility
            web_api_url = web_config.get("VITE_API_URL") or web_config.get("VUE_APP_API_URL")
            api_cors_origins = api_config.get("CORS_ORIGINS", "")
            
            if web_api_url:
                # Extract domain from web client API URL
                from urllib.parse import urlparse
                parsed_url = urlparse(web_api_url)
                web_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # Check if web client origin is allowed by API CORS
                if api_cors_origins:
                    allowed_origins = [origin.strip() for origin in api_cors_origins.split(",")]
                    if web_origin not in allowed_origins and "*" not in allowed_origins:
                        result.add_issue(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Web client origin {web_origin} not allowed by API CORS: {api_cors_origins}",
                            file_path=f"{web_client_config_path} vs {api_config_path}",
                            suggestion=f"Add {web_origin} to CORS_ORIGINS in API configuration"
                        ))
            
            # Check authentication configuration
            web_auth_enabled = web_config.get("VITE_AUTH_ENABLED") or web_config.get("VUE_APP_AUTH_ENABLED")
            api_jwt_secret = api_config.get("JWT_SECRET_KEY")
            
            if web_auth_enabled and self._normalize_boolean(web_auth_enabled):
                if not api_jwt_secret:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Web client has authentication enabled but API has no JWT secret",
                        file_path=f"{web_client_config_path} vs {api_config_path}",
                        suggestion="Configure JWT_SECRET_KEY in API configuration"
                    ))
            
            # Check build configuration compatibility
            if "build" in web_config:
                build_config = web_config["build"]
                
                # Check if build output directory conflicts with API static files
                output_dir = build_config.get("outDir", "dist")
                if output_dir in ["api", "src", "config"]:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Web client build output directory '{output_dir}' may conflict with API",
                        file_path=web_client_config_path,
                        suggestion="Use a dedicated build output directory like 'dist' or 'build'"
                    ))
        
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Failed to validate web-client compatibility: {str(e)}",
                file_path=f"{web_client_config_path} vs {api_config_path}",
                suggestion="Check file paths and formats"
            ))
        
        return result
    
    def validate_alembic_database_consistency(self, alembic_config_path: str,
                                            database_configs: List[Tuple[str, str]]) -> ValidationResult:
        """Validate Alembic configuration consistency with database settings"""
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            # Load Alembic configuration
            alembic_config = self._load_config(alembic_config_path, ConfigType.INI)
            alembic_db_url = None
            if "alembic" in alembic_config and "sqlalchemy.url" in alembic_config["alembic"]:
                alembic_db_url = alembic_config["alembic"]["sqlalchemy.url"]
            
            if not alembic_db_url:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Alembic configuration missing database URL",
                    file_path=alembic_config_path,
                    section="alembic",
                    key="sqlalchemy.url",
                    suggestion="Add sqlalchemy.url to [alembic] section"
                ))
                return result
            
            # Parse Alembic database URL
            alembic_db_info = self.db_validator.parse_connection_string(alembic_db_url)
            
            if not alembic_db_info.is_valid:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid Alembic database URL: {alembic_db_info.error_message}",
                    file_path=alembic_config_path,
                    section="alembic",
                    key="sqlalchemy.url",
                    suggestion="Fix Alembic database URL format"
                ))
                return result
            
            # Check consistency with other database configurations
            for config_name, config_path in database_configs:
                try:
                    config_type = ConfigValidatorFactory.detect_config_type(config_path)
                    config_data = self._load_config(config_path, config_type)
                    
                    # Extract database URL from configuration
                    db_url = None
                    if config_type == ConfigType.ENV:
                        db_url = (config_data.get("DATABASE_CONNECTION_STRING") or 
                                config_data.get("DATABASE_URL"))
                    elif config_type == ConfigType.INI:
                        db_url = self._get_nested_value(config_data, "Database.connection_string")
                    
                    if db_url:
                        config_db_info = self.db_validator.parse_connection_string(db_url)
                        
                        if config_db_info.is_valid:
                            # Check database type consistency
                            if alembic_db_info.db_type != config_db_info.db_type:
                                result.add_issue(ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    message=f"Database type mismatch: Alembic uses {alembic_db_info.db_type}, "
                                           f"{config_name} uses {config_db_info.db_type}",
                                    file_path=f"{alembic_config_path} vs {config_path}",
                                    suggestion="Use the same database type in all configurations"
                                ))
                            
                            # Check database instance consistency (for non-SQLite)
                            if alembic_db_info.db_type != 'sqlite':
                                if (alembic_db_info.host != config_db_info.host or
                                    alembic_db_info.database != config_db_info.database):
                                    result.add_issue(ValidationIssue(
                                        severity=ValidationSeverity.WARNING,
                                        message=f"Different database instances: Alembic connects to "
                                               f"{alembic_db_info.host}/{alembic_db_info.database}, "
                                               f"{config_name} connects to "
                                               f"{config_db_info.host}/{config_db_info.database}",
                                        file_path=f"{alembic_config_path} vs {config_path}",
                                        suggestion="Consider using the same database instance"
                                    ))
                
                except Exception as e:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Could not validate {config_name} consistency: {str(e)}",
                        file_path=config_path,
                        suggestion="Check configuration file format and accessibility"
                    ))
        
        except Exception as e:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Failed to validate Alembic consistency: {str(e)}",
                file_path=alembic_config_path,
                suggestion="Check Alembic configuration file"
            ))
        
        return result
    
    def validate_multi_database_consistency(self, database_configs: List[Tuple[str, str]]) -> ValidationResult:
        """Validate consistency across multiple database configurations"""
        result = ValidationResult(is_valid=True, issues=[])
        
        database_info = []
        
        # Parse all database configurations
        for config_name, config_path in database_configs:
            try:
                config_type = ConfigValidatorFactory.detect_config_type(config_path)
                config_data = self._load_config(config_path, config_type)
                
                # Extract database URLs
                db_urls = []
                if config_type == ConfigType.ENV:
                    for key in ["DATABASE_CONNECTION_STRING", "DATABASE_URL"]:
                        if key in config_data and config_data[key]:
                            db_urls.append((key, config_data[key]))
                elif config_type == ConfigType.INI:
                    # Check multiple sections for database configurations
                    for section in ["Database", "PostgreSQL", "MySQL", "SQLite"]:
                        for key in ["connection_string", "database_path", "sqlite_path"]:
                            value = self._get_nested_value(config_data, f"{section}.{key}")
                            if value:
                                db_urls.append((f"{section}.{key}", value))
                
                # Parse each database URL
                for key, url in db_urls:
                    db_info = self.db_validator.parse_connection_string(url)
                    database_info.append({
                        "config_name": config_name,
                        "config_path": config_path,
                        "key": key,
                        "url": url,
                        "db_info": db_info
                    })
            
            except Exception as e:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Could not parse {config_name}: {str(e)}",
                    file_path=config_path,
                    suggestion="Check configuration file format"
                ))
        
        # Check for consistency issues
        if len(database_info) > 1:
            # Group by database type
            db_types = {}
            for db_config in database_info:
                if db_config["db_info"].is_valid:
                    db_type = db_config["db_info"].db_type
                    if db_type not in db_types:
                        db_types[db_type] = []
                    db_types[db_type].append(db_config)
            
            # Check for mixed database types
            if len(db_types) > 1:
                type_names = list(db_types.keys())
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"Mixed database types detected: {', '.join(type_names)}",
                    file_path="multiple configurations",
                    suggestion="Consider standardizing on a single database type"
                ))
            
            # Check for duplicate database instances
            seen_instances = set()
            for db_config in database_info:
                if db_config["db_info"].is_valid:
                    db_info = db_config["db_info"]
                    if db_info.db_type != 'sqlite':
                        instance_key = f"{db_info.host}:{db_info.port}/{db_info.database}"
                        if instance_key in seen_instances:
                            result.add_issue(ValidationIssue(
                                severity=ValidationSeverity.INFO,
                                message=f"Duplicate database instance: {instance_key}",
                                file_path=db_config["config_path"],
                                suggestion="Multiple configurations point to the same database"
                            ))
                        seen_instances.add(instance_key)
        
        return result
    
    def _create_consistency_rules(self) -> List[ConsistencyRule]:
        """Create predefined consistency rules"""
        rules = []
        
        # Database consistency rules
        rules.append(ConsistencyRule(
            rule_id="db_type_consistency",
            description="Database type should be consistent across components",
            source_component=ComponentType.API_SERVER,
            target_component=ComponentType.DESKTOP_CLIENT,
            source_key="DATABASE_TYPE",
            target_key="Database.type",
            consistency_level=ConsistencyLevel.STRICT
        ))
        
        # Sync configuration rules
        rules.append(ConsistencyRule(
            rule_id="sync_enabled_consistency",
            description="Sync enabled setting should be consistent",
            source_component=ComponentType.API_SERVER,
            target_component=ComponentType.DESKTOP_CLIENT,
            source_key="SYNC_ENABLED",
            target_key="Sync.enabled",
            consistency_level=ConsistencyLevel.STRICT,
            value_transformer=self._normalize_boolean
        ))
        
        rules.append(ConsistencyRule(
            rule_id="sync_server_url_consistency",
            description="Sync server URL should be consistent",
            source_component=ComponentType.API_SERVER,
            target_component=ComponentType.DESKTOP_CLIENT,
            source_key="SYNC_SERVER_URL",
            target_key="Sync.server_url",
            consistency_level=ConsistencyLevel.STRICT
        ))
        
        return rules
    
    def _check_rule(self, rule: ConsistencyRule, source_component: ComponentConfig,
                   target_component: ComponentConfig) -> Optional[ConsistencyViolation]:
        """Check a specific consistency rule"""
        try:
            # Get values from components
            source_value = self._get_nested_value(source_component.config_data, rule.source_key)
            target_value = self._get_nested_value(target_component.config_data, rule.target_key)
            
            # Skip if either value is missing
            if source_value is None or target_value is None:
                return None
            
            # Apply value transformer if provided
            if rule.value_transformer:
                source_value = rule.value_transformer(source_value)
                target_value = rule.value_transformer(target_value)
            
            # Check consistency based on level
            is_consistent = True
            if rule.consistency_level == ConsistencyLevel.STRICT:
                is_consistent = source_value == target_value
            elif rule.consistency_level == ConsistencyLevel.COMPATIBLE:
                if rule.validation_function:
                    is_consistent = rule.validation_function(source_value, target_value)
                else:
                    is_consistent = source_value == target_value
            
            if not is_consistent:
                severity = ValidationSeverity.ERROR
                if rule.consistency_level == ConsistencyLevel.INFORMATIONAL:
                    severity = ValidationSeverity.INFO
                elif rule.consistency_level == ConsistencyLevel.COMPATIBLE:
                    severity = ValidationSeverity.WARNING
                
                return ConsistencyViolation(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    source_component=rule.source_component,
                    target_component=rule.target_component,
                    source_value=source_value,
                    target_value=target_value,
                    severity=severity,
                    suggestion=f"Ensure {rule.source_key} and {rule.target_key} have consistent values"
                )
        
        except Exception as e:
            self.logger.warning(f"Error checking rule {rule.rule_id}: {str(e)}")
        
        return None
    
    def _load_config(self, config_path: str, config_type: ConfigType) -> Dict[str, Any]:
        """Load configuration from file"""
        validator = ConfigValidatorFactory.create_validator(config_type)
        return validator.parse_config(config_path)
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get nested value from configuration using dot notation"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def _normalize_value(self, value: Any) -> str:
        """Normalize value for comparison"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return value.strip().lower()
        else:
            return str(value)
    
    def _normalize_boolean(self, value: Any) -> bool:
        """Normalize boolean value"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on', 'enabled']
        else:
            return bool(value)


def create_component_config(component_type: ComponentType, file_path: str) -> ComponentConfig:
    """Create a ComponentConfig from a file path"""
    config_type = ConfigValidatorFactory.detect_config_type(file_path)
    validator = ConfigValidatorFactory.create_validator(config_type)
    config_data = validator.parse_config(file_path)
    
    return ComponentConfig(
        component_type=component_type,
        file_path=file_path,
        config_data=config_data,
        config_type=config_type
    )


# Example usage functions
def check_desktop_api_consistency(desktop_config_path: str, api_config_path: str) -> ValidationResult:
    """Check consistency between desktop and API configurations"""
    checker = CrossComponentConsistencyChecker()
    
    components = [
        create_component_config(ComponentType.DESKTOP_CLIENT, desktop_config_path),
        create_component_config(ComponentType.API_SERVER, api_config_path)
    ]
    
    return checker.check_consistency(components)


def check_all_components_consistency(config_paths: Dict[ComponentType, str]) -> ValidationResult:
    """Check consistency across all configuration components"""
    checker = CrossComponentConsistencyChecker()
    
    components = []
    for component_type, file_path in config_paths.items():
        if os.path.exists(file_path):
            components.append(create_component_config(component_type, file_path))
    
    return checker.check_consistency(components)
"""Sync Service Initializer

This module handles automatic initialization of synchronization service
based on configuration settings.
"""

import os
import configparser
import logging
from typing import Optional
from ..data.database_manager import DatabaseManager
from .sync_service import SyncService

logger = logging.getLogger(__name__)


class SyncInitializer:
    """Handles initialization of sync service"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sync_service: Optional[SyncService] = None
    
    def initialize_sync_service(self) -> Optional[SyncService]:
        """Initialize sync service based on configuration
        
        Returns:
            SyncService instance if sync is enabled and configured, None otherwise
        """
        try:
            config = self._load_sync_config()
            
            if not config:
                logger.info("No sync configuration found")
                return None
            
            if not config.get('enabled', False):
                logger.info("Sync is disabled in configuration")
                return None
            
            server_url = config.get('server_url', '').strip()
            node_code = config.get('node_code', '').strip()
            
            if not server_url or not node_code:
                logger.warning("Sync configuration incomplete: missing server_url or node_code")
                return None
            
            # Create sync service
            self.sync_service = SyncService(
                db_manager=self.db_manager,
                server_url=server_url,
                node_code=node_code
            )
            
            # Apply additional configuration
            self._apply_sync_config(self.sync_service, config)
            
            # Try to register node if not already registered
            if not config.get('auth_token', '').strip():
                logger.info("No auth token found, attempting node registration")
                try:
                    self.sync_service._register_node()
                    # Save the token back to config
                    if self.sync_service.auth_token:
                        self._save_auth_token(self.sync_service.auth_token)
                        logger.info("Node registered successfully")
                except Exception as e:
                    logger.warning(f"Failed to register node: {e}")
            else:
                self.sync_service.auth_token = config.get('auth_token')
                self.sync_service.node_id = config.get('node_id')
            
            logger.info(f"Sync service initialized for node: {node_code}")
            return self.sync_service
            
        except Exception as e:
            logger.error(f"Failed to initialize sync service: {e}")
            return None
    
    def _load_sync_config(self) -> Optional[dict]:
        """Load sync configuration from env.ini
        
        Returns:
            Dictionary with sync configuration or None if not found
        """
        config_path = "env.ini"
        
        if not os.path.exists(config_path):
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            if 'Sync' not in config:
                return None
            
            sync_section = config['Sync']
            
            return {
                'enabled': sync_section.getboolean('enabled', False),
                'server_url': sync_section.get('server_url', ''),
                'node_code': sync_section.get('node_code', ''),
                'node_id': sync_section.get('node_id', ''),
                'auth_token': sync_section.get('auth_token', ''),
                'auto_sync': sync_section.getboolean('auto_sync', True),
                'sync_interval': sync_section.getint('sync_interval', 300),
                'compression_enabled': sync_section.getboolean('compression_enabled', True),
                'conflict_resolution': sync_section.get('conflict_resolution', 'server_wins'),
                'version_history': sync_section.getboolean('version_history', True),
                'debug_logging': sync_section.getboolean('debug_logging', False),
                'batch_size': sync_section.getint('batch_size', 100),
                'log_level': sync_section.get('log_level', 'INFO')
            }
            
        except Exception as e:
            logger.error(f"Error loading sync config: {e}")
            return None
    
    def _apply_sync_config(self, sync_service: SyncService, config: dict):
        """Apply configuration to sync service
        
        Args:
            sync_service: SyncService instance to configure
            config: Configuration dictionary
        """
        try:
            # Set sync interval
            if config.get('auto_sync', True):
                sync_interval = config.get('sync_interval', 300)
                sync_service.set_sync_interval(sync_interval)
            
            # Set other properties
            sync_service.auth_token = config.get('auth_token', '')
            sync_service.node_id = config.get('node_id', '')
            
            # Configure logging if debug is enabled
            if config.get('debug_logging', False):
                log_level = config.get('log_level', 'INFO')
                logging.getLogger('src.services.sync_service').setLevel(
                    getattr(logging, log_level, logging.INFO)
                )
            
            logger.info("Sync configuration applied successfully")
            
        except Exception as e:
            logger.error(f"Error applying sync config: {e}")
    
    def _save_auth_token(self, auth_token: str):
        """Save auth token to configuration
        
        Args:
            auth_token: Authentication token to save
        """
        try:
            config_path = "env.ini"
            config = configparser.ConfigParser()
            
            if os.path.exists(config_path):
                config.read(config_path)
            
            if 'Sync' not in config:
                config.add_section('Sync')
            
            config['Sync']['auth_token'] = auth_token
            
            with open(config_path, 'w') as f:
                config.write(f)
            
            logger.info("Auth token saved to configuration")
            
        except Exception as e:
            logger.error(f"Error saving auth token: {e}")
    
    def get_sync_service(self) -> Optional[SyncService]:
        """Get the initialized sync service
        
        Returns:
            SyncService instance or None if not initialized
        """
        return self.sync_service
    
    def is_sync_enabled(self) -> bool:
        """Check if sync is enabled in configuration
        
        Returns:
            True if sync is enabled, False otherwise
        """
        config = self._load_sync_config()
        return config is not None and config.get('enabled', False)
    
    def create_default_config(self):
        """Create default sync configuration file"""
        try:
            config_path = "env.ini"
            config = configparser.ConfigParser()
            
            if os.path.exists(config_path):
                config.read(config_path)
            
            if 'Sync' not in config:
                config.add_section('Sync')
            
            sync_section = config['Sync']
            
            # Set default values only if not already present
            if 'enabled' not in sync_section:
                sync_section['enabled'] = 'false'
            if 'server_url' not in sync_section:
                sync_section['server_url'] = 'http://localhost:8000'
            if 'node_code' not in sync_section:
                sync_section['node_code'] = 'DESKTOP-CLIENT'
            if 'auto_sync' not in sync_section:
                sync_section['auto_sync'] = 'true'
            if 'sync_interval' not in sync_section:
                sync_section['sync_interval'] = '300'
            if 'compression_enabled' not in sync_section:
                sync_section['compression_enabled'] = 'true'
            if 'conflict_resolution' not in sync_section:
                sync_section['conflict_resolution'] = 'server_wins'
            if 'version_history' not in sync_section:
                sync_section['version_history'] = 'true'
            if 'debug_logging' not in sync_section:
                sync_section['debug_logging'] = 'false'
            if 'batch_size' not in sync_section:
                sync_section['batch_size'] = '100'
            if 'log_level' not in sync_section:
                sync_section['log_level'] = 'INFO'
            
            with open(config_path, 'w') as f:
                config.write(f)
            
            logger.info("Default sync configuration created")
            
        except Exception as e:
            logger.error(f"Error creating default sync config: {e}")


def initialize_sync_for_app(db_manager: DatabaseManager) -> Optional[SyncService]:
    """Convenience function to initialize sync service for the application
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        SyncService instance if successfully initialized, None otherwise
    """
    initializer = SyncInitializer(db_manager)
    
    # Create default config if it doesn't exist
    if not initializer.is_sync_enabled():
        initializer.create_default_config()
    
    return initializer.initialize_sync_service()
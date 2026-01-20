"""Test Environment Manager

This module manages the setup and teardown of the test environment,
including server startup, desktop client creation, and resource management.
"""

import os
import sys
import time
import uuid
import shutil
import logging
import subprocess
import configparser
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.database_manager import DatabaseManager
from src.services.sync_service import SyncService


class TestDesktopClient:
    """Wrapper for desktop client instance in test environment"""
    
    def __init__(self, client_id: str, database_path: str, server_url: str, logger: logging.Logger):
        """Initialize test desktop client
        
        Args:
            client_id: Unique identifier for this client
            database_path: Path to client's isolated database
            server_url: URL of the sync server
            logger: Logger instance
        """
        self.client_id = client_id
        self.database_path = database_path
        self.server_url = server_url
        self.logger = logger
        
        # Client components
        self.db_manager: Optional[DatabaseManager] = None
        self.sync_service: Optional[SyncService] = None
        self.process: Optional[subprocess.Popen] = None
        
        # Client state
        self.is_running = False
        self.is_registered = False
        self.node_code = f"TEST-{client_id.upper()}"
        
        self.logger.debug(f"Test desktop client initialized: {client_id}")
    
    def start_client(self) -> bool:
        """Start the desktop client process
        
        Returns:
            True if client started successfully
        """
        try:
            self.logger.info(f"Starting desktop client: {self.client_id}")
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            success = self.db_manager.initialize(self.database_path)
            
            if not success:
                raise Exception(f"Failed to initialize database: {self.database_path}")
            
            # Create sync configuration for this client
            self._create_sync_config()
            
            # Initialize sync service
            self.sync_service = SyncService(
                db_manager=self.db_manager,
                server_url=self.server_url,
                node_code=self.node_code
            )
            
            # Register with server
            self._register_with_server()
            
            self.is_running = True
            self.logger.info(f"Desktop client started successfully: {self.client_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start desktop client {self.client_id}: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the desktop client"""
        try:
            self.logger.info(f"Stopping desktop client: {self.client_id}")
            
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
            
            self.is_running = False
            self.logger.info(f"Desktop client stopped: {self.client_id}")
            
        except subprocess.TimeoutExpired:
            if self.process:
                self.process.kill()
            self.logger.warning(f"Desktop client killed after timeout: {self.client_id}")
        except Exception as e:
            self.logger.error(f"Error stopping desktop client {self.client_id}: {e}")
    
    def create_document(self, doc_type: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document in this client's database
        
        Args:
            doc_type: Type of document (estimate, daily_report, timesheet)
            doc_data: Document data dictionary
            
        Returns:
            Created document information
        """
        try:
            self.logger.debug(f"Creating {doc_type} document on {self.client_id}")
            
            if not self.db_manager:
                raise Exception("Database manager not initialized")
            
            # Create document based on type
            if doc_type == 'estimate':
                return self._create_estimate(doc_data)
            elif doc_type == 'daily_report':
                return self._create_daily_report(doc_data)
            elif doc_type == 'timesheet':
                return self._create_timesheet(doc_data)
            else:
                raise ValueError(f"Unknown document type: {doc_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to create {doc_type} document on {self.client_id}: {e}")
            raise
    
    def trigger_sync(self) -> Dict[str, Any]:
        """Trigger manual synchronization
        
        Returns:
            Sync result information
        """
        try:
            self.logger.info(f"Triggering sync on {self.client_id}")
            
            if not self.sync_service:
                raise Exception("Sync service not initialized")
            
            start_time = time.time()
            
            # Trigger sync
            success = self.sync_service.sync_now()
            
            if not success:
                raise Exception("Failed to start sync operation")
            
            # Wait for sync completion (with timeout)
            timeout = 30  # 30 seconds timeout
            elapsed = 0
            
            while self.sync_service.is_syncing and elapsed < timeout:
                time.sleep(0.5)
                elapsed = time.time() - start_time
            
            if self.sync_service.is_syncing:
                raise Exception(f"Sync timeout after {timeout} seconds")
            
            duration = time.time() - start_time
            
            # Get sync status
            status = self.sync_service.get_sync_status()
            
            result = {
                'client_id': self.client_id,
                'status': 'success' if status['is_online'] else 'failed',
                'duration': round(duration, 2),
                'pending_changes': status['pending_changes'],
                'last_sync_time': status['last_sync_time']
            }
            
            self.logger.info(f"Sync completed on {self.client_id}: {result['status']} in {duration:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Sync failed on {self.client_id}: {e}")
            return {
                'client_id': self.client_id,
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def verify_documents(self, expected_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify that expected documents exist in this client's database
        
        Args:
            expected_documents: List of expected document information
            
        Returns:
            Verification results
        """
        try:
            self.logger.debug(f"Verifying documents on {self.client_id}")
            
            if not self.db_manager:
                raise Exception("Database manager not initialized")
            
            results = {
                'client_id': self.client_id,
                'total_expected': len(expected_documents),
                'found_documents': 0,
                'missing_documents': [],
                'verification_details': []
            }
            
            for expected_doc in expected_documents:
                doc_type = expected_doc['type']
                doc_id = expected_doc['document_id']
                
                # Query database for document
                found = self._query_document(doc_type, doc_id)
                
                if found:
                    results['found_documents'] += 1
                    results['verification_details'].append({
                        'type': doc_type,
                        'id': doc_id,
                        'status': 'found',
                        'data': found
                    })
                else:
                    results['missing_documents'].append({
                        'type': doc_type,
                        'id': doc_id
                    })
                    results['verification_details'].append({
                        'type': doc_type,
                        'id': doc_id,
                        'status': 'missing'
                    })
            
            results['success'] = len(results['missing_documents']) == 0
            
            self.logger.debug(f"Document verification on {self.client_id}: "
                            f"{results['found_documents']}/{results['total_expected']} found")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Document verification failed on {self.client_id}: {e}")
            return {
                'client_id': self.client_id,
                'success': False,
                'error': str(e)
            }
    
    def _create_sync_config(self) -> None:
        """Create sync configuration file for this client"""
        try:
            # Create client-specific config directory
            config_dir = Path(f"test_configs/{self.client_id}")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_path = config_dir / "env.ini"
            
            # Create configuration
            config = configparser.ConfigParser()
            config.add_section('Sync')
            config['Sync']['enabled'] = 'true'
            config['Sync']['server_url'] = self.server_url
            config['Sync']['node_code'] = self.node_code
            config['Sync']['auto_sync'] = 'false'  # Manual sync only for testing
            config['Sync']['debug_logging'] = 'true'
            
            with open(config_path, 'w') as f:
                config.write(f)
            
            self.logger.debug(f"Created sync config for {self.client_id}: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create sync config for {self.client_id}: {e}")
            raise
    
    def _register_with_server(self) -> None:
        """Register this client with the sync server"""
        try:
            if not self.sync_service:
                raise Exception("Sync service not initialized")
            
            # Attempt registration
            self.sync_service._register_node()
            
            # Verify registration
            status = self.sync_service.get_sync_status()
            if status['is_registered']:
                self.is_registered = True
                self.logger.info(f"Client {self.client_id} registered successfully")
            else:
                raise Exception("Registration failed - client not registered")
                
        except Exception as e:
            self.logger.error(f"Failed to register client {self.client_id}: {e}")
            raise
    
    def _create_estimate(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an estimate document"""
        # Implementation for creating estimate
        # This would use the actual database schema
        pass
    
    def _create_daily_report(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a daily report document"""
        # Implementation for creating daily report
        pass
    
    def _create_timesheet(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a timesheet document"""
        # Implementation for creating timesheet
        pass
    
    def _query_document(self, doc_type: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Query for a specific document in the database"""
        # Implementation for querying documents
        pass


class TestEnvironmentManager:
    """Manages the test environment setup and teardown"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize test environment manager
        
        Args:
            config: Test configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Environment state
        self.server_process: Optional[subprocess.Popen] = None
        self.desktop_clients: List[TestDesktopClient] = []
        self.test_databases: List[str] = []
        
        # Setup test directories
        self._setup_test_directories()
        
        self.logger.info("Test environment manager initialized")
    
    def _setup_test_directories(self) -> None:
        """Setup test directories for databases and configs"""
        directories = [
            "test_databases",
            "test_configs", 
            "test_logs",
            "test_reports"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            self.logger.debug(f"Created test directory: {directory}")
    
    def start_server(self) -> subprocess.Popen:
        """Start the local test server
        
        Returns:
            Server process handle
        """
        try:
            self.logger.info(f"Starting server on port {self.config['server_port']}")
            
            # Start API server
            server_cmd = [
                sys.executable, "-m", "uvicorn",
                "api.main:app",
                "--host", "0.0.0.0",
                "--port", str(self.config['server_port']),
                "--log-level", "info"
            ]
            
            self.server_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            self._wait_for_server_startup()
            
            self.logger.info(f"Server started successfully on port {self.config['server_port']}")
            return self.server_process
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    def _wait_for_server_startup(self, timeout: int = 30) -> None:
        """Wait for server to be ready to accept connections
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        import requests
        
        start_time = time.time()
        server_url = self.config['server_url']
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{server_url}/api/health", timeout=5)
                if response.status_code == 200:
                    self.logger.debug("Server is ready to accept connections")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        raise Exception(f"Server failed to start within {timeout} seconds")
    
    def create_desktop_client(self, client_id: str) -> TestDesktopClient:
        """Create a new desktop client instance
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            TestDesktopClient instance
        """
        try:
            self.logger.info(f"Creating desktop client: {client_id}")
            
            # Create isolated database for this client
            db_path = f"test_databases/{client_id}_test.db"
            
            # Remove existing database if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Create client instance
            client = TestDesktopClient(
                client_id=client_id,
                database_path=db_path,
                server_url=self.config['server_url'],
                logger=self.logger
            )
            
            # Start the client
            if not client.start_client():
                raise Exception(f"Failed to start client: {client_id}")
            
            self.desktop_clients.append(client)
            self.test_databases.append(db_path)
            
            self.logger.info(f"Desktop client created successfully: {client_id}")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to create desktop client {client_id}: {e}")
            raise
    
    def verify_client_connections(self, clients: List[TestDesktopClient]) -> None:
        """Verify all clients can connect to the server
        
        Args:
            clients: List of desktop clients to verify
        """
        try:
            self.logger.info("Verifying client connections to server")
            
            for client in clients:
                if not client.is_registered:
                    raise Exception(f"Client {client.client_id} is not registered with server")
                
                # Test sync service connectivity
                if client.sync_service:
                    diagnostics = client.sync_service.get_network_diagnostics()
                    if diagnostics['connectivity_test'] != 'success':
                        raise Exception(f"Client {client.client_id} cannot connect to server: "
                                      f"{diagnostics.get('error', 'Unknown error')}")
            
            self.logger.info(f"All {len(clients)} clients verified successfully")
            
        except Exception as e:
            self.logger.error(f"Client connection verification failed: {e}")
            raise
    
    def cleanup_environment(self) -> None:
        """Clean up the test environment"""
        try:
            self.logger.info("Cleaning up test environment")
            
            # Stop all desktop clients
            for client in self.desktop_clients:
                try:
                    client.stop()
                except Exception as e:
                    self.logger.warning(f"Error stopping client {client.client_id}: {e}")
            
            # Stop server
            if self.server_process:
                try:
                    self.server_process.terminate()
                    self.server_process.wait(timeout=10)
                    self.logger.info("Server stopped successfully")
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                    self.logger.warning("Server killed after timeout")
                except Exception as e:
                    self.logger.error(f"Error stopping server: {e}")
            
            # Clean up test files if configured
            if self.config.get('cleanup', True):
                self._cleanup_test_files()
            
            self.logger.info("Test environment cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during environment cleanup: {e}")
    
    def _cleanup_test_files(self) -> None:
        """Clean up temporary test files"""
        try:
            # Remove test databases
            for db_path in self.test_databases:
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.logger.debug(f"Removed test database: {db_path}")
            
            # Remove test config directories
            test_configs_dir = Path("test_configs")
            if test_configs_dir.exists():
                shutil.rmtree(test_configs_dir)
                self.logger.debug("Removed test configs directory")
            
        except Exception as e:
            self.logger.warning(f"Error cleaning up test files: {e}")
#!/usr/bin/env python3
"""
Desktop Sync End-to-End Testing Controller

This module provides comprehensive end-to-end testing for the desktop synchronization system.
It creates a controlled environment with one server and multiple desktop clients to validate
synchronization behavior, data consistency, and error handling.

Usage:
    python test_sync_end_to_end.py --verbose --report-file sync_test_report.json
"""

import os
import sys
import json
import time
import uuid
import logging
import argparse
import threading
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.database_manager import DatabaseManager
from src.services.sync_service import SyncService
from src.services.sync_initializer import SyncInitializer

# Import test framework components
from test_environment_manager import TestEnvironmentManager, TestDesktopClient
from document_creation_engine import DocumentCreationEngine
from synchronization_orchestrator import SynchronizationOrchestrator
from data_verification_engine import DataVerificationEngine
from test_logging_system import TestLoggingSystem
from test_report_generator import TestReportGenerator
from test_config_manager import TestConfiguration, create_configuration_from_args


class SyncEndToEndTestController:
    """Main controller for end-to-end synchronization testing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize test controller
        
        Args:
            config: Test configuration dictionary
        """
        self.config = config
        self.test_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now(timezone.utc)
        
        # Test environment components
        self.server_process: Optional[subprocess.Popen] = None
        self.desktop_clients: List['TestDesktopClient'] = []
        self.test_databases: List[str] = []
        
        # Test results and logging
        self.test_results: Dict[str, Any] = {
            'test_id': self.test_id,
            'start_time': self.start_time.isoformat(),
            'config': config,
            'phases': {},
            'documents_created': [],
            'verification_results': {},
            'performance_metrics': {},
            'errors': []
        }
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Test components
        self.environment_manager: Optional['TestEnvironmentManager'] = None
        self.document_engine: Optional['DocumentCreationEngine'] = None
        self.sync_orchestrator: Optional['SynchronizationOrchestrator'] = None
        self.verification_engine: Optional['DataVerificationEngine'] = None
        
        self.logger.info(f"Test controller initialized with ID: {self.test_id}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging system
        
        Returns:
            Configured logger instance
        """
        # Create logs directory
        logs_dir = Path("test_logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Setup logger
        logger = logging.getLogger(f"sync_test_{self.test_id}")
        logger.setLevel(logging.DEBUG if self.config.get('verbose', False) else logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler with detailed format
        log_file = logs_dir / f"sync_test_{self.test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if self.config.get('verbose', False) else logging.WARNING)
        
        # Detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Store log file path for report
        self.test_results['log_file'] = str(log_file)
        
        return logger
    
    def run_full_test_scenario(self) -> Dict[str, Any]:
        """Execute the complete end-to-end test scenario
        
        Returns:
            Comprehensive test results dictionary
        """
        try:
            self.logger.info("Starting comprehensive sync end-to-end test scenario")
            
            # Phase 1: Environment Setup
            self._execute_phase("setup", self._setup_test_environment)
            
            # Phase 2: Document Creation
            self._execute_phase("document_creation", self._create_test_documents)
            
            # Phase 3: Synchronization
            self._execute_phase("synchronization", self._perform_synchronization)
            
            # Phase 4: Verification
            self._execute_phase("verification", self._verify_data_consistency)
            
            # Phase 5: Cleanup
            self._execute_phase("cleanup", self._cleanup_test_environment)
            
            # Generate final report
            self._finalize_test_results()
            
            self.logger.info("Test scenario completed successfully")
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"Test scenario failed: {e}")
            self.test_results['status'] = 'FAILED'
            self.test_results['error'] = str(e)
            
            # Attempt cleanup even on failure
            try:
                self._cleanup_test_environment()
            except Exception as cleanup_error:
                self.logger.error(f"Cleanup failed: {cleanup_error}")
            
            return self.test_results
    
    def _execute_phase(self, phase_name: str, phase_function) -> None:
        """Execute a test phase with timing and error handling
        
        Args:
            phase_name: Name of the test phase
            phase_function: Function to execute for this phase
        """
        phase_start = time.time()
        self.logger.info(f"Starting phase: {phase_name}")
        
        try:
            phase_function()
            phase_duration = time.time() - phase_start
            
            self.test_results['phases'][phase_name] = {
                'status': 'PASSED',
                'duration': round(phase_duration, 2),
                'start_time': datetime.fromtimestamp(phase_start, timezone.utc).isoformat()
            }
            
            self.logger.info(f"Phase {phase_name} completed in {phase_duration:.2f}s")
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            error_msg = f"Phase {phase_name} failed: {e}"
            
            self.test_results['phases'][phase_name] = {
                'status': 'FAILED',
                'duration': round(phase_duration, 2),
                'error': str(e),
                'start_time': datetime.fromtimestamp(phase_start, timezone.utc).isoformat()
            }
            
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _setup_test_environment(self) -> None:
        """Setup the test environment with server and desktop clients"""
        self.logger.info("Setting up test environment")
        
        # Initialize environment manager
        self.environment_manager = TestEnvironmentManager(self.config, self.logger)
        
        # Start server
        self.server_process = self.environment_manager.start_server()
        self.logger.info(f"Server started on {self.config['server_url']}")
        
        # Create desktop clients
        client_count = self.config.get('client_count', 3)
        for i in range(client_count):
            client = self.environment_manager.create_desktop_client(f"client_{i+1}")
            self.desktop_clients.append(client)
            self.test_databases.append(client.database_path)
        
        self.logger.info(f"Created {len(self.desktop_clients)} desktop clients")
        
        # Verify all clients can connect to server
        self.environment_manager.verify_client_connections(self.desktop_clients)
        
        self.logger.info("Test environment setup completed")
    
    def _create_test_documents(self) -> None:
        """Create test documents on different desktop clients"""
        self.logger.info("Creating test documents")
        
        # Initialize document creation engine
        self.document_engine = DocumentCreationEngine(self.desktop_clients, self.logger)
        
        # Document templates for each client
        document_templates = [
            {'type': 'estimate', 'client_index': 0},
            {'type': 'daily_report', 'client_index': 1},
            {'type': 'timesheet', 'client_index': 2}
        ]
        
        # Create documents
        for template in document_templates:
            if template['client_index'] < len(self.desktop_clients):
                client = self.desktop_clients[template['client_index']]
                document = self.document_engine.create_document(client, template['type'])
                
                self.test_results['documents_created'].append({
                    'type': template['type'],
                    'client_id': client.client_id,
                    'document_id': document['id'],
                    'created_at': document['created_at']
                })
                
                self.logger.info(f"Created {template['type']} document on {client.client_id}")
        
        # Verify documents exist only in their respective databases
        self.document_engine.verify_initial_document_distribution(self.desktop_clients)
        
        self.logger.info("Test document creation completed")
    
    def _perform_synchronization(self) -> None:
        """Perform synchronization across all desktop clients"""
        self.logger.info("Starting synchronization phase")
        
        # Initialize synchronization orchestrator
        self.sync_orchestrator = SynchronizationOrchestrator(
            self.desktop_clients, 
            self.config,
            self.logger
        )
        
        # Perform manual sync on each client
        sync_results = []
        for client in self.desktop_clients:
            result = self.sync_orchestrator.trigger_manual_sync(client)
            sync_results.append(result)
            
            self.logger.info(f"Sync completed for {client.client_id}: {result['status']}")
        
        # Collect performance metrics
        self.test_results['performance_metrics'] = {
            'total_sync_operations': len(sync_results),
            'successful_syncs': sum(1 for r in sync_results if r['status'] == 'success'),
            'failed_syncs': sum(1 for r in sync_results if r['status'] == 'failed'),
            'average_sync_duration': sum(r.get('duration', 0) for r in sync_results) / len(sync_results),
            'total_data_transferred': sum(r.get('data_size', 0) for r in sync_results)
        }
        
        self.logger.info("Synchronization phase completed")
    
    def _verify_data_consistency(self) -> None:
        """Verify data consistency across all desktop clients"""
        self.logger.info("Starting data consistency verification")
        
        # Initialize verification engine
        self.verification_engine = DataVerificationEngine(
            self.desktop_clients,
            self.test_results['documents_created'],
            self.logger
        )
        
        # Verify all documents exist in all databases
        verification_results = self.verification_engine.verify_document_propagation()
        
        # Verify document content consistency
        content_results = self.verification_engine.verify_content_consistency()
        
        # Verify no duplicates
        duplicate_results = self.verification_engine.verify_no_duplicates()
        
        # Aggregate verification results
        self.test_results['verification_results'] = {
            'documents_verified': verification_results['total_documents'],
            'propagation_success': verification_results['success'],
            'content_consistency': content_results['success'],
            'no_duplicates': duplicate_results['success'],
            'consistency_checks_passed': (
                verification_results['passed_checks'] +
                content_results['passed_checks'] +
                duplicate_results['passed_checks']
            ),
            'data_integrity_score': self._calculate_integrity_score(
                verification_results, content_results, duplicate_results
            )
        }
        
        self.logger.info("Data consistency verification completed")
    
    def _cleanup_test_environment(self) -> None:
        """Clean up test environment and resources"""
        self.logger.info("Starting test environment cleanup")
        
        # Stop desktop clients
        for client in self.desktop_clients:
            try:
                client.stop()
                self.logger.debug(f"Stopped client: {client.client_id}")
            except Exception as e:
                self.logger.warning(f"Failed to stop client {client.client_id}: {e}")
        
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
                self.logger.error(f"Failed to stop server: {e}")
        
        # Archive test databases if configured
        if self.config.get('archive_databases', True):
            self._archive_test_databases()
        
        self.logger.info("Test environment cleanup completed")
    
    def _calculate_integrity_score(self, *results) -> int:
        """Calculate overall data integrity score
        
        Args:
            *results: Verification result dictionaries
            
        Returns:
            Integrity score as percentage (0-100)
        """
        total_checks = sum(r.get('total_checks', 0) for r in results)
        passed_checks = sum(r.get('passed_checks', 0) for r in results)
        
        if total_checks == 0:
            return 0
        
        return int((passed_checks / total_checks) * 100)
    
    def _archive_test_databases(self) -> None:
        """Archive test databases for later analysis"""
        try:
            archive_dir = Path("test_databases") / f"test_{self.test_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            for i, db_path in enumerate(self.test_databases):
                if os.path.exists(db_path):
                    archive_path = archive_dir / f"client_{i+1}_database.db"
                    import shutil
                    shutil.copy2(db_path, archive_path)
                    self.logger.debug(f"Archived database: {db_path} -> {archive_path}")
            
            self.test_results['archived_databases'] = str(archive_dir)
            
        except Exception as e:
            self.logger.warning(f"Failed to archive databases: {e}")
    
    def _finalize_test_results(self) -> None:
        """Finalize test results and generate report"""
        self.test_results['end_time'] = datetime.now(timezone.utc).isoformat()
        self.test_results['total_duration'] = (
            datetime.now(timezone.utc) - self.start_time
        ).total_seconds()
        
        # Determine overall test status
        failed_phases = [name for name, phase in self.test_results['phases'].items() 
                        if phase['status'] == 'FAILED']
        
        if failed_phases:
            self.test_results['status'] = 'FAILED'
            self.test_results['failed_phases'] = failed_phases
        else:
            self.test_results['status'] = 'PASSED'
        
        # Generate report file
        if self.config.get('report_file'):
            self._generate_report_file()
    
    def _generate_report_file(self) -> None:
        """Generate detailed test report file"""
        try:
            report_file = self.config['report_file']
            
            # Add timestamp to filename if not present
            if not any(ts in report_file for ts in ['%Y', '%m', '%d', '%H', '%M', '%S']):
                name, ext = os.path.splitext(report_file)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = f"{name}_{timestamp}{ext}"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Test report generated: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate report file: {e}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Desktop Sync End-to-End Testing Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_sync_end_to_end.py --verbose
  python test_sync_end_to_end.py --client-count 5 --timeout 60
  python test_sync_end_to_end.py --report-file results.json --cleanup
        """
    )
    
    parser.add_argument(
        '--client-count', 
        type=int, 
        default=3,
        help='Number of desktop clients to create (default: 3)'
    )
    
    parser.add_argument(
        '--server-port', 
        type=int, 
        default=8000,
        help='Local server port (default: 8000)'
    )
    
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=30,
        help='Sync timeout in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--cleanup', 
        action='store_true',
        help='Auto-cleanup after test (default: true)'
    )
    
    parser.add_argument(
        '--no-cleanup', 
        action='store_true',
        help='Skip cleanup after test'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--report-file', 
        type=str,
        help='Path to save test report JSON file'
    )
    
    parser.add_argument(
        '--archive-databases', 
        action='store_true',
        default=True,
        help='Archive test databases for analysis (default: true)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the test controller"""
    args = parse_arguments()
    
    # Create configuration from arguments
    config = create_configuration_from_args(args)
    
    # Create and run test controller
    controller = SyncEndToEndTestController(config.to_dict())
    results = controller.run_full_test_scenario()
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"SYNC END-TO-END TEST RESULTS")
    print(f"{'='*60}")
    print(f"Test ID: {results['test_id']}")
    print(f"Status: {results['status']}")
    print(f"Duration: {results.get('total_duration', 0):.2f} seconds")
    print(f"Documents Created: {len(results.get('documents_created', []))}")
    
    if results.get('verification_results'):
        vr = results['verification_results']
        print(f"Data Integrity Score: {vr.get('data_integrity_score', 0)}%")
        print(f"Consistency Checks Passed: {vr.get('consistency_checks_passed', 0)}")
    
    if results.get('performance_metrics'):
        pm = results['performance_metrics']
        print(f"Successful Syncs: {pm.get('successful_syncs', 0)}/{pm.get('total_sync_operations', 0)}")
        print(f"Average Sync Duration: {pm.get('average_sync_duration', 0):.2f}s")
    
    if results['status'] == 'FAILED':
        print(f"Failed Phases: {', '.join(results.get('failed_phases', []))}")
        if results.get('error'):
            print(f"Error: {results['error']}")
    
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if results['status'] == 'PASSED' else 1)


if __name__ == "__main__":
    main()
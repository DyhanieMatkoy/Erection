#!/usr/bin/env python3
"""Multi-Database Synchronization Testing Script

This script executes comprehensive end-to-end testing of the desktop synchronization
system across multiple database types (PostgreSQL, MySQL, SQLite) and validates
Alembic schema migration propagation.

Usage:
    python test_multi_database_sync.py --all-scenarios
    python test_multi_database_sync.py --scenario postgresql_mixed
    python test_multi_database_sync.py --migration-tests-only
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_database_test_environment_manager import MultiDatabaseTestEnvironmentManager
from test_logging_system import TestLoggingSystem
from test_report_generator import TestReportGenerator


class MultiDatabaseSyncTester:
    """Main class for multi-database synchronization testing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize multi-database sync tester
        
        Args:
            config: Test configuration dictionary
        """
        self.config = config
        
        # Test execution state
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_results: Dict[str, Any] = {}
        
        # Initialize logging
        self.logging_system = TestLoggingSystem(self.test_session_id, config)
        self.logger = self.logging_system.get_logger("MultiDatabaseSyncTester")
        
        # Initialize test environment manager
        self.env_manager = MultiDatabaseTestEnvironmentManager(config, self.logger)
        
        # Initialize report generator
        self.report_generator = TestReportGenerator(config, self.logger)
        
        self.logger.info("Multi-database sync tester initialized")
    
    def execute_all_scenarios(self) -> Dict[str, Any]:
        """Execute all predefined test scenarios
        
        Returns:
            Comprehensive test results
        """
        try:
            self.logger.info("Starting execution of all multi-database test scenarios")
            
            # Get available scenarios
            scenarios = self.env_manager.get_test_scenarios()
            self.logger.info(f"Found {len(scenarios)} test scenarios: {list(scenarios.keys())}")
            
            # Execute all scenarios
            results = self.env_manager.execute_all_test_scenarios()
            
            # Add metadata
            results['test_session_id'] = self.test_session_id
            results['test_configuration'] = self.config
            results['available_scenarios'] = scenarios
            
            self.test_results = results
            
            # Generate and save reports
            self._generate_and_save_reports(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute all scenarios: {e}")
            return {
                'overall_success': False,
                'error': str(e),
                'test_session_id': self.test_session_id
            }
    
    def execute_single_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Execute a single test scenario
        
        Args:
            scenario_name: Name of the scenario to execute
            
        Returns:
            Test results for the scenario
        """
        try:
            self.logger.info(f"Starting execution of scenario: {scenario_name}")
            
            # Validate scenario exists
            scenarios = self.env_manager.get_test_scenarios()
            if scenario_name not in scenarios:
                raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(scenarios.keys())}")
            
            # Setup environment
            setup_success = self.env_manager.setup_multi_database_environment(scenario_name)
            if not setup_success:
                raise Exception(f"Failed to setup environment for scenario: {scenario_name}")
            
            results = {
                'scenario_name': scenario_name,
                'scenario_info': scenarios[scenario_name],
                'test_session_id': self.test_session_id,
                'setup_success': setup_success,
                'sync_workflow_results': None,
                'migration_test_results': None,
                'cleanup_success': False,
                'overall_success': False
            }
            
            try:
                # Execute sync workflow test
                self.logger.info("Executing sync workflow test")
                sync_results = self.env_manager.execute_full_sync_workflow_test()
                results['sync_workflow_results'] = sync_results
                
                # Execute migration tests
                self.logger.info("Executing migration tests")
                migration_results = self.env_manager.execute_migration_test_scenario()
                results['migration_test_results'] = migration_results
                
                # Determine overall success
                results['overall_success'] = (
                    sync_results['overall_success'] and 
                    migration_results['overall_success']
                )
                
            finally:
                # Always attempt cleanup
                try:
                    self.env_manager.cleanup_multi_database_environment()
                    results['cleanup_success'] = True
                except Exception as cleanup_error:
                    self.logger.error(f"Cleanup failed: {cleanup_error}")
                    results['cleanup_success'] = False
            
            self.test_results = results
            
            # Generate and save reports
            self._generate_and_save_reports(results)
            
            status = "SUCCESS" if results['overall_success'] else "FAILED"
            self.logger.info(f"Scenario execution completed: {scenario_name} - {status}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute scenario {scenario_name}: {e}")
            return {
                'scenario_name': scenario_name,
                'overall_success': False,
                'error': str(e),
                'test_session_id': self.test_session_id
            }
    
    def execute_migration_tests_only(self, scenario_name: str = 'postgresql_mixed', migration_names: Optional[list] = None) -> Dict[str, Any]:
        """Execute only migration tests without full sync workflow
        
        Args:
            scenario_name: Scenario to use for migration testing
            migration_names: Specific migrations to test (uses scenario default if None)
            
        Returns:
            Migration test results
        """
        try:
            self.logger.info(f"Starting migration-only testing with scenario: {scenario_name}")
            
            # Setup environment
            setup_success = self.env_manager.setup_multi_database_environment(scenario_name)
            if not setup_success:
                raise Exception(f"Failed to setup environment for migration testing")
            
            results = {
                'test_type': 'migration_only',
                'scenario_name': scenario_name,
                'test_session_id': self.test_session_id,
                'setup_success': setup_success,
                'migration_test_results': None,
                'cleanup_success': False,
                'overall_success': False
            }
            
            try:
                # Execute migration tests
                migration_results = self.env_manager.execute_migration_test_scenario(migration_names)
                results['migration_test_results'] = migration_results
                results['overall_success'] = migration_results['overall_success']
                
            finally:
                # Always attempt cleanup
                try:
                    self.env_manager.cleanup_multi_database_environment()
                    results['cleanup_success'] = True
                except Exception as cleanup_error:
                    self.logger.error(f"Cleanup failed: {cleanup_error}")
                    results['cleanup_success'] = False
            
            self.test_results = results
            
            # Generate and save reports
            self._generate_and_save_reports(results)
            
            status = "SUCCESS" if results['overall_success'] else "FAILED"
            self.logger.info(f"Migration-only testing completed: {status}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute migration tests: {e}")
            return {
                'test_type': 'migration_only',
                'scenario_name': scenario_name,
                'overall_success': False,
                'error': str(e),
                'test_session_id': self.test_session_id
            }
    
    def _generate_and_save_reports(self, results: Dict[str, Any]) -> None:
        """Generate and save test reports
        
        Args:
            results: Test results to generate reports from
        """
        try:
            # Generate JSON report
            json_report_path = f"test_reports/multi_database_sync_report_{self.test_session_id}.json"
            Path(json_report_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(json_report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"JSON report saved: {json_report_path}")
            
            # Generate text report
            if 'scenario_results' in results:
                # Multi-scenario report
                text_report = self.env_manager.generate_multi_database_test_report(results)
            else:
                # Single scenario report
                text_report = self._generate_single_scenario_report(results)
            
            text_report_path = f"test_reports/multi_database_sync_report_{self.test_session_id}.txt"
            
            with open(text_report_path, 'w') as f:
                f.write(text_report)
            
            self.logger.info(f"Text report saved: {text_report_path}")
            
            # Generate summary report using report generator
            summary_report = self.report_generator.generate_test_summary(results)
            summary_report_path = f"test_reports/multi_database_sync_summary_{self.test_session_id}.txt"
            
            with open(summary_report_path, 'w') as f:
                f.write(summary_report)
            
            self.logger.info(f"Summary report saved: {summary_report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")
    
    def _generate_single_scenario_report(self, results: Dict[str, Any]) -> str:
        """Generate report for single scenario execution
        
        Args:
            results: Single scenario test results
            
        Returns:
            Formatted report as string
        """
        try:
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("MULTI-DATABASE SYNCHRONIZATION TEST REPORT")
            report_lines.append("=" * 80)
            report_lines.append("")
            
            # Test information
            report_lines.append("TEST INFORMATION")
            report_lines.append("-" * 40)
            report_lines.append(f"Test Session ID: {results.get('test_session_id', 'Unknown')}")
            report_lines.append(f"Test Type: {results.get('test_type', 'Full Scenario')}")
            report_lines.append(f"Scenario: {results.get('scenario_name', 'Unknown')}")
            
            if 'scenario_info' in results:
                info = results['scenario_info']
                report_lines.append(f"Description: {info['description']}")
                report_lines.append(f"Server DB: {info['server_db_type']}")
                report_lines.append(f"Client DBs: {', '.join([f'{k}={v}' for k, v in info['client_db_types'].items()])}")
            
            report_lines.append(f"Overall Result: {'PASS' if results['overall_success'] else 'FAIL'}")
            report_lines.append("")
            
            # Sync workflow results
            if results.get('sync_workflow_results'):
                sync_results = results['sync_workflow_results']
                report_lines.append("SYNC WORKFLOW RESULTS")
                report_lines.append("-" * 40)
                report_lines.append(f"Result: {'PASS' if sync_results['overall_success'] else 'FAIL'}")
                report_lines.append(f"Duration: {sync_results['duration']} seconds")
                
                # Document creation
                if sync_results.get('document_creation'):
                    doc_success = sum(1 for r in sync_results['document_creation'].values() if r['success'])
                    doc_total = len(sync_results['document_creation'])
                    report_lines.append(f"Document Creation: {doc_success}/{doc_total} successful")
                
                # Synchronization
                if sync_results.get('synchronization_results'):
                    sync_success = sum(1 for r in sync_results['synchronization_results'].values() if r['status'] == 'success')
                    sync_total = len(sync_results['synchronization_results'])
                    report_lines.append(f"Synchronization: {sync_success}/{sync_total} successful")
                
                # Data verification
                if sync_results.get('data_verification'):
                    verify_success = sum(1 for r in sync_results['data_verification'].values() if r['success'])
                    verify_total = len(sync_results['data_verification'])
                    report_lines.append(f"Data Verification: {verify_success}/{verify_total} successful")
                
                report_lines.append("")
            
            # Migration test results
            if results.get('migration_test_results'):
                migration_results = results['migration_test_results']
                report_lines.append("MIGRATION TEST RESULTS")
                report_lines.append("-" * 40)
                report_lines.append(f"Result: {'PASS' if migration_results['overall_success'] else 'FAIL'}")
                report_lines.append(f"Duration: {migration_results['duration']} seconds")
                report_lines.append(f"Migrations Tested: {len(migration_results['migrations_tested'])}")
                
                # Migration details
                if migration_results.get('migration_results'):
                    migration_success = sum(1 for r in migration_results['migration_results'].values() if r['success'])
                    migration_total = len(migration_results['migration_results'])
                    report_lines.append(f"Migration Success Rate: {migration_success}/{migration_total}")
                    
                    for migration_name, migration_result in migration_results['migration_results'].items():
                        status = "PASS" if migration_result['success'] else "FAIL"
                        report_lines.append(f"  {migration_name}: {status}")
                
                report_lines.append("")
            
            # Error information
            if 'error' in results:
                report_lines.append("ERROR INFORMATION")
                report_lines.append("-" * 40)
                report_lines.append(f"Error: {results['error']}")
                report_lines.append("")
            
            report_lines.append("=" * 80)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"Error generating single scenario report: {e}"
    
    def list_available_scenarios(self) -> None:
        """List all available test scenarios"""
        try:
            scenarios = self.env_manager.get_test_scenarios()
            
            print("\nAvailable Multi-Database Test Scenarios:")
            print("=" * 60)
            
            for name, info in scenarios.items():
                print(f"\nScenario: {name}")
                print(f"  Description: {info['description']}")
                print(f"  Server DB: {info['server_db_type']}")
                print(f"  Client DBs: {', '.join([f'{k}={v}' for k, v in info['client_db_types'].items()])}")
                print(f"  Migration Tests: {', '.join(info['migration_tests'])}")
                print(f"  Expected Duration: {info['expected_duration']} seconds")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"Error listing scenarios: {e}")


def create_default_config() -> Dict[str, Any]:
    """Create default test configuration
    
    Returns:
        Default configuration dictionary
    """
    return {
        'server_port': 8000,
        'server_url': 'http://localhost:8000',
        'client_count': 3,
        'timeout': 30,
        'cleanup': True,
        'log_level': 'INFO',
        'verbose': False,
        'report_format': 'json',
        'test_databases_dir': 'test_databases',
        'test_configs_dir': 'test_configs',
        'test_logs_dir': 'test_logs',
        'test_reports_dir': 'test_reports'
    }


def main():
    """Main entry point for multi-database sync testing"""
    parser = argparse.ArgumentParser(
        description='Multi-Database Synchronization Testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_multi_database_sync.py --all-scenarios
  python test_multi_database_sync.py --scenario postgresql_mixed --verbose
  python test_multi_database_sync.py --migration-tests-only --scenario mysql_mixed
  python test_multi_database_sync.py --list-scenarios
        """
    )
    
    # Test execution options
    parser.add_argument('--all-scenarios', action='store_true',
                       help='Execute all predefined test scenarios')
    
    parser.add_argument('--scenario', type=str,
                       help='Execute specific test scenario')
    
    parser.add_argument('--migration-tests-only', action='store_true',
                       help='Execute only migration tests (no sync workflow)')
    
    parser.add_argument('--list-scenarios', action='store_true',
                       help='List all available test scenarios')
    
    # Configuration options
    parser.add_argument('--server-port', type=int, default=8000,
                       help='Server port (default: 8000)')
    
    parser.add_argument('--timeout', type=int, default=30,
                       help='Sync timeout in seconds (default: 30)')
    
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup after tests (for debugging)')
    
    parser.add_argument('--report-format', choices=['json', 'text', 'both'], default='both',
                       help='Report format (default: both)')
    
    parser.add_argument('--alembic-config', type=str, default='alembic.ini',
                       help='Path to Alembic configuration file')
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_default_config()
    config.update({
        'server_port': args.server_port,
        'server_url': f'http://localhost:{args.server_port}',
        'timeout': args.timeout,
        'verbose': args.verbose,
        'cleanup': not args.no_cleanup,
        'report_format': args.report_format,
        'log_level': 'DEBUG' if args.verbose else 'INFO',
        'alembic_config': args.alembic_config
    })
    
    try:
        # Initialize tester
        tester = MultiDatabaseSyncTester(config)
        
        # Execute based on arguments
        if args.list_scenarios:
            tester.list_available_scenarios()
            return
        
        elif args.all_scenarios:
            print("Executing all multi-database test scenarios...")
            results = tester.execute_all_scenarios()
            
        elif args.scenario:
            if args.migration_tests_only:
                print(f"Executing migration tests only for scenario: {args.scenario}")
                results = tester.execute_migration_tests_only(args.scenario)
            else:
                print(f"Executing scenario: {args.scenario}")
                results = tester.execute_single_scenario(args.scenario)
                
        elif args.migration_tests_only:
            print("Executing migration tests only (default scenario: postgresql_mixed)")
            results = tester.execute_migration_tests_only()
            
        else:
            parser.print_help()
            return
        
        # Print results summary
        if results['overall_success']:
            print(f"\n✅ Tests PASSED (Session: {results['test_session_id']})")
            exit_code = 0
        else:
            print(f"\n❌ Tests FAILED (Session: {results['test_session_id']})")
            if 'error' in results:
                print(f"Error: {results['error']}")
            exit_code = 1
        
        # Print report locations
        print(f"\nReports saved in: test_reports/")
        print(f"Session ID: {results['test_session_id']}")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
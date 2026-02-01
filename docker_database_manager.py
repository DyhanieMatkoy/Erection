#!/usr/bin/env python3
"""Docker Database Manager for Multi-Database Testing

This module manages Docker containers for PostgreSQL and MySQL databases
used in multi-database synchronization testing.
"""

import os
import sys
import time
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class DockerDatabaseConfig:
    """Docker database configuration"""
    service_name: str
    container_name: str
    image: str
    port: int
    database_name: str
    username: str
    password: str
    environment: Dict[str, str]
    healthcheck_command: List[str]


class DockerDatabaseManager:
    """Manager for Docker-based test databases"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize Docker database manager
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.compose_file = "docker-compose.test.yml"
        self.running_containers: List[str] = []
        
        # Docker compose command (will be determined during availability check)
        self.compose_command = ['docker-compose']
        
        # Database configurations
        self.database_configs = {
            'postgresql': DockerDatabaseConfig(
                service_name='postgres-test',
                container_name='ctm-postgres-test',
                image='postgres:15-alpine',
                port=5432,
                database_name='construction_test',
                username='postgres',
                password='postgres_password',
                environment={
                    'POSTGRES_DB': 'construction_test',
                    'POSTGRES_USER': 'postgres',
                    'POSTGRES_PASSWORD': 'postgres_password',
                    'POSTGRES_HOST_AUTH_METHOD': 'trust'
                },
                healthcheck_command=['pg_isready', '-U', 'postgres', '-d', 'construction_test']
            ),
            'mysql': DockerDatabaseConfig(
                service_name='mysql-test',
                container_name='ctm-mysql-test',
                image='mysql:8.0',
                port=3306,
                database_name='construction_test',
                username='test_user',
                password='test_password',
                environment={
                    'MYSQL_ROOT_PASSWORD': 'root_password',
                    'MYSQL_DATABASE': 'construction_test',
                    'MYSQL_USER': 'test_user',
                    'MYSQL_PASSWORD': 'test_password'
                },
                healthcheck_command=['mysqladmin', 'ping', '-h', 'localhost', '-u', 'test_user', '-ptest_password']
            )
        }
        
        self.logger.info("Docker database manager initialized")
    
    def check_docker_availability(self) -> Tuple[bool, str]:
        """Check if Docker is available and running
        
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            # Check if Docker is installed and working
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check if command executed successfully and produced output
            if result.returncode != 0 or not result.stdout.strip():
                return False, f"Docker is not properly installed. Return code: {result.returncode}, Output: '{result.stdout}', Error: '{result.stderr}'"
            
            # Verify it's actually Docker by checking version output
            if 'Docker version' not in result.stdout and 'docker version' not in result.stdout.lower():
                return False, f"Docker command found but doesn't appear to be Docker. Output: '{result.stdout}'"
            
            # Check if Docker daemon is running
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return False, f"Docker daemon is not running. Error: {result.stderr}"
            
            # Check for docker-compose
            result = subprocess.run(
                ['docker-compose', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # Try docker compose (newer syntax)
                result = subprocess.run(
                    ['docker', 'compose', 'version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    return False, "Docker Compose is not available"
                else:
                    self.compose_command = ['docker', 'compose']
            else:
                self.compose_command = ['docker-compose']
            
            self.logger.info("Docker is available and running")
            return True, ""
            
        except subprocess.TimeoutExpired:
            return False, "Docker command timed out - Docker may not be properly installed"
        except FileNotFoundError:
            return False, "Docker command not found - Docker is not installed or not in PATH"
        except Exception as e:
            return False, f"Error checking Docker: {e}"
    
    def start_database_containers(self, database_types: List[str]) -> bool:
        """Start Docker containers for specified database types
        
        Args:
            database_types: List of database types to start ('postgresql', 'mysql')
            
        Returns:
            True if all containers started successfully
        """
        try:
            self.logger.info(f"Starting Docker containers for databases: {database_types}")
            
            # Check Docker availability first
            docker_available, error = self.check_docker_availability()
            if not docker_available:
                self.logger.error(f"Docker not available: {error}")
                return False
            
            # Stop any existing containers first
            self.stop_all_containers()
            
            # Start containers using docker-compose
            services_to_start = []
            for db_type in database_types:
                if db_type in self.database_configs:
                    config = self.database_configs[db_type]
                    services_to_start.append(config.service_name)
                else:
                    self.logger.warning(f"Unknown database type: {db_type}")
            
            if not services_to_start:
                self.logger.error("No valid database services to start")
                return False
            
            # Start services with docker-compose
            cmd = self.compose_command + ['-f', self.compose_file, 'up', '-d'] + services_to_start
            
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to start containers: {result.stderr}")
                return False
            
            self.logger.info("Docker containers started, waiting for health checks...")
            
            # Wait for containers to be healthy
            for db_type in database_types:
                if not self.wait_for_database_ready(db_type):
                    self.logger.error(f"Database {db_type} failed to become ready")
                    return False
            
            # Track running containers
            for db_type in database_types:
                config = self.database_configs[db_type]
                self.running_containers.append(config.container_name)
            
            self.logger.info("All database containers are ready")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Docker container startup timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start database containers: {e}")
            return False
    
    def wait_for_database_ready(self, database_type: str, max_wait: int = 60) -> bool:
        """Wait for database to be ready for connections
        
        Args:
            database_type: Type of database ('postgresql', 'mysql')
            max_wait: Maximum wait time in seconds
            
        Returns:
            True if database is ready
        """
        try:
            config = self.database_configs.get(database_type)
            if not config:
                self.logger.error(f"Unknown database type: {database_type}")
                return False
            
            self.logger.info(f"Waiting for {database_type} to be ready...")
            
            start_time = time.time()
            while time.time() - start_time < max_wait:
                # Check container health
                result = subprocess.run(
                    ['docker', 'inspect', '--format={{.State.Health.Status}}', config.container_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    health_status = result.stdout.strip()
                    if health_status == 'healthy':
                        self.logger.info(f"{database_type} is ready")
                        return True
                    elif health_status == 'unhealthy':
                        self.logger.warning(f"{database_type} is unhealthy")
                        break
                
                # Also try direct connection test
                if self.test_database_connection(database_type):
                    self.logger.info(f"{database_type} connection test passed")
                    return True
                
                time.sleep(2)
            
            self.logger.error(f"{database_type} did not become ready within {max_wait} seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for {database_type}: {e}")
            return False
    
    def test_database_connection(self, database_type: str) -> bool:
        """Test database connection
        
        Args:
            database_type: Type of database to test
            
        Returns:
            True if connection successful
        """
        try:
            config = self.database_configs.get(database_type)
            if not config:
                return False
            
            if database_type == 'postgresql':
                # Test PostgreSQL connection
                cmd = [
                    'docker', 'exec', config.container_name,
                    'pg_isready', '-h', 'localhost', '-p', '5432',
                    '-U', config.username, '-d', config.database_name
                ]
            elif database_type == 'mysql':
                # Test MySQL connection
                cmd = [
                    'docker', 'exec', config.container_name,
                    'mysqladmin', 'ping', '-h', 'localhost',
                    '-u', 'root', '-proot_password'
                ]
            else:
                return False
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def get_database_connection_string(self, database_type: str) -> Optional[str]:
        """Get connection string for database
        
        Args:
            database_type: Type of database
            
        Returns:
            Connection string or None if not available
        """
        config = self.database_configs.get(database_type)
        if not config:
            return None
        
        if database_type == 'postgresql':
            return f"postgresql://{config.username}:{config.password}@localhost:{config.port}/{config.database_name}"
        elif database_type == 'mysql':
            return f"mysql+pymysql://root:root_password@localhost:{config.port}/{config.database_name}"
        
        return None
    
    def get_database_config(self, database_type: str) -> Optional[Dict[str, Any]]:
        """Get database configuration for testing
        
        Args:
            database_type: Type of database
            
        Returns:
            Database configuration dictionary
        """
        config = self.database_configs.get(database_type)
        if not config:
            return None
        
        return {
            'type': database_type,
            'host': 'localhost',
            'port': config.port,
            'database': config.database_name,
            'username': 'root' if database_type == 'mysql' else config.username,
            'password': 'root_password' if database_type == 'mysql' else config.password,
            'connection_string': self.get_database_connection_string(database_type)
        }
    
    def stop_all_containers(self) -> None:
        """Stop all running test database containers"""
        try:
            self.logger.info("Stopping all test database containers")
            
            # Stop using docker-compose
            cmd = self.compose_command + ['-f', self.compose_file, 'down']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Docker-compose down failed: {result.stderr}")
                
                # Fallback: stop containers individually
                for container_name in self.running_containers:
                    try:
                        subprocess.run(
                            ['docker', 'stop', container_name],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        subprocess.run(
                            ['docker', 'rm', container_name],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to stop container {container_name}: {e}")
            
            self.running_containers.clear()
            self.logger.info("All containers stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping containers: {e}")
    
    def cleanup_volumes(self) -> None:
        """Clean up Docker volumes"""
        try:
            self.logger.info("Cleaning up Docker volumes")
            
            # Remove volumes using docker-compose
            cmd = self.compose_command + ['-f', self.compose_file, 'down', '-v']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Volume cleanup failed: {result.stderr}")
            else:
                self.logger.info("Docker volumes cleaned up")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up volumes: {e}")


def main():
    """Main function for testing Docker database manager"""
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("DockerDatabaseManager")
    
    parser = argparse.ArgumentParser(description='Docker Database Manager for Testing')
    parser.add_argument('--check', action='store_true',
                       help='Check Docker availability')
    parser.add_argument('--start', nargs='+', choices=['postgresql', 'mysql'],
                       help='Start database containers')
    parser.add_argument('--stop', action='store_true',
                       help='Stop all containers')
    parser.add_argument('--test-connection', choices=['postgresql', 'mysql'],
                       help='Test database connection')
    
    args = parser.parse_args()
    
    manager = DockerDatabaseManager(logger)
    
    if args.check:
        available, error = manager.check_docker_availability()
        if available:
            print("✅ Docker is available and ready")
        else:
            print(f"❌ Docker is not available: {error}")
            sys.exit(1)
    
    elif args.start:
        success = manager.start_database_containers(args.start)
        if success:
            print("✅ Database containers started successfully")
            for db_type in args.start:
                config = manager.get_database_config(db_type)
                if config:
                    print(f"  {db_type}: {config['connection_string']}")
        else:
            print("❌ Failed to start database containers")
            sys.exit(1)
    
    elif args.stop:
        manager.stop_all_containers()
        manager.cleanup_volumes()
        print("✅ All containers stopped and cleaned up")
    
    elif args.test_connection:
        success = manager.test_database_connection(args.test_connection)
        if success:
            print(f"✅ {args.test_connection} connection successful")
        else:
            print(f"❌ {args.test_connection} connection failed")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
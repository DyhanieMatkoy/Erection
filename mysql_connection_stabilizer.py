#!/usr/bin/env python3
"""MySQL Connection Stabilizer

This module provides utilities to improve MySQL connection stability
in Docker environments and handle connection issues gracefully.
"""

import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    import pymysql
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError, DisconnectionError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    pymysql = None
    OperationalError = Exception
    DisconnectionError = Exception


class MySQLConnectionStabilizer:
    """Utilities for stabilizing MySQL connections in Docker environments"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize MySQL connection stabilizer
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        if not MYSQL_AVAILABLE:
            self.logger.warning("MySQL dependencies not available")
    
    def wait_for_mysql_ready(self, connection_string: str, max_wait_time: int = 120, check_interval: int = 2) -> bool:
        """Wait for MySQL server to be ready for connections
        
        Args:
            connection_string: MySQL connection string
            max_wait_time: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            True if MySQL is ready, False if timeout
        """
        if not MYSQL_AVAILABLE:
            self.logger.error("MySQL dependencies not available")
            return False
        
        self.logger.info(f"Waiting for MySQL to be ready (max {max_wait_time}s)...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait_time:
            attempt += 1
            try:
                # Try to create engine and connect
                engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    connect_args={
                        'connect_timeout': 10,
                        'read_timeout': 30,
                        'write_timeout': 30
                    }
                )
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        elapsed = time.time() - start_time
                        self.logger.info(f"MySQL ready after {elapsed:.1f}s ({attempt} attempts)")
                        engine.dispose()
                        return True
                
                engine.dispose()
                
            except Exception as e:
                self.logger.debug(f"MySQL not ready (attempt {attempt}): {e}")
                
            time.sleep(check_interval)
        
        self.logger.error(f"MySQL not ready after {max_wait_time}s")
        return False
    
    def test_mysql_connection_stability(self, connection_string: str, test_duration: int = 30) -> Dict[str, Any]:
        """Test MySQL connection stability over time
        
        Args:
            connection_string: MySQL connection string
            test_duration: Test duration in seconds
            
        Returns:
            Test results dictionary
        """
        if not MYSQL_AVAILABLE:
            return {'success': False, 'error': 'MySQL dependencies not available'}
        
        self.logger.info(f"Testing MySQL connection stability for {test_duration}s...")
        
        results = {
            'success': True,
            'test_duration': test_duration,
            'total_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'connection_errors': [],
            'average_connection_time': 0,
            'max_connection_time': 0,
            'min_connection_time': float('inf')
        }
        
        start_time = time.time()
        connection_times = []
        
        try:
            engine = create_engine(
                connection_string,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=1800,
                connect_args={
                    'connect_timeout': 30,
                    'read_timeout': 300,
                    'write_timeout': 300,
                    'charset': 'utf8mb4'
                }
            )
            
            while time.time() - start_time < test_duration:
                results['total_attempts'] += 1
                
                try:
                    conn_start = time.time()
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    conn_time = time.time() - conn_start
                    
                    connection_times.append(conn_time)
                    results['successful_connections'] += 1
                    results['max_connection_time'] = max(results['max_connection_time'], conn_time)
                    results['min_connection_time'] = min(results['min_connection_time'], conn_time)
                    
                except Exception as e:
                    results['failed_connections'] += 1
                    error_info = {
                        'timestamp': time.time() - start_time,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    results['connection_errors'].append(error_info)
                    self.logger.warning(f"Connection failed: {e}")
                
                time.sleep(1)  # Test every second
            
            engine.dispose()
            
            # Calculate statistics
            if connection_times:
                results['average_connection_time'] = sum(connection_times) / len(connection_times)
            else:
                results['min_connection_time'] = 0
            
            success_rate = results['successful_connections'] / results['total_attempts'] if results['total_attempts'] > 0 else 0
            results['success_rate'] = success_rate
            results['success'] = success_rate > 0.9  # 90% success rate threshold
            
            self.logger.info(f"Connection stability test completed: {success_rate:.1%} success rate")
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.error(f"Connection stability test failed: {e}")
        
        return results
    
    @contextmanager
    def robust_mysql_connection(self, connection_string: str, max_retries: int = 5):
        """Create a robust MySQL connection with automatic retry
        
        Args:
            connection_string: MySQL connection string
            max_retries: Maximum number of retry attempts
            
        Yields:
            SQLAlchemy connection
        """
        if not MYSQL_AVAILABLE:
            raise Exception("MySQL dependencies not available")
        
        engine = None
        connection = None
        
        for attempt in range(max_retries):
            try:
                if engine is None:
                    engine = create_engine(
                        connection_string,
                        pool_pre_ping=True,
                        pool_recycle=1800,
                        connect_args={
                            'connect_timeout': 60,
                            'read_timeout': 600,
                            'write_timeout': 600,
                            'charset': 'utf8mb4'
                        }
                    )
                
                connection = engine.connect()
                
                # Test connection
                connection.execute(text("SELECT 1"))
                
                yield connection
                break
                
            except (OperationalError, DisconnectionError) as e:
                if connection:
                    try:
                        connection.close()
                    except:
                        pass
                    connection = None
                
                if engine:
                    try:
                        engine.dispose()
                    except:
                        pass
                    engine = None
                
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                    self.logger.warning(f"MySQL connection failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"MySQL connection failed after {max_retries} attempts: {e}")
                    raise
            
            except Exception as e:
                if connection:
                    try:
                        connection.close()
                    except:
                        pass
                if engine:
                    try:
                        engine.dispose()
                    except:
                        pass
                raise
        
        try:
            yield connection
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    self.logger.warning(f"Error closing connection: {e}")
            if engine:
                try:
                    engine.dispose()
                except Exception as e:
                    self.logger.warning(f"Error disposing engine: {e}")
    
    def optimize_mysql_for_testing(self, connection_string: str) -> bool:
        """Apply MySQL optimizations for testing environment
        
        Args:
            connection_string: MySQL connection string
            
        Returns:
            True if optimizations applied successfully
        """
        if not MYSQL_AVAILABLE:
            self.logger.error("MySQL dependencies not available")
            return False
        
        optimizations = [
            "SET GLOBAL innodb_flush_log_at_trx_commit = 2",
            "SET GLOBAL sync_binlog = 0",
            "SET GLOBAL innodb_buffer_pool_size = 536870912",  # 512MB
            "SET GLOBAL innodb_log_file_size = 268435456",     # 256MB
            "SET GLOBAL max_connections = 1000",
            "SET GLOBAL wait_timeout = 28800",
            "SET GLOBAL interactive_timeout = 28800",
            "SET GLOBAL connect_timeout = 60",
            "SET GLOBAL lock_wait_timeout = 120"
        ]
        
        try:
            with self.robust_mysql_connection(connection_string) as conn:
                for optimization in optimizations:
                    try:
                        conn.execute(text(optimization))
                        self.logger.debug(f"Applied: {optimization}")
                    except Exception as e:
                        self.logger.warning(f"Failed to apply optimization '{optimization}': {e}")
                
                self.logger.info("MySQL optimizations applied for testing")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to apply MySQL optimizations: {e}")
            return False


def main():
    """Test MySQL connection stabilizer"""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    stabilizer = MySQLConnectionStabilizer()
    
    connection_string = "mysql+pymysql://test_user:test_password@localhost:3306/construction_test"
    
    # Wait for MySQL to be ready
    if stabilizer.wait_for_mysql_ready(connection_string):
        print("✅ MySQL is ready")
        
        # Test connection stability
        results = stabilizer.test_mysql_connection_stability(connection_string, 10)
        print(f"Connection stability: {results['success_rate']:.1%}")
        
        # Apply optimizations
        if stabilizer.optimize_mysql_for_testing(connection_string):
            print("✅ MySQL optimizations applied")
    else:
        print("❌ MySQL not ready")


if __name__ == '__main__':
    main()
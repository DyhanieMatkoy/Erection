"""Test Logging System

This module provides comprehensive logging functionality for the sync end-to-end testing system.
It supports structured logging, correlation IDs, performance metrics, and multiple output formats.
"""

import os
import json
import time
import uuid
import logging
import threading
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger_name: str
    message: str
    correlation_id: Optional[str] = None
    component: Optional[str] = None
    client_id: Optional[str] = None
    operation: Optional[str] = None
    duration: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def filter(self, record):
        """Add correlation ID to record"""
        correlation_id = getattr(self._local, 'correlation_id', None)
        record.correlation_id = correlation_id or 'no-correlation'
        return True
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread"""
        self._local.correlation_id = correlation_id
    
    def clear_correlation_id(self):
        """Clear correlation ID for current thread"""
        if hasattr(self._local, 'correlation_id'):
            delattr(self._local, 'correlation_id')


class StructuredFormatter(logging.Formatter):
    """Formatter for structured JSON logging"""
    
    def format(self, record):
        """Format record as structured JSON"""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            correlation_id=getattr(record, 'correlation_id', None),
            component=getattr(record, 'component', None),
            client_id=getattr(record, 'client_id', None),
            operation=getattr(record, 'operation', None),
            duration=getattr(record, 'duration', None),
            details=getattr(record, 'details', None)
        )
        
        return json.dumps(log_entry.to_dict(), ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """Formatter for human-readable console output"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        """Format record for human reading"""
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'no-correlation'
        
        # Truncate long correlation IDs for readability
        if record.correlation_id and len(record.correlation_id) > 8:
            record.correlation_id = record.correlation_id[:8]
        
        formatted = super().format(record)
        
        # Add additional context if available
        context_parts = []
        
        if hasattr(record, 'component') and record.component:
            context_parts.append(f"component={record.component}")
        
        if hasattr(record, 'client_id') and record.client_id:
            context_parts.append(f"client={record.client_id}")
        
        if hasattr(record, 'operation') and record.operation:
            context_parts.append(f"op={record.operation}")
        
        if hasattr(record, 'duration') and record.duration is not None:
            context_parts.append(f"duration={record.duration:.2f}s")
        
        if context_parts:
            formatted += f" [{', '.join(context_parts)}]"
        
        return formatted


class PerformanceMetricsCollector:
    """Collects and manages performance metrics during testing"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
    
    def record_metric(self, 
                     metric_type: str,
                     value: Union[float, int],
                     labels: Optional[Dict[str, str]] = None,
                     timestamp: Optional[datetime] = None):
        """Record a performance metric
        
        Args:
            metric_type: Type of metric (e.g., 'sync_duration', 'db_query_time')
            value: Metric value
            labels: Optional labels for the metric
            timestamp: Optional timestamp (defaults to now)
        """
        with self._lock:
            if metric_type not in self.metrics:
                self.metrics[metric_type] = []
            
            metric_entry = {
                'timestamp': (timestamp or datetime.now(timezone.utc)).isoformat(),
                'value': value,
                'labels': labels or {}
            }
            
            self.metrics[metric_type].append(metric_entry)
    
    def get_metrics(self, metric_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get collected metrics
        
        Args:
            metric_type: Optional specific metric type to retrieve
            
        Returns:
            Dictionary of metrics
        """
        with self._lock:
            if metric_type:
                return {metric_type: self.metrics.get(metric_type, [])}
            return self.metrics.copy()
    
    def get_metric_summary(self, metric_type: str) -> Dict[str, Any]:
        """Get summary statistics for a metric type
        
        Args:
            metric_type: Type of metric to summarize
            
        Returns:
            Summary statistics
        """
        with self._lock:
            values = [entry['value'] for entry in self.metrics.get(metric_type, [])]
            
            if not values:
                return {'count': 0}
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'total': sum(values)
            }
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        with self._lock:
            self.metrics.clear()


class TestLoggingSystem:
    """Main logging system for sync end-to-end testing"""
    
    def __init__(self, test_id: str, config: Dict[str, Any]):
        """Initialize logging system
        
        Args:
            test_id: Unique test identifier
            config: Test configuration
        """
        self.test_id = test_id
        self.config = config
        
        # Create logs directory
        self.logs_dir = Path("test_logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.correlation_filter = CorrelationIdFilter()
        self.metrics_collector = PerformanceMetricsCollector()
        
        # Setup loggers
        self.main_logger = self._setup_main_logger()
        self.structured_logger = self._setup_structured_logger()
        
        # Log files
        self.log_files = {
            'main': self.logs_dir / f"sync_test_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            'structured': self.logs_dir / f"sync_test_{test_id}_structured.jsonl",
            'performance': self.logs_dir / f"sync_test_{test_id}_performance.json"
        }
        
        self.main_logger.info(f"Logging system initialized for test {test_id}")
    
    def _setup_main_logger(self) -> logging.Logger:
        """Setup main logger with file and console handlers"""
        logger = logging.getLogger(f"sync_test_{self.test_id}")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(
            self.logs_dir / f"sync_test_{self.test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(self.correlation_filter)
        file_handler.setFormatter(HumanReadableFormatter())
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_level = logging.DEBUG if self.config.get('verbose', False) else logging.INFO
        console_handler.setLevel(console_level)
        console_handler.addFilter(self.correlation_filter)
        console_handler.setFormatter(HumanReadableFormatter())
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_structured_logger(self) -> logging.Logger:
        """Setup structured logger for JSON output"""
        logger = logging.getLogger(f"sync_test_{self.test_id}_structured")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Structured file handler
        structured_handler = logging.FileHandler(
            self.logs_dir / f"sync_test_{self.test_id}_structured.jsonl",
            encoding='utf-8'
        )
        structured_handler.setLevel(logging.DEBUG)
        structured_handler.addFilter(self.correlation_filter)
        structured_handler.setFormatter(StructuredFormatter())
        
        logger.addHandler(structured_handler)
        
        return logger
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance
        
        Args:
            name: Optional logger name suffix
            
        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"sync_test_{self.test_id}.{name}")
        return self.main_logger
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """Context manager for correlation ID
        
        Args:
            correlation_id: Optional correlation ID (generates one if None)
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())[:8]
        
        self.correlation_filter.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            self.correlation_filter.clear_correlation_id()
    
    @contextmanager
    def operation_context(self, 
                         operation: str,
                         component: Optional[str] = None,
                         client_id: Optional[str] = None,
                         correlation_id: Optional[str] = None):
        """Context manager for operation logging with timing
        
        Args:
            operation: Operation name
            component: Optional component name
            client_id: Optional client ID
            correlation_id: Optional correlation ID
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())[:8]
        
        start_time = time.time()
        
        with self.correlation_context(correlation_id):
            # Log operation start
            self.log_operation_start(operation, component, client_id)
            
            try:
                yield correlation_id
                
                # Log operation success
                duration = time.time() - start_time
                self.log_operation_end(operation, component, client_id, duration, True)
                
                # Record performance metric
                self.metrics_collector.record_metric(
                    f"{operation}_duration",
                    duration,
                    labels={
                        'component': component,
                        'client_id': client_id,
                        'status': 'success'
                    }
                )
                
            except Exception as e:
                # Log operation failure
                duration = time.time() - start_time
                self.log_operation_end(operation, component, client_id, duration, False, str(e))
                
                # Record performance metric
                self.metrics_collector.record_metric(
                    f"{operation}_duration",
                    duration,
                    labels={
                        'component': component,
                        'client_id': client_id,
                        'status': 'failed'
                    }
                )
                
                raise
    
    def log_operation_start(self, 
                           operation: str,
                           component: Optional[str] = None,
                           client_id: Optional[str] = None):
        """Log operation start"""
        extra = {
            'operation': operation,
            'component': component,
            'client_id': client_id
        }
        
        message = f"Starting operation: {operation}"
        if component:
            message += f" (component: {component})"
        if client_id:
            message += f" (client: {client_id})"
        
        self.main_logger.info(message, extra=extra)
        self.structured_logger.info(message, extra=extra)
    
    def log_operation_end(self,
                         operation: str,
                         component: Optional[str] = None,
                         client_id: Optional[str] = None,
                         duration: Optional[float] = None,
                         success: bool = True,
                         error: Optional[str] = None):
        """Log operation end"""
        extra = {
            'operation': operation,
            'component': component,
            'client_id': client_id,
            'duration': duration
        }
        
        status = "completed" if success else "failed"
        message = f"Operation {status}: {operation}"
        
        if duration is not None:
            message += f" (duration: {duration:.2f}s)"
        
        if component:
            message += f" (component: {component})"
        if client_id:
            message += f" (client: {client_id})"
        
        if error:
            message += f" (error: {error})"
            extra['details'] = {'error': error}
        
        log_level = logging.INFO if success else logging.ERROR
        self.main_logger.log(log_level, message, extra=extra)
        self.structured_logger.log(log_level, message, extra=extra)
    
    def log_database_state(self, 
                          client_id: str,
                          state_info: Dict[str, Any]):
        """Log database state information"""
        extra = {
            'component': 'database',
            'client_id': client_id,
            'operation': 'state_capture',
            'details': state_info
        }
        
        message = f"Database state captured for {client_id}: {len(state_info)} tables"
        
        self.main_logger.debug(message, extra=extra)
        self.structured_logger.info(message, extra=extra)
    
    def log_sync_progress(self,
                         client_id: str,
                         current: int,
                         total: int,
                         operation: str = "sync"):
        """Log synchronization progress"""
        extra = {
            'component': 'sync',
            'client_id': client_id,
            'operation': operation,
            'details': {
                'current': current,
                'total': total,
                'progress_percent': (current / total * 100) if total > 0 else 0
            }
        }
        
        message = f"Sync progress for {client_id}: {current}/{total} ({current/total*100:.1f}%)"
        
        self.main_logger.info(message, extra=extra)
        self.structured_logger.info(message, extra=extra)
    
    def log_performance_metric(self,
                              metric_name: str,
                              value: Union[float, int],
                              labels: Optional[Dict[str, str]] = None):
        """Log performance metric"""
        self.metrics_collector.record_metric(metric_name, value, labels)
        
        extra = {
            'component': 'performance',
            'operation': 'metric_recorded',
            'details': {
                'metric_name': metric_name,
                'value': value,
                'labels': labels or {}
            }
        }
        
        message = f"Performance metric: {metric_name} = {value}"
        if labels:
            label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
            message += f" [{label_str}]"
        
        self.main_logger.debug(message, extra=extra)
        self.structured_logger.info(message, extra=extra)
    
    def save_performance_metrics(self):
        """Save performance metrics to file"""
        try:
            metrics_data = {
                'test_id': self.test_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metrics': self.metrics_collector.get_metrics(),
                'summaries': {}
            }
            
            # Generate summaries for each metric type
            for metric_type in self.metrics_collector.metrics.keys():
                metrics_data['summaries'][metric_type] = self.metrics_collector.get_metric_summary(metric_type)
            
            with open(self.log_files['performance'], 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            self.main_logger.info(f"Performance metrics saved to {self.log_files['performance']}")
            
        except Exception as e:
            self.main_logger.error(f"Failed to save performance metrics: {e}")
    
    def get_log_files(self) -> Dict[str, Path]:
        """Get paths to log files
        
        Returns:
            Dictionary of log file paths
        """
        return self.log_files.copy()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics
        
        Returns:
            Metrics summary
        """
        summaries = {}
        for metric_type in self.metrics_collector.metrics.keys():
            summaries[metric_type] = self.metrics_collector.get_metric_summary(metric_type)
        
        return summaries
    
    def finalize_logging(self):
        """Finalize logging system and save metrics"""
        try:
            # Save performance metrics
            self.save_performance_metrics()
            
            # Log final summary
            self.main_logger.info(f"Test logging finalized for {self.test_id}")
            self.main_logger.info(f"Log files: {list(self.log_files.values())}")
            
            # Close handlers
            for handler in self.main_logger.handlers[:]:
                handler.close()
                self.main_logger.removeHandler(handler)
            
            for handler in self.structured_logger.handlers[:]:
                handler.close()
                self.structured_logger.removeHandler(handler)
            
        except Exception as e:
            print(f"Error finalizing logging: {e}")


def setup_test_logging(test_id: str, config: Dict[str, Any]) -> TestLoggingSystem:
    """Setup test logging system
    
    Args:
        test_id: Unique test identifier
        config: Test configuration
        
    Returns:
        Configured logging system
    """
    return TestLoggingSystem(test_id, config)
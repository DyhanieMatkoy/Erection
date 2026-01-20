"""Synchronization Orchestrator

This module orchestrates synchronization operations across multiple desktop clients
for the sync end-to-end testing system. It manages sync timing, progress monitoring,
and error handling.
"""

import time
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict


@dataclass
class SyncOperation:
    """Represents a synchronization operation"""
    client_id: str
    operation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed, timeout
    duration: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncProgress:
    """Represents synchronization progress"""
    client_id: str
    operation_id: str
    current_step: int
    total_steps: int
    step_description: str
    progress_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SyncProgressMonitor:
    """Monitors synchronization progress across clients"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize progress monitor
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.progress_data: Dict[str, List[SyncProgress]] = {}
        self.progress_callbacks: List[Callable[[SyncProgress], None]] = []
        self._lock = threading.Lock()
    
    def update_progress(self, 
                       client_id: str,
                       operation_id: str,
                       current_step: int,
                       total_steps: int,
                       step_description: str):
        """Update synchronization progress
        
        Args:
            client_id: Client identifier
            operation_id: Operation identifier
            current_step: Current step number
            total_steps: Total number of steps
            step_description: Description of current step
        """
        progress_percent = (current_step / total_steps * 100) if total_steps > 0 else 0
        
        progress = SyncProgress(
            client_id=client_id,
            operation_id=operation_id,
            current_step=current_step,
            total_steps=total_steps,
            step_description=step_description,
            progress_percent=progress_percent,
            timestamp=datetime.now(timezone.utc)
        )
        
        with self._lock:
            if client_id not in self.progress_data:
                self.progress_data[client_id] = []
            self.progress_data[client_id].append(progress)
        
        # Notify callbacks
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                self.logger.warning(f"Progress callback error: {e}")
        
        self.logger.debug(f"Sync progress {client_id}: {current_step}/{total_steps} - {step_description}")
    
    def get_progress(self, client_id: str) -> List[SyncProgress]:
        """Get progress history for a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of progress updates
        """
        with self._lock:
            return self.progress_data.get(client_id, []).copy()
    
    def get_latest_progress(self, client_id: str) -> Optional[SyncProgress]:
        """Get latest progress for a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Latest progress update or None
        """
        with self._lock:
            progress_list = self.progress_data.get(client_id, [])
            return progress_list[-1] if progress_list else None
    
    def add_progress_callback(self, callback: Callable[[SyncProgress], None]):
        """Add progress update callback
        
        Args:
            callback: Callback function
        """
        self.progress_callbacks.append(callback)
    
    def clear_progress(self, client_id: Optional[str] = None):
        """Clear progress data
        
        Args:
            client_id: Optional client ID to clear (clears all if None)
        """
        with self._lock:
            if client_id:
                self.progress_data.pop(client_id, None)
            else:
                self.progress_data.clear()


class SynchronizationOrchestrator:
    """Orchestrates synchronization operations across multiple desktop clients"""
    
    def __init__(self, 
                 desktop_clients: List,
                 config: Dict[str, Any],
                 logger: logging.Logger):
        """Initialize synchronization orchestrator
        
        Args:
            desktop_clients: List of TestDesktopClient instances
            config: Test configuration
            logger: Logger instance
        """
        self.desktop_clients = desktop_clients
        self.config = config
        self.logger = logger
        
        # Sync configuration
        self.sync_timeout = config.get('sync_timeout', 30)
        self.max_concurrent_syncs = config.get('max_concurrent_syncs', 3)
        self.retry_count = config.get('sync_retry_count', 3)
        self.retry_interval = config.get('sync_retry_interval', 5)
        
        # Components
        self.progress_monitor = SyncProgressMonitor(logger)
        
        # Operation tracking
        self.sync_operations: Dict[str, SyncOperation] = {}
        self.operation_counter = 0
        self._lock = threading.Lock()
        
        # Setup progress callback
        self.progress_monitor.add_progress_callback(self._on_progress_update)
        
        self.logger.info(f"Synchronization orchestrator initialized for {len(desktop_clients)} clients")
    
    def trigger_manual_sync(self, client) -> Dict[str, Any]:
        """Trigger manual synchronization on a specific client
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            Sync operation result
        """
        try:
            self.logger.info(f"Triggering manual sync on {client.client_id}")
            
            # Create sync operation
            operation_id = self._generate_operation_id()
            sync_op = SyncOperation(
                client_id=client.client_id,
                operation_id=operation_id,
                start_time=datetime.now(timezone.utc),
                status="running"
            )
            
            with self._lock:
                self.sync_operations[operation_id] = sync_op
            
            # Execute sync with monitoring
            result = self._execute_sync_with_monitoring(client, operation_id)
            
            # Update operation status
            sync_op.end_time = datetime.now(timezone.utc)
            sync_op.duration = (sync_op.end_time - sync_op.start_time).total_seconds()
            sync_op.status = "completed" if result['status'] == 'success' else "failed"
            sync_op.error = result.get('error')
            sync_op.details = result.get('details')
            
            self.logger.info(f"Manual sync on {client.client_id} {sync_op.status} in {sync_op.duration:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to trigger manual sync on {client.client_id}: {e}")
            return {
                'client_id': client.client_id,
                'status': 'failed',
                'error': str(e),
                'duration': 0
            }
    
    def trigger_parallel_sync(self, clients: Optional[List] = None) -> List[Dict[str, Any]]:
        """Trigger synchronization on multiple clients in parallel
        
        Args:
            clients: Optional list of clients (uses all if None)
            
        Returns:
            List of sync operation results
        """
        if clients is None:
            clients = self.desktop_clients
        
        self.logger.info(f"Triggering parallel sync on {len(clients)} clients")
        
        results = []
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_concurrent_syncs) as executor:
            # Submit sync tasks
            future_to_client = {
                executor.submit(self.trigger_manual_sync, client): client
                for client in clients
            }
            
            # Collect results
            for future in as_completed(future_to_client):
                client = future_to_client[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Parallel sync failed for {client.client_id}: {e}")
                    results.append({
                        'client_id': client.client_id,
                        'status': 'failed',
                        'error': str(e),
                        'duration': 0
                    })
        
        self.logger.info(f"Parallel sync completed: {len(results)} results")
        return results
    
    def trigger_sequential_sync(self, 
                               clients: Optional[List] = None,
                               delay_between_syncs: float = 0) -> List[Dict[str, Any]]:
        """Trigger synchronization on multiple clients sequentially
        
        Args:
            clients: Optional list of clients (uses all if None)
            delay_between_syncs: Delay between sync operations in seconds
            
        Returns:
            List of sync operation results
        """
        if clients is None:
            clients = self.desktop_clients
        
        self.logger.info(f"Triggering sequential sync on {len(clients)} clients")
        
        results = []
        
        for i, client in enumerate(clients):
            if i > 0 and delay_between_syncs > 0:
                self.logger.debug(f"Waiting {delay_between_syncs}s before next sync")
                time.sleep(delay_between_syncs)
            
            result = self.trigger_manual_sync(client)
            results.append(result)
            
            # Stop on first failure if configured
            if result['status'] == 'failed' and self.config.get('stop_on_first_failure', False):
                self.logger.warning(f"Stopping sequential sync due to failure on {client.client_id}")
                break
        
        self.logger.info(f"Sequential sync completed: {len(results)} results")
        return results
    
    def _execute_sync_with_monitoring(self, client, operation_id: str) -> Dict[str, Any]:
        """Execute sync operation with progress monitoring
        
        Args:
            client: TestDesktopClient instance
            operation_id: Operation identifier
            
        Returns:
            Sync operation result
        """
        try:
            # Step 1: Pre-sync validation
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 1, 5, "Validating client state"
            )
            
            if not self._validate_client_state(client):
                raise Exception("Client state validation failed")
            
            # Step 2: Prepare sync
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 2, 5, "Preparing synchronization"
            )
            
            sync_details = self._prepare_sync(client)
            
            # Step 3: Execute sync
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 3, 5, "Executing synchronization"
            )
            
            sync_result = self._execute_client_sync(client)
            
            # Step 4: Verify sync
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 4, 5, "Verifying sync results"
            )
            
            verification_result = self._verify_sync_result(client, sync_result)
            
            # Step 5: Complete
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 5, 5, "Sync completed successfully"
            )
            
            return {
                'client_id': client.client_id,
                'operation_id': operation_id,
                'status': 'success',
                'duration': sync_result.get('duration', 0),
                'data_size': sync_result.get('data_size', 0),
                'details': {
                    'sync_details': sync_details,
                    'sync_result': sync_result,
                    'verification': verification_result
                }
            }
            
        except Exception as e:
            self.progress_monitor.update_progress(
                client.client_id, operation_id, 0, 5, f"Sync failed: {str(e)}"
            )
            
            return {
                'client_id': client.client_id,
                'operation_id': operation_id,
                'status': 'failed',
                'error': str(e),
                'duration': 0
            }
    
    def _validate_client_state(self, client) -> bool:
        """Validate client state before sync
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            True if client state is valid
        """
        try:
            # Check if client is running
            if not client.is_running:
                self.logger.warning(f"Client {client.client_id} is not running")
                return False
            
            # Check if client is registered
            if not client.is_registered:
                self.logger.warning(f"Client {client.client_id} is not registered")
                return False
            
            # Check sync service
            if not client.sync_service:
                self.logger.warning(f"Client {client.client_id} sync service not available")
                return False
            
            # Check if already syncing
            if client.sync_service.is_syncing:
                self.logger.warning(f"Client {client.client_id} is already syncing")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating client state for {client.client_id}: {e}")
            return False
    
    def _prepare_sync(self, client) -> Dict[str, Any]:
        """Prepare synchronization operation
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            Sync preparation details
        """
        try:
            # Get sync status before operation
            sync_status = client.sync_service.get_sync_status()
            
            # Get pending changes count
            pending_changes = sync_status.get('pending_changes', 0)
            
            # Get network diagnostics
            network_diagnostics = client.sync_service.get_network_diagnostics()
            
            return {
                'pre_sync_status': sync_status,
                'pending_changes': pending_changes,
                'network_diagnostics': network_diagnostics,
                'preparation_time': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Error preparing sync for {client.client_id}: {e}")
            return {'error': str(e)}
    
    def _execute_client_sync(self, client) -> Dict[str, Any]:
        """Execute synchronization on client
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            Sync execution result
        """
        try:
            # Use the client's trigger_sync method
            return client.trigger_sync()
            
        except Exception as e:
            self.logger.error(f"Error executing sync on {client.client_id}: {e}")
            return {
                'client_id': client.client_id,
                'status': 'failed',
                'error': str(e),
                'duration': 0
            }
    
    def _verify_sync_result(self, client, sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify synchronization result
        
        Args:
            client: TestDesktopClient instance
            sync_result: Result from sync execution
            
        Returns:
            Verification result
        """
        try:
            verification = {
                'sync_completed': sync_result.get('status') == 'success',
                'duration_reasonable': sync_result.get('duration', 0) < self.sync_timeout,
                'no_errors': 'error' not in sync_result,
                'client_online': True,
                'verification_time': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if client is still online after sync
            if client.sync_service:
                try:
                    status = client.sync_service.get_sync_status()
                    verification['client_online'] = status.get('is_online', False)
                    verification['post_sync_status'] = status
                except Exception as e:
                    verification['client_online'] = False
                    verification['status_check_error'] = str(e)
            
            # Overall verification result
            verification['success'] = all([
                verification['sync_completed'],
                verification['duration_reasonable'],
                verification['no_errors'],
                verification['client_online']
            ])
            
            return verification
            
        except Exception as e:
            self.logger.warning(f"Error verifying sync result for {client.client_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID
        
        Returns:
            Unique operation identifier
        """
        with self._lock:
            self.operation_counter += 1
            return f"sync_op_{self.operation_counter:04d}"
    
    def _on_progress_update(self, progress: SyncProgress):
        """Handle progress updates
        
        Args:
            progress: Progress update
        """
        # Log progress updates
        self.logger.info(
            f"Sync progress {progress.client_id}: "
            f"{progress.progress_percent:.1f}% - {progress.step_description}"
        )
    
    def get_sync_operations(self) -> Dict[str, SyncOperation]:
        """Get all sync operations
        
        Returns:
            Dictionary of sync operations
        """
        with self._lock:
            return {op_id: op for op_id, op in self.sync_operations.items()}
    
    def get_operation_by_id(self, operation_id: str) -> Optional[SyncOperation]:
        """Get sync operation by ID
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Sync operation or None
        """
        with self._lock:
            return self.sync_operations.get(operation_id)
    
    def get_operations_by_client(self, client_id: str) -> List[SyncOperation]:
        """Get sync operations for a specific client
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of sync operations
        """
        with self._lock:
            return [op for op in self.sync_operations.values() if op.client_id == client_id]
    
    def get_sync_summary(self) -> Dict[str, Any]:
        """Get summary of all sync operations
        
        Returns:
            Sync operations summary
        """
        with self._lock:
            operations = list(self.sync_operations.values())
        
        if not operations:
            return {
                'total_operations': 0,
                'completed': 0,
                'failed': 0,
                'running': 0,
                'success_rate': 0.0,
                'average_duration': 0.0
            }
        
        completed_ops = [op for op in operations if op.status == 'completed']
        failed_ops = [op for op in operations if op.status == 'failed']
        running_ops = [op for op in operations if op.status == 'running']
        
        durations = [op.duration for op in operations if op.duration is not None]
        
        return {
            'total_operations': len(operations),
            'completed': len(completed_ops),
            'failed': len(failed_ops),
            'running': len(running_ops),
            'success_rate': (len(completed_ops) / len(operations) * 100) if operations else 0.0,
            'average_duration': sum(durations) / len(durations) if durations else 0.0,
            'min_duration': min(durations) if durations else 0.0,
            'max_duration': max(durations) if durations else 0.0
        }
    
    def wait_for_all_syncs(self, timeout: Optional[float] = None) -> bool:
        """Wait for all running sync operations to complete
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            True if all syncs completed, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                running_ops = [op for op in self.sync_operations.values() if op.status == 'running']
            
            if not running_ops:
                self.logger.info("All sync operations completed")
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                self.logger.warning(f"Timeout waiting for {len(running_ops)} sync operations")
                return False
            
            time.sleep(0.5)
    
    def cancel_all_syncs(self):
        """Cancel all running sync operations"""
        with self._lock:
            running_ops = [op for op in self.sync_operations.values() if op.status == 'running']
        
        for op in running_ops:
            try:
                # Find client and attempt to stop sync
                client = next((c for c in self.desktop_clients if c.client_id == op.client_id), None)
                if client and client.sync_service:
                    # Note: SyncService doesn't have a cancel method, so we just mark as failed
                    op.status = 'cancelled'
                    op.end_time = datetime.now(timezone.utc)
                    op.error = 'Cancelled by orchestrator'
                    
                    self.logger.info(f"Cancelled sync operation {op.operation_id} for {op.client_id}")
                    
            except Exception as e:
                self.logger.error(f"Error cancelling sync operation {op.operation_id}: {e}")
        
        self.logger.info(f"Cancelled {len(running_ops)} sync operations")
    
    def get_progress_monitor(self) -> SyncProgressMonitor:
        """Get progress monitor instance
        
        Returns:
            Progress monitor
        """
        return self.progress_monitor
"""Synchronization Service for Desktop Client

This module provides synchronization functionality for the desktop client,
including background sync, conflict handling, and offline queue management.
"""

import json
import logging
import threading
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from ..data.database_manager import DatabaseManager
from ..data.sync_manager import get_sync_manager
from ..data.packet_manager import PacketManager
from ..data.conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


class SyncService(QObject):
    """Synchronization service for desktop client"""
    
    # Signals
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(dict)
    sync_failed = pyqtSignal(str)
    sync_progress = pyqtSignal(int, int)  # current, total
    conflict_detected = pyqtSignal(dict)
    status_changed = pyqtSignal(str)  # online/offline/syncing
    
    def __init__(self, db_manager: DatabaseManager, server_url: str, node_code: str):
        """Initialize sync service
        
        Args:
            db_manager: Database manager instance
            server_url: Base URL of sync server
            node_code: Unique code for this client node
        """
        super().__init__()
        
        self.db_manager = db_manager
        self.server_url = server_url.rstrip('/')
        self.node_code = node_code
        self.node_id = None
        self.auth_token = None
        
        # Initialize sync components
        self.sync_manager = get_sync_manager(db_manager)
        self.packet_manager = PacketManager(self.sync_manager)
        self.conflict_resolver = ConflictResolver(self.sync_manager)
        
        # Sync state
        self.is_online = False
        self.is_syncing = False
        self.last_sync_time = None
        self.sync_interval = 300  # 5 minutes
        
        # Enhanced retry configuration
        self.base_retry_interval = 1  # Start with 1 second
        self.max_retry_interval = 300  # Maximum 5 minutes
        self.max_retries = 10  # Increased retry attempts
        self.retry_multiplier = 2  # Exponential backoff multiplier
        self.jitter_range = 0.1  # 10% jitter to avoid thundering herd
        
        # Background sync timer
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(self.sync_interval * 1000)  # Convert to milliseconds
        
        # Enhanced retry timer with exponential backoff
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._retry_sync)
        self.retry_count = 0
        self.current_retry_interval = self.base_retry_interval
        
        # Network connectivity check timer
        self.connectivity_timer = QTimer()
        self.connectivity_timer.timeout.connect(self._check_connectivity)
        self.connectivity_timer.start(30000)  # Check every 30 seconds
        
        # Status callbacks
        self.status_callbacks: List[Callable[[str], None]] = []
        
        # Initialize node registration
        # self._register_node()
    
    def _register_node(self) -> None:
        """Register this client node with the server"""
        try:
            url = f"{self.server_url}/api/sync/register"
            data = {
                "code": self.node_code,
                "name": f"Desktop Client - {self.node_code}",
                "description": "Desktop client for construction time management"
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.node_id = result['node_id']
                self.auth_token = result['auth_token']
                
                logger.info(f"Registered node: {self.node_code} -> {self.node_id}")
                
                # Update sync manager with node ID
                self.sync_manager.node_id = self.node_id
                
                # Reset retry state on successful registration
                self._reset_retry_state()
                
                # Set online status
                self._set_status("online")
                
            else:
                logger.error(f"Failed to register node: {response.status_code} - {response.text}")
                self._set_status("offline")
                self._schedule_retry("Node registration failed")
        
        except ConnectionError as e:
            logger.error(f"Connection error during node registration: {e}")
            self._set_status("offline")
            self._schedule_retry("Connection error")
        
        except Timeout as e:
            logger.error(f"Timeout during node registration: {e}")
            self._set_status("offline")
            self._schedule_retry("Request timeout")
        
        except HTTPError as e:
            logger.error(f"HTTP error during node registration: {e}")
            self._set_status("offline")
            self._schedule_retry("HTTP error")
        
        except RequestException as e:
            logger.error(f"Request error during node registration: {e}")
            self._set_status("offline")
            self._schedule_retry("Request error")
        
        except Exception as e:
            logger.error(f"Unexpected error during node registration: {e}")
            self._set_status("offline")
            self._schedule_retry("Unexpected error")
    
    def sync_now(self) -> bool:
        """Trigger immediate synchronization
        
        Returns:
            True if sync was started successfully
        """
        if self.is_syncing:
            logger.warning("Sync already in progress")
            return False
        
        if not self.node_id or not self.auth_token:
            logger.warning("Node not registered, cannot sync")
            return False
        
        if not self.is_online:
            logger.warning("Node is offline, cannot sync")
            return False
        
        # Start sync in background thread
        sync_thread = threading.Thread(target=self._perform_sync, daemon=True)
        sync_thread.start()
        
        return True
    
    def _auto_sync(self) -> None:
        """Perform automatic sync if conditions are met"""
        if (not self.is_syncing and 
            self.is_online and 
            self.node_id and 
            self.auth_token):
            
            # Check if we have pending changes
            pending_changes = len(self.sync_manager.get_pending_changes(
                self.node_id, limit=1
            ))
            
            if pending_changes > 0:
                self.sync_now()
    
    def _retry_sync(self) -> None:
        """Retry node registration or failed sync with exponential backoff"""
        if self.retry_count >= self.max_retries:
            logger.error(f"Max sync retries ({self.max_retries}) reached, giving up")
            self.retry_timer.stop()
            self._reset_retry_state()
            return
        
        self.retry_count += 1
        logger.info(f"Retrying sync (attempt {self.retry_count}/{self.max_retries})")
        
        if not self.node_id:
            # Retry node registration
            logger.info("Retrying node registration...")
            self._register_node()
        else:
            # Retry failed sync
            logger.info("Retrying synchronization...")
            self.sync_now()
        
        # If we still need to retry, schedule next attempt with exponential backoff
        if self.retry_count < self.max_retries:
            self._schedule_next_retry()
    
    def _schedule_retry(self, reason: str) -> None:
        """Schedule retry with exponential backoff
        
        Args:
            reason: Reason for the retry
        """
        if self.retry_count >= self.max_retries:
            logger.error(f"Max retries reached, not scheduling more retries. Reason: {reason}")
            return
        
        # Calculate next retry interval with exponential backoff
        self.current_retry_interval = min(
            self.base_retry_interval * (self.retry_multiplier ** self.retry_count),
            self.max_retry_interval
        )
        
        # Add jitter to avoid thundering herd
        jitter = random.uniform(-self.jitter_range, self.jitter_range)
        actual_interval = self.current_retry_interval * (1 + jitter)
        actual_interval = max(1, actual_interval)  # Minimum 1 second
        
        logger.info(f"Scheduling retry in {actual_interval:.1f} seconds (attempt {self.retry_count + 1}/{self.max_retries}). Reason: {reason}")
        
        self.retry_timer.start(int(actual_interval * 1000))
    
    def _schedule_next_retry(self) -> None:
        """Schedule next retry attempt"""
        self._schedule_retry("Previous attempt failed")
    
    def _reset_retry_state(self) -> None:
        """Reset retry state after successful operation"""
        self.retry_count = 0
        self.current_retry_interval = self.base_retry_interval
        self.retry_timer.stop()
        logger.debug("Retry state reset after successful operation")
    
    def _check_connectivity(self) -> None:
        """Check network connectivity to server"""
        if self.is_syncing:
            return  # Don't check during sync
        
        try:
            # Simple connectivity check
            url = f"{self.server_url}/api/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                if not self.is_online:
                    logger.info("Network connectivity restored")
                    self.is_online = True  # Set online status directly
                    self.status_changed.emit("online")
                    # Try to register if not registered
                    if not self.node_id:
                        self._register_node()
            else:
                if self.is_online:
                    logger.warning(f"Server returned {response.status_code}, marking as offline")
                    self.is_online = False  # Set offline status directly
                    self.status_changed.emit("offline")
        
        except (ConnectionError, Timeout, RequestException):
            if self.is_online:
                logger.warning("Network connectivity lost")
                self.is_online = False  # Set offline status directly
                self.status_changed.emit("offline")
        
        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            # Don't change status for unexpected errors
    
    def _perform_sync(self) -> None:
        """Perform synchronization with server"""
        try:
            self.is_syncing = True
            self.sync_started.emit()
            self._set_status("syncing")
            
            # Get pending packets
            packets = self.packet_manager.get_pending_packets("SERVER")  # Server node ID
            
            if not packets:
                # No changes to send, just check for incoming data
                self._check_incoming_sync()
                self._complete_sync({"processed_count": 0, "error_count": 0})
                return
            
            # Send packets and process responses
            total_processed = 0
            total_errors = 0
            
            for packet in packets:
                try:
                    result = self._send_packet(packet)
                    
                    if result['success']:
                        total_processed += result.get('processed_count', 0)
                        total_errors += result.get('error_count', 0)
                        
                        # Process response packet if any
                        if result.get('packet_data'):
                            self._process_response_packet(result['packet_data'])
                        
                        # Mark packet as sent
                        change_ids = [change.id for change in 
                                     self.sync_manager.get_pending_changes("SERVER", limit=1000)]
                        self.packet_manager.mark_packet_sent(
                            "SERVER", packet['header']['packet_no'], change_ids
                        )
                    else:
                        total_errors += 1
                        logger.error(f"Failed to send packet: {result.get('error', 'Unknown error')}")
                
                except ConnectionError as e:
                    total_errors += 1
                    logger.error(f"Connection error sending packet: {e}")
                    self._set_status("offline")
                
                except Timeout as e:
                    total_errors += 1
                    logger.error(f"Timeout sending packet: {e}")
                
                except HTTPError as e:
                    total_errors += 1
                    logger.error(f"HTTP error sending packet: {e}")
                
                except RequestException as e:
                    total_errors += 1
                    logger.error(f"Request error sending packet: {e}")
                
                except Exception as e:
                    total_errors += 1
                    logger.error(f"Unexpected error sending packet: {e}")
            
            self._complete_sync({
                "processed_count": total_processed,
                "error_count": total_errors
            })
        
        except ConnectionError as e:
            logger.error(f"Connection error during sync: {e}")
            self._set_status("offline")
            self._fail_sync(f"Connection error: {str(e)}")
        
        except Timeout as e:
            logger.error(f"Timeout during sync: {e}")
            self._fail_sync(f"Request timeout: {str(e)}")
        
        except HTTPError as e:
            logger.error(f"HTTP error during sync: {e}")
            self._fail_sync(f"HTTP error: {str(e)}")
        
        except RequestException as e:
            logger.error(f"Request error during sync: {e}")
            self._set_status("offline")
            self._fail_sync(f"Request error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during sync: {e}")
            self._fail_sync(f"Unexpected error: {str(e)}")
        
        finally:
            self.is_syncing = False
    
    def _send_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Send a packet to the server with enhanced error handling
        
        Args:
            packet: Packet data to send
            
        Returns:
            Server response
        """
        url = f"{self.server_url}/api/sync/exchange"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Compress packet
            compressed_data = self.packet_manager.compress_packet(packet)
            
            # Send request with retry logic
            response = requests.post(
                url,
                json={"packet_data": compressed_data.hex()},  # Send as hex string
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Authentication failed, try to re-register
                logger.warning("Authentication failed, attempting re-registration")
                self._register_node()
                return {"success": False, "error": "Authentication failed, re-registering"}
            elif response.status_code == 503:
                # Service unavailable, server overloaded
                logger.warning("Server unavailable (503), will retry later")
                return {"success": False, "error": "Server temporarily unavailable"}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Server error: {error_msg}")
                return {"success": False, "error": error_msg}
        
        except ConnectionError as e:
            logger.error(f"Connection error sending packet: {e}")
            self._set_status("offline")
            return {"success": False, "error": f"Connection error: {str(e)}"}
        
        except Timeout as e:
            logger.error(f"Timeout sending packet: {e}")
            return {"success": False, "error": f"Request timeout: {str(e)}"}
        
        except HTTPError as e:
            logger.error(f"HTTP error sending packet: {e}")
            return {"success": False, "error": f"HTTP error: {str(e)}"}
        
        except RequestException as e:
            logger.error(f"Request error sending packet: {e}")
            return {"success": False, "error": f"Request error: {str(e)}"}
        
        except Exception as e:
            logger.error(f"Unexpected error sending packet: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def _check_incoming_sync(self) -> None:
        """Check for incoming sync data from server with enhanced error handling"""
        try:
            url = f"{self.server_url}/api/sync/exchange"
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Send empty packet to trigger server response
            response = requests.post(
                url,
                json={"packet_data": None},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('packet_data'):
                    self._process_response_packet(result['packet_data'])
            elif response.status_code == 401:
                logger.warning("Authentication failed during incoming sync check")
                self._register_node()
            else:
                logger.warning(f"Server returned {response.status_code} during incoming sync check")
        
        except ConnectionError as e:
            logger.debug(f"Connection error checking incoming sync: {e}")
            self._set_status("offline")
        
        except Timeout as e:
            logger.debug(f"Timeout checking incoming sync: {e}")
        
        except HTTPError as e:
            logger.warning(f"HTTP error checking incoming sync: {e}")
        
        except RequestException as e:
            logger.debug(f"Request error checking incoming sync: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error checking incoming sync: {e}")
    
    def _process_response_packet(self, packet_data: Dict[str, Any]) -> None:
        """Process response packet from server
        
        Args:
            packet_data: Response packet data
        """
        try:
            # Validate packet
            is_valid, error_msg = self.packet_manager.validate_packet(packet_data)
            if not is_valid:
                logger.error(f"Invalid response packet: {error_msg}")
                return
            
            # Process packet
            result = self.sync_manager.process_sync_packet(packet_data)
            
            if result['success']:
                logger.info(f"Processed response packet: {result.get('processed_count', 0)} entities")
                
                # Check for conflicts
                if result.get('error_count', 0) > 0:
                    self._check_conflicts()
            else:
                logger.error(f"Failed to process response packet: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing response packet: {e}")
    
    def _check_conflicts(self) -> None:
        """Check for unresolved conflicts and emit signals"""
        try:
            conflicts = self.conflict_resolver.get_unresolved_conflicts()
            
            for conflict in conflicts:
                conflict_data = {
                    'id': str(conflict.id),
                    'entity_type': conflict.entity_type,
                    'entity_uuid': str(conflict.entity_uuid),
                    'arrival_time': conflict.arrival_time.isoformat(),
                    'source_node_id': str(conflict.source_node_id)
                }
                self.conflict_detected.emit(conflict_data)
        
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
    
    def _complete_sync(self, result: Dict[str, Any]) -> None:
        """Complete synchronization successfully
        
        Args:
            result: Sync result data
        """
        self.last_sync_time = datetime.now(timezone.utc)
        self._reset_retry_state()  # Reset retry state on success
        
        self.sync_completed.emit(result)
        
        # Update status based on current connectivity
        if self.is_online:
            self._set_status("online")
        
        logger.info(f"Sync completed successfully: {result}")
    
    def _fail_sync(self, error: str) -> None:
        """Fail synchronization with error and schedule retry
        
        Args:
            error: Error message
        """
        self.sync_failed.emit(error)
        
        # Determine if we should retry based on error type
        should_retry = self._should_retry_on_error(error)
        
        if should_retry and self.retry_count < self.max_retries:
            self._schedule_retry(f"Sync failed: {error}")
        else:
            if self.retry_count >= self.max_retries:
                logger.error(f"Max retries reached for sync. Last error: {error}")
                self._reset_retry_state()
            else:
                logger.info(f"Not retrying sync due to error type: {error}")
        
        logger.error(f"Sync failed: {error}")
    
    def _should_retry_on_error(self, error: str) -> bool:
        """Determine if sync should be retried based on error type
        
        Args:
            error: Error message
            
        Returns:
            True if should retry, False otherwise
        """
        error_lower = error.lower()
        
        # Don't retry on authentication errors (need manual intervention)
        if any(keyword in error_lower for keyword in ["authentication", "unauthorized", "forbidden"]):
            return False
        
        # Don't retry on most client errors (4xx except specific ones)
        if "http 4" in error_lower:
            # But do retry on these specific client errors
            retryable_4xx = ["401", "408", "429"]  # Unauthorized, Timeout, Too Many Requests
            if not any(code in error for code in retryable_4xx):
                return False
        
        # Retry on network errors, timeouts, and server errors
        retry_keywords = [
            "connection", "timeout", "network", "dns", "resolve",
            "http 5", "http 502", "http 503", "http 504",  # Server errors
            "http 408", "http 429",  # Specific client errors
            "temporarily unavailable", "service unavailable",
            "bad gateway", "gateway timeout"
        ]
        
        return any(keyword in error_lower for keyword in retry_keywords)
    
    def _set_status(self, status: str) -> None:
        """Set synchronization status and emit signal
        
        Args:
            status: New status (online/offline/syncing)
        """
        old_status = "online" if self.is_online else "offline"
        
        if status == "online":
            self.is_online = True
        elif status == "offline":
            self.is_online = False
        elif status == "syncing":
            # Don't change online status, just emit signal
            pass
        else:
            logger.warning(f"Unknown status: {status}")
            return
        
        # Emit signal if status changed
        if status != old_status:
            self.status_changed.emit(status)
            logger.info(f"Sync status changed: {old_status} -> {status}")
        
        # Call callbacks
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status with enhanced information
        
        Returns:
            Status information dictionary
        """
        pending_changes = len(self.sync_manager.get_pending_changes(
            "SERVER", limit=10000
        )) if self.node_id else 0
        
        # Determine detailed status
        if self.is_syncing:
            status = 'syncing'
        elif self.is_online and self.node_id and self.auth_token:
            status = 'online'
        elif self.node_id and self.auth_token:
            status = 'offline'  # Registered but not connected
        else:
            status = 'not_registered'  # Not registered
        
        return {
            'status': status,
            'node_code': self.node_code,
            'node_id': self.node_id,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'pending_changes': pending_changes,
            'is_registered': bool(self.node_id and self.auth_token),
            'is_online': self.is_online,
            'is_syncing': self.is_syncing,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'next_retry_in': self.retry_timer.remainingTime() / 1000 if self.retry_timer.isActive() else 0,
            'sync_interval': self.sync_interval
        }
    
    def add_status_callback(self, callback: Callable[[str], None]) -> None:
        """Add a status change callback
        
        Args:
            callback: Function to call when status changes
        """
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[str], None]) -> None:
        """Remove a status change callback
        
        Args:
            callback: Function to remove
        """
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def set_sync_interval(self, seconds: int) -> None:
        """Set automatic sync interval
        
        Args:
            seconds: Interval in seconds
        """
        self.sync_interval = max(60, seconds)  # Minimum 1 minute
        self.sync_timer.setInterval(self.sync_interval * 1000)
        logger.info(f"Set sync interval to {self.sync_interval} seconds")
    
    def get_network_diagnostics(self) -> Dict[str, Any]:
        """Get network diagnostics information
        
        Returns:
            Dictionary with network diagnostic data
        """
        diagnostics = {
            'server_url': self.server_url,
            'is_online': self.is_online,
            'is_syncing': self.is_syncing,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'current_retry_interval': self.current_retry_interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'node_registered': bool(self.node_id and self.auth_token)
        }
        
        # Test basic connectivity
        try:
            start_time = time.time()
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            diagnostics.update({
                'connectivity_test': 'success',
                'response_time_ms': round(response_time, 2),
                'server_status_code': response.status_code
            })
        except ConnectionError:
            diagnostics.update({
                'connectivity_test': 'connection_error',
                'error': 'Cannot connect to server'
            })
        except Timeout:
            diagnostics.update({
                'connectivity_test': 'timeout',
                'error': 'Server response timeout'
            })
        except Exception as e:
            diagnostics.update({
                'connectivity_test': 'error',
                'error': str(e)
            })
        
        return diagnostics
    
    def force_reconnect(self) -> bool:
        """Force reconnection to server
        
        Returns:
            True if reconnection initiated successfully
        """
        logger.info("Forcing reconnection to server")
        
        # Reset retry state
        self._reset_retry_state()
        
        # Clear authentication
        self.node_id = None
        self.auth_token = None
        
        # Set offline and try to reconnect
        self._set_status("offline")
        
        # Attempt immediate registration
        try:
            self._register_node()
            return True
        except Exception as e:
            logger.error(f"Failed to force reconnect: {e}")
            return False
    
    def resolve_conflict(self, conflict_id: str, resolution_data: Dict[str, Any]) -> bool:
        """Resolve a conflict manually
        
        Args:
            conflict_id: ID of conflict to resolve
            resolution_data: Resolved entity data
            
        Returns:
            True if resolved successfully
        """
        try:
            success = self.conflict_resolver.manually_resolve_conflict(
                conflict_id, resolution_data, "Desktop User"
            )
            
            if success:
                logger.info(f"Resolved conflict {conflict_id}")
                # Trigger sync to send resolution to server
                self.sync_now()
            
            return success
        
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_id}: {e}")
            return False
    
    def export_pending_changes(self, filename: str) -> bool:
        """Export pending changes to a file for offline transfer
        
        Args:
            filename: Output filename
            
        Returns:
            True if exported successfully
        """
        try:
            if not self.node_id:
                logger.error("Node not registered, cannot export changes")
                return False
            
            # Get pending changes
            changes = self.sync_manager.get_pending_changes("SERVER", limit=10000)
            
            # Create export data
            export_data = {
                'node_id': self.node_id,
                'node_code': self.node_code,
                'export_time': datetime.now(timezone.utc).isoformat(),
                'changes': []
            }
            
            for change in changes:
                entity_data = self.sync_manager.serialize_entity(
                    change.entity_type, change.entity_uuid
                )
                if entity_data:
                    export_data['changes'].append({
                        'entity_type': change.entity_type,
                        'entity_uuid': str(change.entity_uuid),
                        'operation': change.operation.value,
                        'data': entity_data
                    })
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(changes)} pending changes to {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting pending changes: {e}")
            return False
    
    def import_changes(self, filename: str) -> bool:
        """Import changes from a file for offline transfer
        
        Args:
            filename: Input filename
            
        Returns:
            True if imported successfully
        """
        try:
            # Read file
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if 'changes' not in import_data:
                logger.error("Invalid import file format: missing 'changes'")
                return False
            
            # Apply changes
            imported_count = 0
            error_count = 0
            
            for change_data in import_data['changes']:
                try:
                    entity_type = change_data['entity_type']
                    entity_uuid = change_data['entity_uuid']
                    operation = change_data['operation']
                    data = change_data.get('data')
                    
                    success = self.sync_manager.apply_change(
                        entity_type, entity_uuid, operation, data
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        error_count += 1
                
                except Exception as e:
                    logger.error(f"Error importing change: {e}")
                    error_count += 1
            
            logger.info(f"Imported {imported_count} changes, {error_count} errors from {filename}")
            return error_count == 0
        
        except Exception as e:
            logger.error(f"Error importing changes: {e}")
            return False
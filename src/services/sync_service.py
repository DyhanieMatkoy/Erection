"""Synchronization Service for Desktop Client

This module provides synchronization functionality for the desktop client,
including background sync, conflict handling, and offline queue management.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID

import requests
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
        self.retry_interval = 60  # 1 minute
        self.max_retries = 3
        
        # Background sync timer
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(self.sync_interval * 1000)  # Convert to milliseconds
        
        # Retry timer
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._retry_sync)
        self.retry_count = 0
        
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
                
                # Set online status
                self._set_status("online")
                
            else:
                logger.error(f"Failed to register node: {response.status_code} - {response.text}")
                self._set_status("offline")
        
        except Exception as e:
            logger.error(f"Error registering node: {e}")
            self._set_status("offline")
            # Schedule retry
            self.retry_timer.start(self.retry_interval * 1000)
    
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
        """Retry node registration or failed sync"""
        if not self.node_id:
            # Retry node registration
            self._register_node()
        elif self.retry_count < self.max_retries:
            # Retry failed sync
            self.retry_count += 1
            logger.info(f"Retrying sync (attempt {self.retry_count}/{self.max_retries})")
            self.sync_now()
        else:
            # Max retries reached, stop trying
            self.retry_timer.stop()
            self.retry_count = 0
            logger.error("Max sync retries reached, giving up")
    
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
                
                except Exception as e:
                    total_errors += 1
                    logger.error(f"Error sending packet: {e}")
            
            self._complete_sync({
                "processed_count": total_processed,
                "error_count": total_errors
            })
        
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self._fail_sync(str(e))
        
        finally:
            self.is_syncing = False
    
    def _send_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Send a packet to the server
        
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
        
        # Compress packet
        compressed_data = self.packet_manager.compress_packet(packet)
        
        # Send request
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
            self._register_node()
            return {"success": False, "error": "Authentication failed"}
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    
    def _check_incoming_sync(self) -> None:
        """Check for incoming sync data from server"""
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
        
        except Exception as e:
            logger.error(f"Error checking incoming sync: {e}")
    
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
        self.retry_count = 0
        self.retry_timer.stop()
        
        self.sync_completed.emit(result)
        self._set_status("online")
        
        logger.info(f"Sync completed: {result}")
    
    def _fail_sync(self, error: str) -> None:
        """Fail synchronization with error
        
        Args:
            error: Error message
        """
        self.sync_failed.emit(error)
        self._set_status("online")  # Still online, just sync failed
        
        # Schedule retry
        self.retry_timer.start(self.retry_interval * 1000)
        
        logger.error(f"Sync failed: {error}")
    
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
        """Get current synchronization status
        
        Returns:
            Status information dictionary
        """
        pending_changes = len(self.sync_manager.get_pending_changes(
            "SERVER", limit=10000
        )) if self.node_id else 0
        
        return {
            'status': 'syncing' if self.is_syncing else ('online' if self.is_online else 'offline'),
            'node_code': self.node_code,
            'node_id': self.node_id,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'pending_changes': pending_changes,
            'is_registered': bool(self.node_id and self.auth_token)
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
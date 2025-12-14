"""Packet Manager

This module handles packet-based data transmission with acknowledgments,
compression, and retry logic for reliable synchronization.
"""

import gzip
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from .models import SyncNode, SyncChange
from .sync_manager import SyncManager

logger = logging.getLogger(__name__)


class PacketManager:
    """Manages packet-based synchronization with acknowledgments"""
    
    def __init__(self, sync_manager: SyncManager):
        """Initialize packet manager
        
        Args:
            sync_manager: Sync manager instance
        """
        self.sync_manager = sync_manager
        self.packet_timeout = timedelta(minutes=5)  # Packet timeout
        self.max_retries = 3
        self.batch_size = 100  # Max entities per packet
    
    def create_packet(self, target_node_id: str, changes: List[SyncChange]) -> Dict[str, Any]:
        """Create a synchronization packet
        
        Args:
            target_node_id: UUID of target node
            changes: List of changes to include
            
        Returns:
            Packet data
        """
        # Get next packet number
        packet_no = self._get_next_packet_number(target_node_id)
        
        # Serialize entities
        entities = []
        for change in changes:
            entity_data = self.sync_manager.serialize_entity(change.entity_type, change.entity_uuid)
            if entity_data:
                entities.append({
                    'type': change.entity_type,
                    'uuid': str(change.entity_uuid),
                    'operation': change.operation.value,
                    'data': entity_data
                })
        
        # Get source node info
        source_node = self.sync_manager.get_node_by_id(self.sync_manager.node_id) if self.sync_manager.node_id else None
        
        packet = {
            'header': {
                'sender_node_id': self.sync_manager.node_id or 'SERVER',
                'recipient_node_id': target_node_id,
                'packet_no': packet_no,
                'ack_packet_no': self._get_last_ack_packet_no(target_node_id),
                'schema_version': '1.0.0',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'compression': 'gzip'
            },
            'body': {
                'entities': entities,
                'change_count': len(entities)
            }
        }
        
        logger.info(f"Created packet {packet_no} for {target_node_id} with {len(entities)} entities")
        return packet
    
    def compress_packet(self, packet: Dict[str, Any]) -> bytes:
        """Compress packet data
        
        Args:
            packet: Packet data
            
        Returns:
            Compressed packet bytes
        """
        json_data = json.dumps(packet, default=str, separators=(',', ':'))
        compressed = gzip.compress(json_data.encode('utf-8'))
        
        logger.debug(f"Compressed packet: {len(json_data)} -> {len(compressed)} bytes")
        return compressed
    
    def decompress_packet(self, compressed_data: bytes) -> Dict[str, Any]:
        """Decompress packet data
        
        Args:
            compressed_data: Compressed packet bytes
            
        Returns:
            Decompressed packet data
        """
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        packet = json.loads(json_data)
        
        logger.debug(f"Decompressed packet: {len(compressed_data)} -> {len(json_data)} bytes")
        return packet
    
    def validate_packet(self, packet: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate packet format and content
        
        Args:
            packet: Packet data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required header fields
            header = packet.get('header', {})
            required_fields = ['sender_node_id', 'recipient_node_id', 'packet_no', 'timestamp']
            
            for field in required_fields:
                if field not in header:
                    return False, f"Missing required header field: {field}"
            
            # Check body structure
            body = packet.get('body', {})
            if 'entities' not in body:
                return False, "Missing entities in packet body"
            
            # Validate packet number
            packet_no = header.get('packet_no')
            if not isinstance(packet_no, int) or packet_no <= 0:
                return False, "Invalid packet number"
            
            # Validate timestamp
            timestamp_str = header.get('timestamp')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Check if timestamp is reasonable (not too old or future)
                now = datetime.now(timezone.utc)
                if timestamp < now - timedelta(hours=24) or timestamp > now + timedelta(hours=1):
                    return False, "Packet timestamp is out of acceptable range"
            except ValueError:
                return False, "Invalid timestamp format"
            
            # Validate entities
            entities = body.get('entities', [])
            for entity in entities:
                if not isinstance(entity, dict):
                    return False, "Invalid entity format"
                
                required_entity_fields = ['type', 'uuid', 'operation']
                for field in required_entity_fields:
                    if field not in entity:
                        return False, f"Missing required entity field: {field}"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Error validating packet: {e}")
            return False, f"Packet validation error: {str(e)}"
    
    def process_acknowledgment(self, packet_no: int, ack_packet_no: int) -> bool:
        """Process packet acknowledgment
        
        Args:
            packet_no: Our packet number that was acknowledged
            ack_packet_no: Their highest received packet number
            
        Returns:
            True if acknowledgment was processed successfully
        """
        try:
            # Mark our packet as acknowledged
            with self.sync_manager.get_session() as session:
                # Update packet numbers for all nodes
                nodes = session.query(SyncNode).all()
                for node in nodes:
                    if node.sent_packet_no == packet_no:
                        node.sent_packet_no = ack_packet_no
                        node.last_sync_out = datetime.now(timezone.utc)
                
                session.commit()
            
            # Clean up acknowledged changes
            self._cleanup_acknowledged_changes(packet_no)
            
            logger.info(f"Processed acknowledgment: packet {packet_no} -> ack {ack_packet_no}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing acknowledgment: {e}")
            return False
    
    def get_pending_packets(self, target_node_id: str) -> List[Dict[str, Any]]:
        """Get packets that need to be sent to a node
        
        Args:
            target_node_id: UUID of target node
            
        Returns:
            List of pending packets
        """
        packets = []
        
        # Get pending changes
        changes = self.sync_manager.get_pending_changes(target_node_id, self.batch_size)
        
        if not changes:
            return packets
        
        # Create packets in batches
        for i in range(0, len(changes), self.batch_size):
            batch = changes[i:i + self.batch_size]
            packet = self.create_packet(target_node_id, batch)
            packets.append(packet)
        
        return packets
    
    def mark_packet_sent(self, target_node_id: str, packet_no: int, change_ids: List[int]) -> bool:
        """Mark a packet as sent
        
        Args:
            target_node_id: UUID of target node
            packet_no: Packet number
            change_ids: List of change IDs in the packet
            
        Returns:
            True if marked successfully
        """
        try:
            self.sync_manager.mark_changes_sent(change_ids, packet_no)
            
            # Update node's sent packet number
            with self.sync_manager.get_session() as session:
                node = session.query(SyncNode).filter(SyncNode.id == target_node_id).first()
                if node:
                    node.sent_packet_no = packet_no
                    session.commit()
            
            logger.info(f"Marked packet {packet_no} as sent to {target_node_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error marking packet as sent: {e}")
            return False
    
    def get_timeout_packets(self) -> List[Dict[str, Any]]:
        """Get packets that have timed out and need retry
        
        Returns:
            List of timeout packets
        """
        timeout_packets = []
        
        with self.sync_manager.get_session() as session:
            # Get nodes with unacknowledged packets
            nodes = session.query(SyncNode).filter(
                SyncNode.sent_packet_no.isnot(None)
            ).all()
            
            for node in nodes:
                if node.last_sync_out:
                    time_since_sync = datetime.now(timezone.utc) - node.last_sync_out
                    if time_since_sync > self.packet_timeout:
                        # Get changes for this packet
                        changes = session.query(SyncChange).filter(
                            SyncChange.node_id == node.id,
                            SyncChange.packet_no == node.sent_packet_no
                        ).all()
                        
                        if changes:
                            # Recreate packet for retry
                            packet = self.create_packet(str(node.id), changes)
                            timeout_packets.append({
                                'packet': packet,
                                'node_id': str(node.id),
                                'retry_count': 1  # TODO: Track retry count
                            })
        
        return timeout_packets
    
    def _get_next_packet_number(self, target_node_id: str) -> int:
        """Get next packet number for a target node
        
        Args:
            target_node_id: UUID of target node
            
        Returns:
            Next packet number
        """
        with self.sync_manager.get_session() as session:
            node = session.query(SyncNode).filter(SyncNode.id == target_node_id).first()
            if node and node.sent_packet_no:
                return node.sent_packet_no + 1
            else:
                return 1
    
    def _get_last_ack_packet_no(self, target_node_id: str) -> int:
        """Get last acknowledged packet number from a target node
        
        Args:
            target_node_id: UUID of target node
            
        Returns:
            Last acknowledged packet number
        """
        with self.sync_manager.get_session() as session:
            node = session.query(SyncNode).filter(SyncNode.id == target_node_id).first()
            if node:
                return node.received_packet_no or 0
            else:
                return 0
    
    def _cleanup_acknowledged_changes(self, packet_no: int) -> None:
        """Clean up changes that have been acknowledged
        
        Args:
            packet_no: Packet number that was acknowledged
        """
        try:
            with self.sync_manager.get_session() as session:
                # Delete changes with packet numbers <= acknowledged packet
                session.query(SyncChange).filter(
                    SyncChange.packet_no <= packet_no
                ).delete(synchronize_session=False)
                session.commit()
            
            logger.debug(f"Cleaned up acknowledged changes up to packet {packet_no}")
        
        except Exception as e:
            logger.error(f"Error cleaning up acknowledged changes: {e}")
    
    def get_packet_statistics(self) -> Dict[str, Any]:
        """Get packet transmission statistics
        
        Returns:
            Statistics dictionary
        """
        with self.sync_manager.get_session() as session:
            # Count pending changes by node
            pending_counts = {}
            nodes = session.query(SyncNode).all()
            
            for node in nodes:
                pending_count = session.query(SyncChange).filter(
                    SyncChange.node_id == node.id,
                    SyncChange.packet_no.is_(None)
                ).count()
                
                pending_counts[str(node.id)] = {
                    'code': node.code,
                    'name': node.name,
                    'pending_changes': pending_count,
                    'last_sync_in': node.last_sync_in.isoformat() if node.last_sync_in else None,
                    'last_sync_out': node.last_sync_out.isoformat() if node.last_sync_out else None,
                    'sent_packet_no': node.sent_packet_no,
                    'received_packet_no': node.received_packet_no
                }
            
            return {
                'total_nodes': len(nodes),
                'pending_counts': pending_counts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
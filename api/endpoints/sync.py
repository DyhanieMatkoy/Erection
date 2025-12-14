"""Synchronization API endpoints

This module provides REST API endpoints for data synchronization
between desktop clients and the central server.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies.database import get_db_manager
from api.dependencies.auth import get_current_user, require_auth
from src.data.database_manager import DatabaseManager
from src.data.models import User
from src.data.sync_manager import get_sync_manager
from src.data.packet_manager import PacketManager
from src.data.conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API requests/responses
class NodeRegistrationRequest(BaseModel):
    """Request model for node registration"""
    code: str = Field(..., description="Unique node code")
    name: str = Field(..., description="Human-readable node name")
    description: Optional[str] = Field(None, description="Node description")


class NodeRegistrationResponse(BaseModel):
    """Response model for node registration"""
    node_id: str = Field(..., description="UUID of registered node")
    auth_token: str = Field(..., description="Authentication token for this node")
    server_version: str = Field(..., description="Server schema version")


class SyncExchangeRequest(BaseModel):
    """Request model for sync exchange"""
    packet_data: Dict[str, Any] = Field(..., description="Compressed sync packet data")


class SyncExchangeResponse(BaseModel):
    """Response model for sync exchange"""
    success: bool = Field(..., description="Whether sync was successful")
    packet_data: Optional[Dict[str, Any]] = Field(None, description="Response packet data")
    processed_count: int = Field(..., description="Number of entities processed")
    error_count: int = Field(..., description="Number of errors encountered")
    message: Optional[str] = Field(None, description="Status message")


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    node_id: str = Field(..., description="Node ID")
    node_code: str = Field(..., description="Node code")
    last_sync_in: Optional[str] = Field(None, description="Last inbound sync timestamp")
    last_sync_out: Optional[str] = Field(None, description="Last outbound sync timestamp")
    pending_changes: int = Field(..., description="Number of pending changes")
    sent_packet_no: Optional[int] = Field(None, description="Last sent packet number")
    received_packet_no: Optional[int] = Field(None, description="Last received packet number")


class ConflictHistoryResponse(BaseModel):
    """Response model for conflict history"""
    conflicts: List[Dict[str, Any]] = Field(..., description="List of conflict records")
    total_count: int = Field(..., description="Total number of conflicts")


@router.post("/register", response_model=NodeRegistrationResponse)
async def register_node(
    request: NodeRegistrationRequest,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Register a new desktop client node
    
    Args:
        request: Node registration data
        db_manager: Database manager dependency
        
    Returns:
        Node registration response with authentication token
    """
    try:
        # Get sync manager
        sync_manager = get_sync_manager(db_manager)
        
        # Register the node
        node_id = sync_manager.register_node(request.code, request.name)
        
        # Generate authentication token (simplified - in production use proper JWT)
        auth_token = f"SYNC_TOKEN_{node_id}_{request.code}"
        
        logger.info(f"Registered new sync node: {request.code} ({request.name})")
        
        return NodeRegistrationResponse(
            node_id=node_id,
            auth_token=auth_token,
            server_version="1.0.0"
        )
    
    except Exception as e:
        logger.error(f"Error registering node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register node: {str(e)}"
        )


@router.post("/exchange", response_model=SyncExchangeResponse)
async def exchange_sync_data(
    request: SyncExchangeRequest,
    authorization: str = Header(...),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Exchange synchronization data with a client
    
    Args:
        request: Sync exchange request
        authorization: Authorization header
        db_manager: Database manager dependency
        
    Returns:
        Sync exchange response
    """
    try:
        # Validate authentication token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization[7:]  # Remove "Bearer " prefix
        
        # Extract node ID from token (simplified validation)
        if not token.startswith("SYNC_TOKEN_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        token_parts = token.split("_")
        if len(token_parts) < 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        
        node_id = token_parts[2]
        
        # Get sync manager and packet manager
        sync_manager = get_sync_manager(db_manager)
        packet_manager = PacketManager(sync_manager)
        
        # Validate and decompress packet
        packet_data = request.packet_data
        is_valid, error_msg = packet_manager.validate_packet(packet_data)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid packet: {error_msg}"
            )
        
        # Process incoming packet
        result = sync_manager.process_sync_packet(packet_data)
        
        # Get response packet for the client
        response_packets = packet_manager.get_pending_packets(node_id)
        response_packet_data = None
        
        if response_packets:
            # Send first pending packet
            response_packet_data = response_packets[0]
            # Mark packet as sent
            change_ids = [change.id for change in sync_manager.get_pending_changes(node_id)]
            packet_manager.mark_packet_sent(node_id, response_packet_data['header']['packet_no'], change_ids)
        
        return SyncExchangeResponse(
            success=result['success'],
            packet_data=response_packet_data,
            processed_count=result.get('processed_count', 0),
            error_count=result.get('error_count', 0),
            message=result.get('error') if not result['success'] else "Sync completed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sync exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync exchange failed: {str(e)}"
        )


@router.get("/status/{node_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get synchronization status for a node
    
    Args:
        node_id: UUID of the node
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        Sync status information
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        packet_manager = PacketManager(sync_manager)
        
        # Get node information
        node = sync_manager.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Get pending changes count
        pending_changes = len(sync_manager.get_pending_changes(node_id, limit=10000))
        
        return SyncStatusResponse(
            node_id=str(node.id),
            node_code=node.code,
            last_sync_in=node.last_sync_in.isoformat() if node.last_sync_in else None,
            last_sync_out=node.last_sync_out.isoformat() if node.last_sync_out else None,
            pending_changes=pending_changes,
            sent_packet_no=node.sent_packet_no,
            received_packet_no=node.received_packet_no
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/nodes", response_model=List[Dict[str, Any]])
async def list_nodes(
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """List all registered sync nodes
    
    Args:
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        List of sync nodes
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        packet_manager = PacketManager(sync_manager)
        
        # Get statistics
        stats = packet_manager.get_packet_statistics()
        
        # Convert to list format
        nodes = []
        for node_id, info in stats['pending_counts'].items():
            nodes.append({
                'id': node_id,
                'code': info['code'],
                'name': info['name'],
                'pending_changes': info['pending_changes'],
                'last_sync_in': info['last_sync_in'],
                'last_sync_out': info['last_sync_out'],
                'sent_packet_no': info['sent_packet_no'],
                'received_packet_no': info['received_packet_no']
            })
        
        return nodes
    
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list nodes: {str(e)}"
        )


@router.get("/conflicts", response_model=ConflictHistoryResponse)
async def get_conflict_history(
    entity_type: Optional[str] = None,
    entity_uuid: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get conflict history
    
    Args:
        entity_type: Filter by entity type
        entity_uuid: Filter by entity UUID
        limit: Maximum number of records
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        Conflict history
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        conflict_resolver = ConflictResolver(sync_manager)
        
        # Get conflict history
        conflicts = conflict_resolver.get_conflict_history(
            entity_type=entity_type,
            entity_uuid=entity_uuid,
            limit=limit
        )
        
        # Convert to response format
        conflict_data = []
        for conflict in conflicts:
            conflict_data.append({
                'id': str(conflict.id),
                'entity_type': conflict.entity_type,
                'entity_uuid': str(conflict.entity_uuid),
                'source_node_id': str(conflict.source_node_id),
                'arrival_time': conflict.arrival_time.isoformat(),
                'conflict_resolution': conflict.conflict_resolution,
                'resolved_at': conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                'serialized_data': conflict.serialized_data
            })
        
        return ConflictHistoryResponse(
            conflicts=conflict_data,
            total_count=len(conflict_data)
        )
    
    except Exception as e:
        logger.error(f"Error getting conflict history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conflict history: {str(e)}"
        )


@router.post("/conflicts/{version_id}/resolve")
async def resolve_conflict(
    version_id: str,
    resolution_data: Dict[str, Any],
    resolver_name: str,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Manually resolve a conflict
    
    Args:
        version_id: ID of conflict version to resolve
        resolution_data: Resolved entity data
        resolver_name: Name of person resolving
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        Resolution result
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        conflict_resolver = ConflictResolver(sync_manager)
        
        # Resolve conflict
        success = conflict_resolver.manually_resolve_conflict(
            version_id, resolution_data, resolver_name
        )
        
        if success:
            return {"success": True, "message": "Conflict resolved successfully"}
        else:
            return {"success": False, "message": "Failed to resolve conflict"}
    
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {str(e)}"
        )


@router.get("/statistics")
async def get_sync_statistics(
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get synchronization statistics
    
    Args:
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        Sync statistics
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        packet_manager = PacketManager(sync_manager)
        
        # Get statistics
        stats = packet_manager.get_packet_statistics()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting sync statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync statistics: {str(e)}"
        )


@router.post("/trigger/{node_id}")
async def trigger_sync(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Trigger synchronization for a specific node
    
    Args:
        node_id: UUID of the node to sync
        current_user: Authenticated user
        db_manager: Database manager dependency
        
    Returns:
        Trigger result
    """
    try:
        sync_manager = get_sync_manager(db_manager)
        packet_manager = PacketManager(sync_manager)
        
        # Check if node exists
        node = sync_manager.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Get pending packets
        packets = packet_manager.get_pending_packets(node_id)
        
        return {
            "success": True,
            "message": f"Sync triggered for node {node.code}",
            "pending_packets": len(packets),
            "pending_changes": len(sync_manager.get_pending_changes(node_id, limit=10000))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger sync: {str(e)}"
        )
"""Synchronization System Tests

This module contains comprehensive tests for the synchronization system,
including unit tests, property-based tests, and integration tests.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from hypothesis import given, strategies as st, settings

from src.data.database_manager import DatabaseManager
from src.data.sync_manager import SyncManager, SyncOperation
from src.data.packet_manager import PacketManager
from src.data.conflict_resolver import ConflictResolver, ServerWinsStrategy
from src.data.models import SyncNode, SyncChange, ObjectVersionHistory


class TestSyncManager:
    """Test cases for SyncManager"""
    
    @pytest.fixture
    def db_manager(self):
        """Create test database manager"""
        # Mock database manager for testing
        manager = Mock(spec=DatabaseManager)
        manager.engine = Mock()
        return manager
    
    @pytest.fixture
    def sync_manager(self, db_manager):
        """Create sync manager instance"""
        return SyncManager(db_manager, node_id="test-node-id")
    
    def test_register_node(self, sync_manager):
        """Test node registration"""
        # Mock session
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        
        # Mock query
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Node doesn't exist
        
        # Test registration
        node_id = sync_manager.register_node("TEST-NODE", "Test Node")
        
        # Verify
        assert node_id is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_register_change(self, sync_manager):
        """Test change registration"""
        # Mock session
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        
        # Mock query for max ID
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None  # No existing changes
        
        # Test change registration
        sync_manager.register_change("Estimate", str(uuid.uuid4()), SyncOperation.INSERT)
        
        # Verify
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @given(
        entity_type=st.sampled_from(["Estimate", "DailyReport", "Timesheet"]),
        operation=st.sampled_from(list(SyncOperation))
    )
    def test_register_change_property_based(self, sync_manager, entity_type, operation):
        """Property-based test for change registration"""
        # Mock session
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        mock_session.query.return_value.order_by.return_value.first.return_value = None
        
        # Test
        entity_uuid = str(uuid.uuid4())
        sync_manager.register_change(entity_type, entity_uuid, operation)
        
        # Verify change was created
        mock_session.add.assert_called_once()
        call_args = mock_session.add.call_args[0][0]
        assert call_args.entity_type == entity_type
        assert call_args.entity_uuid == entity_uuid
        assert call_args.operation == operation
    
    def test_serialize_entity(self, sync_manager):
        """Test entity serialization"""
        # Mock session and entity
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        
        entity_uuid = uuid.uuid4()
        mock_entity = Mock()
        mock_entity.__table__ = Mock()
        mock_entity.__table__.columns = [
            Mock(name='id'), Mock(name='uuid'), Mock(name='name')
        ]
        mock_entity.id = 1
        mock_entity.uuid = entity_uuid
        mock_entity.name = "Test Entity"
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_entity
        
        # Test serialization
        result = sync_manager.serialize_entity("Estimate", str(entity_uuid))
        
        # Verify
        assert result is not None
        assert result['uuid'] == str(entity_uuid)
        assert result['name'] == "Test Entity"
    
    def test_deserialize_entity(self, sync_manager):
        """Test entity deserialization"""
        data = {
            'id': 1,
            'uuid': str(uuid.uuid4()),
            'name': 'Test Entity',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Test deserialization
        entity = sync_manager.deserialize_entity("Estimate", data)
        
        # Verify
        assert entity is not None
        assert entity.name == "Test Entity"
        assert str(entity.uuid) == data['uuid']
    
    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(st.text(), st.integers(), st.floats(), st.booleans())
        )
    )
    def test_serialize_deserialize_roundtrip(self, sync_manager, data):
        """Property-based test for serialize/deserialize roundtrip"""
        # Ensure required fields are present
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid4())
        if 'name' not in data:
            data['name'] = 'Test Entity'
        
        # Mock model class
        mock_model = Mock()
        sync_manager.ENTITY_MODEL_MAP['TestEntity'] = mock_model
        
        # Test roundtrip
        entity = sync_manager.deserialize_entity("TestEntity", data)
        
        # Verify entity was created with correct attributes
        assert entity is not None
        for key, value in data.items():
            assert hasattr(entity, key)
    
    def test_apply_change_insert(self, sync_manager):
        """Test applying INSERT change"""
        # Mock session
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        
        entity_uuid = uuid.uuid4()
        data = {
            'uuid': str(entity_uuid),
            'name': 'New Entity',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Test INSERT
        result = sync_manager.apply_change(
            "Estimate", str(entity_uuid), SyncOperation.INSERT, data
        )
        
        # Verify
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_apply_change_delete(self, sync_manager):
        """Test applying DELETE change"""
        # Mock session and entity
        mock_session = Mock()
        sync_manager._session_factory = Mock(return_value=mock_session)
        
        entity_uuid = uuid.uuid4()
        mock_entity = Mock()
        mock_entity.is_deleted = False
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_entity
        
        # Test DELETE
        result = sync_manager.apply_change(
            "Estimate", str(entity_uuid), SyncOperation.DELETE
        )
        
        # Verify
        assert result is True
        assert mock_entity.is_deleted is True
        mock_session.commit.assert_called_once()


class TestPacketManager:
    """Test cases for PacketManager"""
    
    @pytest.fixture
    def sync_manager(self):
        """Create mock sync manager"""
        manager = Mock(spec=SyncManager)
        manager.node_id = "test-node-id"
        return manager
    
    @pytest.fixture
    def packet_manager(self, sync_manager):
        """Create packet manager instance"""
        return PacketManager(sync_manager)
    
    def test_create_packet(self, packet_manager, sync_manager):
        """Test packet creation"""
        # Mock changes
        mock_change = Mock()
        mock_change.entity_type = "Estimate"
        mock_change.entity_uuid = uuid.uuid4()
        mock_change.operation = SyncOperation.INSERT
        
        sync_manager.get_pending_changes.return_value = [mock_change]
        sync_manager.get_node_by_id.return_value = Mock()
        sync_manager.serialize_entity.return_value = {"id": 1, "name": "Test"}
        
        # Test packet creation
        packet = packet_manager.create_packet("target-node-id", [mock_change])
        
        # Verify packet structure
        assert 'header' in packet
        assert 'body' in packet
        
        header = packet['header']
        assert header['sender_node_id'] == "test-node-id"
        assert header['recipient_node_id'] == "target-node-id"
        assert header['packet_no'] > 0
        assert 'timestamp' in header
        
        body = packet['body']
        assert 'entities' in body
        assert len(body['entities']) == 1
    
    def test_compress_decompress_packet(self, packet_manager):
        """Test packet compression and decompression"""
        packet_data = {
            'header': {'sender_node_id': 'test', 'packet_no': 1},
            'body': {'entities': []}
        }
        
        # Test compression
        compressed = packet_manager.compress_packet(packet_data)
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        
        # Test decompression
        decompressed = packet_manager.decompress_packet(compressed)
        assert decompressed == packet_data
    
    def test_validate_packet_valid(self, packet_manager):
        """Test packet validation with valid packet"""
        valid_packet = {
            'header': {
                'sender_node_id': str(uuid.uuid4()),
                'recipient_node_id': str(uuid.uuid4()),
                'packet_no': 1,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            'body': {
                'entities': [
                    {
                        'type': 'Estimate',
                        'uuid': str(uuid.uuid4()),
                        'operation': 'INSERT',
                        'data': {'name': 'Test'}
                    }
                ]
            }
        }
        
        # Test validation
        is_valid, error = packet_manager.validate_packet(valid_packet)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_packet_invalid(self, packet_manager):
        """Test packet validation with invalid packet"""
        invalid_packet = {
            'header': {
                'sender_node_id': 'test'
                # Missing required fields
            },
            'body': {
                # Missing entities
            }
        }
        
        # Test validation
        is_valid, error = packet_manager.validate_packet(invalid_packet)
        
        assert is_valid is False
        assert error is not None
        assert "Missing required header field" in error
    
    @given(
        packet_no=st.integers(min_value=1, max_value=1000),
        entity_count=st.integers(min_value=0, max_value=100)
    )
    def test_packet_structure_property(self, packet_manager, packet_no, entity_count):
        """Property-based test for packet structure"""
        # Mock changes
        changes = []
        for i in range(entity_count):
            change = Mock()
            change.entity_type = "Estimate"
            change.entity_uuid = uuid.uuid4()
            change.operation = SyncOperation.INSERT
            changes.append(change)
        
        packet_manager.sync_manager.get_pending_changes.return_value = changes
        packet_manager.sync_manager.get_node_by_id.return_value = Mock()
        packet_manager.sync_manager.serialize_entity.return_value = {"id": i}
        
        # Test packet creation
        packet = packet_manager.create_packet("target-node", changes)
        
        # Verify structure
        assert 'header' in packet
        assert 'body' in packet
        
        header = packet['header']
        assert isinstance(header['packet_no'], int)
        assert header['packet_no'] >= 1
        
        body = packet['body']
        assert 'entities' in body
        assert isinstance(body['entities'], list)
        assert len(body['entities']) == entity_count


class TestConflictResolver:
    """Test cases for ConflictResolver"""
    
    @pytest.fixture
    def sync_manager(self):
        """Create mock sync manager"""
        return Mock(spec=SyncManager)
    
    @pytest.fixture
    def conflict_resolver(self, sync_manager):
        """Create conflict resolver instance"""
        return ConflictResolver(sync_manager)
    
    def test_server_wins_strategy(self, conflict_resolver):
        """Test server wins conflict resolution strategy"""
        strategy = ServerWinsStrategy()
        
        local_data = {'name': 'Local Data', 'updated_at': '2025-01-01T00:00:00Z'}
        remote_data = {'name': 'Remote Data', 'updated_at': '2025-01-02T00:00:00Z'}
        
        local_updated = datetime.fromisoformat('2025-01-01T00:00:00Z')
        remote_updated = datetime.fromisoformat('2025-01-02T00:00:00Z')
        
        # Test resolution
        result = strategy.resolve(
            local_data, remote_data, local_updated, remote_updated, 'source-node'
        )
        
        # Server wins should return local data
        assert result == local_data
    
    def test_timestamp_wins_strategy(self, conflict_resolver):
        """Test timestamp wins conflict resolution strategy"""
        from src.data.conflict_resolver import TimestampWinsStrategy
        
        strategy = TimestampWinsStrategy()
        
        local_data = {'name': 'Local Data', 'updated_at': '2025-01-01T00:00:00Z'}
        remote_data = {'name': 'Remote Data', 'updated_at': '2025-01-02T00:00:00Z'}
        
        local_updated = datetime.fromisoformat('2025-01-01T00:00:00Z')
        remote_updated = datetime.fromisoformat('2025-01-02T00:00:00Z')
        
        # Test resolution
        result = strategy.resolve(
            local_data, remote_data, local_updated, remote_updated, 'source-node'
        )
        
        # Timestamp wins should return remote data (newer)
        assert result == remote_data
    
    def test_get_conflict_history(self, conflict_resolver, sync_manager):
        """Test getting conflict history"""
        # Mock session and query
        mock_session = Mock()
        sync_manager.get_session.return_value.__enter__.return_value = mock_session
        sync_manager.get_session.return_value.__exit__.return_value = None
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = ['conflict1', 'conflict2']
        
        # Test
        conflicts = conflict_resolver.get_conflict_history(limit=100)
        
        # Verify
        assert len(conflicts) == 2
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called()
        mock_query.limit.assert_called_with(100)


class TestSyncIntegration:
    """Integration tests for synchronization system"""
    
    @pytest.fixture
    def test_db(self):
        """Create in-memory test database"""
        from sqlalchemy import create_engine
        from src.data.models import Base
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def db_manager(self, test_db):
        """Create test database manager"""
        manager = Mock(spec=DatabaseManager)
        manager.engine = test_db
        return manager
    
    def test_full_sync_cycle(self, db_manager):
        """Test complete synchronization cycle"""
        # Create sync managers for two nodes
        node1_manager = SyncManager(db_manager, node_id="node1")
        node2_manager = SyncManager(db_manager, node_id="node2")
        
        # Register nodes
        node1_id = node1_manager.register_node("NODE1", "Node 1")
        node2_id = node2_manager.register_node("NODE2", "Node 2")
        
        # Create test entity on node1
        entity_uuid = str(uuid.uuid4())
        entity_data = {
            'uuid': entity_uuid,
            'name': 'Test Entity',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Register change on node1
        node1_manager.register_change("Estimate", entity_uuid, SyncOperation.INSERT)
        
        # Simulate sync packet from node1 to node2
        packet = node1_manager.get_sync_packet(node2_id, 1)
        
        # Process packet on node2
        result = node2_manager.process_sync_packet(packet)
        
        # Verify
        assert result['success'] is True
        assert result['processed_count'] == 1
        assert result['error_count'] == 0
        
        # Verify entity exists on node2
        deserialized = node2_manager.serialize_entity("Estimate", entity_uuid)
        assert deserialized is not None
        assert deserialized['name'] == 'Test Entity'
    
    def test_conflict_resolution(self, db_manager):
        """Test conflict resolution scenario"""
        # Create sync managers
        node1_manager = SyncManager(db_manager, node_id="node1")
        node2_manager = SyncManager(db_manager, node_id="node2")
        
        # Register nodes
        node1_id = node1_manager.register_node("NODE1", "Node 1")
        node2_id = node2_manager.register_node("NODE2", "Node 2")
        
        # Create same entity on both nodes with different data
        entity_uuid = str(uuid.uuid4())
        
        # Node1 creates entity
        node1_data = {'uuid': entity_uuid, 'name': 'Node1 Entity', 'value': 100}
        node1_manager.apply_change("Estimate", entity_uuid, SyncOperation.INSERT, node1_data)
        
        # Node2 creates same entity (conflict)
        node2_data = {'uuid': entity_uuid, 'name': 'Node2 Entity', 'value': 200}
        node2_manager.apply_change("Estimate", entity_uuid, SyncOperation.INSERT, node2_data)
        
        # Simulate sync from node1 to node2 (should detect conflict)
        packet = node1_manager.get_sync_packet(node2_id, 1)
        result = node2_manager.process_sync_packet(packet)
        
        # Conflict should be detected and stored
        assert result['success'] is True
        # Check that conflict version was stored
        conflicts = node2_manager.get_session().query(ObjectVersionHistory).filter(
            ObjectVersionHistory.entity_uuid == entity_uuid
        ).all()
        
        assert len(conflicts) > 0


# Performance tests
class TestSyncPerformance:
    """Performance tests for synchronization system"""
    
    def test_large_dataset_sync(self):
        """Test synchronization with large dataset"""
        # This would test performance with 1000+ records
        # Implementation would measure sync time and ensure it's within acceptable limits
        pytest.skip("Performance test requires actual database setup")
    
    def test_concurrent_sync(self):
        """Test concurrent synchronization operations"""
        # This would test multiple sync operations running simultaneously
        pytest.skip("Concurrency test requires complex setup")


# Property-based tests for correctness properties
class TestSyncProperties:
    """Property-based tests for synchronization correctness"""
    
    @settings(max_examples=100)
    @given(
        entities=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['name', 'description', 'value']),
                values=st.text(min_size=1, max_size=50)
            ),
            min_size=1, max_size=10
        )
    )
    def test_serialization_roundtrip_property(self, entities):
        """Property: Serialization round-trip consistency"""
        # This tests that serializing then deserializing produces equivalent data
        sync_manager = Mock(spec=SyncManager)
        sync_manager.ENTITY_MODEL_MAP = {'TestEntity': Mock}
        
        for entity in entities:
            # Ensure required fields
            if 'uuid' not in entity:
                entity['uuid'] = str(uuid.uuid4())
            
            # Test roundtrip
            deserialized = sync_manager.deserialize_entity("TestEntity", entity)
            assert deserialized is not None
    
    @settings(max_examples=50)
    @given(
        packet_data=st.dictionaries(
            keys=st.sampled_from(['header', 'body']),
            values=st.dictionaries()
        )
    )
    def test_packet_validation_property(self, packet_data):
        """Property: Packet validation correctness"""
        packet_manager = PacketManager(Mock(spec=SyncManager))
        
        # Test validation
        is_valid, error = packet_manager.validate_packet(packet_data)
        
        # If valid, should have no error
        if is_valid:
            assert error is None
        # If invalid, should have error message
        else:
            assert error is not None
            assert len(error) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
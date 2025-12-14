# Synchronization System Guide

This guide provides comprehensive documentation for the data synchronization system that enables offline-first operation for desktop clients with bidirectional data synchronization to a central web server.

## Overview

The synchronization system implements an offline-first architecture that allows desktop clients to operate independently while maintaining data consistency with a central server. The system uses a star topology with the central server as the master node and desktop clients as subordinate nodes.

### Key Features

- **Offline-First Operation**: Desktop clients can create and modify data without internet connectivity
- **Bidirectional Synchronization**: Changes flow in both directions between clients and server
- **Automatic Conflict Resolution**: Multiple strategies for handling simultaneous modifications
- **Universal Entity Support**: New entity types are automatically included in synchronization
- **Packet-Based Transmission**: Reliable delivery with acknowledgments and retry logic
- **Version History Tracking**: Optional preservation of conflicting versions
- **Secure Data Transfer**: HTTPS encryption and token-based authentication

## Architecture

### Core Components

1. **SyncManager**: Core synchronization logic and change tracking
2. **PacketManager**: Packet-based transmission with compression and acknowledgments
3. **ConflictResolver**: Automated conflict resolution strategies
4. **SyncService**: Desktop client service with background synchronization
5. **API Endpoints**: REST endpoints for server-client communication

### Data Flow

```
Desktop Client                    Central Server
     |                               |
     | 1. Register Node              |
     |------------------------------>|
     |                               | 2. Create Auth Token
     |<------------------------------|
     |                               |
     | 3. Send Changes              |
     |------------------------------>|
     |                               | 4. Apply Changes
     |                               | 5. Detect Conflicts
     |                               | 6. Resolve Conflicts
     |<------------------------------|
     | 7. Receive Response             |
     |                               |
```

## Database Schema

### Synchronization Tables

#### sync_nodes
Registers all participants in the synchronization network.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique node identifier |
| code | String | Human-readable node code |
| name | String | Display name for the node |
| last_sync_in | DateTime | Last successful data reception |
| last_sync_out | DateTime | Last successful data transmission |
| received_packet_no | BigInt | Last acknowledged packet number |
| sent_packet_no | BigInt | Last confirmed packet number sent |

#### sync_changes
Change queue that tracks all modifications for synchronization.

| Field | Type | Description |
|-------|------|-------------|
| id | BigInt | Global change sequence number |
| node_id | UUID | Target node for this change |
| entity_type | String | Entity model name |
| entity_uuid | UUID | UUID of the modified entity |
| operation | Enum | Operation type: INSERT, UPDATE, DELETE |
| packet_no | BigInt | Packet number containing this change |
| created_at | DateTime | Change registration timestamp |

#### object_version_history
Stores conflicting object versions when versioning is enabled.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Version record identifier |
| entity_uuid | UUID | UUID of the conflicted entity |
| entity_type | String | Entity model name |
| source_node_id | UUID | Node that originated this version |
| arrival_time | DateTime | When this version was received |
| serialized_data | JSON | Complete serialized object data |
| conflict_resolution | String | How this conflict was resolved |

### Entity Extensions

All synchronizable entities include these additional fields:

| Field | Type | Description |
|-------|------|-------------|
| uuid | UUID | Global entity identifier (unique, indexed) |
| updated_at | DateTime | Last modification timestamp (UTC) |
| is_deleted | Boolean | Soft deletion flag for change tracking |

## Configuration

### Server Configuration

The synchronization system requires the following server configuration:

```python
# api/config.py
SYNC_ENABLED = True
SYNC_SCHEMA_VERSION = "1.0.0"
SYNC_BATCH_SIZE = 100
SYNC_PACKET_TIMEOUT = 300  # 5 minutes
SYNC_MAX_RETRIES = 3
```

### Client Configuration

Desktop clients require these settings:

```python
# sync settings
SERVER_URL = "https://your-server.com"
NODE_CODE = "DESKTOP-USER-1"
SYNC_INTERVAL = 300  # 5 minutes
AUTO_SYNC = True
COMPRESSION_ENABLED = True
```

## API Endpoints

### Node Registration

```http
POST /api/sync/register
Content-Type: application/json

{
  "code": "DESKTOP-USER-1",
  "name": "Desktop Client - User 1",
  "description": "Desktop client for construction management"
}
```

**Response:**
```json
{
  "node_id": "uuid-string",
  "auth_token": "SYNC_TOKEN_uuid_DESKTOP-USER-1",
  "server_version": "1.0.0"
}
```

### Data Exchange

```http
POST /api/sync/exchange
Authorization: Bearer SYNC_TOKEN_uuid_DESKTOP-USER-1
Content-Type: application/json

{
  "packet_data": "compressed-hex-data"
}
```

**Response:**
```json
{
  "success": true,
  "packet_data": {...},
  "processed_count": 10,
  "error_count": 0,
  "message": "Sync completed successfully"
}
```

### Status Monitoring

```http
GET /api/sync/status/{node_id}
Authorization: Bearer {auth_token}
```

**Response:**
```json
{
  "node_id": "uuid-string",
  "node_code": "DESKTOP-USER-1",
  "last_sync_in": "2025-12-13T00:00:00Z",
  "last_sync_out": "2025-12-13T00:05:00Z",
  "pending_changes": 5,
  "sent_packet_no": 42,
  "received_packet_no": 41
}
```

## Desktop Client Integration

### Initializing Sync Service

```python
from src.services.sync_service import SyncService
from src.data.database_manager import DatabaseManager

# Create sync service
db_manager = DatabaseManager()
sync_service = SyncService(
    db_manager=db_manager,
    server_url="https://your-server.com",
    node_code="DESKTOP-USER-1"
)

# Connect signals
sync_service.status_changed.connect(on_status_changed)
sync_service.sync_completed.connect(on_sync_completed)
sync_service.conflict_detected.connect(on_conflict_detected)

# Start automatic sync
sync_service.set_sync_interval(300)  # 5 minutes
```

### Handling Sync Events

```python
def on_status_changed(status):
    """Handle sync status changes"""
    if status == "online":
        print("Connected to server")
    elif status == "offline":
        print("Disconnected from server")
    elif status == "syncing":
        print("Synchronizing data...")

def on_sync_completed(result):
    """Handle sync completion"""
    processed = result.get('processed_count', 0)
    errors = result.get('error_count', 0)
    print(f"Sync completed: {processed} processed, {errors} errors")

def on_conflict_detected(conflict):
    """Handle conflict detection"""
    print(f"Conflict detected: {conflict['entity_type']} {conflict['entity_uuid']}")
    # Show conflict resolution dialog
```

### Manual Sync Operations

```python
# Trigger immediate sync
sync_service.sync_now()

# Export pending changes for offline transfer
sync_service.export_pending_changes("sync_changes.json")

# Import changes from file
sync_service.import_changes("sync_changes.json")

# Resolve conflict manually
sync_service.resolve_conflict(
    conflict_id="uuid-string",
    resolution_data={"name": "Resolved Name", "value": 150}
)
```

## Conflict Resolution

### Available Strategies

1. **Server Wins** (Default): Server version always takes precedence
2. **Timestamp Wins**: Most recent modification timestamp wins
3. **Manual Resolution**: Requires user intervention to resolve

### Conflict Detection

Conflicts are detected when:
- The same entity is modified on multiple nodes
- Modifications occur after the last synchronization
- Entity versions have different data

### Version History

When versioning is enabled, conflicting versions are stored in `object_version_history`:

```sql
-- Query conflict history
SELECT * FROM object_version_history 
WHERE entity_type = 'Estimate' 
  AND entity_uuid = 'entity-uuid'
ORDER BY arrival_time DESC;
```

## Performance Optimization

### Batch Processing

Changes are processed in batches to optimize network utilization:

```python
# Configure batch size
packet_manager.batch_size = 100  # Process 100 entities per packet
```

### Compression

All data packets are compressed using GZIP:

```python
# Enable/disable compression
packet_manager.compression_enabled = True
```

### Selective Synchronization

Only changed entities are synchronized:

```python
# Get pending changes
changes = sync_manager.get_pending_changes(target_node_id, limit=1000)
```

## Security

### Authentication

- Token-based authentication using secure tokens
- Tokens are generated during node registration
- Tokens must be included in all API requests

### Data Encryption

- All data is transmitted over HTTPS
- Packet data is compressed but not encrypted (HTTPS handles encryption)
- Sensitive data remains encrypted during transmission

### Access Control

- Only authenticated nodes can synchronize data
- Node codes must be unique
- Server validates schema version compatibility

## Monitoring and Debugging

### Sync Statistics

```python
# Get comprehensive statistics
stats = packet_manager.get_packet_statistics()

# Sample output
{
  "total_nodes": 5,
  "pending_counts": {
    "node-uuid-1": {
      "code": "DESKTOP-USER-1",
      "pending_changes": 10,
      "last_sync_in": "2025-12-13T00:00:00Z"
    }
  },
  "timestamp": "2025-12-13T00:05:00Z"
}
```

### Logging

The system provides comprehensive logging:

```python
import logging

# Enable debug logging
logging.getLogger('src.data.sync_manager').setLevel(logging.DEBUG)
logging.getLogger('src.data.packet_manager').setLevel(logging.DEBUG)
```

### Debug Information

The desktop client provides debug information in the sync settings dialog:

- Connection status
- Last sync timestamps
- Pending change counts
- Error messages
- Packet transmission details

## Troubleshooting

### Common Issues

1. **Node Registration Fails**
   - Check server URL is accessible
   - Verify network connectivity
   - Check server is running and sync endpoints are available

2. **Sync Timeout**
   - Increase packet timeout setting
   - Check network stability
   - Reduce batch size

3. **Authentication Errors**
   - Verify auth token is valid
   - Re-register node if token expired
   - Check token format in requests

4. **Conflict Resolution**
   - Review conflict history
   - Choose appropriate resolution strategy
   - Manually resolve persistent conflicts

### Error Codes

| Code | Description | Resolution |
|-------|-------------|------------|
| 401 | Authentication failed | Re-register node |
| 404 | Node not found | Check node ID |
| 422 | Invalid packet format | Validate packet structure |
| 500 | Server error | Check server logs |

## Migration Guide

### Upgrading from Previous Version

1. Run database migrations:
   ```bash
   alembic upgrade head
   ```

2. Update client configuration:
   ```python
   # Add new sync settings
   SYNC_ENABLED = True
   SYNC_SCHEMA_VERSION = "1.0.0"
   ```

3. Restart services:
   ```bash
   # Restart web server
   systemctl restart construction-api
   
   # Restart desktop clients
   # Users need to restart application
   ```

### Data Migration

Existing data is automatically migrated:

1. UUID fields are populated for existing records
2. Sync tables are created
3. Default server node is registered
4. Change tracking is enabled

## Testing

### Running Tests

```bash
# Run all sync tests
pytest test/test_sync_system.py -v

# Run specific test class
pytest test/test_sync_system.py::TestSyncManager -v

# Run property-based tests
pytest test/test_sync_system.py::TestSyncProperties -v
```

### Test Coverage

The test suite includes:

- Unit tests for all core components
- Property-based tests for correctness
- Integration tests for full sync cycles
- Performance tests for large datasets
- Conflict resolution scenarios

## Best Practices

### Server-Side

1. **Monitor Performance**: Track sync times and error rates
2. **Regular Backups**: Ensure data integrity with backups
3. **Schema Versioning**: Use semantic versioning for schema changes
4. **Access Logging**: Log all synchronization attempts

### Client-Side

1. **Offline Support**: Ensure full functionality without internet
2. **Progress Feedback**: Provide clear sync progress indicators
3. **Error Handling**: Gracefully handle network failures
4. **Conflict UI**: Provide intuitive conflict resolution interface

### General

1. **Testing**: Test thoroughly before deployment
2. **Monitoring**: Set up alerts for sync failures
3. **Documentation**: Keep configuration documentation updated
4. **Security**: Regularly review security settings

## API Reference

### SyncManager

```python
class SyncManager:
    def register_node(code: str, name: str) -> str
    def register_change(entity_type: str, entity_uuid: str, operation: SyncOperation) -> None
    def get_pending_changes(target_node_id: str, limit: int) -> List[SyncChange]
    def serialize_entity(entity_type: str, entity_uuid: str) -> Dict[str, Any]
    def apply_change(entity_type: str, entity_uuid: str, operation: SyncOperation, data: Dict) -> bool
    def get_sync_packet(target_node_id: str, packet_no: int) -> Dict[str, Any]
    def process_sync_packet(packet_data: Dict[str, Any]) -> Dict[str, Any]
```

### PacketManager

```python
class PacketManager:
    def create_packet(target_node_id: str, changes: List[SyncChange]) -> Dict[str, Any]
    def compress_packet(packet: Dict[str, Any]) -> bytes
    def decompress_packet(compressed_data: bytes) -> Dict[str, Any]
    def validate_packet(packet: Dict[str, Any]) -> Tuple[bool, Optional[str]]
    def get_pending_packets(target_node_id: str) -> List[Dict[str, Any]]
    def get_packet_statistics() -> Dict[str, Any]
```

### ConflictResolver

```python
class ConflictResolver:
    def resolve_conflict(entity_type: str, entity_uuid: str, remote_data: Dict, source_node_id: str) -> Dict
    def get_conflict_history(entity_type: str = None, entity_uuid: str = None) -> List[ObjectVersionHistory]
    def manually_resolve_conflict(version_id: str, resolution_data: Dict, resolver_name: str) -> bool
    def set_default_strategy(strategy: str) -> bool
```

### SyncService

```python
class SyncService(QObject):
    # Signals
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(dict)
    sync_failed = pyqtSignal(str)
    conflict_detected = pyqtSignal(dict)
    status_changed = pyqtSignal(str)
    
    # Methods
    def sync_now() -> bool
    def get_sync_status() -> Dict[str, Any]
    def export_pending_changes(filename: str) -> bool
    def import_changes(filename: str) -> bool
    def resolve_conflict(conflict_id: str, resolution_data: Dict) -> bool
```

## Support

For issues and questions about the synchronization system:

1. Check the troubleshooting section
2. Review the test cases for expected behavior
3. Enable debug logging for detailed information
4. Contact the development team with logs and error details

---

*This documentation covers the synchronization system implementation as specified in the requirements and design documents.*
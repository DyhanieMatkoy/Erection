# Design Document

## Overview

The Data Synchronization System implements an offline-first architecture that enables desktop clients to operate independently while maintaining data consistency with a central server. The system uses a star topology with the central server as the master node and desktop clients as subordinate nodes. The design incorporates proven distributed system patterns including change tracking, packet-based transmission with acknowledgments, and automatic conflict resolution.

## Architecture

The system follows a hub-and-spoke architecture where all synchronization flows through the central server. This design ensures data consistency and simplifies conflict resolution by maintaining a single source of truth.

### Core Components

- **Central Server (Master Node)**: Maintains the authoritative data store and coordinates all synchronization activities
- **Desktop Clients (Subordinate Nodes)**: Offline-capable applications that maintain local data copies and sync changes
- **Exchange Plan Manager**: Tracks synchronization state and manages change propagation between nodes
- **Conflict Resolution Engine**: Automatically resolves data conflicts using configurable strategies
- **Generic Serializer**: Provides universal entity serialization without entity-specific code

### Network Topology

The system uses a star topology where desktop clients communicate exclusively with the central server. Direct client-to-client synchronization is not supported, ensuring all data flows through the authoritative central node.

## Components and Interfaces

### Synchronization Engine

The core synchronization component manages the exchange of data between nodes using a packet-based protocol with acknowledgments.

**Key Interfaces:**
- `ISyncNode`: Defines node identification and state management
- `IChangeTracker`: Handles registration and queuing of data modifications
- `IConflictResolver`: Manages conflict detection and resolution strategies
- `IPacketManager`: Handles packet creation, transmission, and acknowledgment

### Change Registration System

Tracks all modifications to synchronizable entities using triggers or ORM events. Changes are queued for transmission to appropriate target nodes.

**Key Interfaces:**
- `IChangeRegistry`: Manages change registration and queuing
- `IEntityTracker`: Tracks entity modifications and deletions
- `IPacketBuilder`: Constructs synchronization packets from queued changes

### Generic Serialization Framework

Provides entity-agnostic serialization and deserialization capabilities, allowing new entity types to be added without code changes.

**Key Interfaces:**
- `IEntitySerializer`: Handles entity serialization to/from JSON
- `IEntityRegistry`: Manages mapping between entity names and model classes
- `IVersionManager`: Handles schema version compatibility checking

## Data Models

### Core Synchronization Tables

#### sync_nodes
Registers all participants in the synchronization network.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique node identifier |
| code | String | Human-readable node code (e.g., "DESKTOP-USER-1") |
| name | String | Display name for the node |
| last_sync_in | DateTime | Last successful data reception timestamp |
| last_sync_out | DateTime | Last successful data transmission timestamp |
| received_packet_no | BigInt | Last acknowledged packet number from this node |
| sent_packet_no | BigInt | Last confirmed packet number sent to this node |

#### sync_changes
Change queue that tracks all modifications for synchronization.

| Field | Type | Description |
|-------|------|-------------|
| id | BigInt | Global change sequence number |
| node_id | UUID | Target node for this change |
| entity_type | String | Entity model name (e.g., "DailyReport") |
| entity_uuid | UUID | UUID of the modified entity |
| operation | Enum | Operation type: INSERT, UPDATE, DELETE |
| packet_no | BigInt | Packet number containing this change (NULL if not sent) |
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

### Business Entity Extensions

All synchronizable entities require these additional fields:

- `uuid` (UUID, Unique, Indexed): Global entity identifier
- `updated_at` (DateTime): Last modification timestamp (UTC)
- `is_deleted` (Boolean): Soft deletion flag for change tracking

### Synchronization Protocol

The system uses HTTP POST requests with JSON payloads for all synchronization communication.

#### Message Envelope Structure

```json
{
  "header": {
    "sender_node_id": "uuid-sender",
    "recipient_node_id": "uuid-recipient", 
    "packet_no": 105,
    "ack_packet_no": 98,
    "schema_version": "1.2.0",
    "timestamp": "2025-12-12T10:30:00Z"
  },
  "body": {
    "entities": [
      {
        "type": "DailyReport",
        "uuid": "uuid-entity",
        "operation": "UPDATE",
        "data": {
          "date": "2025-12-12",
          "brigade_id": "uuid-brigade",
          "lines": []
        }
      }
    ]
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Offline operation support
*For any* supported document type and any valid operation, performing the operation while offline should succeed and queue the change for later synchronization
**Validates: Requirements 1.1, 1.4, 1.5**

Property 2: Automatic synchronization completeness
*For any* set of offline changes, reconnecting to the server should result in all changes being transmitted and acknowledged
**Validates: Requirements 1.2**

Property 3: Data integrity preservation
*For any* document with relationships, synchronization should preserve all referential integrity constraints
**Validates: Requirements 1.3, 4.5**

Property 4: Universal change tracking
*For any* entity modification on any node, the change should be registered in the change tracking system
**Validates: Requirements 2.1**

Property 5: Packet-based delivery protocol
*For any* synchronization transmission, the data should be packaged according to the packet format and require acknowledgment
**Validates: Requirements 2.2**

Property 6: Packet retention until acknowledgment
*For any* sent packet, it should remain in the transmission queue until acknowledgment is received
**Validates: Requirements 2.3**

Property 7: Retry on timeout
*For any* packet transmission that times out, the system should retry transmission
**Validates: Requirements 2.4**

Property 8: At-least-once delivery guarantee
*For any* registered change, it should be delivered at least once to the target node
**Validates: Requirements 2.5**

Property 9: Conflict detection
*For any* entity modified simultaneously on multiple nodes, conflicts should be detected during synchronization
**Validates: Requirements 3.1**

Property 10: Server-wins conflict resolution
*For any* detected conflict, the server version should be preserved by default
**Validates: Requirements 3.2, 3.5**

Property 11: Timestamp-based resolution
*For any* conflict resolution using timestamps, the change with the most recent UTC timestamp should be selected
**Validates: Requirements 3.3**

Property 12: Conflict resolution audit logging
*For any* resolved conflict, an audit log entry should be created documenting the resolution decision
**Validates: Requirements 3.4**

Property 13: UUID identification
*For any* synchronizable entity, it should have a valid UUID as its global identifier
**Validates: Requirements 4.1**

Property 14: Generic entity synchronization
*For any* entity type registered in the system, it should be automatically included in synchronization without code changes
**Validates: Requirements 4.2**

Property 15: Hierarchical data support
*For any* hierarchical entity structure, parent-child relationships should be preserved during synchronization
**Validates: Requirements 4.3**

Property 16: Serialization round-trip consistency
*For any* entity, serializing then deserializing should produce an equivalent entity
**Validates: Requirements 4.4**

Property 17: Schema version validation
*For any* synchronization attempt, schema version compatibility should be validated between nodes
**Validates: Requirements 5.1**

Property 18: Version mismatch blocking
*For any* outdated schema version, synchronization should be blocked
**Validates: Requirements 5.2**

Property 19: Version mismatch error messaging
*For any* schema version mismatch, clear error messages should be provided
**Validates: Requirements 5.3**

Property 20: Protocol version inclusion
*For any* synchronization message, schema version information should be included
**Validates: Requirements 5.4**

Property 21: Compatible version processing
*For any* compatible schema versions, synchronization should proceed normally
**Validates: Requirements 5.5**

Property 22: GZIP compression
*For any* transmitted data packet, it should be compressed using GZIP before transmission
**Validates: Requirements 6.2**

Property 23: Batch processing optimization
*For any* multiple changes, they should be transmitted in batches to optimize network utilization
**Validates: Requirements 6.3**

Property 24: Redundant transmission avoidance
*For any* acknowledged change, it should not be retransmitted
**Validates: Requirements 6.4**

Property 25: Progress feedback provision
*For any* large dataset synchronization, progress information should be provided to users
**Validates: Requirements 6.5**

Property 26: Token-based authentication
*For any* synchronization attempt, valid secure tokens should be required for authentication
**Validates: Requirements 7.1**

Property 27: HTTPS-only transmission
*For any* data transmission, only HTTPS encrypted connections should be used
**Validates: Requirements 7.2**

Property 28: Authentication failure handling
*For any* authentication failure, synchronization should be rejected and security events logged
**Validates: Requirements 7.3**

Property 29: Per-session validation
*For any* synchronization session, node certificates or tokens should be validated
**Validates: Requirements 7.4**

Property 30: Data encryption during transmission
*For any* sensitive data transmission, the data should remain encrypted throughout the process
**Validates: Requirements 7.5**

Property 31: Version history preservation
*For any* conflict when versioning is enabled, conflicting object versions should be preserved in ObjectVersionHistory
**Validates: Requirements 8.1, 8.5**

Property 32: Source node recording
*For any* stored conflicting version, the source node identifier should be recorded
**Validates: Requirements 8.2**

Property 33: Arrival timestamp recording
*For any* stored conflicting version, the arrival timestamp should be recorded
**Validates: Requirements 8.3**

Property 34: Complete field serialization
*For any* conflicting object serialization, all original field values should be preserved
**Validates: Requirements 8.4**

Property 35: File export completeness
*For any* selected pending changes, exporting to file should include all selected change data
**Validates: Requirements 9.3**

Property 36: File import correctness
*For any* valid change file, importing should correctly apply all changes from the file
**Validates: Requirements 9.4**

Property 37: Queue integrity maintenance
*For any* change queue management operation, data integrity should be maintained and corruption prevented
**Validates: Requirements 9.5**

## Error Handling

The system implements comprehensive error handling across all synchronization operations:

### Network Error Handling
- Connection timeouts trigger automatic retry with exponential backoff
- Network interruptions preserve partial synchronization state for resumption
- Invalid responses are logged and trigger fallback to previous known good state

### Data Error Handling
- Schema validation errors block synchronization and provide detailed error messages
- Serialization failures are logged with entity details for debugging
- Corrupt packets are rejected and request retransmission

### Conflict Resolution Errors
- Unresolvable conflicts are escalated to manual resolution queues
- Resolution failures preserve all conflicting versions for later analysis
- Audit trails maintain complete conflict resolution history

### Authentication and Security Errors
- Invalid tokens result in immediate session termination
- Certificate validation failures are logged as security events
- Encryption errors abort transmission and require manual intervention

## Testing Strategy

The system employs a dual testing approach combining unit tests and property-based tests to ensure comprehensive correctness validation.

### Property-Based Testing

Property-based testing will be implemented using Hypothesis for Python, configured to run a minimum of 100 iterations per property. Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format: **Feature: sync-system, Property {number}: {property_text}**

Property-based tests will verify universal properties that should hold across all inputs, including:
- Serialization round-trip consistency for all entity types
- Conflict resolution correctness under various timing scenarios
- Change tracking completeness across all supported operations
- Protocol message format compliance for all packet types

### Unit Testing

Unit tests will cover specific examples, edge cases, and integration points:
- Specific conflict resolution scenarios with known outcomes
- Error handling for various failure modes
- Authentication and security validation edge cases
- Performance benchmarks for synchronization operations

### Integration Testing

End-to-end integration tests will validate complete synchronization workflows:
- Full offline-to-online synchronization cycles
- Multi-node conflict resolution scenarios
- Schema version compatibility validation
- Security and authentication enforcement

The testing strategy ensures that unit tests catch concrete bugs while property tests verify general correctness, providing comprehensive coverage of both specific scenarios and universal system behaviors.
-- Правильные SQL схемы для sync таблиц

-- Sync Nodes
CREATE TABLE IF NOT EXISTS sync_nodes (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    last_sync_in TIMESTAMP,
    last_sync_out TIMESTAMP,
    received_packet_no INTEGER,
    sent_packet_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_nodes_code ON sync_nodes(code);

-- Sync Changes
CREATE TABLE IF NOT EXISTS sync_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT REFERENCES sync_nodes(id),
    entity_type TEXT NOT NULL,
    entity_uuid TEXT NOT NULL,
    operation TEXT NOT NULL,
    packet_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_changes_node_id ON sync_changes(node_id);
CREATE INDEX IF NOT EXISTS idx_sync_changes_packet_no ON sync_changes(packet_no);
CREATE INDEX IF NOT EXISTS idx_sync_changes_created_at ON sync_changes(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_changes_entity ON sync_changes(entity_type, entity_uuid);
CREATE INDEX IF NOT EXISTS idx_sync_changes_node_operation ON sync_changes(node_id, operation);

-- Object Version History
CREATE TABLE IF NOT EXISTS object_version_history (
    id TEXT PRIMARY KEY,
    entity_uuid TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    source_node_id TEXT REFERENCES sync_nodes(id),
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    serialized_data TEXT NOT NULL,
    conflict_resolution TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_object_version_source_node ON object_version_history(source_node_id);
CREATE INDEX IF NOT EXISTS idx_object_version_arrival_time ON object_version_history(arrival_time);
CREATE INDEX IF NOT EXISTS idx_object_version_entity ON object_version_history(entity_type, entity_uuid);
CREATE INDEX IF NOT EXISTS idx_object_version_conflict ON object_version_history(entity_type, entity_uuid, resolved_at);

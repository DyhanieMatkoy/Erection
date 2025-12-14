"""Create synchronization tables

Revision ID: 20251213_003600
Revises: 20251213_003500
Create Date: 2025-12-13 00:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mssql

# revision identifiers, used by Alembic.
revision = '20251213_003600'
down_revision = '20251213_003500'
branch_labels = None
depends_on = None


def upgrade():
    # Import UUID type for different databases
    if op.get_bind().dialect.name == 'postgresql':
        uuid_type = postgresql.UUID
    elif op.get_bind().dialect.name == 'mssql':
        uuid_type = mssql.UNIQUEIDENTIFIER
    else:
        uuid_type = sa.String(36)

    # Create sync_nodes table
    op.create_table('sync_nodes',
        sa.Column('id', uuid_type(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('last_sync_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_packet_no', sa.BigInteger(), nullable=True),
        sa.Column('sent_packet_no', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_sync_nodes_code', 'sync_nodes', ['code'])

    # Create sync_changes table
    op.create_table('sync_changes',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('node_id', uuid_type(), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_uuid', uuid_type(), nullable=False),
        sa.Column('operation', sa.Enum('INSERT', 'UPDATE', 'DELETE', name='sync_operation'), nullable=False),
        sa.Column('packet_no', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_changes_node_id', 'sync_changes', ['node_id'])
    op.create_index('idx_sync_changes_entity', 'sync_changes', ['entity_type', 'entity_uuid'])
    op.create_index('idx_sync_changes_packet_no', 'sync_changes', ['packet_no'])
    op.create_index('idx_sync_changes_created_at', 'sync_changes', ['created_at'])

    # Create object_version_history table
    op.create_table('object_version_history',
        sa.Column('id', uuid_type(), nullable=False),
        sa.Column('entity_uuid', uuid_type(), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('source_node_id', uuid_type(), nullable=False),
        sa.Column('arrival_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('serialized_data', sa.JSON(), nullable=False),
        sa.Column('conflict_resolution', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_object_version_entity', 'object_version_history', ['entity_type', 'entity_uuid'])
    op.create_index('idx_object_version_source_node', 'object_version_history', ['source_node_id'])
    op.create_index('idx_object_version_arrival_time', 'object_version_history', ['arrival_time'])

    # Create sequence for sync_changes.id
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("CREATE SEQUENCE sync_changes_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1")
        op.execute("ALTER TABLE sync_changes ALTER COLUMN id SET DEFAULT nextval('sync_changes_id_seq')")
        op.execute("ALTER SEQUENCE sync_changes_id_seq OWNED BY sync_changes.id")
    elif op.get_bind().dialect.name == 'mssql':
        op.execute("CREATE SEQUENCE sync_changes_id_seq AS BIGINT START WITH 1 INCREMENT BY 1")
        op.execute("ALTER TABLE sync_changes ADD CONSTRAINT DF_sync_changes_id DEFAULT (NEXT VALUE FOR sync_changes_id_seq) FOR id")

    # Insert default server node
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("INSERT INTO sync_nodes (id, code, name) VALUES (gen_random_uuid(), 'SERVER', 'Central Server')")
    elif op.get_bind().dialect.name == 'mssql':
        op.execute("INSERT INTO sync_nodes (id, code, name) VALUES (NEWID(), 'SERVER', 'Central Server')")
    else:
        import uuid
        op.execute(f"INSERT INTO sync_nodes (id, code, name) VALUES ('{uuid.uuid4()}', 'SERVER', 'Central Server')")


def downgrade():
    # Drop tables in reverse order
    op.drop_table('object_version_history')
    op.drop_table('sync_changes')
    op.drop_table('sync_nodes')

    # Drop sequence if exists
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP SEQUENCE IF EXISTS sync_changes_id_seq")
    elif op.get_bind().dialect.name == 'mssql':
        op.execute("DROP SEQUENCE IF EXISTS sync_changes_id_seq")
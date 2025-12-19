"""Add sync fields (UUID, updated_at, is_deleted) to all tables

Revision ID: 20251217_000001
Revises: 50fb17bd38f9
Create Date: 2025-12-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid
import sys
import os

# revision identifiers, used by Alembic.
revision = '20251217000001'
down_revision = '50fb17bd38f9'
branch_labels = None
depends_on = None

tables_standard = [
    'daily_reports', 'daily_report_lines', 'estimates', 'estimate_lines',
    'timesheets', 'timesheet_lines', 'works',
    'materials', 'cost_items', 'units', 'persons', 'organizations',
    'counterparties', 'objects'
]

def upgrade():
    connection = op.get_bind()
    
    # 1. Handle standard tables
    for table in tables_standard:
        # Add columns as nullable first
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column('uuid', sa.String(36), nullable=True))
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('0'), nullable=False))

        # Populate UUIDs
        records = connection.execute(sa.text(f"SELECT id FROM {table}")).fetchall()
        for record in records:
            new_uuid = str(uuid.uuid4())
            connection.execute(sa.text(f"UPDATE {table} SET uuid = '{new_uuid}' WHERE id = {record[0]}"))
            
        # Alter UUID to be non-nullable and add index
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column('uuid', nullable=False, existing_type=sa.String(36))
            batch_op.create_index(f'idx_{table}_uuid', ['uuid'], unique=True)

    # 2. Handle work_specifications manually (due to Computed column issues in batch mode)
    # Rename existing table
    op.rename_table('work_specifications', 'work_specifications_old')
    
    # Step 1: Create temp table with UUID nullable
    op.execute("""
        CREATE TABLE work_specifications_temp (
            id INTEGER NOT NULL,
            work_id INTEGER NOT NULL,
            component_type VARCHAR(20) NOT NULL,
            component_name VARCHAR(500) NOT NULL,
            unit_id INTEGER,
            consumption_rate DECIMAL(15, 6) DEFAULT '0' NOT NULL,
            unit_price DECIMAL(15, 2) DEFAULT '0' NOT NULL,
            total_cost DECIMAL(15, 2) GENERATED ALWAYS AS (consumption_rate * unit_price) STORED,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            marked_for_deletion BOOLEAN DEFAULT '0', 
            material_id INTEGER,
            uuid VARCHAR(36),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(unit_id) REFERENCES units (id),
            FOREIGN KEY(work_id) REFERENCES works (id) ON DELETE CASCADE
        )
    """)
    
    # Step 2: Copy data from old table to temp table (excluding total_cost)
    op.execute("""
        INSERT INTO work_specifications_temp (
            id, work_id, component_type, component_name, unit_id, material_id,
            consumption_rate, unit_price, created_at, modified_at, marked_for_deletion
        )
        SELECT 
            id, work_id, component_type, component_name, unit_id, material_id,
            consumption_rate, unit_price, created_at, modified_at, marked_for_deletion
        FROM work_specifications_old
    """)
    
    # Step 3: Populate UUIDs
    records = connection.execute(sa.text("SELECT id FROM work_specifications_temp")).fetchall()
    for record in records:
        new_uuid = str(uuid.uuid4())
        connection.execute(sa.text(f"UPDATE work_specifications_temp SET uuid = '{new_uuid}' WHERE id = {record[0]}"))
        
    # Step 4: Create final table with UUID NOT NULL
    op.execute("""
        CREATE TABLE work_specifications (
            id INTEGER NOT NULL,
            work_id INTEGER NOT NULL,
            component_type VARCHAR(20) NOT NULL,
            component_name VARCHAR(500) NOT NULL,
            unit_id INTEGER,
            consumption_rate DECIMAL(15, 6) DEFAULT '0' NOT NULL,
            unit_price DECIMAL(15, 2) DEFAULT '0' NOT NULL,
            total_cost DECIMAL(15, 2) GENERATED ALWAYS AS (consumption_rate * unit_price) STORED,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            marked_for_deletion BOOLEAN DEFAULT '0', 
            material_id INTEGER,
            uuid VARCHAR(36) NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(unit_id) REFERENCES units (id),
            FOREIGN KEY(work_id) REFERENCES works (id) ON DELETE CASCADE
        )
    """)
    
    # Step 5: Copy data from temp to final
    op.execute("""
        INSERT INTO work_specifications (
            id, work_id, component_type, component_name, unit_id, material_id,
            consumption_rate, unit_price, created_at, modified_at, marked_for_deletion,
            uuid, updated_at, is_deleted
        )
        SELECT 
            id, work_id, component_type, component_name, unit_id, material_id,
            consumption_rate, unit_price, created_at, modified_at, marked_for_deletion,
            uuid, updated_at, is_deleted
        FROM work_specifications_temp
    """)
    
    # Step 6: Drop old and temp tables
    op.drop_table('work_specifications_old')
    op.drop_table('work_specifications_temp')
    
    # Step 7: Create Index
    op.create_index('idx_work_specifications_uuid', 'work_specifications', ['uuid'], unique=True)


def downgrade():
    tables = tables_standard
    for table in tables:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_index(f'idx_{table}_uuid')
            batch_op.drop_column('is_deleted')
            batch_op.drop_column('updated_at')
            batch_op.drop_column('uuid')
            
    # Downgrade work_specifications manually would be complex, skipping for now as per previous scripts
    # But for completeness:
    op.drop_index('idx_work_specifications_uuid', table_name='work_specifications')
    with op.batch_alter_table('work_specifications') as batch_op:
        batch_op.drop_column('is_deleted')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('uuid')

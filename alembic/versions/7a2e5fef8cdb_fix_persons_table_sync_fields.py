"""fix_persons_table_sync_fields

Revision ID: 7a2e5fef8cdb
Revises: 08e1d80543bb
Create Date: 2026-01-27 22:38:19.971232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a2e5fef8cdb'
down_revision: Union[str, Sequence[str], None] = '08e1d80543bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix persons table sync fields."""
    
    # Check if persons table needs fixing
    connection = op.get_bind()
    
    try:
        # Check if updated_at column exists
        result = connection.execute(sa.text("PRAGMA table_info(persons)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'updated_at' not in columns:
            # Recreate persons table with all sync fields
            _recreate_persons_table_complete()
        
    except Exception as e:
        print(f"Warning: Could not fix persons table: {e}")


def downgrade() -> None:
    """Downgrade persons table."""
    pass  # We don't want to break the persons table


def _recreate_persons_table_complete():
    """Recreate persons table with complete sync fields."""
    
    connection = op.get_bind()
    
    # Create new table with all fields including sync fields
    op.create_table('persons_temp',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('full_name', sa.Text, nullable=False),
        sa.Column('position', sa.Text),
        sa.Column('phone', sa.Text),
        sa.Column('user_id', sa.Integer),
        sa.Column('parent_id', sa.Integer),
        sa.Column('marked_for_deletion', sa.Integer, server_default='0'),
        sa.Column('is_group', sa.Integer, server_default='0'),
        sa.Column('hourly_rate', sa.Float, server_default='0'),
        # Complete sync fields
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='0')
    )
    
    # Copy data from old table, generating missing fields
    connection.execute(sa.text("""
        INSERT INTO persons_temp (
            id, full_name, position, phone, user_id, parent_id, 
            marked_for_deletion, is_group, hourly_rate, uuid, updated_at, is_deleted
        )
        SELECT 
            id, full_name, position, phone, user_id, parent_id,
            marked_for_deletion, is_group, hourly_rate,
            COALESCE(uuid, (
                lower(hex(randomblob(4))) || '-' || 
                lower(hex(randomblob(2))) || '-4' || 
                substr(lower(hex(randomblob(2))),2) || '-' || 
                substr('89ab',abs(random()) % 4 + 1, 1) || 
                substr(lower(hex(randomblob(2))),2) || '-' || 
                lower(hex(randomblob(6)))
            )) as uuid,
            CURRENT_TIMESTAMP as updated_at,
            COALESCE(is_deleted, 0) as is_deleted
        FROM persons
    """))
    
    # Drop old table and rename new one
    op.drop_table('persons')
    op.rename_table('persons_temp', 'persons')
    
    # Create indexes for sync fields
    try:
        op.create_index('idx_persons_uuid', 'persons', ['uuid'])
        op.create_index('idx_persons_updated_at', 'persons', ['updated_at'])
        op.create_index('idx_persons_is_deleted', 'persons', ['is_deleted'])
    except Exception:
        pass  # Indexes might already exist

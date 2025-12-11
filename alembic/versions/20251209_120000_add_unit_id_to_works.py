"""Add unit_id to works table

Revision ID: 20251209_120000
Revises: 20251209_100000
Create Date: 2025-12-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251209_120000'
down_revision: Union[str, Sequence[str], None] = '20251209_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection to check if column exists
    conn = op.get_bind()
    
    # Check if unit_id column exists in works
    result = conn.execute(sa.text("PRAGMA table_info(works)"))
    works_columns = [row[1] for row in result.fetchall()]
    
    if 'unit_id' not in works_columns:
        # Add unit_id column
        op.add_column('works', sa.Column('unit_id', sa.Integer(), nullable=True))
        
        # Add foreign key (SQLite doesn't support adding FK constraints to existing tables,
        # so we rely on the model definition)
        
        # Migrate existing units to unit_id
        op.execute("""
            UPDATE works
            SET unit_id = (SELECT id FROM units WHERE units.name = works.unit)
            WHERE works.unit IS NOT NULL AND works.unit != ''
        """)
    
    # Check if created_at and modified_at exist
    # For SQLite, we need to add columns without server_default first, then update
    if 'created_at' not in works_columns:
        op.add_column('works', sa.Column('created_at', sa.DateTime(), nullable=True))
        # Set default value for existing rows
        op.execute("UPDATE works SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    
    if 'modified_at' not in works_columns:
        op.add_column('works', sa.Column('modified_at', sa.DateTime(), nullable=True))
        # Set default value for existing rows
        op.execute("UPDATE works SET modified_at = CURRENT_TIMESTAMP WHERE modified_at IS NULL")


def downgrade() -> None:
    # Remove columns
    op.drop_column('works', 'modified_at')
    op.drop_column('works', 'created_at')
    op.drop_column('works', 'unit_id')

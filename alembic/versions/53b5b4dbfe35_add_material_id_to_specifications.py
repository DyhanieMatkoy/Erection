"""add_material_id_to_specifications

Revision ID: 53b5b4dbfe35
Revises: 5dc09ae7800b
Create Date: 2025-12-11 01:25:39.098348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53b5b4dbfe35'
down_revision: Union[str, Sequence[str], None] = '5dc09ae7800b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use standard add_column which works in SQLite.
    # We skip creating the foreign key constraint because it requires batch mode,
    # and batch mode fails due to reflection issues with the 'total_cost' Computed column.
    op.add_column('work_specifications', sa.Column('material_id', sa.Integer(), nullable=True))
    op.create_index('idx_work_specifications_material_id', 'work_specifications', ['material_id'], unique=False)


def downgrade() -> None:
    # Downgrade requires batch mode to drop column in SQLite.
    # This might fail due to the same Computed column issue.
    with op.batch_alter_table('work_specifications', schema=None) as batch_op:
        batch_op.drop_index('idx_work_specifications_material_id')
        batch_op.drop_column('material_id')

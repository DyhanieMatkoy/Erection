"""add_work_specifications

Revision ID: 5dc09ae7800b
Revises: 20251209_120000
Create Date: 2025-12-11 00:32:22.085111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dc09ae7800b'
down_revision: Union[str, Sequence[str], None] = '20251209_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create work_specifications table
    op.create_table('work_specifications',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('work_id', sa.Integer(), nullable=False),
    sa.Column('component_type', sa.String(length=20), nullable=False),
    sa.Column('component_name', sa.String(length=500), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('consumption_rate', sa.DECIMAL(precision=15, scale=6), nullable=False, server_default='0'),
    sa.Column('unit_price', sa.DECIMAL(precision=15, scale=2), nullable=False, server_default='0'),
    sa.Column('total_cost', sa.DECIMAL(precision=15, scale=2), sa.Computed('consumption_rate * unit_price', persisted=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    sa.Column('marked_for_deletion', sa.Boolean(), server_default='0', nullable=True),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_work_specifications_component_type', 'work_specifications', ['component_type'], unique=False)
    op.create_index('idx_work_specifications_work_id', 'work_specifications', ['work_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_work_specifications_work_id', table_name='work_specifications')
    op.drop_index('idx_work_specifications_component_type', table_name='work_specifications')
    op.drop_table('work_specifications')

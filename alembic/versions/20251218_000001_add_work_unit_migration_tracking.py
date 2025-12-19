"""Add work unit migration tracking table

Revision ID: 20251218_000001
Revises: 20251217_000001
Create Date: 2025-12-18 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251218000001'
down_revision: Union[str, Sequence[str], None] = '20251217000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create work_unit_migration table
    op.create_table('work_unit_migration',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('legacy_unit', sa.String(50), nullable=True),
        sa.Column('matched_unit_id', sa.Integer(), nullable=True),
        sa.Column('migration_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('manual_review_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.ForeignKeyConstraint(['matched_unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('work_id')
    )
    
    # Create indexes
    op.create_index('idx_work_unit_migration_status', 'work_unit_migration', ['migration_status'])
    op.create_index('idx_work_unit_migration_legacy_unit', 'work_unit_migration', ['legacy_unit'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_work_unit_migration_legacy_unit', table_name='work_unit_migration')
    op.drop_index('idx_work_unit_migration_status', table_name='work_unit_migration')
    
    # Drop table
    op.drop_table('work_unit_migration')
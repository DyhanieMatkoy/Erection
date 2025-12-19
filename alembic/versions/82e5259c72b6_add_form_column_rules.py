"""add_form_column_rules

Revision ID: 82e5259c72b6
Revises: 313043d00dbc
Create Date: 2025-12-17 16:27:06.609705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82e5259c72b6'
down_revision: Union[str, Sequence[str], None] = '313043d00dbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('form_column_rules',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('form_id', sa.String(length=100), nullable=False),
    sa.Column('column_id', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), nullable=True),
    sa.Column('is_restricted', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('form_id', 'column_id', 'role', name='uq_form_column_rules')
    )
    op.create_index('idx_form_column_rules', 'form_column_rules', ['form_id', 'role'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_form_column_rules', table_name='form_column_rules')
    op.drop_table('form_column_rules')

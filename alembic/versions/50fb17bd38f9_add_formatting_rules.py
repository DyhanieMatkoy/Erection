"""add_formatting_rules

Revision ID: 50fb17bd38f9
Revises: 82e5259c72b6
Create Date: 2025-12-17 16:33:31.225634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50fb17bd38f9'
down_revision: Union[str, Sequence[str], None] = '82e5259c72b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('form_formatting_rules',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('form_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('condition', sa.JSON(), nullable=False),
    sa.Column('style', sa.JSON(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_form_formatting_rules', 'form_formatting_rules', ['form_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_form_formatting_rules', table_name='form_formatting_rules')
    op.drop_table('form_formatting_rules')

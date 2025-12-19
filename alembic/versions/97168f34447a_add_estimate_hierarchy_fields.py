"""add_estimate_hierarchy_fields

Revision ID: 97168f34447a
Revises: 53b5b4dbfe35
Create Date: 2025-12-17 13:25:40.727858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97168f34447a'
down_revision: Union[str, Sequence[str], None] = '53b5b4dbfe35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns already exist (they might have been added manually)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('estimates')]
    
    # Add columns only if they don't exist
    if 'base_document_id' not in columns:
        op.add_column('estimates', sa.Column('base_document_id', sa.Integer(), nullable=True))
    
    if 'estimate_type' not in columns:
        op.add_column('estimates', sa.Column('estimate_type', sa.String(20), nullable=False, server_default='General'))
    
    # Create indexes on base_document_id and estimate_type for performance
    op.create_index('idx_estimates_base_document_id', 'estimates', ['base_document_id'])
    op.create_index('idx_estimates_estimate_type', 'estimates', ['estimate_type'])
    
    # Set existing estimates to 'General' type with NULL base_document_id
    # This is already handled by the server_default='General' and nullable=True for base_document_id


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_estimates_estimate_type', 'estimates')
    op.drop_index('idx_estimates_base_document_id', 'estimates')
    
    # Drop columns
    op.drop_column('estimates', 'estimate_type')
    op.drop_column('estimates', 'base_document_id')

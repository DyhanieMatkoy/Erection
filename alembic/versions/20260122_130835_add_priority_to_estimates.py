"""Test migration: add_priority_to_estimates

Add priority column to estimates table

Revision ID: 20260122_130835_add_priority_to_estimates
Revises: 
Create Date: 2026-01-22T13:08:35.616919

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '20260122_130835_add_priority_to_estimates'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    op.add_column('estimates', sa.Column('priority', sa.Integer, default=1))


def downgrade():
    """Downgrade database schema"""
    op.drop_column('estimates', 'priority')

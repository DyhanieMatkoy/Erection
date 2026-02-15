"""Test migration: add_project_phases_table

Add project phases table for testing

Revision ID: 20260122_130833_add_project_phases_table
Revises: 
Create Date: 2026-01-22T13:08:33.558724

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '20260122_130833_add_project_phases_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    op.create_table('project_phases',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('start_date', sa.Date),
        sa.Column('end_date', sa.Date),
        sa.Column('project_id', sa.Integer), sa.ForeignKey('projects.id'),
        sa.Column('created_at', sa.DateTime, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=func.now()),
    )


def downgrade():
    """Downgrade database schema"""
    op.drop_table('project_phases')

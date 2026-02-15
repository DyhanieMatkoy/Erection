"""Test migration: add_project_phases_table

Add project phases table for testing

Revision ID: 20260201_223459_add_project_phases_table
Revises: 20260122_000000_initial_test_schema
Create Date: 2026-02-01T22:34:59.005266

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '20260201_223459_add_project_phases_table'
down_revision = '20260122_000000_initial_test_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    # Check if we're in test mode - create tables if they don't exist
    try:
        # Create basic tables if they don't exist (for test isolation)
        _ensure_basic_tables_exist()
    except Exception:
        pass  # Continue with migration even if table creation fails
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


def _ensure_basic_tables_exist():
    """Ensure basic tables exist for test migrations"""
    # This function creates basic tables if they don't exist
    # to support isolated test migrations
    
    # Check if estimates table exists, if not create basic structure
    try:
        op.get_bind().execute(sa.text("SELECT 1 FROM estimates LIMIT 1"))
    except Exception:
        # Create basic estimates table
        op.create_table('estimates',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(255)),
            sa.Column('description', sa.Text),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
        )
    
    # Check if daily_reports table exists
    try:
        op.get_bind().execute(sa.text("SELECT 1 FROM daily_reports LIMIT 1"))
    except Exception:
        # Create basic daily_reports table
        op.create_table('daily_reports',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('date', sa.Date),
            sa.Column('description', sa.String(255)),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
        )

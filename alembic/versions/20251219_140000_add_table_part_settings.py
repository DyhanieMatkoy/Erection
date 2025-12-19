"""Add table part settings tables

Revision ID: 20251219_140000
Revises: 20251219_120000
Create Date: 2024-12-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251219_140000_add_table_part_settings'
down_revision = '20251219_120000_optimize_hierarchical_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add table part settings tables"""
    
    # Create user_table_part_settings table
    op.create_table(
        'user_table_part_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('table_part_id', sa.String(100), nullable=False),
        sa.Column('settings_data', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for user_table_part_settings
    op.create_index(
        'idx_user_table_part_settings_user_id',
        'user_table_part_settings',
        ['user_id']
    )
    op.create_index(
        'idx_user_table_part_settings_document_type',
        'user_table_part_settings',
        ['document_type']
    )
    op.create_index(
        'idx_user_table_part_settings_table_part_id',
        'user_table_part_settings',
        ['table_part_id']
    )
    op.create_index(
        'idx_user_table_part_settings_lookup',
        'user_table_part_settings',
        ['user_id', 'document_type', 'table_part_id']
    )
    
    # Create unique constraint
    op.create_unique_constraint(
        'uq_user_table_part_settings',
        'user_table_part_settings',
        ['user_id', 'document_type', 'table_part_id']
    )
    
    # Create table_part_command_config table
    op.create_table(
        'table_part_command_config',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('table_part_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('command_id', sa.String(100), nullable=False),
        sa.Column('is_visible', sa.Boolean, nullable=False, default=True),
        sa.Column('is_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('position', sa.Integer, nullable=False, default=0),
        sa.Column('is_in_more_menu', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for table_part_command_config
    op.create_index(
        'idx_table_part_command_config_document_type',
        'table_part_command_config',
        ['document_type']
    )
    op.create_index(
        'idx_table_part_command_config_table_part_id',
        'table_part_command_config',
        ['table_part_id']
    )
    op.create_index(
        'idx_table_part_command_config_user_id',
        'table_part_command_config',
        ['user_id']
    )
    op.create_index(
        'idx_table_part_command_config_command_id',
        'table_part_command_config',
        ['command_id']
    )
    op.create_index(
        'idx_table_part_command_config_lookup',
        'table_part_command_config',
        ['document_type', 'table_part_id', 'user_id']
    )
    
    # Create unique constraint
    op.create_unique_constraint(
        'uq_table_part_command_config',
        'table_part_command_config',
        ['document_type', 'table_part_id', 'user_id', 'command_id']
    )


def downgrade():
    """Remove table part settings tables"""
    
    # Drop table_part_command_config table
    op.drop_table('table_part_command_config')
    
    # Drop user_table_part_settings table
    op.drop_table('user_table_part_settings')
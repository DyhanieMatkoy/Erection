"""Add costs and materials tables

Revision ID: 001_add_costs_and_materials
Revises: 
Create Date: 2025-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite, postgresql, mssql

# revision identifiers, used by Alembic.
revision = '001_add_costs_and_materials'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create cost_items table
    op.create_table('cost_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_folder', sa.Boolean(), nullable=False, default=False),
        sa.Column('price', sa.Float(), nullable=False, default=0.0),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('labor_coefficient', sa.Float(), nullable=False, default=0.0),
        sa.Column('marked_for_deletion', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('modified_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['parent_id'], ['cost_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cost_items_code'), 'cost_items', ['code'], unique=False)
    op.create_index(op.f('ix_cost_items_description'), 'cost_items', ['description'], unique=False)
    
    # Create materials table
    op.create_table('materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('price', sa.Float(), nullable=False, default=0.0),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('marked_for_deletion', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('modified_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_materials_code'), 'materials', ['code'], unique=False)
    op.create_index(op.f('ix_materials_description'), 'materials', ['description'], unique=False)
    
    # Create cost_item_materials association table
    op.create_table('cost_item_materials',
        sa.Column('cost_item_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('quantity_per_unit', sa.Float(), nullable=False, default=0.0),
        sa.ForeignKeyConstraint(['cost_item_id'], ['cost_items.id'], ),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('cost_item_id', 'material_id')
    )
    
    # Add columns to estimate_lines table
    op.add_column('estimate_lines', sa.Column('material_id', sa.Integer(), nullable=True))
    op.add_column('estimate_lines', sa.Column('material_quantity', sa.Float(), nullable=False, default=0.0))
    op.add_column('estimate_lines', sa.Column('material_price', sa.Float(), nullable=False, default=0.0))
    op.add_column('estimate_lines', sa.Column('material_sum', sa.Float(), nullable=False, default=0.0))
    op.create_foreign_key('fk_estimate_lines_material_id_materials', 'estimate_lines', 'materials', ['material_id'], ['id'])
    
    # Add columns to daily_report_lines table
    op.add_column('daily_report_lines', sa.Column('material_id', sa.Integer(), nullable=True))
    op.add_column('daily_report_lines', sa.Column('planned_material_quantity', sa.Float(), nullable=False, default=0.0))
    op.add_column('daily_report_lines', sa.Column('actual_material_quantity', sa.Float(), nullable=False, default=0.0))
    op.add_column('daily_report_lines', sa.Column('material_deviation_percent', sa.Float(), nullable=False, default=0.0))
    op.create_foreign_key('fk_daily_report_lines_material_id_materials', 'daily_report_lines', 'materials', ['material_id'], ['id'])


def downgrade():
    # Remove columns from daily_report_lines table
    op.drop_constraint('fk_daily_report_lines_material_id_materials', 'daily_report_lines', type_='foreignkey')
    op.drop_column('daily_report_lines', 'material_deviation_percent')
    op.drop_column('daily_report_lines', 'actual_material_quantity')
    op.drop_column('daily_report_lines', 'planned_material_quantity')
    op.drop_column('daily_report_lines', 'material_id')
    
    # Remove columns from estimate_lines table
    op.drop_constraint('fk_estimate_lines_material_id_materials', 'estimate_lines', type_='foreignkey')
    op.drop_column('estimate_lines', 'material_sum')
    op.drop_column('estimate_lines', 'material_price')
    op.drop_column('estimate_lines', 'material_quantity')
    op.drop_column('estimate_lines', 'material_id')
    
    # Drop cost_item_materials table
    op.drop_table('cost_item_materials')
    
    # Drop materials table
    op.drop_index(op.f('ix_materials_description'), table_name='materials')
    op.drop_index(op.f('ix_materials_code'), table_name='materials')
    op.drop_table('materials')
    
    # Drop cost_items table
    op.drop_index(op.f('ix_cost_items_description'), table_name='cost_items')
    op.drop_index(op.f('ix_cost_items_code'), table_name='cost_items')
    op.drop_table('cost_items')
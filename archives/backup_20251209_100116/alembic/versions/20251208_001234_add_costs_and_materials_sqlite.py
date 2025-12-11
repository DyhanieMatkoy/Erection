"""Add costs and materials tables (SQLite compatible)

Revision ID: 20251208_001234
Revises: 201f5ef24462
Create Date: 2025-12-08 00:12:34.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251208_001234'
down_revision: Union[str, Sequence[str], None] = '201f5ef24462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    
    # For SQLite, we need to recreate the estimate_lines table with the new columns
    # First, get the data from the existing table
    op.execute("CREATE TABLE estimate_lines_backup AS SELECT * FROM estimate_lines")
    
    # Drop the original table
    op.drop_table('estimate_lines')
    
    # Create the new estimate_lines table with material columns
    op.create_table('estimate_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estimate_id', sa.Integer(), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('work_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('labor_rate', sa.Float(), nullable=True),
        sa.Column('sum', sa.Float(), nullable=True),
        sa.Column('planned_labor', sa.Float(), nullable=True),
        sa.Column('is_group', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('group_name', sa.String(length=100), nullable=True),
        sa.Column('parent_group_id', sa.Integer(), nullable=True),
        sa.Column('is_collapsed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('material_quantity', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('material_price', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('material_sum', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.ForeignKeyConstraint(['parent_group_id'], ['estimate_lines.id'], ),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore the data from the backup
    op.execute("""
        INSERT INTO estimate_lines (
            id, estimate_id, line_number, work_id, quantity, unit, price, 
            labor_rate, sum, planned_labor, is_group, group_name, 
            parent_group_id, is_collapsed
        )
        SELECT 
            id, estimate_id, line_number, work_id, quantity, unit, price, 
            labor_rate, sum, planned_labor, is_group, group_name, 
            parent_group_id, is_collapsed
        FROM estimate_lines_backup
    """)
    
    # Drop the backup table
    op.drop_table('estimate_lines_backup')
    
    # For SQLite, we need to recreate the daily_report_lines table with the new columns
    # First, get the data from the existing table
    op.execute("CREATE TABLE daily_report_lines_backup AS SELECT * FROM daily_report_lines")
    
    # Drop the original table
    op.drop_table('daily_report_lines')
    
    # Create the new daily_report_lines table with material columns
    op.create_table('daily_report_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('work_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('sum', sa.Float(), nullable=True),
        sa.Column('planned_labor', sa.Float(), nullable=True),
        sa.Column('actual_labor', sa.Float(), nullable=True),
        sa.Column('labor_deviation_percent', sa.Float(), nullable=True),
        sa.Column('is_group', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('group_name', sa.String(length=100), nullable=True),
        sa.Column('parent_group_id', sa.Integer(), nullable=True),
        sa.Column('is_collapsed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('planned_material_quantity', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('actual_material_quantity', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('material_deviation_percent', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.ForeignKeyConstraint(['daily_report_id'], ['daily_reports.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.ForeignKeyConstraint(['parent_group_id'], ['daily_report_lines.id'], ),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore the data from the backup
    op.execute("""
        INSERT INTO daily_report_lines (
            id, daily_report_id, line_number, work_id, quantity, unit, price, 
            sum, planned_labor, actual_labor, labor_deviation_percent, is_group, 
            group_name, parent_group_id, is_collapsed
        )
        SELECT 
            id, report_id, line_number, work_id, 0, '', 0, 
            0, planned_labor, actual_labor, deviation_percent, is_group, 
            group_name, parent_group_id, is_collapsed
        FROM daily_report_lines_backup
    """)
    
    # Drop the backup table
    op.drop_table('daily_report_lines_backup')


def downgrade() -> None:
    # For SQLite, we need to recreate the daily_report_lines table without the material columns
    # First, get the data from the existing table
    op.execute("CREATE TABLE daily_report_lines_backup AS SELECT * FROM daily_report_lines")
    
    # Drop the original table
    op.drop_table('daily_report_lines')
    
    # Create the original daily_report_lines table without material columns
    op.create_table('daily_report_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), nullable=True),
        sa.Column('work_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('sum', sa.Float(), nullable=True),
        sa.Column('planned_labor', sa.Float(), nullable=True),
        sa.Column('actual_labor', sa.Float(), nullable=True),
        sa.Column('labor_deviation_percent', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['daily_report_id'], ['daily_reports(id)'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works(id)'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore the data from the backup
    op.execute("""
        INSERT INTO daily_report_lines (
            id, daily_report_id, work_id, quantity, unit, price, 
            sum, planned_labor, actual_labor, labor_deviation_percent
        )
        SELECT 
            id, daily_report_id, work_id, quantity, unit, price, 
            sum, planned_labor, actual_labor, labor_deviation_percent
        FROM daily_report_lines_backup
    """)
    
    # Drop the backup table
    op.drop_table('daily_report_lines_backup')
    
    # For SQLite, we need to recreate the estimate_lines table without the material columns
    # First, get the data from the existing table
    op.execute("CREATE TABLE estimate_lines_backup AS SELECT * FROM estimate_lines")
    
    # Drop the original table
    op.drop_table('estimate_lines')
    
    # Create the original estimate_lines table without material columns
    op.create_table('estimate_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estimate_id', sa.Integer(), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('work_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('labor_rate', sa.Float(), nullable=True),
        sa.Column('sum', sa.Float(), nullable=True),
        sa.Column('planned_labor', sa.Float(), nullable=True),
        sa.Column('is_group', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('group_name', sa.String(length=100), nullable=True),
        sa.Column('parent_group_id', sa.Integer(), nullable=True),
        sa.Column('is_collapsed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates(id)'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works(id)'], ),
        sa.ForeignKeyConstraint(['parent_group_id'], ['estimate_lines(id)'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore the data from the backup
    op.execute("""
        INSERT INTO estimate_lines (
            id, estimate_id, line_number, work_id, quantity, unit, price, 
            labor_rate, sum, planned_labor, is_group, group_name, 
            parent_group_id, is_collapsed
        )
        SELECT 
            id, estimate_id, line_number, work_id, quantity, unit, price, 
            labor_rate, sum, planned_labor, is_group, group_name, 
            parent_group_id, is_collapsed
        FROM estimate_lines_backup
    """)
    
    # Drop the backup table
    op.drop_table('estimate_lines_backup')
    
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
"""Add work_id to cost_item_materials and create units table

Revision ID: 20251209_100000
Revises: 20251208_001234
Create Date: 2025-12-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251209_100000'
down_revision: Union[str, Sequence[str], None] = '20251208_001234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection to check if tables/columns exist
    conn = op.get_bind()
    
    # ========================================================================
    # 1. Create units table (if not exists)
    # ========================================================================
    # Check if units table exists
    result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='units'"))
    units_exists = result.fetchone() is not None
    
    if not units_exists:
        op.create_table('units',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('marked_for_deletion', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('modified_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        op.create_index(op.f('idx_unit_name'), 'units', ['name'], unique=False)
        
        # Insert common units
        op.execute("""
            INSERT INTO units (name, description) VALUES
            ('м', 'Метр'),
            ('м²', 'Квадратный метр'),
            ('м³', 'Кубический метр'),
            ('кг', 'Килограмм'),
            ('т', 'Тонна'),
            ('шт', 'Штука'),
            ('л', 'Литр'),
            ('компл', 'Комплект'),
            ('час', 'Час'),
            ('смена', 'Смена'),
            ('м.п.', 'Метр погонный')
        """)
    
    # ========================================================================
    # 2. Add unit_id to cost_items (if not exists)
    # ========================================================================
    # Check if unit_id column exists in cost_items
    result = conn.execute(sa.text("PRAGMA table_info(cost_items)"))
    cost_items_columns = [row[1] for row in result.fetchall()]
    
    if 'unit_id' not in cost_items_columns:
        op.add_column('cost_items', sa.Column('unit_id', sa.Integer(), nullable=True))
        
        # Migrate existing units to unit_id
        op.execute("""
            UPDATE cost_items
            SET unit_id = (SELECT id FROM units WHERE units.name = cost_items.unit)
            WHERE cost_items.unit IS NOT NULL AND cost_items.unit != ''
        """)
    
    # ========================================================================
    # 3. Add unit_id to materials (if not exists)
    # ========================================================================
    # Check if unit_id column exists in materials
    result = conn.execute(sa.text("PRAGMA table_info(materials)"))
    materials_columns = [row[1] for row in result.fetchall()]
    
    if 'unit_id' not in materials_columns:
        op.add_column('materials', sa.Column('unit_id', sa.Integer(), nullable=True))
        
        # Migrate existing units to unit_id
        op.execute("""
            UPDATE materials
            SET unit_id = (SELECT id FROM units WHERE units.name = materials.unit)
            WHERE materials.unit IS NOT NULL AND materials.unit != ''
        """)
    
    # ========================================================================
    # 4. Recreate cost_item_materials with work_id
    # ========================================================================
    
    # Backup existing data
    op.execute("CREATE TABLE cost_item_materials_backup AS SELECT * FROM cost_item_materials")
    
    # Drop old table
    op.drop_table('cost_item_materials')
    
    # Create new table with work_id
    op.create_table('cost_item_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('cost_item_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('quantity_per_unit', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cost_item_id'], ['cost_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_id', 'cost_item_id', 'material_id', name='uq_work_cost_item_material')
    )
    
    # Create indexes
    op.create_index(op.f('idx_cost_item_material_work'), 'cost_item_materials', ['work_id'], unique=False)
    op.create_index(op.f('idx_cost_item_material_cost_item'), 'cost_item_materials', ['cost_item_id'], unique=False)
    op.create_index(op.f('idx_cost_item_material_material'), 'cost_item_materials', ['material_id'], unique=False)
    
    # Create a default "General Work" for migration
    op.execute("""
        INSERT INTO works (name, code, is_group, marked_for_deletion)
        VALUES ('Общие работы (миграция)', 'MIGRATION', 0, 0)
    """)
    
    # Migrate old data to new structure with default work
    op.execute("""
        INSERT INTO cost_item_materials (work_id, cost_item_id, material_id, quantity_per_unit)
        SELECT 
            (SELECT id FROM works WHERE code = 'MIGRATION'),
            cost_item_id,
            material_id,
            quantity_per_unit
        FROM cost_item_materials_backup
    """)
    
    # Drop backup table
    op.drop_table('cost_item_materials_backup')
    
    # ========================================================================
    # 5. Add missing indexes to existing tables (if they don't exist)
    # ========================================================================
    
    # Note: SQLite will silently ignore if index already exists
    try:
        op.create_index(op.f('idx_estimate_customer'), 'estimates', ['customer_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_estimate_object'), 'estimates', ['object_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_estimate_contractor'), 'estimates', ['contractor_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_estimate_line_work'), 'estimate_lines', ['work_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_estimate_line_material'), 'estimate_lines', ['material_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_daily_report_line_work'), 'daily_report_lines', ['work_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_daily_report_line_material'), 'daily_report_lines', ['material_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_person_user'), 'persons', ['user_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_person_parent'), 'persons', ['parent_id'], unique=False)
    except:
        pass
    
    try:
        op.create_index(op.f('idx_object_owner'), 'objects', ['owner_id'], unique=False)
    except:
        pass


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('idx_object_owner'), table_name='objects')
    op.drop_index(op.f('idx_person_parent'), table_name='persons')
    op.drop_index(op.f('idx_person_user'), table_name='persons')
    op.drop_index(op.f('idx_daily_report_line_material'), table_name='daily_report_lines')
    op.drop_index(op.f('idx_daily_report_line_work'), table_name='daily_report_lines')
    op.drop_index(op.f('idx_estimate_line_material'), table_name='estimate_lines')
    op.drop_index(op.f('idx_estimate_line_work'), table_name='estimate_lines')
    op.drop_index(op.f('idx_estimate_contractor'), table_name='estimates')
    op.drop_index(op.f('idx_estimate_object'), table_name='estimates')
    op.drop_index(op.f('idx_estimate_customer'), table_name='estimates')
    
    # Recreate old cost_item_materials structure
    op.execute("CREATE TABLE cost_item_materials_backup AS SELECT * FROM cost_item_materials")
    op.drop_table('cost_item_materials')
    
    op.create_table('cost_item_materials',
        sa.Column('cost_item_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('quantity_per_unit', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.ForeignKeyConstraint(['cost_item_id'], ['cost_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('cost_item_id', 'material_id')
    )
    
    # Restore data (only where material_id is not null)
    op.execute("""
        INSERT INTO cost_item_materials (cost_item_id, material_id, quantity_per_unit)
        SELECT cost_item_id, material_id, quantity_per_unit
        FROM cost_item_materials_backup
        WHERE material_id IS NOT NULL
    """)
    
    op.drop_table('cost_item_materials_backup')
    
    # Remove unit_id from materials
    op.drop_column('materials', 'unit_id')
    
    # Remove unit_id from cost_items
    op.drop_column('cost_items', 'unit_id')
    
    # Drop units table
    op.drop_index(op.f('idx_unit_name'), table_name='units')
    op.drop_table('units')
    
    # Delete migration work
    op.execute("DELETE FROM works WHERE code = 'MIGRATION'")

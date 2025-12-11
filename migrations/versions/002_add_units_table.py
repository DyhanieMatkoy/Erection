"""Add units table and update materials and cost_items tables

Revision ID: 002_add_units_table
Revises: 001_add_costs_and_materials
Create Date: 2025-12-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_units_table'
down_revision = '001_add_costs_and_materials'
branch_labels = None
depends_on = None


def upgrade():
    # Create units table
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255)),
        sa.Column('marked_for_deletion', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Add unit_id column to materials table
    op.add_column('materials', sa.Column('unit_id', sa.Integer(), sa.ForeignKey('units.id')))
    
    # Add unit_id column to cost_items table
    op.add_column('cost_items', sa.Column('unit_id', sa.Integer(), sa.ForeignKey('units.id')))
    
    # Insert common units
    op.execute("""
        INSERT INTO units (name, description) VALUES 
        ('шт', 'штуки'),
        ('м', 'метры'),
        ('м2', 'квадратные метры'),
        ('м3', 'кубические метры'),
        ('кг', 'килограммы'),
        ('т', 'тонны'),
        ('л', 'литры'),
        ('ч', 'часы'),
        ('день', 'дни'),
        ('компл', 'комплекты')
    """)
    
    # Update materials with unit_id based on unit string
    op.execute("""
        UPDATE materials SET unit_id = (
            SELECT id FROM units WHERE units.name = materials.unit
        )
        WHERE materials.unit IN (SELECT name FROM units)
    """)
    
    # Update cost_items with unit_id based on unit string
    op.execute("""
        UPDATE cost_items SET unit_id = (
            SELECT id FROM units WHERE units.name = cost_items.unit
        )
        WHERE cost_items.unit IN (SELECT name FROM units)
    """)


def downgrade():
    # Remove unit_id columns
    op.drop_column('cost_items', 'unit_id')
    op.drop_column('materials', 'unit_id')
    
    # Drop units table
    op.drop_table('units')
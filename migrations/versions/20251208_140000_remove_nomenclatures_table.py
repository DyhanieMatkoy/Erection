"""Remove nomenclatures table and update works

Revision ID: 20251208_140000
Revises: 20251208_120000
Create Date: 2025-12-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251208_140000'
down_revision = '20251208_120000'
branch_labels = None
depends_on = None


def upgrade():
    # Remove nomenclature_id column from works table
    op.drop_column('works', 'nomenclature_id')
    
    # Drop nomenclatures table
    op.drop_table('nomenclatures')
    
    # Drop index
    op.drop_index('ix_nomenclatures_parent_id', 'nomenclatures')


def downgrade():
    # Create nomenclatures table
    op.create_table(
        'nomenclatures',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('nomenclatures.id')),
        sa.Column('code', sa.String(50)),
        sa.Column('description', sa.String(500)),
        sa.Column('is_folder', sa.Boolean(), default=False),
        sa.Column('marked_for_deletion', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Add nomenclature_id column to works table
    op.add_column('works', sa.Column('nomenclature_id', sa.Integer(), sa.ForeignKey('nomenclatures.id')))
    
    # Create index on parent_id for hierarchical queries
    op.create_index('ix_nomenclatures_parent_id', 'nomenclatures', ['parent_id'])
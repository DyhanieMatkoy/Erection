"""Optimize hierarchical indexes for bulk operations

Revision ID: 20251219120000
Revises: 20251219000001
Create Date: 2025-12-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219_120000_optimize_hierarchical_indexes'
down_revision: Union[str, Sequence[str], None] = '20251219_000001_remove_legacy_unit_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optimized indexes for hierarchical queries and bulk operations"""
    
    # Get connection to check database type
    conn = op.get_bind()
    
    try:
        # Composite index for hierarchy queries with unit information
        # This supports queries that filter by parent_id and join with units
        try:
            op.create_index(
                'idx_works_parent_unit_composite', 
                'works', 
                ['parent_id', 'unit_id', 'marked_for_deletion']
            )
        except Exception:
            # Index might already exist or not supported
            pass
        
        # Index for bulk operations on marked_for_deletion
        try:
            op.create_index(
                'idx_works_marked_for_deletion', 
                'works', 
                ['marked_for_deletion']
            )
        except Exception:
            pass
        
        # Composite index for hierarchy traversal with deletion status
        try:
            op.create_index(
                'idx_works_hierarchy_active', 
                'works', 
                ['parent_id', 'marked_for_deletion', 'is_group']
            )
        except Exception:
            pass
        
        # Index for unit migration queries
        try:
            op.create_index(
                'idx_works_unit_migration', 
                'works', 
                ['unit_id', 'unit', 'marked_for_deletion']
            )
        except Exception:
            pass
        
        # Index for search operations
        try:
            op.create_index(
                'idx_works_name_search', 
                'works', 
                ['name', 'marked_for_deletion']
            )
        except Exception:
            pass
        
        # Index for UUID-based operations
        try:
            op.create_index(
                'idx_works_uuid_active', 
                'works', 
                ['uuid', 'marked_for_deletion']
            )
        except Exception:
            pass
            
        # Optimize work_unit_migration table indexes
        try:
            op.create_index(
                'idx_work_unit_migration_status_work', 
                'work_unit_migration', 
                ['migration_status', 'work_id']
            )
        except Exception:
            pass
        
        try:
            op.create_index(
                'idx_work_unit_migration_confidence', 
                'work_unit_migration', 
                ['confidence_score', 'migration_status']
            )
        except Exception:
            pass
            
    except Exception as e:
        # If any index creation fails, continue - the model will still work
        print(f"Warning: Could not create some optimization indexes: {e}")


def downgrade() -> None:
    """Remove optimization indexes added in upgrade"""
    
    # Drop indexes if they exist
    indexes_to_drop = [
        'idx_work_unit_migration_confidence',
        'idx_work_unit_migration_status_work',
        'idx_works_uuid_active',
        'idx_works_name_search',
        'idx_works_unit_migration',
        'idx_works_hierarchy_active',
        'idx_works_marked_for_deletion',
        'idx_works_parent_unit_composite'
    ]
    
    for index_name in indexes_to_drop:
        try:
            if 'work_unit_migration' in index_name:
                op.drop_index(index_name, 'work_unit_migration')
            else:
                op.drop_index(index_name, 'works')
        except Exception:
            pass
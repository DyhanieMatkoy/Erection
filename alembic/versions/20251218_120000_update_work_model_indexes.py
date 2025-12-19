"""Update Work model with indexes and constraints

Revision ID: 20251218_120000
Revises: 20251218_000001
Create Date: 2025-12-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251218120000'
down_revision: Union[str, Sequence[str], None] = '20251218000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes and constraints for improved Work model performance"""
    
    # Get connection to check database type
    conn = op.get_bind()
    
    # Check if we're using SQLite (which has limited index support)
    try:
        # Try to create indexes for better performance
        # Note: SQLite doesn't support all index types, so we'll be conservative
        
        # Index on unit_id for foreign key lookups
        try:
            op.create_index('idx_works_unit_id', 'works', ['unit_id'])
        except Exception:
            # Index might already exist or not supported
            pass
        
        # Index on parent_id for hierarchy queries
        try:
            op.create_index('idx_works_parent_id', 'works', ['parent_id'])
        except Exception:
            # Index might already exist or not supported
            pass
        
        # Index on uuid for synchronization
        try:
            op.create_index('idx_works_uuid', 'works', ['uuid'])
        except Exception:
            # Index might already exist or not supported
            pass
        
        # Index on name for search operations
        try:
            op.create_index('idx_works_name', 'works', ['name'])
        except Exception:
            # Index might already exist or not supported
            pass
            
    except Exception as e:
        # If any index creation fails, continue - the model will still work
        print(f"Warning: Could not create some indexes: {e}")


def downgrade() -> None:
    """Remove indexes added in upgrade"""
    
    # Drop indexes if they exist
    try:
        op.drop_index('idx_works_name', 'works')
    except Exception:
        pass
        
    try:
        op.drop_index('idx_works_uuid', 'works')
    except Exception:
        pass
        
    try:
        op.drop_index('idx_works_parent_id', 'works')
    except Exception:
        pass
        
    try:
        op.drop_index('idx_works_unit_id', 'works')
    except Exception:
        pass
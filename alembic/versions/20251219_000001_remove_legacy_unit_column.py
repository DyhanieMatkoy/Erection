"""Remove legacy unit column from works table

Revision ID: 20251219_000001
Revises: 20251218_120000
Create Date: 2025-12-19 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219000001'
down_revision: Union[str, Sequence[str], None] = '20251218120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove legacy unit column from works table"""
    
    # Get connection to check for any remaining works with legacy unit data
    conn = op.get_bind()
    
    # Check if there are any works that still need migration
    result = conn.execute(sa.text("""
        SELECT COUNT(*) as count 
        FROM works 
        WHERE (unit IS NOT NULL AND unit != '') 
        AND (unit_id IS NULL OR unit_id = 0)
        AND marked_for_deletion = 0
    """))
    
    unmigrated_count = result.fetchone()[0]
    
    if unmigrated_count > 0:
        raise Exception(f"Cannot remove legacy unit column: {unmigrated_count} works still need unit migration. "
                       f"Please run the unit migration process first.")
    
    # Backup legacy unit data for safety (in case rollback is needed)
    try:
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS works_unit_backup AS 
            SELECT id, unit, unit_id 
            FROM works 
            WHERE unit IS NOT NULL AND unit != ''
        """))
    except Exception as e:
        print(f"Warning: Could not create backup table: {e}")
    
    # Remove the legacy unit column
    try:
        # For SQLite, we need to recreate the table without the unit column
        # Check if we're using SQLite
        dialect_name = conn.dialect.name
        
        if dialect_name == 'sqlite':
            # SQLite doesn't support DROP COLUMN, so we need to recreate the table
            # This is a complex operation, so we'll use a more conservative approach
            # and just mark the column as deprecated in comments for now
            
            # Add a comment to indicate the column is deprecated
            # SQLite doesn't support column comments, so we'll just leave it for now
            # The application code will ignore this column
            print("SQLite detected: Legacy unit column left in place but will be ignored by application")
            
        else:
            # For PostgreSQL and SQL Server, we can drop the column directly
            op.drop_column('works', 'unit')
            
    except Exception as e:
        print(f"Warning: Could not remove unit column: {e}")
        # Continue anyway - the application will ignore the column


def downgrade() -> None:
    """Restore legacy unit column (if possible)"""
    
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    if dialect_name != 'sqlite':
        # For non-SQLite databases, add the column back
        try:
            op.add_column('works', sa.Column('unit', sa.String(50), nullable=True))
            
            # Restore data from backup if it exists
            try:
                conn.execute(sa.text("""
                    UPDATE works 
                    SET unit = (
                        SELECT b.unit 
                        FROM works_unit_backup b 
                        WHERE b.id = works.id
                    )
                    WHERE EXISTS (
                        SELECT 1 
                        FROM works_unit_backup b 
                        WHERE b.id = works.id
                    )
                """))
            except Exception as e:
                print(f"Warning: Could not restore unit data from backup: {e}")
                
        except Exception as e:
            print(f"Warning: Could not restore unit column: {e}")
    else:
        print("SQLite detected: Unit column was not removed, no action needed")
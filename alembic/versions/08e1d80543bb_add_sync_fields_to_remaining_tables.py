"""add_sync_fields_to_remaining_tables

Revision ID: 08e1d80543bb
Revises: 97168f34447a
Create Date: 2026-01-27 21:31:17.997397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08e1d80543bb'
down_revision: Union[str, Sequence[str], None] = '97168f34447a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add sync fields to remaining tables that don't have them yet."""
    
    # List of tables that should have sync fields (excluding those that already have them)
    tables_to_update = [
        'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
        'timesheets', 'timesheet_lines', 'works', 'persons', 'organizations', 
        'counterparties', 'objects'
    ]
    
    for table_name in tables_to_update:
        try:
            # Add sync fields if they don't exist
            _add_sync_fields_safe(table_name)
        except Exception as e:
            print(f"Warning: Could not add sync fields to {table_name}: {e}")
            continue


def downgrade() -> None:
    """Remove sync fields from tables."""
    
    # List of tables to remove sync fields from
    tables_to_update = [
        'estimates', 'estimate_lines', 'daily_reports', 'daily_report_lines',
        'timesheets', 'timesheet_lines', 'works', 'persons', 'organizations',
        'counterparties', 'objects'
    ]
    
    for table_name in tables_to_update:
        try:
            # Remove sync fields if they exist
            _remove_sync_fields_safe(table_name)
        except Exception as e:
            print(f"Warning: Could not remove sync fields from {table_name}: {e}")
            continue


def _add_sync_fields_safe(table_name: str) -> None:
    """Safely add sync fields to table."""
    
    # Add UUID field
    try:
        op.add_column(table_name, sa.Column('uuid', sa.String(36), nullable=False, 
                                          server_default=''))
        # Update existing records with UUIDs
        connection = op.get_bind()
        connection.execute(sa.text(f"""
            UPDATE {table_name} 
            SET uuid = (
                lower(hex(randomblob(4))) || '-' || 
                lower(hex(randomblob(2))) || '-4' || 
                substr(lower(hex(randomblob(2))),2) || '-' || 
                substr('89ab',abs(random()) % 4 + 1, 1) || 
                substr(lower(hex(randomblob(2))),2) || '-' || 
                lower(hex(randomblob(6)))
            )
            WHERE uuid = '' OR uuid IS NULL
        """))
    except Exception:
        pass  # Column might already exist
    
    # Add updated_at field
    try:
        op.add_column(table_name, sa.Column('updated_at', sa.DateTime, nullable=False, 
                                          server_default=sa.text('CURRENT_TIMESTAMP')))
    except Exception:
        pass  # Column might already exist
    
    # Add is_deleted field
    try:
        op.add_column(table_name, sa.Column('is_deleted', sa.Boolean, nullable=False, 
                                          server_default='0'))
    except Exception:
        pass  # Column might already exist


def _remove_sync_fields_safe(table_name: str) -> None:
    """Safely remove sync fields from table."""
    
    sync_fields = ['uuid', 'updated_at', 'is_deleted']
    
    for field in sync_fields:
        try:
            op.drop_column(table_name, field)
        except Exception:
            pass  # Column might not exist

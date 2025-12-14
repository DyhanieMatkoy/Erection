"""Populate UUID values for existing records

Revision ID: 20251213_003700
Revises: 20251213_003600
Create Date: 2025-12-13 00:37:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '20251213_003700'
down_revision = '20251213_003600'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    
    # Get database dialect
    dialect = connection.dialect.name
    
    # Generate UUIDs for existing records in all tables
    tables_to_update = [
        'daily_reports',
        'daily_report_lines', 
        'estimates',
        'estimate_lines',
        'timesheets',
        'timesheet_lines',
        'work_specifications',
        'works',
        'materials',
        'cost_items',
        'units',
        'persons',
        'organizations',
        'counterparties',
        'objects'
    ]
    
    for table in tables_to_update:
        # Check if table has any records with NULL UUID
        result = connection.execute(f"SELECT COUNT(*) FROM {table} WHERE uuid IS NULL").scalar()
        
        if result > 0:
            print(f"Updating {result} records in {table}")
            
            if dialect == 'postgresql':
                # Use PostgreSQL's gen_random_uuid() for efficiency
                connection.execute(f"UPDATE {table} SET uuid = gen_random_uuid() WHERE uuid IS NULL")
            else:
                # For other databases, generate UUIDs individually
                records = connection.execute(f"SELECT id FROM {table} WHERE uuid IS NULL").fetchall()
                for record in records:
                    new_uuid = str(uuid.uuid4())
                    connection.execute(f"UPDATE {table} SET uuid = '{new_uuid}' WHERE id = {record[0]}")
        
        # Set updated_at to created_at for existing records if it's NULL
        connection.execute(f"UPDATE {table} SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade():
    # No downgrade needed - this is a data migration
    pass
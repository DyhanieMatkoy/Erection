"""Add UUID and audit fields for synchronization

Revision ID: 20251213_003500
Revises: 002_add_units_table
Create Date: 2025-12-13 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mssql
import uuid

# revision identifiers, used by Alembic.
revision = '20251213_003500'
down_revision = '002_add_units_table'
branch_labels = None
depends_on = None


def upgrade():
    # Import UUID type for different databases
    if op.get_bind().dialect.name == 'postgresql':
        uuid_type = postgresql.UUID
    elif op.get_bind().dialect.name == 'mssql':
        uuid_type = mssql.UNIQUEIDENTIFIER
    else:
        uuid_type = sa.String(36)

    # Add UUID and audit fields to main document tables
    # Daily Reports
    op.add_column('daily_reports', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('daily_reports', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('daily_reports', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_daily_reports_uuid', 'daily_reports', ['uuid'], unique=True)

    # Daily Report Lines
    op.add_column('daily_report_lines', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('daily_report_lines', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('daily_report_lines', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_daily_report_lines_uuid', 'daily_report_lines', ['uuid'], unique=True)

    # Estimates
    op.add_column('estimates', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('estimates', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('estimates', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_estimates_uuid', 'estimates', ['uuid'], unique=True)

    # Estimate Lines
    op.add_column('estimate_lines', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('estimate_lines', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('estimate_lines', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_estimate_lines_uuid', 'estimate_lines', ['uuid'], unique=True)

    # Timesheets
    op.add_column('timesheets', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('timesheets', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('timesheets', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_timesheets_uuid', 'timesheets', ['uuid'], unique=True)

    # Timesheet Lines
    op.add_column('timesheet_lines', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('timesheet_lines', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('timesheet_lines', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_timesheet_lines_uuid', 'timesheet_lines', ['uuid'], unique=True)

    # Work Specifications
    op.add_column('work_specifications', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('work_specifications', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('work_specifications', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_work_specifications_uuid', 'work_specifications', ['uuid'], unique=True)

    # Reference tables (optional for sync)
    # Works
    op.add_column('works', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('works', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('works', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_works_uuid', 'works', ['uuid'], unique=True)

    # Materials
    op.add_column('materials', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('materials', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('materials', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_materials_uuid', 'materials', ['uuid'], unique=True)

    # Cost Items
    op.add_column('cost_items', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('cost_items', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('cost_items', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_cost_items_uuid', 'cost_items', ['uuid'], unique=True)

    # Units
    op.add_column('units', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('units', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('units', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_units_uuid', 'units', ['uuid'], unique=True)

    # Persons
    op.add_column('persons', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('persons', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('persons', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_persons_uuid', 'persons', ['uuid'], unique=True)

    # Organizations
    op.add_column('organizations', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('organizations', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('organizations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_organizations_uuid', 'organizations', ['uuid'], unique=True)

    # Counterparties
    op.add_column('counterparties', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('counterparties', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('counterparties', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_counterparties_uuid', 'counterparties', ['uuid'], unique=True)

    # Objects
    op.add_column('objects', sa.Column('uuid', uuid_type(), nullable=False, server_default=sa.text('gen_random_uuid()') if op.get_bind().dialect.name == 'postgresql' else None))
    op.add_column('objects', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    op.add_column('objects', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.create_index('idx_objects_uuid', 'objects', ['uuid'], unique=True)


def downgrade():
    # Remove indexes first
    op.drop_index('idx_daily_reports_uuid', table_name='daily_reports')
    op.drop_index('idx_daily_report_lines_uuid', table_name='daily_report_lines')
    op.drop_index('idx_estimates_uuid', table_name='estimates')
    op.drop_index('idx_estimate_lines_uuid', table_name='estimate_lines')
    op.drop_index('idx_timesheets_uuid', table_name='timesheets')
    op.drop_index('idx_timesheet_lines_uuid', table_name='timesheet_lines')
    op.drop_index('idx_work_specifications_uuid', table_name='work_specifications')
    op.drop_index('idx_works_uuid', table_name='works')
    op.drop_index('idx_materials_uuid', table_name='materials')
    op.drop_index('idx_cost_items_uuid', table_name='cost_items')
    op.drop_index('idx_units_uuid', table_name='units')
    op.drop_index('idx_persons_uuid', table_name='persons')
    op.drop_index('idx_organizations_uuid', table_name='organizations')
    op.drop_index('idx_counterparties_uuid', table_name='counterparties')
    op.drop_index('idx_objects_uuid', table_name='objects')

    # Remove columns in reverse order
    op.drop_column('objects', 'is_deleted')
    op.drop_column('objects', 'updated_at')
    op.drop_column('objects', 'uuid')

    op.drop_column('counterparties', 'is_deleted')
    op.drop_column('counterparties', 'updated_at')
    op.drop_column('counterparties', 'uuid')

    op.drop_column('organizations', 'is_deleted')
    op.drop_column('organizations', 'updated_at')
    op.drop_column('organizations', 'uuid')

    op.drop_column('persons', 'is_deleted')
    op.drop_column('persons', 'updated_at')
    op.drop_column('persons', 'uuid')

    op.drop_column('units', 'is_deleted')
    op.drop_column('units', 'updated_at')
    op.drop_column('units', 'uuid')

    op.drop_column('cost_items', 'is_deleted')
    op.drop_column('cost_items', 'updated_at')
    op.drop_column('cost_items', 'uuid')

    op.drop_column('materials', 'is_deleted')
    op.drop_column('materials', 'updated_at')
    op.drop_column('materials', 'uuid')

    op.drop_column('works', 'is_deleted')
    op.drop_column('works', 'updated_at')
    op.drop_column('works', 'uuid')

    op.drop_column('work_specifications', 'is_deleted')
    op.drop_column('work_specifications', 'updated_at')
    op.drop_column('work_specifications', 'uuid')

    op.drop_column('timesheet_lines', 'is_deleted')
    op.drop_column('timesheet_lines', 'updated_at')
    op.drop_column('timesheet_lines', 'uuid')

    op.drop_column('timesheets', 'is_deleted')
    op.drop_column('timesheets', 'updated_at')
    op.drop_column('timesheets', 'uuid')

    op.drop_column('estimate_lines', 'is_deleted')
    op.drop_column('estimate_lines', 'updated_at')
    op.drop_column('estimate_lines', 'uuid')

    op.drop_column('estimates', 'is_deleted')
    op.drop_column('estimates', 'updated_at')
    op.drop_column('estimates', 'uuid')

    op.drop_column('daily_report_lines', 'is_deleted')
    op.drop_column('daily_report_lines', 'updated_at')
    op.drop_column('daily_report_lines', 'uuid')

    op.drop_column('daily_reports', 'is_deleted')
    op.drop_column('daily_reports', 'updated_at')
    op.drop_column('daily_reports', 'uuid')
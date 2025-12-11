# Schema Management Quick Reference Guide

## Overview

This guide provides quick reference for common schema management tasks using the Alembic migration system.

## Prerequisites

- Alembic is installed (included in requirements.txt)
- Database is configured in env.ini
- SQLAlchemy models are defined in src/data/models/sqlalchemy_models.py

## Common Tasks

### 1. Initialize a New Database

```python
from src.data.database_manager import DatabaseManager

# Initialize database with automatic schema creation
db_manager = DatabaseManager()
db_manager.initialize("env.ini")

# Schema is automatically created and stamped with current version
```

### 2. Check Schema Status

```python
# Get schema manager
schema_manager = db_manager.get_schema_manager()

# Check if database is empty
is_empty = schema_manager.is_database_empty()

# Check if migrations are needed
needs_update = schema_manager.needs_migration()

# Get current version
current = schema_manager.get_current_revision()
head = schema_manager.get_head_revision()

print(f"Current: {current}, Latest: {head}")
```

### 3. Verify Schema Integrity

```python
# Comprehensive schema verification
result = schema_manager.verify_schema()

print(f"Valid: {result['valid']}")
print(f"Missing tables: {result['missing_tables']}")
print(f"Extra tables: {result['extra_tables']}")
print(f"Needs migration: {result['needs_migration']}")
```

### 4. Create a New Migration

After modifying SQLAlchemy models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add email column to users"

# Create empty migration (for data migrations)
alembic revision -m "Migrate user data"
```

### 5. Apply Migrations

```python
# Apply all pending migrations
schema_manager.upgrade_schema("head")

# Apply to specific revision
schema_manager.upgrade_schema("abc123")
```

Or using Alembic CLI:

```bash
# Apply all pending migrations
alembic upgrade head

# Apply one migration at a time
alembic upgrade +1

# Apply to specific revision
alembic upgrade abc123
```

### 6. Rollback Migrations

```python
# Rollback to specific revision
schema_manager.downgrade_schema("previous_revision")
```

Or using Alembic CLI:

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### 7. View Migration History

```python
# Get migration history
history = schema_manager.get_migration_history()

for rev in history:
    current = " (current)" if rev['is_current'] else ""
    print(f"{rev['revision']}: {rev['message']}{current}")
```

Or using Alembic CLI:

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show verbose history
alembic history --verbose
```

## Alembic CLI Commands

### Basic Commands

```bash
# Show current database revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Advanced Commands

```bash
# Show SQL that would be executed (don't apply)
alembic upgrade head --sql

# Stamp database with specific revision (without running migrations)
alembic stamp head

# Show difference between database and models
alembic check

# Merge multiple heads
alembic merge -m "Merge branches" head1 head2
```

## Migration File Structure

Generated migration files are located in `alembic/versions/`:

```python
"""Add email column to users

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add column
    op.add_column('users', sa.Column('email', sa.String(255)))

def downgrade():
    # Remove column
    op.drop_column('users', 'email')
```

## Best Practices

### 1. Always Review Auto-Generated Migrations

Auto-generated migrations may not be perfect. Always review and test them:

```bash
# Generate migration
alembic revision --autogenerate -m "Changes"

# Review the generated file in alembic/versions/

# Test on development database
alembic upgrade head

# Test rollback
alembic downgrade -1
```

### 2. Use Descriptive Migration Messages

```bash
# Good
alembic revision -m "Add email and phone columns to users table"

# Bad
alembic revision -m "Update users"
```

### 3. Test Migrations Before Deployment

```python
# In test environment
schema_manager.upgrade_schema("head")
result = schema_manager.verify_schema()
assert result['valid']

# Test rollback
schema_manager.downgrade_schema("-1")
schema_manager.upgrade_schema("head")
```

### 4. Keep Migrations Small and Focused

- One logical change per migration
- Easier to review and rollback
- Reduces risk of conflicts

### 5. Handle Data Migrations Carefully

For migrations that modify data:

```python
def upgrade():
    # Create new column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Migrate data
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET full_name = first_name || ' ' || last_name"
    )
    
    # Drop old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

### 6. Backup Before Major Migrations

```bash
# SQLite
cp construction.db construction.db.backup

# PostgreSQL
pg_dump dbname > backup.sql

# MSSQL
# Use SQL Server Management Studio or sqlcmd
```

## Troubleshooting

### Migration Conflicts

If you have multiple developers creating migrations:

```bash
# Check for multiple heads
alembic heads

# Merge heads
alembic merge -m "Merge feature branches" head1 head2
```

### Failed Migration

If a migration fails partway through:

```bash
# Check current state
alembic current

# Manually fix the issue in the database

# Stamp to correct revision
alembic stamp revision_id
```

### Schema Out of Sync

If database schema doesn't match models:

```python
# Verify schema
result = schema_manager.verify_schema()
print(result)

# Generate migration to fix
alembic revision --autogenerate -m "Sync schema"
alembic upgrade head
```

### Foreign Key Errors (SQLite)

If foreign key constraints are not working:

```python
# Ensure foreign keys are enabled
schema_manager.ensure_foreign_keys_enabled()

# Verify
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA foreign_keys"))
    print(f"Foreign keys: {result.scalar()}")  # Should be 1
```

## Environment-Specific Configurations

### Development

```ini
[Database]
type = sqlite
sqlite_path = construction_dev.db
```

### Testing

```ini
[Database]
type = sqlite
sqlite_path = :memory:  # In-memory database for tests
```

### Production (PostgreSQL)

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction_prod
postgres_user = app_user
postgres_password = secure_password
pool_size = 10
max_overflow = 20
```

### Production (MSSQL)

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction_prod
mssql_user = app_user
mssql_password = secure_password
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 10
max_overflow = 20
```

## Integration with Application

### Startup Check

```python
def initialize_application():
    """Initialize application with schema check"""
    db_manager = DatabaseManager()
    db_manager.initialize("env.ini")
    
    schema_manager = db_manager.get_schema_manager()
    
    # Check if migrations are needed
    if schema_manager.needs_migration():
        print("WARNING: Database needs migration!")
        print("Run: alembic upgrade head")
        # Optionally auto-apply in development
        if is_development():
            schema_manager.upgrade_schema("head")
    
    # Verify schema
    result = schema_manager.verify_schema()
    if not result['valid']:
        raise RuntimeError("Database schema is invalid!")
```

### Health Check Endpoint

```python
@app.get("/health/database")
def database_health():
    """Database health check endpoint"""
    schema_manager = db_manager.get_schema_manager()
    result = schema_manager.verify_schema()
    
    return {
        "status": "healthy" if result['valid'] else "unhealthy",
        "current_revision": result['current_revision'],
        "head_revision": result['head_revision'],
        "needs_migration": result['needs_migration']
    }
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project-specific: `docs/SCHEMA_MIGRATION_IMPLEMENTATION.md`

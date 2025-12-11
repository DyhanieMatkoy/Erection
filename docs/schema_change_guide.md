# Schema Change Guide for Erection Project

This guide provides a standardized process for implementing database schema changes in the Erection project.

## Overview

The Erection project uses SQLAlchemy with Alembic for database migrations. This guide outlines the complete process for making schema changes, from planning to implementation.

## Process Overview

1. **Planning Phase**
   - Analyze requirements
   - Design schema changes
   - Create migration plan

2. **Implementation Phase**
   - Create database backup
   - Generate Alembic migration
   - Update SQLAlchemy models
   - Create data migration scripts (if needed)

3. **Testing Phase**
   - Test migration on development environment
   - Verify data integrity
   - Test application functionality

4. **Deployment Phase**
   - Apply migration to production
   - Monitor for issues
   - Update documentation

## Step-by-Step Guide

### 1. Planning Phase

#### 1.1. Analyze Requirements
- Understand the business requirements
- Identify affected tables and relationships
- Consider data migration needs
- Plan for backward compatibility

#### 1.2. Design Schema Changes
- Create ERD (Entity Relationship Diagram) for new schema
- Define new tables, columns, and relationships
- Plan indexes for performance optimization
- Document constraints and validation rules

#### 1.3. Create Migration Plan
- Document all changes in a markdown file
- Include before/after schema comparison
- List potential risks and mitigation strategies
- Define rollback strategy

### 2. Implementation Phase

#### 2.1. Create Database Backup
```bash
# For SQLite
cp construction.db construction_backup_YYYYMMDD.db

# For PostgreSQL
pg_dump erection_db > erection_backup_YYYYMMDD.sql

# For MSSQL
sqlcmd -S server_name -Q "BACKUP DATABASE erection_db TO DISK='C:\backup\erection_backup_YYYYMMDD.bak'"
```

#### 2.2. Generate Alembic Migration
```bash
# Generate new migration
python -m alembic revision --autogenerate -m "Description of changes"

# Or create manual migration
python -m alembic revision -m "Description of changes"
```

#### 2.3. Write Migration Script
Edit the generated migration file in `migrations/versions/`:

```python
"""Description of changes

Revision ID: xxx
Revises: yyy
Create Date: YYYY-MM-DD HH:MM:SS.SSSSSS

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade():
    # Add new tables
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add new columns
    op.add_column('existing_table', sa.Column('new_column', sa.String(length=50), nullable=True))
    
    # Add indexes
    op.create_index('ix_new_table_name', 'new_table', ['name'], unique=False)

def downgrade():
    # Remove indexes
    op.drop_index('ix_new_table_name', table_name='new_table')
    
    # Remove columns
    op.drop_column('existing_table', 'new_column')
    
    # Remove tables
    op.drop_table('new_table')
```

#### 2.4. Update SQLAlchemy Models
Update models in `src/data/models/sqlalchemy_models.py`:

```python
class NewTable(Base):
    __tablename__ = 'new_table'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    
    def __repr__(self):
        return f"<NewTable(id={self.id}, name='{self.name}')>"
```

#### 2.5. Create Data Migration Scripts (if needed)
Create scripts in `scripts/database/` for data migration:

```python
#!/usr/bin/env python3
"""
Script to migrate data for schema changes
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.database_manager import DatabaseManager

def migrate_data():
    """Migrate data according to schema changes"""
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    
    with db_manager.session_scope() as session:
        # Migration logic here
        pass

if __name__ == "__main__":
    migrate_data()
```

### 3. Testing Phase

#### 3.1. Test Migration on Development Environment
```bash
# Apply migration
python -m alembic upgrade head

# Verify schema
python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); print('Migration successful')"
```

#### 3.2. Verify Data Integrity
- Check that all data is correctly migrated
- Verify relationships are maintained
- Run data validation scripts

#### 3.3. Test Application Functionality
- Run unit tests
- Test affected UI components
- Verify API endpoints

### 4. Deployment Phase

#### 4.1. Apply Migration to Production
```bash
# Create production backup
# (See section 2.1 for backup commands)

# Apply migration
python -m alembic upgrade head
```

#### 4.2. Monitor for Issues
- Check application logs
- Monitor database performance
- Verify user workflows

#### 4.3. Update Documentation
- Update ERD diagrams
- Update API documentation
- Update user guides

## Best Practices

### Migration Scripts
1. Always provide both `upgrade()` and `downgrade()` methods
2. Use descriptive revision IDs and messages
3. Include comments explaining complex changes
4. Test downgrade paths

### Data Migration
1. Handle large datasets in batches
2. Provide progress feedback for long operations
3. Create rollback scripts for critical data
4. Validate data after migration

### Testing
1. Test migrations on a copy of production data
2. Verify both forward and rollback migrations
3. Test with different database backends if applicable
4. Include performance testing for large datasets

### Version Control
1. Commit migration files with model changes
2. Include migration documentation in commits
3. Tag releases with migration versions
4. Maintain migration history

## Common Scenarios

### Adding a New Table
1. Create Alembic migration with `op.create_table()`
2. Add SQLAlchemy model
3. Create repository class
4. Update UI components

### Adding a New Column
1. Create Alembic migration with `op.add_column()`
2. Update SQLAlchemy model
3. Handle default values for existing records
4. Update forms and views

### Changing Column Type
1. Create Alembic migration with `op.alter_column()`
2. Update SQLAlchemy model
3. Handle data conversion if needed
4. Update validation logic

### Adding Relationships
1. Add foreign key columns with `op.add_column()`
2. Create constraints with `op.create_foreign_key()`
3. Update SQLAlchemy models with relationships
4. Update repository methods

## Troubleshooting

### Migration Failures
1. Check database connection
2. Verify permissions
3. Check for conflicting constraints
4. Review SQL syntax

### Data Issues
1. Verify data types match schema
2. Check for NULL constraints
3. Validate foreign key relationships
4. Review character encoding

### Performance Issues
1. Add appropriate indexes
2. Optimize queries
3. Consider batch processing
4. Monitor query execution plans

## Rollback Procedures

### Automatic Rollback
```bash
# Rollback to previous revision
python -m alembic downgrade -1

# Rollback to specific revision
python -m alembic downgrade <revision_id>
```

### Manual Rollback
1. Restore database from backup
2. Identify and fix the issue
3. Reapply migrations correctly

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Database Migration Best Practices](https://docs.microsoft.com/en-us/azure/architecture/patterns/database-migration)
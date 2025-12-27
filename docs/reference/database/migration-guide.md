# Database Migration Guide

## Overview

This guide provides step-by-step instructions for migrating your construction management system from SQLite to PostgreSQL or Microsoft SQL Server.

## Quick Start

For a fast migration using the automated tool:

**Windows (using batch files):**

```bash
# 1. Backup your database
copy construction.db construction_backup.db

# 2. Set up target database and configure env_postgresql.ini or env_mssql.ini
# See Phase 2 below for detailed instructions

# 3. Run migration to PostgreSQL
migrate_to_postgresql.bat

# OR run migration to MSSQL
migrate_to_mssql.bat
```

**Manual (all platforms):**

```bash
# 1. Backup your database
copy construction.db construction_backup.db

# 2. Set up target database (PostgreSQL or MSSQL)
# See Phase 2 below for detailed instructions

# 3. Configure target database in env.ini
# See DATABASE_CONFIGURATION.md for examples

# 4. Run automated migration
python migrate_database.py --source construction.db --target-config env.ini --verify

# 5. Test the application
python main.py
```

## Migration Scenarios

1. **SQLite to PostgreSQL** - Recommended for production deployments
2. **SQLite to MSSQL** - For Windows-based enterprise environments
3. **Between PostgreSQL and MSSQL** - For infrastructure changes

## Prerequisites

### General Requirements

- Backup of existing SQLite database
- Administrative access to target database server
- Network connectivity to database server
- Python environment with required drivers installed

### PostgreSQL Requirements

- PostgreSQL 12 or later installed
- `psycopg2-binary` Python package installed
- Database administrator credentials

### MSSQL Requirements

- SQL Server 2017 or later installed
- ODBC Driver 17 for SQL Server installed
- `pyodbc` Python package installed
- Database administrator credentials

## Migration Process

### Phase 1: Preparation

#### Step 1: Backup Current Database

**Create a backup of your SQLite database:**

```bash
# Windows
copy construction.db construction_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

# Or use Python script
python -c "import shutil; import datetime; shutil.copy('construction.db', f'construction_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')"
```

#### Step 2: Verify Current Data

**Check data integrity:**

```bash
# Run verification script
python check_status.py

# Or manually check
sqlite3 construction.db "SELECT COUNT(*) FROM estimates;"
sqlite3 construction.db "SELECT COUNT(*) FROM persons;"
```

#### Step 3: Install Required Drivers

**For PostgreSQL:**

```bash
pip install psycopg2-binary
```

**For MSSQL:**

```bash
pip install pyodbc

# Verify ODBC driver installation
odbcinst -q -d
```

### Phase 2: Target Database Setup

#### PostgreSQL Setup

**1. Create database:**

```sql
-- Connect as postgres user
psql -U postgres

-- Create database
CREATE DATABASE construction
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create user
CREATE USER construction_app WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE construction TO construction_app;

-- Connect to database
\c construction

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO construction_app;
GRANT ALL ON ALL TABLES IN SCHEMA public TO construction_app;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO construction_app;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO construction_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO construction_app;
```

**2. Verify connection:**

```bash
psql -h localhost -U construction_app -d construction
```

#### MSSQL Setup

**1. Create database:**

```sql
-- Connect as sa or administrator
sqlcmd -S localhost -U sa

-- Create database
CREATE DATABASE construction
    COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

-- Create login
CREATE LOGIN construction_app WITH PASSWORD = 'YourSecurePassword123!';
GO

-- Use database
USE construction;
GO

-- Create user
CREATE USER construction_app FOR LOGIN construction_app;
GO

-- Grant permissions
ALTER ROLE db_owner ADD MEMBER construction_app;
GO
```

**2. Verify connection:**

```bash
sqlcmd -S localhost -U construction_app -P YourSecurePassword123! -d construction
```

### Phase 3: Schema Migration

#### Automatic Schema Creation

The system automatically creates the schema when connecting to an empty database.

**1. Update configuration:**

**For PostgreSQL:**

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = construction_app
postgres_password = your_secure_password
pool_size = 5
max_overflow = 10
```

**For MSSQL:**

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = construction_app
mssql_password = YourSecurePassword123!
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 5
max_overflow = 10
```

**2. Initialize schema:**

```python
from src.data.database_manager import DatabaseManager

# Initialize with new configuration
db_manager = DatabaseManager()
success = db_manager.initialize("env.ini")

if success:
    print("✓ Schema created successfully")
else:
    print("✗ Schema creation failed")
```

The system will automatically:
- Create all tables
- Set up foreign key constraints
- Create indexes
- Initialize sequences/auto-increment

#### Manual Schema Verification

**Verify tables were created:**

**PostgreSQL:**

```sql
-- List all tables
\dt

-- Check specific table
\d estimates

-- Count tables
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
```

**MSSQL:**

```sql
-- List all tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';

-- Check specific table
EXEC sp_help 'estimates';

-- Count tables
SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
```

### Phase 4: Data Migration

#### Option 1: Using Automated Migration Tool (Recommended)

The system includes an automated migration tool that handles the entire migration process.

**Usage:**

```bash
# Basic migration
python migrate_database.py --source construction.db --target-config env.ini

# Migration with verification
python migrate_database.py --source construction.db --target-config env.ini --verify

# Verify existing migration
python migrate_database.py --source construction.db --target-config env.ini --verify-only

# Verbose output
python migrate_database.py --source construction.db --target-config env.ini --verify --verbose
```

**Features:**
- Automatically migrates all tables in correct order (respecting foreign keys)
- Handles data type conversions (boolean, dates, etc.)
- Batch processing for large datasets
- Progress reporting
- Error handling with detailed logging
- Verification of record counts
- Rollback on failure

**Example output:**

```
============================================================
Starting database migration
============================================================
Migrating table: users
  Found 5 records to migrate
  ✓ Migrated 5 records (0 failed)
Migrating table: persons
  Found 25 records to migrate
  ✓ Migrated 25 records (0 failed)
...
============================================================
Migration Summary
============================================================
✓ users: 5 migrated, 0 failed
✓ persons: 25 migrated, 0 failed
✓ estimates: 150 migrated, 0 failed
------------------------------------------------------------
Total: 500 records migrated, 0 failed
============================================================
```

#### Option 2: Using Custom SQLAlchemy Script

For advanced scenarios, create a custom migration script:

```python
# migrate_data.py
import sqlite3
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import *
from sqlalchemy.orm import Session

def migrate_sqlite_to_target():
    """Migrate data from SQLite to target database"""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('construction.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to target database
    db_manager = DatabaseManager()
    db_manager.initialize("env.ini")
    
    with db_manager.session_scope() as session:
        # Migrate users
        print("Migrating users...")
        cursor = sqlite_conn.execute("SELECT * FROM users")
        for row in cursor:
            user = User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                role=row['role'],
                is_active=bool(row['is_active'])
            )
            session.add(user)
        session.flush()
        
        # Migrate persons
        print("Migrating persons...")
        cursor = sqlite_conn.execute("SELECT * FROM persons")
        for row in cursor:
            person = Person(
                id=row['id'],
                full_name=row['full_name'],
                position=row['position'],
                phone=row['phone'],
                hourly_rate=row['hourly_rate'],
                user_id=row['user_id'],
                parent_id=row['parent_id'],
                marked_for_deletion=bool(row['marked_for_deletion'])
            )
            session.add(person)
        session.flush()
        
        # Migrate organizations
        print("Migrating organizations...")
        cursor = sqlite_conn.execute("SELECT * FROM organizations")
        for row in cursor:
            org = Organization(
                id=row['id'],
                name=row['name'],
                inn=row['inn'],
                address=row['address'],
                phone=row['phone'],
                marked_for_deletion=bool(row['marked_for_deletion'])
            )
            session.add(org)
        session.flush()
        
        # Continue for all tables...
        # See full migration script in migration_scripts/migrate_data.py
        
        print("Migration completed successfully!")
    
    sqlite_conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_target()
```

**Run migration:**

```bash
python migrate_data.py
```

#### Option 3: Using Database Tools

**PostgreSQL (using pgloader):**

```bash
# Install pgloader
# Windows: Download from https://github.com/dimitri/pgloader/releases

# Create migration config
cat > migration.load << EOF
LOAD DATABASE
    FROM sqlite://construction.db
    INTO postgresql://construction_app:password@localhost/construction
    WITH include drop, create tables, create indexes, reset sequences
    SET work_mem to '16MB', maintenance_work_mem to '512 MB';
EOF

# Run migration
pgloader migration.load
```

**MSSQL (using SQL Server Migration Assistant):**

1. Download SSMA for Access (works with SQLite)
2. Create new migration project
3. Connect to SQLite database
4. Connect to SQL Server
5. Map schema
6. Migrate data

#### Option 4: Export/Import via CSV

**Export from SQLite:**

```python
# export_data.py
import sqlite3
import csv
import os

def export_table(conn, table_name):
    """Export table to CSV"""
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    
    # Get column names
    columns = [description[0] for description in cursor.description]
    
    # Write to CSV
    os.makedirs('migration_data', exist_ok=True)
    with open(f'migration_data/{table_name}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(cursor)
    
    print(f"✓ Exported {table_name}")

# Export all tables
conn = sqlite3.connect('construction.db')
tables = ['users', 'persons', 'organizations', 'counterparties', 
          'objects', 'works', 'estimates', 'estimate_lines', 
          'daily_reports', 'daily_report_lines', 'timesheets', 
          'timesheet_lines', 'work_execution_register', 'payroll_register']

for table in tables:
    export_table(conn, table)

conn.close()
print("Export completed!")
```

**Import to PostgreSQL:**

```sql
-- Import users
COPY users FROM '/path/to/migration_data/users.csv' 
    WITH (FORMAT csv, HEADER true);

-- Import persons
COPY persons FROM '/path/to/migration_data/persons.csv' 
    WITH (FORMAT csv, HEADER true);

-- Continue for all tables...

-- Reset sequences
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('persons_id_seq', (SELECT MAX(id) FROM persons));
-- Continue for all sequences...
```

**Import to MSSQL:**

```sql
-- Import users
BULK INSERT users
FROM 'C:\migration_data\users.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

-- Continue for all tables...

-- Reset identity columns
DBCC CHECKIDENT ('users', RESEED, (SELECT MAX(id) FROM users));
DBCC CHECKIDENT ('persons', RESEED, (SELECT MAX(id) FROM persons));
-- Continue for all tables...
```

### Phase 5: Verification

#### Data Integrity Checks

**1. Count records:**

```python
# verify_migration.py
import sqlite3
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import *

def verify_counts():
    """Verify record counts match"""
    
    # SQLite counts
    sqlite_conn = sqlite3.connect('construction.db')
    sqlite_counts = {}
    
    tables = ['users', 'persons', 'organizations', 'estimates', 'daily_reports']
    for table in tables:
        cursor = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_counts[table] = cursor.fetchone()[0]
    
    sqlite_conn.close()
    
    # Target database counts
    db_manager = DatabaseManager()
    db_manager.initialize("env.ini")
    
    target_counts = {}
    with db_manager.session_scope() as session:
        target_counts['users'] = session.query(User).count()
        target_counts['persons'] = session.query(Person).count()
        target_counts['organizations'] = session.query(Organization).count()
        target_counts['estimates'] = session.query(Estimate).count()
        target_counts['daily_reports'] = session.query(DailyReport).count()
    
    # Compare
    print("\nMigration Verification:")
    print("-" * 50)
    all_match = True
    for table in tables:
        sqlite_count = sqlite_counts[table]
        target_count = target_counts[table]
        match = "✓" if sqlite_count == target_count else "✗"
        print(f"{match} {table}: SQLite={sqlite_count}, Target={target_count}")
        if sqlite_count != target_count:
            all_match = False
    
    print("-" * 50)
    if all_match:
        print("✓ All counts match!")
    else:
        print("✗ Count mismatch detected!")
    
    return all_match

if __name__ == "__main__":
    verify_counts()
```

**2. Test application functionality:**

```bash
# Start application with new database
python main.py

# Test key operations:
# - Login
# - View estimates
# - Create new estimate
# - View daily reports
# - Run reports
```

**3. Check foreign key integrity:**

**PostgreSQL:**

```sql
-- Check for orphaned records
SELECT 'estimates' as table_name, COUNT(*) as orphaned
FROM estimates e
LEFT JOIN counterparties c ON e.customer_id = c.id
WHERE e.customer_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT 'estimate_lines', COUNT(*)
FROM estimate_lines el
LEFT JOIN estimates e ON el.estimate_id = e.id
WHERE el.estimate_id IS NOT NULL AND e.id IS NULL;
```

**MSSQL:**

```sql
-- Check for orphaned records
SELECT 'estimates' as table_name, COUNT(*) as orphaned
FROM estimates e
LEFT JOIN counterparties c ON e.customer_id = c.id
WHERE e.customer_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT 'estimate_lines', COUNT(*)
FROM estimate_lines el
LEFT JOIN estimates e ON el.estimate_id = e.id
WHERE el.estimate_id IS NOT NULL AND e.id IS NULL;
```

### Phase 6: Cutover

#### Preparation

1. **Schedule downtime** - Inform users of migration window
2. **Final backup** - Create final SQLite backup
3. **Stop services** - Stop all applications using the database
4. **Final data sync** - Migrate any changes since last migration

#### Cutover Steps

**1. Update configuration:**

```ini
# env.ini - Switch to new database
[Database]
type = postgresql  # or mssql
# ... rest of configuration
```

**2. Test connection:**

```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()
if db_manager.initialize("env.ini"):
    print("✓ Connected to new database")
else:
    print("✗ Connection failed - ROLLBACK")
```

**3. Start application:**

```bash
python main.py
```

**4. Verify functionality:**

- Test all major features
- Check data accuracy
- Verify reports
- Test concurrent access (if applicable)

#### Rollback Plan

If issues occur, rollback to SQLite:

```ini
# env.ini - Rollback to SQLite
[Database]
type = sqlite
sqlite_path = construction.db
```

```bash
# Restore from backup if needed
copy construction_backup_YYYYMMDD.db construction.db

# Restart application
python main.py
```

## Post-Migration Tasks

### Performance Optimization

**PostgreSQL:**

```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- Create additional indexes if needed
CREATE INDEX idx_estimates_date ON estimates(date);
CREATE INDEX idx_daily_reports_date ON daily_reports(date);
```

**MSSQL:**

```sql
-- Update statistics
EXEC sp_updatestats;

-- Rebuild indexes
ALTER INDEX ALL ON estimates REBUILD;
ALTER INDEX ALL ON daily_reports REBUILD;

-- Create additional indexes if needed
CREATE INDEX idx_estimates_date ON estimates(date);
CREATE INDEX idx_daily_reports_date ON daily_reports(date);
```

### Monitoring Setup

**1. Enable query logging:**

**PostgreSQL (postgresql.conf):**

```ini
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000  # Log queries > 1 second
```

**MSSQL:**

```sql
-- Enable query store
ALTER DATABASE construction SET QUERY_STORE = ON;
```

**2. Monitor connection pool:**

Check application logs for:
- Connection pool exhaustion
- Slow queries
- Connection timeouts

### Backup Strategy

**PostgreSQL:**

```bash
# Daily backup script
pg_dump -h localhost -U construction_app -d construction > backup_$(date +%Y%m%d).sql

# Automated backup (cron/Task Scheduler)
0 2 * * * /usr/bin/pg_dump -h localhost -U construction_app -d construction > /backups/construction_$(date +\%Y\%m\%d).sql
```

**MSSQL:**

```sql
-- Full backup
BACKUP DATABASE construction 
TO DISK = 'C:\Backups\construction_full.bak'
WITH FORMAT, COMPRESSION;

-- Differential backup
BACKUP DATABASE construction 
TO DISK = 'C:\Backups\construction_diff.bak'
WITH DIFFERENTIAL, COMPRESSION;
```

## Troubleshooting

See [TROUBLESHOOTING_DATABASE.md](TROUBLESHOOTING_DATABASE.md) for common migration issues and solutions.

## Migration Checklist

- [ ] Backup current SQLite database
- [ ] Verify current data integrity
- [ ] Install required database drivers
- [ ] Set up target database server
- [ ] Create database and user
- [ ] Grant appropriate permissions
- [ ] Update env.ini configuration
- [ ] Run schema migration (automatic on first connection)
- [ ] Verify schema creation
- [ ] Run data migration using `migrate_database.py` tool
  ```bash
  python migrate_database.py --source construction.db --target-config env.ini --verify
  ```
- [ ] Verify data integrity (automatic with --verify flag)
- [ ] Test application functionality
- [ ] Check foreign key constraints
- [ ] Perform cutover
- [ ] Monitor for issues
- [ ] Set up backup strategy
- [ ] Document configuration
- [ ] Train team on new setup

## Automated Migration Tool

The `migrate_database.py` tool provides automated migration with the following features:

- Automatic schema creation
- Batch processing with progress reporting
- Data type conversion
- Error handling and rollback
- Built-in verification
- Detailed logging

See [MIGRATION_TOOL_README.md](../MIGRATION_TOOL_README.md) for complete documentation.

## Support

For migration assistance:
1. Check [MIGRATION_TOOL_README.md](../MIGRATION_TOOL_README.md) for tool documentation
2. Check [TROUBLESHOOTING_DATABASE.md](TROUBLESHOOTING_DATABASE.md) for common issues
3. Review application logs
4. Check database server logs
5. Verify network connectivity
6. Confirm credentials and permissions

## Next Steps

- Configure connection pooling for optimal performance
- Set up monitoring and alerting
- Implement backup and recovery procedures
- Review security settings
- Plan for high availability (if needed)

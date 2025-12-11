# Database Migration Tool

Automated tool for migrating data from SQLite to PostgreSQL or Microsoft SQL Server.

## Features

- ✅ Automatic schema creation in target database
- ✅ Migrates all tables in correct order (respects foreign key dependencies)
- ✅ Handles data type conversions automatically
- ✅ Batch processing for large datasets
- ✅ Progress reporting and detailed logging
- ✅ Built-in verification of record counts
- ✅ Error handling with rollback on failure
- ✅ Supports SQLite → PostgreSQL migration
- ✅ Supports SQLite → MSSQL migration

## Prerequisites

1. Source SQLite database file
2. Target database server (PostgreSQL or MSSQL) installed and running
3. Target database created with appropriate user permissions
4. Configuration file (env.ini) with target database settings

## Quick Start

### 1. Backup Your Database

```bash
copy construction.db construction_backup.db
```

### 2. Configure Target Database

Create or update `env.ini` with target database settings:

**For PostgreSQL:**

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = construction_app
postgres_password = your_password
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
mssql_password = your_password
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 5
max_overflow = 10
```

### 3. Run Migration

```bash
# Basic migration
python migrate_database.py --source construction.db --target-config env.ini

# Migration with verification
python migrate_database.py --source construction.db --target-config env.ini --verify
```

## Usage

### Command Line Options

```
python migrate_database.py [OPTIONS]

Required Arguments:
  --source SOURCE              Path to source SQLite database file
  --target-config CONFIG       Path to target database configuration file

Optional Arguments:
  --verify                     Verify migration after completion
  --verify-only                Only verify existing migration (do not migrate)
  --verbose                    Enable verbose logging
  -h, --help                   Show help message
```

### Examples

**Migrate to PostgreSQL:**

```bash
python migrate_database.py --source construction.db --target-config env_postgresql.ini
```

**Migrate to MSSQL with verification:**

```bash
python migrate_database.py --source construction.db --target-config env_mssql.ini --verify
```

**Verify existing migration:**

```bash
python migrate_database.py --source construction.db --target-config env.ini --verify-only
```

**Verbose output for debugging:**

```bash
python migrate_database.py --source construction.db --target-config env.ini --verify --verbose
```

## Migration Process

The tool performs the following steps:

1. **Connect to source database** - Opens SQLite database file
2. **Connect to target database** - Connects using configuration file
3. **Create schema** - Target database schema is created automatically
4. **Migrate tables** - Tables are migrated in dependency order:
   - users
   - persons
   - organizations
   - counterparties
   - objects
   - works
   - estimates
   - estimate_lines
   - daily_reports
   - daily_report_lines
   - daily_report_executors
   - timesheets
   - timesheet_lines
   - work_execution_register
   - payroll_register
   - user_settings
   - constants
5. **Verify migration** (if --verify flag used) - Compares record counts

## Output

### Successful Migration

```
============================================================
Starting database migration
============================================================
Connecting to source database: construction.db
✓ Connected to source database
Connecting to target database using config: env.ini
✓ Connected to target database (postgresql)
Migrating table: users
  Found 5 records to migrate
  ✓ Migrated 5 records (0 failed)
Migrating table: persons
  Found 25 records to migrate
  ✓ Migrated 25 records (0 failed)
Migrating table: estimates
  Found 150 records to migrate
  Migrated 100/150 records
  ✓ Migrated 150 records (0 failed)
...
============================================================
Migration Summary
============================================================
✓ users: 5 migrated, 0 failed
✓ persons: 25 migrated, 0 failed
✓ organizations: 10 migrated, 0 failed
✓ estimates: 150 migrated, 0 failed
✓ estimate_lines: 500 migrated, 0 failed
------------------------------------------------------------
Total: 690 records migrated, 0 failed
============================================================
✓ Migration completed successfully!
```

### With Verification

```
============================================================
Verifying migration
============================================================
✓ users: Source=5, Target=5
✓ persons: Source=25, Target=25
✓ organizations: Source=10, Target=10
✓ estimates: Source=150, Target=150
✓ estimate_lines: Source=500, Target=500
============================================================
✓ Verification successful! All counts match.
============================================================
```

## Troubleshooting

### Connection Errors

**Problem:** Cannot connect to target database

**Solution:**
1. Verify database server is running
2. Check connection parameters in env.ini
3. Test connection manually:
   ```bash
   # PostgreSQL
   psql -h localhost -U construction_app -d construction
   
   # MSSQL
   sqlcmd -S localhost -U construction_app -d construction
   ```

### Migration Failures

**Problem:** Some records fail to migrate

**Solution:**
1. Check logs for specific error messages
2. Verify foreign key references exist
3. Check data type compatibility
4. Run with --verbose flag for detailed output

### Verification Mismatches

**Problem:** Record counts don't match

**Solution:**
1. Check for migration errors in logs
2. Verify all tables were migrated
3. Check for records marked for deletion
4. Re-run migration if needed

## Data Type Conversions

The tool automatically handles these conversions:

| SQLite Type | PostgreSQL/MSSQL Type | Notes |
|-------------|----------------------|-------|
| INTEGER (0/1) | BOOLEAN | For is_active, marked_for_deletion fields |
| TEXT | VARCHAR/NVARCHAR | String fields |
| REAL | FLOAT/DECIMAL | Numeric fields |
| TEXT (dates) | DATE | Date fields |
| TEXT (timestamps) | TIMESTAMP/DATETIME | Timestamp fields |

## Performance

- **Batch size:** 100 records per commit
- **Progress reporting:** Every 100 records
- **Typical speed:** 1000-5000 records/second (depends on network and server)

## Safety Features

- **Rollback on error:** Transaction is rolled back if any error occurs
- **Non-destructive:** Source database is never modified
- **Verification:** Optional verification ensures data integrity
- **Logging:** Detailed logs for troubleshooting

## Post-Migration

After successful migration:

1. **Test application:**
   ```bash
   python main.py
   ```

2. **Verify functionality:**
   - Login
   - View estimates
   - Create new records
   - Run reports

3. **Update configuration:**
   - Keep env.ini pointing to new database
   - Archive old SQLite database

4. **Set up backups:**
   - Configure regular database backups
   - Test restore procedures

## Related Documentation

- [DATABASE_CONFIGURATION.md](docs/DATABASE_CONFIGURATION.md) - Database configuration guide
- [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) - Complete migration guide
- [TROUBLESHOOTING_DATABASE.md](docs/TROUBLESHOOTING_DATABASE.md) - Troubleshooting guide

## Support

For issues or questions:
1. Check [TROUBLESHOOTING_DATABASE.md](docs/TROUBLESHOOTING_DATABASE.md)
2. Review application logs
3. Run with --verbose flag for detailed output
4. Check database server logs

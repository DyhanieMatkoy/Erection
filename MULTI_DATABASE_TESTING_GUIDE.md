# Multi-Database Synchronization Testing Guide

## Overview

This guide describes the comprehensive multi-database testing system for validating synchronization between desktop clients and server across different database types (PostgreSQL, MySQL, SQLite) and Alembic schema migrations.

## Features

### Supported Database Types
- **PostgreSQL** (PostgreSQL_1C_17.4_64bit)
- **MySQL** 
- **SQLite**

### Test Scenarios
1. **PostgreSQL Mixed**: PostgreSQL server with SQLite + MySQL clients
2. **MySQL Mixed**: MySQL server with SQLite + MySQL clients  
3. **SQLite MySQL**: SQLite server with MySQL clients

### Testing Capabilities
- Cross-database synchronization validation
- Alembic schema migration propagation testing
- Data integrity verification across database types
- Performance monitoring and reporting
- Automated error detection and reporting

## Quick Start

### Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip install psycopg2-binary pymysql alembic sqlalchemy
   ```

2. **Database Servers** (for non-SQLite testing):
   - PostgreSQL server running on localhost:5432
   - MySQL server running on localhost:3306

3. **Project Setup**:
   - Ensure the main application is properly configured
   - Alembic is initialized with `alembic.ini`

### Running Tests

#### Option 1: Interactive Script (Recommended)
```bash
run_multi_database_tests.bat
```

#### Option 2: Command Line

**Run all scenarios:**
```bash
python test_multi_database_sync.py --all-scenarios --verbose
```

**Run specific scenario:**
```bash
python test_multi_database_sync.py --scenario postgresql_mixed --verbose
```

**Migration tests only:**
```bash
python test_multi_database_sync.py --migration-tests-only --verbose
```

**List available scenarios:**
```bash
python test_multi_database_sync.py --list-scenarios
```

## Test Scenarios Detail

### Scenario 1: PostgreSQL Mixed
- **Server**: PostgreSQL database
- **Client 1**: SQLite local database
- **Client 2**: MySQL local database
- **Client 3**: MySQL local database
- **Tests**: Document sync + Alembic migrations
- **Duration**: ~5 minutes

### Scenario 2: MySQL Mixed
- **Server**: MySQL database
- **Client 1**: SQLite local database
- **Client 2**: SQLite local database
- **Client 3**: MySQL local database
- **Tests**: Document sync + Alembic migrations
- **Duration**: ~4.5 minutes

### Scenario 3: SQLite MySQL
- **Server**: SQLite database
- **Client 1**: MySQL local database
- **Client 2**: MySQL local database
- **Client 3**: MySQL local database
- **Tests**: Document sync + Alembic migrations
- **Duration**: ~4 minutes

## Test Process

### Phase 1: Environment Setup
1. Configure server database (PostgreSQL/MySQL/SQLite)
2. Create isolated client databases
3. Start server with appropriate database configuration
4. Initialize desktop clients with specific database types
5. Verify connectivity between all components

### Phase 2: Document Creation and Sync
1. Create different document types on each client:
   - Client 1: Estimate document
   - Client 2: Daily report document
   - Client 3: Timesheet document
2. Trigger manual synchronization on each client
3. Verify all documents appear on all clients
4. Validate data integrity and consistency

### Phase 3: Schema Migration Testing
1. Create test migration scripts using Alembic
2. Execute migrations on server database
3. Trigger synchronization to propagate schema changes
4. Verify schema consistency across all database types
5. Test migration rollback capabilities

### Phase 4: Validation and Reporting
1. Perform comprehensive schema comparison
2. Validate cross-database data type mappings
3. Check foreign key relationships and constraints
4. Generate detailed test reports

## Migration Test Types

### 1. Add New Table
```python
# Creates project_phases table with columns and relationships
add_project_phases_table = {
    'operations': [
        {
            'type': 'create_table',
            'table_name': 'project_phases',
            'columns': [...]
        }
    ]
}
```

### 2. Add New Column
```python
# Adds priority column to estimates table
add_priority_to_estimates = {
    'operations': [
        {
            'type': 'add_column',
            'table_name': 'estimates',
            'column': {'name': 'priority', 'type': 'Integer', 'default': 1}
        }
    ]
}
```

### 3. Modify Column Type
```python
# Extends description field length
extend_description_length = {
    'operations': [
        {
            'type': 'alter_column',
            'table_name': 'daily_reports',
            'column_name': 'description',
            'new_type': 'String(500)'
        }
    ]
}
```

### 4. Add Indexes
```python
# Creates performance indexes
add_indexes_for_performance = {
    'operations': [
        {
            'type': 'create_index',
            'table_name': 'estimates',
            'columns': ['created_at', 'status'],
            'index_name': 'idx_estimates_created_status'
        }
    ]
}
```

### 5. Add Foreign Keys
```python
# Creates foreign key constraints
add_foreign_key_constraints = {
    'operations': [
        {
            'type': 'create_foreign_key',
            'table_name': 'estimate_items',
            'column_name': 'estimate_id',
            'referenced_table': 'estimates',
            'referenced_column': 'id'
        }
    ]
}
```

## Database Configuration

### PostgreSQL Setup
```sql
-- Create test database and user
CREATE DATABASE construction_test_db;
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE construction_test_db TO test_user;
```

### MySQL Setup
```sql
-- Create test database and user
CREATE DATABASE construction_test_db;
CREATE USER 'test_user'@'localhost' IDENTIFIED BY 'test_password';
GRANT ALL PRIVILEGES ON construction_test_db.* TO 'test_user'@'localhost';
FLUSH PRIVILEGES;
```

### SQLite Setup
No additional setup required - databases are created automatically.

## Configuration Files

### Multi-Database Config (`test_configs/multi_database_config.ini`)
```ini
[PostgreSQL]
host = localhost
port = 5432
database = construction_test_db
username = test_user
password = test_password

[MySQL]
host = localhost
port = 3306
database = construction_test_db
username = test_user
password = test_password

[SQLite]
database_path = test_databases/server_test.db
```

### Environment Variables
```bash
# Optional: Override default database passwords
export POSTGRES_PASSWORD=your_postgres_password
export MYSQL_ROOT_PASSWORD=your_mysql_root_password
```

## Test Reports

### Report Types Generated
1. **JSON Report**: Detailed machine-readable results
2. **Text Report**: Human-readable comprehensive report
3. **Summary Report**: Executive summary with key metrics

### Report Location
```
test_reports/
├── multi_database_sync_report_YYYYMMDD_HHMMSS.json
├── multi_database_sync_report_YYYYMMDD_HHMMSS.txt
└── multi_database_sync_summary_YYYYMMDD_HHMMSS.txt
```

### Key Metrics Tracked
- Test execution duration
- Document creation success rate
- Synchronization success rate
- Data verification results
- Migration execution status
- Schema consistency validation
- Cross-database compatibility
- Performance metrics

## Troubleshooting

### Common Issues

#### Database Connection Failures
```bash
# Check PostgreSQL service
net start postgresql-x64-17

# Check MySQL service  
net start mysql80

# Verify database credentials
psql -h localhost -U test_user -d construction_test_db
mysql -h localhost -u test_user -p construction_test_db
```

#### Migration Failures
```bash
# Check Alembic configuration
alembic current
alembic history

# Verify migration files
ls alembic/versions/

# Reset migration state if needed
alembic stamp head
```

#### Sync Service Issues
```bash
# Check server connectivity
curl http://localhost:8000/api/health

# Verify client registration
# Check test logs in test_logs/ directory
```

### Debug Mode
```bash
# Run with verbose logging
python test_multi_database_sync.py --scenario postgresql_mixed --verbose

# Skip cleanup for debugging
python test_multi_database_sync.py --scenario postgresql_mixed --no-cleanup
```

### Log Files
```
test_logs/
├── sync_test_SESSION_ID_TIMESTAMP.log
└── multi_database_test_SESSION_ID.log
```

## Advanced Usage

### Custom Migration Testing
```python
# Create custom migration for testing
custom_migration = {
    'name': 'add_custom_table',
    'description': 'Add custom table for testing',
    'operations': [
        {
            'type': 'create_table',
            'table_name': 'custom_test_table',
            'columns': [
                {'name': 'id', 'type': 'Integer', 'primary_key': True},
                {'name': 'name', 'type': 'String(100)', 'nullable': False}
            ]
        }
    ]
}

# Execute custom migration test
python test_multi_database_sync.py --migration-tests-only --custom-migration custom_migration.json
```

### Performance Benchmarking
```bash
# Run performance-focused tests
python test_multi_database_sync.py --all-scenarios --benchmark-mode
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run Multi-Database Tests
  run: |
    python test_multi_database_sync.py --all-scenarios --report-format json
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: test_reports/
```

## Success Criteria

### Test Passes When:
- ✅ All database types connect successfully
- ✅ Documents sync across all client-server combinations
- ✅ Schema migrations propagate to all clients
- ✅ Data integrity maintained across database types
- ✅ No sync errors or timeouts occur
- ✅ Cross-database type mappings work correctly
- ✅ Foreign key relationships preserved
- ✅ Performance within acceptable limits

### Test Fails When:
- ❌ Database connectivity issues
- ❌ Document sync failures
- ❌ Schema inconsistencies after migration
- ❌ Data corruption or loss
- ❌ Sync timeouts or errors
- ❌ Cross-database compatibility issues

## Integration with Deployment

The multi-database testing system integrates with the existing deployment workflow:

1. **Pre-deployment**: Run full test suite to validate changes
2. **Staging**: Execute specific scenarios matching production setup
3. **Production**: Monitor using same validation logic
4. **Rollback**: Use migration rollback capabilities if issues detected

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test logs in `test_logs/` directory
3. Examine detailed reports in `test_reports/` directory
4. Verify database server status and connectivity
5. Ensure all required Python packages are installed
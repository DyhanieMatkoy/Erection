# Database Troubleshooting Guide

## Overview

This guide provides solutions to common database connection and operation issues for SQLite, PostgreSQL, and Microsoft SQL Server backends.

## Quick Diagnostics

### Check Database Connection

```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()
success = db_manager.initialize("env.ini")

if success:
    print("✓ Database connection successful")
    print(f"Backend: {db_manager._config.db_type}")
else:
    print("✗ Database connection failed")
    print("Check logs for details")
```

### Check Configuration

```python
from src.data.database_config import DatabaseConfig

config = DatabaseConfig("env.ini")
print(f"Database type: {config.db_type}")
print(f"Configuration valid: {config.validate()}")
```

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Common Issues by Backend

## SQLite Issues

### Issue: Database is Locked

**Symptoms:**
- Error: `database is locked`
- Operations hang or timeout
- Cannot write to database

**Causes:**
- Another process has the database open
- Desktop application is running
- Incomplete transaction
- File system lock

**Solutions:**

**1. Close other connections:**

```bash
# Windows - Find processes using the file
handle.exe construction.db

# Or use Process Explorer to find the process
```

**2. Check for hung transactions:**

```python
import sqlite3

conn = sqlite3.connect('construction.db', timeout=10)
conn.execute("PRAGMA busy_timeout = 10000")  # 10 second timeout
```

**3. Use WAL mode for better concurrency:**

```python
import sqlite3

conn = sqlite3.connect('construction.db')
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
```

**4. Restart application:**

```bash
# Close all applications using the database
# Restart the application
python main.py
```

### Issue: Database File Not Found

**Symptoms:**
- Error: `unable to open database file`
- Application fails to start

**Causes:**
- Incorrect path in configuration
- File doesn't exist
- Permission issues

**Solutions:**

**1. Check file path:**

```ini
[Database]
type = sqlite
sqlite_path = construction.db  # Relative to project root
```

**2. Create database if missing:**

```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize("env.ini")  # Will create if doesn't exist
```

**3. Check file permissions:**

```bash
# Windows - Check file properties
# Ensure user has read/write permissions
```

### Issue: Database Corruption

**Symptoms:**
- Error: `database disk image is malformed`
- Unexpected query results
- Application crashes

**Solutions:**

**1. Check integrity:**

```bash
sqlite3 construction.db "PRAGMA integrity_check;"
```

**2. Attempt recovery:**

```bash
# Dump and restore
sqlite3 construction.db ".dump" > backup.sql
sqlite3 construction_new.db < backup.sql

# Replace corrupted database
move construction.db construction_corrupted.db
move construction_new.db construction.db
```

**3. Restore from backup:**

```bash
copy construction_backup.db construction.db
```

## PostgreSQL Issues

### Issue: Connection Refused

**Symptoms:**
- Error: `could not connect to server: Connection refused`
- Error: `Is the server running on host "localhost" and accepting TCP/IP connections on port 5432?`

**Causes:**
- PostgreSQL server not running
- Wrong host/port
- Firewall blocking connection
- PostgreSQL not configured to accept TCP connections

**Solutions:**

**1. Check if PostgreSQL is running:**

```bash
# Windows
sc query postgresql-x64-14

# Linux
sudo systemctl status postgresql

# Or check process
psql -U postgres -c "SELECT version();"
```

**2. Start PostgreSQL:**

```bash
# Windows
net start postgresql-x64-14

# Linux
sudo systemctl start postgresql
```

**3. Verify host and port:**

```ini
[Database]
type = postgresql
postgres_host = localhost  # Try 127.0.0.1 if localhost fails
postgres_port = 5432       # Default PostgreSQL port
```

**4. Check PostgreSQL configuration (postgresql.conf):**

```ini
listen_addresses = '*'  # Or 'localhost' for local only
port = 5432
```

**5. Check pg_hba.conf for connection permissions:**

```
# Allow local connections
host    all    all    127.0.0.1/32    md5
host    all    all    ::1/128         md5
```

**6. Restart PostgreSQL after config changes:**

```bash
# Windows
net stop postgresql-x64-14
net start postgresql-x64-14

# Linux
sudo systemctl restart postgresql
```

### Issue: Authentication Failed

**Symptoms:**
- Error: `FATAL: password authentication failed for user "construction_app"`
- Error: `FATAL: role "construction_app" does not exist`

**Causes:**
- Wrong username or password
- User doesn't exist
- Insufficient permissions

**Solutions:**

**1. Verify credentials:**

```bash
# Test connection manually
psql -h localhost -U construction_app -d construction
```

**2. Reset password:**

```sql
-- Connect as postgres superuser
psql -U postgres

-- Reset password
ALTER USER construction_app WITH PASSWORD 'new_password';
```

**3. Create user if doesn't exist:**

```sql
-- Connect as postgres
psql -U postgres

-- Create user
CREATE USER construction_app WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE construction TO construction_app;
```

**4. Check pg_hba.conf authentication method:**

```
# Use md5 or scram-sha-256 for password authentication
host    construction    construction_app    127.0.0.1/32    md5
```

### Issue: Database Does Not Exist

**Symptoms:**
- Error: `FATAL: database "construction" does not exist`

**Solutions:**

**1. Create database:**

```sql
-- Connect as postgres
psql -U postgres

-- Create database
CREATE DATABASE construction;
GRANT ALL PRIVILEGES ON DATABASE construction TO construction_app;
```

**2. Verify database name in configuration:**

```ini
[Database]
postgres_database = construction  # Must match actual database name
```

### Issue: Connection Pool Exhausted

**Symptoms:**
- Error: `QueuePool limit of size X overflow Y reached`
- Application hangs waiting for connections
- Slow response times

**Causes:**
- Too many concurrent requests
- Connections not being released
- Pool size too small

**Solutions:**

**1. Increase pool size:**

```ini
[Database]
pool_size = 10        # Increase from default 5
max_overflow = 20     # Increase from default 10
pool_timeout = 60     # Increase timeout
```

**2. Check for connection leaks:**

```python
# Ensure using context manager
with db_manager.session_scope() as session:
    # Do work
    pass  # Session automatically closed
```

**3. Monitor connection usage:**

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity 
WHERE datname = 'construction';

-- Check connection details
SELECT pid, usename, application_name, state, query 
FROM pg_stat_activity 
WHERE datname = 'construction';
```

**4. Kill stuck connections:**

```sql
-- Kill specific connection
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'construction' AND pid = <pid>;
```

### Issue: Slow Queries

**Symptoms:**
- Application feels sluggish
- Queries take long time
- Timeouts

**Solutions:**

**1. Analyze query performance:**

```sql
-- Enable query logging (postgresql.conf)
log_min_duration_statement = 1000  # Log queries > 1 second

-- Analyze specific query
EXPLAIN ANALYZE SELECT * FROM estimates WHERE date > '2024-01-01';
```

**2. Update statistics:**

```sql
ANALYZE;
```

**3. Add indexes:**

```sql
-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC;

-- Create indexes for frequently queried columns
CREATE INDEX idx_estimates_date ON estimates(date);
CREATE INDEX idx_estimates_responsible ON estimates(responsible_id);
```

**4. Vacuum database:**

```sql
VACUUM ANALYZE;
```

## Microsoft SQL Server Issues

### Issue: Cannot Connect to Server

**Symptoms:**
- Error: `[Microsoft][ODBC Driver 17 for SQL Server]Named Pipes Provider: Could not open a connection to SQL Server`
- Error: `Login timeout expired`

**Causes:**
- SQL Server not running
- Wrong server name
- TCP/IP not enabled
- Firewall blocking connection

**Solutions:**

**1. Check if SQL Server is running:**

```bash
# Windows Services
sc query MSSQLSERVER

# Or
net start MSSQLSERVER
```

**2. Enable TCP/IP:**

```
1. Open SQL Server Configuration Manager
2. SQL Server Network Configuration > Protocols for MSSQLSERVER
3. Enable TCP/IP
4. Restart SQL Server service
```

**3. Check firewall:**

```bash
# Add firewall rule for SQL Server
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
```

**4. Verify server name:**

```ini
[Database]
mssql_host = localhost          # For default instance
# OR
mssql_host = localhost\SQLEXPRESS  # For named instance
```

**5. Test connection:**

```bash
sqlcmd -S localhost -U construction_app -P password
```

### Issue: ODBC Driver Not Found

**Symptoms:**
- Error: `[Microsoft][ODBC Driver Manager] Data source name not found and no default driver specified`
- Error: `Can't open lib 'ODBC Driver 17 for SQL Server'`

**Causes:**
- ODBC driver not installed
- Wrong driver name in configuration

**Solutions:**

**1. Check installed drivers:**

```bash
odbcinst -q -d
```

**2. Install ODBC Driver 17:**

Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**3. Verify driver name in configuration:**

```ini
[Database]
mssql_driver = ODBC Driver 17 for SQL Server  # Must match installed driver
```

**4. Alternative drivers:**

```ini
# Try other versions if 17 not available
mssql_driver = ODBC Driver 18 for SQL Server
# OR
mssql_driver = SQL Server Native Client 11.0
```

### Issue: Login Failed for User

**Symptoms:**
- Error: `Login failed for user 'construction_app'`
- Error: `Cannot open database "construction" requested by the login`

**Causes:**
- Wrong credentials
- User doesn't exist
- User doesn't have access to database

**Solutions:**

**1. Verify credentials:**

```bash
sqlcmd -S localhost -U construction_app -P password -d construction
```

**2. Create login and user:**

```sql
-- Connect as sa
sqlcmd -S localhost -U sa

-- Create login
CREATE LOGIN construction_app WITH PASSWORD = 'YourPassword123!';
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

**3. Check user permissions:**

```sql
-- Check user's roles
USE construction;
GO

SELECT r.name AS role_name
FROM sys.database_role_members AS rm
JOIN sys.database_principals AS r ON rm.role_principal_id = r.principal_id
JOIN sys.database_principals AS m ON rm.member_principal_id = m.principal_id
WHERE m.name = 'construction_app';
```

### Issue: Connection String Errors

**Symptoms:**
- Error: `Invalid connection string attribute`
- Connection fails with cryptic errors

**Solutions:**

**1. Check connection string format:**

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = construction_app
mssql_password = password
mssql_driver = ODBC Driver 17 for SQL Server
```

**2. Test connection string manually:**

```python
import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=construction;"
    "UID=construction_app;"
    "PWD=password"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✓ Connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### Issue: Timeout Errors

**Symptoms:**
- Error: `Timeout expired`
- Queries take too long

**Solutions:**

**1. Increase timeout:**

```ini
[Database]
pool_timeout = 60  # Increase from default 30
```

**2. Check for blocking:**

```sql
-- Find blocking queries
SELECT 
    blocking_session_id,
    session_id,
    wait_type,
    wait_time,
    wait_resource
FROM sys.dm_exec_requests
WHERE blocking_session_id <> 0;
```

**3. Kill blocking session:**

```sql
KILL <session_id>;
```

## General Issues

### Issue: Schema Not Created

**Symptoms:**
- Tables don't exist
- Error: `no such table` or `invalid object name`

**Solutions:**

**1. Manually trigger schema creation:**

```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize("env.ini")
# Schema should be created automatically
```

**2. Check for errors in logs:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Re-run initialization
db_manager = DatabaseManager()
db_manager.initialize("env.ini")
```

**3. Verify user permissions:**

Ensure database user has CREATE TABLE permissions.

### Issue: Foreign Key Constraint Violations

**Symptoms:**
- Error: `FOREIGN KEY constraint failed`
- Error: `violates foreign key constraint`

**Solutions:**

**1. Check referenced record exists:**

```sql
-- Example: Check if customer exists before creating estimate
SELECT * FROM counterparties WHERE id = <customer_id>;
```

**2. Insert in correct order:**

```python
# Insert parent records first
session.add(customer)
session.flush()  # Get customer.id

# Then insert child records
estimate.customer_id = customer.id
session.add(estimate)
session.commit()
```

**3. Check for orphaned records:**

```sql
-- Find estimates with non-existent customers
SELECT e.* 
FROM estimates e
LEFT JOIN counterparties c ON e.customer_id = c.id
WHERE e.customer_id IS NOT NULL AND c.id IS NULL;
```

### Issue: Data Type Mismatches

**Symptoms:**
- Error: `invalid input syntax for type`
- Error: `Conversion failed`

**Solutions:**

**1. Check data types:**

```python
# Ensure correct types
estimate.date = datetime.date(2024, 1, 1)  # Not string
estimate.amount = Decimal('1000.50')       # Not float for money
```

**2. Handle NULL values:**

```python
# Use None for NULL
person.phone = None  # Not empty string if NULL allowed
```

### Issue: Transaction Deadlocks

**Symptoms:**
- Error: `deadlock detected`
- Error: `Transaction was deadlocked`

**Solutions:**

**1. Use consistent lock order:**

```python
# Always access tables in same order
with db_manager.session_scope() as session:
    # Always lock estimates before estimate_lines
    estimate = session.query(Estimate).filter_by(id=1).first()
    lines = session.query(EstimateLine).filter_by(estimate_id=1).all()
```

**2. Keep transactions short:**

```python
# Bad - long transaction
with db_manager.session_scope() as session:
    # ... lots of processing ...
    session.commit()

# Good - short transaction
# ... do processing ...
with db_manager.session_scope() as session:
    session.add(record)
    session.commit()
```

**3. Use appropriate isolation level:**

```python
from sqlalchemy import create_engine

engine = create_engine(
    connection_string,
    isolation_level="READ COMMITTED"  # Less strict than SERIALIZABLE
)
```

## Performance Issues

### Issue: Slow Application Startup

**Symptoms:**
- Application takes long time to start
- Database initialization is slow

**Solutions:**

**1. Check connection timeout:**

```ini
[Database]
pool_timeout = 10  # Reduce if too high
```

**2. Verify network connectivity:**

```bash
# Test connection to database server
ping database-server
telnet database-server 5432  # PostgreSQL
telnet database-server 1433  # MSSQL
```

**3. Check database server load:**

Monitor CPU, memory, and disk I/O on database server.

### Issue: Memory Usage Growing

**Symptoms:**
- Application memory usage increases over time
- Out of memory errors

**Solutions:**

**1. Check for connection leaks:**

```python
# Always use context manager
with db_manager.session_scope() as session:
    # Work with session
    pass  # Automatically closed

# Don't do this:
session = db_manager.get_session()
# ... work ...
# Forgot to close!
```

**2. Limit query results:**

```python
# Use pagination
results = session.query(Estimate)\
    .limit(100)\
    .offset(page * 100)\
    .all()
```

**3. Clear session cache:**

```python
session.expunge_all()  # Remove all objects from session
```

## Diagnostic Tools

### Connection Test Script

```python
# test_connection.py
from src.data.database_manager import DatabaseManager
from src.data.database_config import DatabaseConfig
import logging

logging.basicConfig(level=logging.DEBUG)

print("Testing database connection...")
print("-" * 50)

# Load configuration
config = DatabaseConfig("env.ini")
print(f"Database type: {config.db_type}")
print(f"Configuration valid: {config.validate()}")
print()

# Test connection
db_manager = DatabaseManager()
success = db_manager.initialize("env.ini")

if success:
    print("✓ Connection successful!")
    
    # Test query
    try:
        with db_manager.session_scope() as session:
            from src.data.models.sqlalchemy_models import User
            count = session.query(User).count()
            print(f"✓ Query successful! Found {count} users.")
    except Exception as e:
        print(f"✗ Query failed: {e}")
else:
    print("✗ Connection failed!")
    print("Check logs above for details")
```

### Performance Monitoring Script

```python
# monitor_performance.py
from src.data.database_manager import DatabaseManager
import time

db_manager = DatabaseManager()
db_manager.initialize("env.ini")

# Monitor query performance
queries = [
    "SELECT COUNT(*) FROM estimates",
    "SELECT COUNT(*) FROM daily_reports",
    "SELECT COUNT(*) FROM persons"
]

print("Query Performance:")
print("-" * 50)

for query in queries:
    start = time.time()
    with db_manager.session_scope() as session:
        result = session.execute(query).scalar()
    elapsed = time.time() - start
    print(f"{query}: {elapsed:.3f}s (result: {result})")
```

## Getting Help

### Log Files

Check application logs for detailed error messages:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
```

### Database Server Logs

**PostgreSQL:**
- Location: `/var/log/postgresql/` (Linux) or PostgreSQL data directory (Windows)
- File: `postgresql-<version>-main.log`

**MSSQL:**
- Location: SQL Server error log (view in SSMS)
- Or: `C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER\MSSQL\Log\ERRORLOG`

### Support Checklist

When seeking help, provide:

- [ ] Database backend (SQLite/PostgreSQL/MSSQL)
- [ ] Configuration (env.ini) - remove passwords
- [ ] Error message (full stack trace)
- [ ] Application logs
- [ ] Database server logs
- [ ] Steps to reproduce
- [ ] Expected vs actual behavior

## Additional Resources

- [DATABASE_CONFIGURATION.md](DATABASE_CONFIGURATION.md) - Configuration examples
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration procedures
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development guidelines
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- SQL Server Documentation: https://docs.microsoft.com/en-us/sql/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/

# MSSQL Setup Guide

## Quick Start Guide for Microsoft SQL Server Backend

This guide helps you configure the construction management system to use Microsoft SQL Server (MSSQL) as the database backend.

## Prerequisites

### 1. MSSQL Server
- Microsoft SQL Server 2017 or later
- SQL Server Authentication enabled (not just Windows Authentication)
- TCP/IP protocol enabled in SQL Server Configuration Manager
- Firewall configured to allow connections on port 1433

### 2. ODBC Driver
- **ODBC Driver 17 for SQL Server** (recommended)
- Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### 3. Python Dependencies
Already included in requirements.txt:
```
pyodbc>=5.0.0
sqlalchemy>=2.0.0
```

## Installation Steps

### Step 1: Install ODBC Driver

1. Download ODBC Driver 17 for SQL Server from Microsoft
2. Run the installer
3. Follow the installation wizard
4. Verify installation by running:
   ```cmd
   python -c "import pyodbc; print(pyodbc.drivers())"
   ```
   You should see "ODBC Driver 17 for SQL Server" in the list

### Step 2: Create Database

#### Option A: Using the provided script
```cmd
python test/create_mssql_db.py
```

#### Option B: Manual creation
Connect to MSSQL Server and run:
```sql
CREATE DATABASE construction;
GO

USE construction;
GO

-- Grant permissions to your user (if needed)
-- CREATE USER your_user FOR LOGIN your_user;
-- ALTER ROLE db_owner ADD MEMBER your_user;
```

### Step 3: Configure env.ini

Edit your `env.ini` file:

```ini
[Database]
# Change type to mssql
type = mssql

# MSSQL configuration
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = your_username
mssql_password = your_password
mssql_driver = ODBC Driver 17 for SQL Server

# Connection pool settings (optional, these are defaults)
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

### Step 4: Initialize Schema

The schema will be created automatically when you first run the application:

```cmd
python main.py
```

Or you can run the schema creation explicitly:
```python
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Base

db_manager = DatabaseManager()
db_manager.initialize()
Base.metadata.create_all(db_manager.get_engine())
```

## Verification

### Verify Setup
Run the setup verification script:
```cmd
python test/setup_mssql_test.py
```

This will check:
- ✓ ODBC Driver installation
- ✓ Connection to MSSQL server
- ✓ Database existence
- ✓ User permissions

### Run Tests
Verify everything works with the test suite:
```cmd
pytest test/test_mssql_backend.py -v
```

Expected result: All 20 tests should pass ✅

## Configuration Options

### Connection Pool Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `pool_size` | 5 | Number of connections to maintain in the pool |
| `max_overflow` | 10 | Maximum additional connections beyond pool_size |
| `pool_timeout` | 30 | Seconds to wait for a connection before timeout |
| `pool_recycle` | 3600 | Seconds before recycling connections (prevents stale connections) |

### Recommended Settings by Deployment Size

#### Small (1-5 concurrent users)
```ini
pool_size = 3
max_overflow = 5
pool_timeout = 30
pool_recycle = 3600
```

#### Medium (5-20 concurrent users)
```ini
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

#### Large (20+ concurrent users)
```ini
pool_size = 10
max_overflow = 20
pool_timeout = 30
pool_recycle = 1800
```

## Troubleshooting

### Issue: "No module named 'pyodbc'"
**Solution**: Install pyodbc
```cmd
pip install pyodbc
```

### Issue: "ODBC Driver not found"
**Solution**: Install ODBC Driver 17 for SQL Server from Microsoft's website

### Issue: "Cannot connect to server"
**Solution**: Check the following:
1. MSSQL Server is running
2. TCP/IP is enabled in SQL Server Configuration Manager
3. Firewall allows connections on port 1433
4. SQL Server Authentication is enabled (not just Windows Auth)

### Issue: "Login failed for user"
**Solution**: 
1. Verify username and password are correct
2. Ensure SQL Server Authentication is enabled
3. Check that the user has permissions on the database:
   ```sql
   USE construction;
   ALTER ROLE db_owner ADD MEMBER your_user;
   ```

### Issue: "Database does not exist"
**Solution**: Create the database:
```cmd
python test/create_mssql_db.py
```

### Issue: "Connection timeout"
**Solution**: 
1. Check network connectivity
2. Verify server name and port
3. Increase `pool_timeout` in configuration

### Issue: "Pool exhausted"
**Solution**: Increase pool settings:
```ini
pool_size = 10
max_overflow = 20
```

## Remote Server Configuration

For connecting to a remote MSSQL server:

```ini
[Database]
type = mssql
mssql_host = your-server.example.com
mssql_port = 1433
mssql_database = construction
mssql_user = your_username
mssql_password = your_password
mssql_driver = ODBC Driver 17 for SQL Server
```

### Security Considerations for Remote Connections

1. **Use SSL/TLS**: Modify connection string to require encryption
2. **Strong passwords**: Use complex passwords for database users
3. **Firewall rules**: Restrict access to specific IP addresses
4. **VPN**: Consider using VPN for remote access
5. **Least privilege**: Grant only necessary permissions to users

## Performance Tips

### 1. Connection Pooling
- Always use connection pooling for production
- Adjust pool size based on concurrent user count
- Monitor pool exhaustion in logs

### 2. Indexing
- Schema automatically creates necessary indexes
- Monitor slow queries and add indexes as needed

### 3. Connection Recycling
- Use `pool_recycle` to prevent stale connections
- Recommended: 3600 seconds (1 hour)

### 4. Query Optimization
- Use SQLAlchemy's query optimization features
- Enable query logging for debugging:
  ```python
  import logging
  logging.basicConfig()
  logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
  ```

## Switching from SQLite to MSSQL

### Migration Steps

1. **Backup SQLite database**
   ```cmd
   copy construction.db construction.db.backup
   ```

2. **Export data from SQLite** (if needed)
   - Use SQLAlchemy to read from SQLite
   - Write to MSSQL using the same models

3. **Update env.ini**
   - Change `type` from `sqlite` to `mssql`
   - Add MSSQL connection parameters

4. **Initialize MSSQL schema**
   - Schema will be created automatically on first run

5. **Import data** (if needed)
   - Run data migration script
   - Verify data integrity

### Example Migration Script

```python
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Base, User, Person, Organization

# Connect to SQLite
sqlite_manager = DatabaseManager()
sqlite_manager.initialize("env_sqlite.ini")

# Connect to MSSQL
mssql_manager = DatabaseManager()
mssql_manager.initialize("env_mssql.ini")

# Create schema in MSSQL
Base.metadata.create_all(mssql_manager.get_engine())

# Migrate data
with sqlite_manager.session_scope() as sqlite_session:
    with mssql_manager.session_scope() as mssql_session:
        # Migrate users
        users = sqlite_session.query(User).all()
        for user in users:
            mssql_session.merge(user)
        
        # Migrate other entities...
        mssql_session.commit()

print("Migration complete!")
```

## Monitoring and Maintenance

### Check Connection Pool Status
```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()
pool = db_manager.get_engine().pool

print(f"Pool size: {pool.size()}")
print(f"Checked out connections: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
```

### Enable Query Logging
Add to your code:
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Monitor Performance
- Use SQL Server Management Studio (SSMS)
- Check query execution plans
- Monitor connection count
- Review slow query logs

## Support

### Documentation
- [MSSQL Backend Testing Complete](../test/MSSQL_BACKEND_TESTING_COMPLETE.md)
- [Database Configuration Guide](DATABASE_AND_CONFIG_GUIDE.md)
- [Schema Management Guide](SCHEMA_MANAGEMENT_GUIDE.md)

### Test Scripts
- `test/setup_mssql_test.py` - Verify setup
- `test/create_mssql_db.py` - Create database
- `test/test_mssql_backend.py` - Run tests

### Getting Help
If you encounter issues:
1. Run `python test/setup_mssql_test.py` to diagnose
2. Check the troubleshooting section above
3. Review test results for specific errors
4. Check MSSQL Server logs

## Summary

✅ **MSSQL backend is production-ready**

Key benefits:
- Multi-user concurrent access
- Enterprise database features
- Centralized data management
- Scalability and performance
- Automatic schema management
- Connection pooling
- Transaction support

The system seamlessly works with MSSQL Server while maintaining the same API and functionality as SQLite.

---

**Last updated**: November 28, 2025
**Tested with**: Microsoft SQL Server 2022
**ODBC Driver**: ODBC Driver 17 for SQL Server

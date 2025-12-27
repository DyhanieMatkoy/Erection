# Database Configuration Guide

## Overview

The construction management system supports three database backends:

- **SQLite** - Lightweight, file-based database (default)
- **PostgreSQL** - Enterprise-grade relational database
- **Microsoft SQL Server (MSSQL)** - Microsoft's enterprise database

This guide provides complete configuration examples for each backend.

## Configuration File

All database configuration is stored in the `env.ini` file in the project root directory.

## SQLite Configuration

### Basic Setup

SQLite is the default database backend and requires minimal configuration.

```ini
[Database]
type = sqlite
sqlite_path = construction.db
```

### Configuration Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `type` | Database backend type | `sqlite` | Yes |
| `sqlite_path` | Path to database file | `construction.db` | Yes |

### Example Configurations

**Default configuration (single database file):**

```ini
[Database]
type = sqlite
sqlite_path = construction.db
```

**Multiple database files (different projects):**

```ini
[Database]
type = sqlite
sqlite_path = project_alpha.db
```

**Absolute path:**

```ini
[Database]
type = sqlite
sqlite_path = C:\Data\Databases\construction.db
```

### Advantages

- No server installation required
- Zero configuration
- Portable (single file)
- Perfect for desktop applications
- Excellent for development and testing

### Limitations

- Single writer at a time
- Not suitable for high-concurrency scenarios
- Limited to local file system
- No built-in replication

### Use Cases

- Desktop application deployments
- Single-user environments
- Development and testing
- Portable installations
- Small to medium datasets

## PostgreSQL Configuration

### Prerequisites

1. PostgreSQL 12 or later installed
2. Database created
3. User with appropriate permissions
4. Python driver installed: `psycopg2-binary`

### Basic Setup

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = postgres
postgres_password = your_secure_password

# Connection pool settings (optional)
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

### Configuration Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `type` | Database backend type | - | Yes |
| `postgres_host` | PostgreSQL server hostname or IP | `localhost` | Yes |
| `postgres_port` | PostgreSQL server port | `5432` | Yes |
| `postgres_database` | Database name | - | Yes |
| `postgres_user` | Database username | - | Yes |
| `postgres_password` | Database password | - | Yes |
| `pool_size` | Number of connections in pool | `5` | No |
| `max_overflow` | Additional connections beyond pool | `10` | No |
| `pool_timeout` | Timeout for getting connection (seconds) | `30` | No |
| `pool_recycle` | Connection recycle time (seconds) | `3600` | No |

### Example Configurations

**Local development:**

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction_dev
postgres_user = devuser
postgres_password = devpass123
pool_size = 3
max_overflow = 5
```

**Production server:**

```ini
[Database]
type = postgresql
postgres_host = db.example.com
postgres_port = 5432
postgres_database = construction_prod
postgres_user = app_user
postgres_password = StrongP@ssw0rd!
pool_size = 10
max_overflow = 20
pool_timeout = 30
pool_recycle = 3600
```

**Remote server with custom port:**

```ini
[Database]
type = postgresql
postgres_host = 192.168.1.100
postgres_port = 5433
postgres_database = construction
postgres_user = construction_app
postgres_password = SecurePassword123!
pool_size = 8
max_overflow = 15
```

### Database Setup

**Create database and user:**

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE construction;

-- Create user
CREATE USER construction_app WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE construction TO construction_app;

-- Connect to the database
\c construction

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO construction_app;
```

### Advantages

- Excellent concurrency support
- ACID compliant
- Rich data types
- Advanced indexing
- Full-text search
- JSON support
- Mature and stable
- Open source

### Use Cases

- Multi-user web applications
- Production deployments
- High-concurrency environments
- Large datasets
- Complex queries
- Distributed teams

## Microsoft SQL Server Configuration

### Prerequisites

1. SQL Server 2017 or later installed
2. Database created
3. User with appropriate permissions
4. ODBC Driver 17 for SQL Server installed
5. Python driver installed: `pyodbc`

### Basic Setup

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = sa
mssql_password = YourStrong!Password
mssql_driver = ODBC Driver 17 for SQL Server

# Connection pool settings (optional)
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

### Configuration Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `type` | Database backend type | - | Yes |
| `mssql_host` | SQL Server hostname or IP | `localhost` | Yes |
| `mssql_port` | SQL Server port | `1433` | Yes |
| `mssql_database` | Database name | - | Yes |
| `mssql_user` | Database username | - | Yes |
| `mssql_password` | Database password | - | Yes |
| `mssql_driver` | ODBC driver name | `ODBC Driver 17 for SQL Server` | Yes |
| `pool_size` | Number of connections in pool | `5` | No |
| `max_overflow` | Additional connections beyond pool | `10` | No |
| `pool_timeout` | Timeout for getting connection (seconds) | `30` | No |
| `pool_recycle` | Connection recycle time (seconds) | `3600` | No |

### Example Configurations

**Local development (SQL Server Express):**

```ini
[Database]
type = mssql
mssql_host = localhost\SQLEXPRESS
mssql_port = 1433
mssql_database = construction_dev
mssql_user = dev_user
mssql_password = DevPass123!
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 3
max_overflow = 5
```

**Production server:**

```ini
[Database]
type = mssql
mssql_host = sqlserver.example.com
mssql_port = 1433
mssql_database = construction_prod
mssql_user = app_user
mssql_password = Pr0d!Passw0rd
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 10
max_overflow = 20
pool_timeout = 30
pool_recycle = 3600
```

**Windows Authentication (trusted connection):**

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = 
mssql_password = 
mssql_driver = ODBC Driver 17 for SQL Server
mssql_trusted_connection = yes
```

### Database Setup

**Create database and user:**

```sql
-- Connect to SQL Server as administrator
sqlcmd -S localhost -U sa

-- Create database
CREATE DATABASE construction;
GO

-- Create login
CREATE LOGIN construction_app WITH PASSWORD = 'YourPassword123!';
GO

-- Use the database
USE construction;
GO

-- Create user
CREATE USER construction_app FOR LOGIN construction_app;
GO

-- Grant permissions
ALTER ROLE db_owner ADD MEMBER construction_app;
GO
```

### ODBC Driver Installation

**Windows:**

Download and install from Microsoft:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**Verify installation:**

```bash
# List available ODBC drivers
odbcinst -q -d
```

### Advantages

- Enterprise features
- Windows integration
- Excellent tooling (SSMS)
- High performance
- Advanced security
- Backup and recovery
- Replication support

### Use Cases

- Enterprise deployments
- Windows-based infrastructure
- Existing SQL Server environments
- Organizations with SQL Server expertise
- Integration with Microsoft ecosystem

## Connection Pool Settings

Connection pooling improves performance by reusing database connections instead of creating new ones for each request.

### Pool Size

Number of connections to maintain in the pool.

```ini
pool_size = 5
```

**Recommendations:**
- Development: 3-5 connections
- Production (low traffic): 5-10 connections
- Production (high traffic): 10-20 connections
- Formula: `pool_size = (number of concurrent users) / 2`

### Max Overflow

Additional connections that can be created beyond the pool size during peak load.

```ini
max_overflow = 10
```

**Recommendations:**
- Set to 2x pool_size for burst capacity
- Monitor connection usage to tune this value

### Pool Timeout

Maximum time (in seconds) to wait for a connection from the pool.

```ini
pool_timeout = 30
```

**Recommendations:**
- Development: 10-30 seconds
- Production: 30-60 seconds
- Increase if you see timeout errors

### Pool Recycle

Time (in seconds) before a connection is recycled to prevent stale connections.

```ini
pool_recycle = 3600
```

**Recommendations:**
- PostgreSQL: 3600 seconds (1 hour)
- MSSQL: 3600 seconds (1 hour)
- Adjust based on database server timeout settings

## Security Best Practices

### Password Security

**Don't:**
- Commit passwords to version control
- Use default passwords
- Share passwords in plain text

**Do:**
- Use strong passwords (12+ characters, mixed case, numbers, symbols)
- Use environment variables for sensitive values
- Rotate passwords regularly
- Use different passwords for dev/prod

### Connection Security

**PostgreSQL SSL:**

```ini
[Database]
type = postgresql
postgres_host = db.example.com
postgres_port = 5432
postgres_database = construction
postgres_user = app_user
postgres_password = SecurePass123!
postgres_sslmode = require
```

**SQL Server Encryption:**

```ini
[Database]
type = mssql
mssql_host = sqlserver.example.com
mssql_port = 1433
mssql_database = construction
mssql_user = app_user
mssql_password = SecurePass123!
mssql_driver = ODBC Driver 17 for SQL Server
mssql_encrypt = yes
mssql_trust_server_certificate = no
```

### User Permissions

Grant only necessary permissions:

**PostgreSQL:**

```sql
-- Grant only necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

**SQL Server:**

```sql
-- Grant only necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE TO app_user;
```

## Testing Configuration

### Verify Connection

The system will log connection status on startup. Check the logs for:

```
INFO: Database initialized successfully
INFO: Using PostgreSQL backend
INFO: Connection pool created with 5 connections
```

### Test Script

Create a test script to verify configuration:

```python
from src.data.database_manager import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
success = db_manager.initialize("env.ini")

if success:
    print("✓ Database connection successful")
    print(f"✓ Backend: {db_manager._config.db_type}")
else:
    print("✗ Database connection failed")
```

## Environment-Specific Configuration

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

### Production

```ini
[Database]
type = postgresql
postgres_host = prod-db.example.com
postgres_port = 5432
postgres_database = construction_prod
postgres_user = prod_user
postgres_password = ${DB_PASSWORD}  # From environment variable
pool_size = 15
max_overflow = 25
pool_timeout = 60
pool_recycle = 3600
```

## Quick Reference

### SQLite

```ini
[Database]
type = sqlite
sqlite_path = construction.db
```

### PostgreSQL

```ini
[Database]
type = postgresql
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = postgres
postgres_password = password
pool_size = 5
max_overflow = 10
```

### MSSQL

```ini
[Database]
type = mssql
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = sa
mssql_password = password
mssql_driver = ODBC Driver 17 for SQL Server
pool_size = 5
max_overflow = 10
```

## Next Steps

- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for migrating from SQLite to PostgreSQL/MSSQL
- See [TROUBLESHOOTING_DATABASE.md](TROUBLESHOOTING_DATABASE.md) for common issues
- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for SQLAlchemy usage patterns

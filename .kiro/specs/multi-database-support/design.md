# Multi-Database Support Design Document

## Overview

This design document outlines the architecture for adding PostgreSQL and Microsoft SQL Server support to the construction management system. The system currently uses SQLite with direct SQL queries through a custom DatabaseManager class. This design introduces SQLAlchemy ORM as an abstraction layer to support multiple database backends while maintaining backward compatibility with existing SQLite deployments.

The key design principle is to minimize disruption to existing code while providing a clean migration path. We will introduce SQLAlchemy models alongside the existing dataclass models, gradually migrate repositories to use SQLAlchemy sessions, and provide configuration-based database backend selection.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Views, ViewModels, Services, API Endpoints)               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Repository Layer                            │
│  (EstimateRepository, ReferenceRepository, etc.)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Database Abstraction Layer                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         DatabaseManager (Enhanced)                    │  │
│  │  - Configuration loading                              │  │
│  │  - Backend selection                                  │  │
│  │  - Session management                                 │  │
│  │  - Connection pooling                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         SQLAlchemy Core                               │  │
│  │  - ORM models                                         │  │
│  │  - Session factory                                    │  │
│  │  - Engine management                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                Database Backends                             │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  SQLite  │    │PostgreSQL│    │  MSSQL   │             │
│  └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **DatabaseManager**: Singleton that manages database configuration, engine creation, and session lifecycle
2. **SQLAlchemy Models**: Declarative ORM models that map to database tables
3. **Repositories**: Data access layer that uses SQLAlchemy sessions for CRUD operations
4. **Migration System**: Alembic-based migration framework for schema versioning
5. **Configuration**: INI-based configuration for database connection parameters

## Components and Interfaces

### 1. Enhanced DatabaseManager

The DatabaseManager will be refactored to use SQLAlchemy while maintaining backward compatibility:

```python
class DatabaseManager:
    """Enhanced database manager with multi-backend support"""
    
    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    _config: DatabaseConfig = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config_path: str = "env.ini") -> bool:
        """Initialize database from configuration"""
        pass
    
    def get_session(self) -> Session:
        """Get a new SQLAlchemy session"""
        pass
    
    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine"""
        pass
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        pass
```

### 2. Database Configuration

Configuration will be read from env.ini with the following structure:

```ini
[Database]
# Database type: sqlite, postgresql, mssql
type = sqlite

# SQLite configuration
sqlite_path = construction.db

# PostgreSQL configuration
postgres_host = localhost
postgres_port = 5432
postgres_database = construction
postgres_user = postgres
postgres_password = password

# MSSQL configuration
mssql_host = localhost
mssql_port = 1433
mssql_database = construction
mssql_user = sa
mssql_password = password
mssql_driver = ODBC Driver 17 for SQL Server

# Connection pool settings (PostgreSQL and MSSQL only)
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

### 3. SQLAlchemy Models

All existing tables will be defined as SQLAlchemy models:

```python
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)

class Person(Base):
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    position = Column(String(255))
    phone = Column(String(50))
    hourly_rate = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey('users.id'))
    parent_id = Column(Integer, ForeignKey('persons.id'))
    marked_for_deletion = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", backref="person")
    parent = relationship("Person", remote_side=[id], backref="children")

# Similar models for all other tables...
```

### 4. Repository Pattern with SQLAlchemy

Repositories will be updated to use SQLAlchemy sessions:

```python
class EstimateRepository:
    """Repository for estimate operations using SQLAlchemy"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, estimate_id: int) -> Optional[Estimate]:
        """Find estimate by ID"""
        with self.db_manager.session_scope() as session:
            return session.query(EstimateModel).filter_by(id=estimate_id).first()
    
    def save(self, estimate: EstimateModel) -> bool:
        """Save estimate"""
        try:
            with self.db_manager.session_scope() as session:
                session.add(estimate)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save estimate: {e}")
            return False
    
    def find_by_responsible(self, person_id: int) -> List[EstimateModel]:
        """Find estimates by responsible person"""
        with self.db_manager.session_scope() as session:
            return session.query(EstimateModel)\
                .filter_by(responsible_id=person_id)\
                .order_by(EstimateModel.date.desc())\
                .all()
```

### 5. Connection String Builder

A utility to build database-specific connection strings:

```python
class ConnectionStringBuilder:
    """Build database connection strings for different backends"""
    
    @staticmethod
    def build_sqlite(db_path: str) -> str:
        """Build SQLite connection string"""
        return f"sqlite:///{db_path}"
    
    @staticmethod
    def build_postgresql(host: str, port: int, database: str, 
                         user: str, password: str) -> str:
        """Build PostgreSQL connection string"""
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def build_mssql(host: str, port: int, database: str,
                    user: str, password: str, driver: str) -> str:
        """Build MSSQL connection string"""
        driver_encoded = driver.replace(' ', '+')
        return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver={driver_encoded}"
```

## Data Models

### SQLAlchemy Model Hierarchy

All models will inherit from a common Base class provided by SQLAlchemy's declarative_base(). The models will mirror the existing database schema:

**Core Models:**
- User
- Person
- Organization
- Counterparty
- Object
- Work

**Document Models:**
- Estimate
- EstimateLine
- DailyReport
- DailyReportLine
- DailyReportExecutor
- Timesheet
- TimesheetLine

**Register Models:**
- WorkExecutionRegister
- PayrollRegister

**System Models:**
- UserSetting
- Constant

### Model Relationships

SQLAlchemy relationships will be defined to handle foreign keys:

```python
class Estimate(Base):
    __tablename__ = 'estimates'
    
    # ... columns ...
    
    # Relationships
    customer = relationship("Counterparty", foreign_keys=[customer_id])
    object = relationship("Object", foreign_keys=[object_id])
    contractor = relationship("Organization", foreign_keys=[contractor_id])
    responsible = relationship("Person", foreign_keys=[responsible_id])
    lines = relationship("EstimateLine", back_populates="estimate", 
                        cascade="all, delete-orphan")
```

## 
##
 Error Handling

### Connection Errors

```python
class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass

class DatabaseConfigurationError(Exception):
    """Raised when database configuration is invalid"""
    pass

class DatabaseOperationError(Exception):
    """Raised when a database operation fails"""
    pass
```

Error handling strategy:
1. **Connection failures**: Log detailed error with connection parameters (excluding password), raise DatabaseConnectionError
2. **Query failures**: Log query context and parameters, rollback transaction, raise DatabaseOperationError
3. **Configuration errors**: Validate configuration on startup, fail fast with clear error messages
4. **Pool exhaustion**: Log warning, wait for timeout, raise clear timeout error with pool statistics

### Transaction Management

All database operations will use the session_scope context manager to ensure proper transaction handling:

```python
@contextmanager
def session_scope(self):
    """Provide a transactional scope"""
    session = self._session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise DatabaseOperationError(f"Database operation failed: {e}")
    finally:
        session.close()
```

## Testing Strategy

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property-Based Testing

We will use **Hypothesis** as the property-based testing library for Python. Hypothesis will generate random test data to verify that our database abstraction layer maintains correctness across all backends.

**Configuration**: Each property-based test will run a minimum of 100 iterations to ensure thorough coverage of the input space.

**Tagging**: Each property-based test will be tagged with a comment in the format: `# Feature: multi-database-support, Property {number}: {property_text}`


### Property Reflection

After analyzing all acceptance criteria, I've identified the following areas where properties can be consolidated:

**Redundancy Analysis:**

1. **Data Round-Trip Properties**: Criteria 2.4, 2.5, 10.1, and 10.2 all relate to data being stored and retrieved correctly. These can be consolidated into comprehensive round-trip properties for different data types.

2. **Transaction Properties**: Criteria 2.3 and 6.3 both relate to transaction atomicity and rollback behavior. These can be combined into a single comprehensive transaction property.

3. **Connection Pool Properties**: Criteria 7.2 and 7.4 both relate to connection pool lifecycle. These can be combined into a single property about pool connection reuse.

4. **Schema Creation Properties**: Criteria 3.3, 3.4, and 3.5 all relate to schema creation correctness. While they test different aspects, they can be verified together in schema validation.

5. **Primary Key Generation**: Criteria 9.1 and 9.5 both relate to primary key generation and return. These are part of the same operation and can be tested together.

6. **Date/Time Handling**: Criteria 10.1, 10.2, 10.3, 10.4, and 10.5 all relate to datetime handling. The round-trip property (10.1 + 10.2) is the most comprehensive test, while 10.3-10.5 are more specific cases that can be tested separately.

**Consolidated Property Set:**

After reflection, we will focus on these core properties that provide unique validation value:
- Configuration-based backend initialization
- Data type round-trip consistency across backends
- Transaction atomicity and rollback
- Query interface consistency across backends
- Primary key generation and uniqueness
- Datetime round-trip with timezone handling
- Connection pool lifecycle management
- Schema initialization idempotence
- Error handling consistency

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration-based backend initialization

*For any* valid database configuration (SQLite, PostgreSQL, or MSSQL), when the Database Manager initializes, it should successfully create an engine for the specified backend type and that engine should be capable of executing queries.

**Validates: Requirements 1.2, 1.4**

### Property 2: Invalid configuration defaults to SQLite

*For any* invalid or malformed database configuration, the Database Manager should default to SQLite backend and log a warning message, allowing the system to continue operating.

**Validates: Requirements 1.3**

### Property 3: Data round-trip consistency

*For any* Python data value (string, integer, float, boolean, None) and any database backend, storing the value in a table and then retrieving it should return an equivalent value.

**Validates: Requirements 2.4, 2.5**

### Property 4: Datetime round-trip with timezone handling

*For any* Python datetime object (timezone-aware or timezone-naive) and any database backend, storing the datetime and retrieving it should return an equivalent datetime with the same timezone information preserved.

**Validates: Requirements 10.1, 10.2, 10.5**

### Property 5: Transaction atomicity

*For any* sequence of database operations within a transaction, if any operation fails, then all operations in that transaction should be rolled back, leaving the database in its original state before the transaction began.

**Validates: Requirements 2.3, 6.3**

### Property 6: Query interface consistency

*For any* repository method call (find_by_id, save, delete, etc.) and any database backend, the method should accept the same parameters and return results in the same format regardless of which backend is active.

**Validates: Requirements 2.2, 5.5**

### Property 7: Primary key generation uniqueness

*For any* new record inserted into any table on any backend, the Database Adapter should generate a unique primary key value, and that value should be returned to the caller and should never collide with existing keys.

**Validates: Requirements 9.1, 9.5**

### Property 8: Schema initialization idempotence

*For any* database backend, running the schema initialization process multiple times should be safe and should result in the same schema structure without errors or data loss.

**Validates: Requirements 3.2**

### Property 9: Connection pool reuse

*For any* sequence of database operations using PostgreSQL or MSSQL, when a session is closed, the underlying connection should be returned to the pool and should be reusable for subsequent operations.

**Validates: Requirements 7.2, 7.4**

### Property 10: Foreign key constraint enforcement

*For any* attempt to insert a record with an invalid foreign key reference on any backend, the database should reject the operation with a constraint violation error.

**Validates: Requirements 3.4**

### Property 11: Date comparison query consistency

*For any* date comparison query (greater than, less than, between) and any database backend, the query should return the same set of results regardless of which backend is used.

**Validates: Requirements 10.3, 10.4**

### Property 12: Connection failure error handling

*For any* connection failure scenario (invalid host, wrong credentials, network timeout), the Database Manager should raise a DatabaseConnectionError with detailed error information and should not leave the system in an inconsistent state.

**Validates: Requirements 6.1, 6.5**

### Property 13: Query failure error handling

*For any* query that fails (syntax error, constraint violation, etc.), the Database Adapter should provide a meaningful error message that includes query context and should properly rollback any pending transaction.

**Validates: Requirements 6.2**

### Property 14: Existing SQLite database compatibility

*For any* existing SQLite database file from the current system, the enhanced Database Manager should be able to connect to it and execute all standard operations without requiring migration or schema changes.

**Validates: Requirements 5.2, 5.3**

## Migration Strategy

### Phase 1: Foundation (Parallel Implementation)

1. Install SQLAlchemy and database drivers
2. Create SQLAlchemy models alongside existing dataclasses
3. Implement enhanced DatabaseManager with configuration support
4. Create connection string builder utilities
5. Set up Alembic for migrations

### Phase 2: Repository Migration

1. Update one repository at a time to use SQLAlchemy sessions
2. Maintain backward compatibility during transition
3. Add integration tests for each migrated repository
4. Verify functionality with SQLite first

### Phase 3: Multi-Backend Support

1. Test with PostgreSQL backend
2. Test with MSSQL backend
3. Verify all properties hold across all backends
4. Performance testing and optimization

### Phase 4: Documentation and Deployment

1. Create configuration documentation
2. Create migration guide for existing deployments
3. Update deployment scripts
4. Create troubleshooting guide

## Database-Specific Considerations

### SQLite

- **Advantages**: No server required, simple deployment, existing compatibility
- **Limitations**: No concurrent writes, limited data types, no connection pooling needed
- **Configuration**: File path only
- **Use Case**: Single-user desktop deployments, development, testing

### PostgreSQL

- **Advantages**: Full ACID compliance, excellent concurrency, rich data types, mature ecosystem
- **Limitations**: Requires server installation and management
- **Configuration**: Host, port, database, username, password, pool settings
- **Use Case**: Multi-user deployments, production environments, high concurrency

### Microsoft SQL Server

- **Advantages**: Enterprise features, Windows integration, familiar to many organizations
- **Limitations**: Requires server installation, licensing costs, Windows-centric
- **Configuration**: Host, port, database, username, password, ODBC driver, pool settings
- **Use Case**: Enterprise deployments, Windows-based infrastructure, existing MSSQL environments

## Performance Considerations

### Connection Pooling

- **Pool Size**: Default 5 connections, configurable based on concurrent user count
- **Max Overflow**: Default 10 additional connections during peak load
- **Pool Recycle**: Default 3600 seconds (1 hour) to prevent stale connections
- **Timeout**: Default 30 seconds before raising pool exhaustion error

### Query Optimization

- SQLAlchemy will use lazy loading by default for relationships
- Eager loading can be specified where needed using `joinedload()` or `subqueryload()`
- Existing indices will be preserved and created on all backends
- Query logging can be enabled for performance analysis

### Caching Strategy

- SQLAlchemy's identity map provides session-level caching
- Application-level caching can be added for frequently accessed reference data
- Cache invalidation on write operations

## Security Considerations

### Connection Security

- Support for SSL/TLS connections to PostgreSQL and MSSQL
- Encrypted password storage in configuration (future enhancement)
- Connection string passwords not logged in error messages
- Principle of least privilege for database users

### SQL Injection Prevention

- SQLAlchemy ORM automatically parameterizes queries
- No raw SQL string concatenation
- Input validation at application layer

### Access Control

- Database-level user permissions
- Application-level role-based access control (existing)
- Audit logging for sensitive operations (future enhancement)

## Deployment Considerations

### Requirements

**Python Packages:**
- `sqlalchemy>=2.0.0` - Core ORM framework
- `alembic>=1.12.0` - Database migrations
- `psycopg2-binary>=2.9.0` - PostgreSQL driver
- `pyodbc>=5.0.0` - MSSQL driver (Windows)

**System Requirements:**
- PostgreSQL 12+ (if using PostgreSQL backend)
- SQL Server 2017+ (if using MSSQL backend)
- ODBC Driver 17 for SQL Server (if using MSSQL on Windows)

### Configuration Management

- Configuration stored in `env.ini` file
- Environment variables can override INI settings
- Sensitive values (passwords) should be managed securely
- Different configurations for development, testing, production

### Backward Compatibility

- Existing SQLite databases continue to work without changes
- Default configuration uses SQLite if no database type specified
- Migration path provided for moving from SQLite to PostgreSQL/MSSQL
- All existing APIs remain unchanged

## Testing Approach

### Unit Tests

Unit tests will verify specific functionality:
- Configuration parsing and validation
- Connection string building for each backend
- Error handling for various failure scenarios
- Session lifecycle management
- Model relationship definitions

### Property-Based Tests

Property-based tests will verify universal properties using Hypothesis:
- Data round-trip consistency across all backends
- Transaction atomicity and rollback behavior
- Primary key generation and uniqueness
- Query interface consistency
- Datetime handling across timezones
- Connection pool behavior
- Schema initialization idempotence

Each property test will:
- Run minimum 100 iterations
- Test across all three database backends (SQLite, PostgreSQL, MSSQL)
- Use Hypothesis strategies to generate diverse test data
- Be tagged with the property number and description

### Integration Tests

Integration tests will verify end-to-end functionality:
- Complete CRUD operations through repositories
- Multi-table transactions
- Foreign key constraint enforcement
- Concurrent access patterns (PostgreSQL/MSSQL)
- Migration application and rollback

### Backend-Specific Tests

Tests specific to each backend:
- SQLite: File locking, concurrent read behavior
- PostgreSQL: Connection pooling, concurrent writes, advanced data types
- MSSQL: Windows authentication, ODBC driver compatibility

## Documentation Deliverables

1. **Configuration Guide**: Complete reference for all configuration options
2. **Migration Guide**: Step-by-step instructions for migrating from SQLite to PostgreSQL/MSSQL
3. **Troubleshooting Guide**: Common issues and solutions for each backend
4. **Developer Guide**: How to work with SQLAlchemy models and sessions
5. **Deployment Guide**: Production deployment best practices for each backend

# Implementation Plan

- [x] 1. Set up SQLAlchemy foundation and dependencies





  - Install SQLAlchemy, Alembic, and database drivers (psycopg2-binary, pyodbc)
  - Update requirements.txt with new dependencies
  - Create base SQLAlchemy configuration module
  - _Requirements: 4.1, 11.1_

- [x] 2. Create database configuration system









  - Implement DatabaseConfig class to parse env.ini database settings
  - Create ConnectionStringBuilder utility for all three backends
  - Add configuration validation with sensible defaults
  - Update env.ini with example database configuration sections
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 8.1-8.5_

- [ ]* 2.1 Write property test for configuration parsing
  - **Property 1: Configuration-based backend initialization**
  - **Validates: Requirements 1.2, 1.4**

- [ ]* 2.2 Write property test for invalid configuration handling
  - **Property 2: Invalid configuration defaults to SQLite**
  - **Validates: Requirements 1.3**

- [x] 3. Define SQLAlchemy models for all tables









  - Create Base declarative base class
  - Define User, Person, Organization, Counterparty, Object, Work models
  - Define Estimate, EstimateLine, DailyReport, DailyReportLine models
  - Define Timesheet, TimesheetLine models
  - Define WorkExecutionRegister, PayrollRegister models
  - Define UserSetting, Constant models
  - Configure all relationships and foreign keys
  - _Requirements: 4.1, 4.4_

- [x] 4. Enhance DatabaseManager with SQLAlchemy support





  - Refactor DatabaseManager to use SQLAlchemy Engine and Session
  - Implement session_scope() context manager for transaction management
  - Add connection pooling configuration for PostgreSQL and MSSQL
  - Maintain backward compatibility with existing get_connection() method
  - Implement proper error handling with custom exceptions
  - _Requirements: 2.2, 2.3, 6.1, 6.3, 7.1-7.5_

- [ ]* 4.1 Write property test for transaction atomicity
  - **Property 5: Transaction atomicity**
  - **Validates: Requirements 2.3, 6.3**

- [ ]* 4.2 Write property test for connection pool reuse
  - **Property 9: Connection pool reuse**
  - **Validates: Requirements 7.2, 7.4**

- [x] 5. Implement schema creation and migration system





  - Create Alembic migration environment
  - Generate initial migration from SQLAlchemy models
  - Implement automatic schema creation for empty databases
  - Add schema verification and update logic for existing databases
  - Ensure proper index creation across all backends
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 11.2, 11.3, 11.4_

- [ ]* 5.1 Write property test for schema initialization idempotence
  - **Property 8: Schema initialization idempotence**
  - **Validates: Requirements 3.2**

- [ ]* 5.2 Write property test for foreign key constraint enforcement
  - **Property 10: Foreign key constraint enforcement**
  - **Validates: Requirements 3.4**

- [x] 6. Migrate EstimateRepository to SQLAlchemy





  - Update find_by_id() to use SQLAlchemy session
  - Update save() to use SQLAlchemy session with transaction handling
  - Update find_by_responsible() to use SQLAlchemy query API
  - Ensure EstimateLine cascade operations work correctly
  - Test with SQLite backend first
  - _Requirements: 2.1, 2.2, 4.2, 4.3_

- [ ]* 6.1 Write property test for data round-trip consistency
  - **Property 3: Data round-trip consistency**
  - **Validates: Requirements 2.4, 2.5**

- [ ]* 6.2 Write property test for primary key generation
  - **Property 7: Primary key generation uniqueness**
  - **Validates: Requirements 9.1, 9.5**

- [x] 7. Migrate ReferenceRepository to SQLAlchemy





  - Update all find_*_usages() methods to use SQLAlchemy queries
  - Update can_delete_*() methods to use SQLAlchemy sessions
  - Ensure query performance is maintained with proper joins
  - Test with SQLite backend
  - _Requirements: 2.1, 2.2, 4.2, 4.3_

- [ ]* 7.1 Write property test for query interface consistency
  - **Property 6: Query interface consistency**
  - **Validates: Requirements 2.2, 5.5**

- [x] 8. Migrate remaining repositories to SQLAlchemy





  - Update TimesheetRepository to use SQLAlchemy
  - Update UserRepository to use SQLAlchemy
  - Update WorkExecutionRegisterRepository to use SQLAlchemy
  - Update PayrollRegisterRepository to use SQLAlchemy
  - Ensure all repositories follow consistent patterns
  - _Requirements: 2.1, 2.2, 4.2, 4.3_

- [x] 9. Implement datetime handling across backends





  - Add datetime conversion utilities for timezone handling
  - Update models to properly handle timezone-aware and naive datetimes
  - Implement date comparison query helpers
  - Test datetime storage and retrieval across all backends
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 9.1 Write property test for datetime round-trip
  - **Property 4: Datetime round-trip with timezone handling**
  - **Validates: Requirements 10.1, 10.2, 10.5**

- [ ]* 9.2 Write property test for date comparison queries
  - **Property 11: Date comparison query consistency**
  - **Validates: Requirements 10.3, 10.4**

- [x] 10. Implement comprehensive error handling





  - Create custom exception classes (DatabaseConnectionError, DatabaseOperationError, DatabaseConfigurationError)
  - Add error handling to DatabaseManager initialization
  - Add error handling to session operations with proper rollback
  - Implement connection failure detection and logging
  - Add query failure context to error messages
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 10.1 Write property test for connection failure handling
  - **Property 12: Connection failure error handling**
  - **Validates: Requirements 6.1, 6.5**

- [ ]* 10.2 Write property test for query failure handling
  - **Property 13: Query failure error handling**
  - **Validates: Requirements 6.2**

- [x] 11. Test with PostgreSQL backend





  - Set up PostgreSQL test database (ip:localhost login:q1 pass:q1)
  - Configure connection parameters in env.ini
  - Run all repository tests against PostgreSQL
  - Verify connection pooling behavior
  - Test concurrent access patterns
  - Verify all property tests pass with PostgreSQL
  - _Requirements: 1.2, 1.4, 1.5, 2.1-2.5, 7.1-7.5_

- [x] 12. Test with MSSQL backend





  - Set up MSSQL test database (ip:localhost login:q1 pass:q1)
  - Install and configure ODBC Driver 17 for SQL Server
  - Configure connection parameters in env.ini
  - Run all repository tests against MSSQL
  - Verify connection pooling behavior
  - Verify all property tests pass with MSSQL
  - _Requirements: 1.2, 1.4, 2.1-2.5, 7.1-7.5_

- [x] 13. Verify SQLite backward compatibility





  - Test with existing construction.db file
  - Verify all existing functionality works without migration
  - Ensure default configuration uses SQLite
  - Test that no schema changes are required for existing databases
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ]* 13.1 Write property test for SQLite compatibility
  - **Property 14: Existing SQLite database compatibility**
  - **Validates: Requirements 5.2, 5.3**

- [x] 14. Update API layer to use new database system





  - Update api/config.py to support database configuration
  - Update API endpoints to use SQLAlchemy sessions
  - Ensure FastAPI dependency injection works with new session management
  - Test all API endpoints with each database backend
  - _Requirements: 2.2, 4.3, 5.5_

- [x] 15. Create comprehensive documentation





  - Write DATABASE_CONFIGURATION.md with examples for all three backends
  - Write MIGRATION_GUIDE.md for moving from SQLite to PostgreSQL/MSSQL
  - Write TROUBLESHOOTING_DATABASE.md with common issues and solutions
  - Update DEVELOPER_GUIDE.md with SQLAlchemy usage patterns
  - Document all configuration parameters and defaults
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

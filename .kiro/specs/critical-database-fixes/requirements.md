# Critical Database Fixes Requirements

## Introduction

This specification addresses two critical database issues that are preventing normal system operation:
1. UUID constraint failure when saving estimates
2. Work list displaying only test records instead of all available works

## Glossary

- **System**: The Construction Time Management application
- **Estimate**: A document containing cost calculations for construction work
- **Work**: A reference item representing a type of construction work
- **UUID**: Universally Unique Identifier used for synchronization
- **SQLAlchemy Model**: Object-relational mapping class representing database tables

## Requirements

### Requirement 1

**User Story:** As a user, I want to save estimates without database errors, so that I can create and manage cost calculations effectively.

#### Acceptance Criteria

1. WHEN a user creates a new estimate THEN the system SHALL generate a UUID automatically and save the estimate successfully
2. WHEN a user updates an existing estimate THEN the system SHALL preserve the existing UUID and save changes without constraint errors
3. WHEN the system saves an estimate THEN the system SHALL ensure all required fields including UUID are populated
4. WHEN an estimate is saved THEN the system SHALL update the modified timestamp automatically
5. WHEN the database schema includes UUID fields THEN the SQLAlchemy models SHALL include corresponding UUID columns

### Requirement 2

**User Story:** As a user, I want to see all available works in the main work list, so that I can access and manage all work types in the system.

#### Acceptance Criteria

1. WHEN a user opens the work list form THEN the system SHALL display all non-deleted works from the database
2. WHEN the system queries works THEN the system SHALL not apply any test-data-only filters
3. WHEN a user searches for works THEN the system SHALL search across all available works, not just test records
4. WHEN works are displayed THEN the system SHALL show both individual works and work groups
5. WHEN the work list loads THEN the system SHALL apply only user-specified filters, not hidden system filters

### Requirement 3

**User Story:** As a system administrator, I want the database schema and ORM models to be synchronized, so that all database operations work correctly.

#### Acceptance Criteria

1. WHEN the database contains UUID fields THEN the SQLAlchemy models SHALL include matching UUID columns
2. WHEN models are used for database operations THEN the system SHALL handle all required fields automatically
3. WHEN synchronization fields exist in the database THEN the system SHALL populate them correctly during CRUD operations
4. WHEN new records are created THEN the system SHALL generate UUIDs automatically using the default value mechanism
5. WHEN the system performs database migrations THEN the system SHALL ensure model definitions match the resulting schema
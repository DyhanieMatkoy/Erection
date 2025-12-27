# Reference Documentation

This section contains detailed reference documentation for developers and advanced users who need in-depth technical information about the application.

## Database Reference

Complete database schema, tables, and relationships are documented in the [Database Reference](database/).

## Configuration Reference

All configuration options and settings are documented in the [Configuration Reference](configuration/).

## API Reference

Complete API documentation including endpoints, request/response formats, and examples is available in the [API Reference](api/).

## Table of Contents

### Database Reference
- [Database Schema](database/schema.md)
- [Table Definitions](database/tables.md)
- [Relationships](database/relationships.md)

### Configuration Reference
- [env.ini Configuration](configuration/env-ini.md)
- [Sync Settings](configuration/sync-settings.md)
- [UI Settings](configuration/ui-settings.md)

### API Reference
- [API Endpoints](api/endpoints.md)
- [Data Models](api/models.md)
- [Authentication](api/authentication.md)

## Quick Reference

### Configuration Files

#### env.ini
```ini
[Database]
connection_string=...
provider=...

[Sync]
enabled=true|false

[Interface]
theme=...
button_position=...
```

#### Database Connection
- **SQLite**: `sqlite:///path/to/database.db`
- **MS SQL Server**: `mssql+pyodbc://server/database`

### API Endpoints

#### Authentication
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout
- `GET /api/user` - Current user info

#### Data Operations
- `GET /api/estimates` - List estimates
- `POST /api/estimates` - Create estimate
- `PUT /api/estimates/{id}` - Update estimate
- `DELETE /api/estimates/{id}` - Delete estimate

### Database Schema Overview

#### Core Tables
- `users` - User accounts and authentication
- `estimates` - Cost estimates and calculations
- `timesheets` - Employee timesheet data
- `daily_reports` - Daily work reports
- `sync_changes` - Synchronization tracking

#### Configuration Tables
- `settings` - Application settings
- `user_preferences` - User-specific preferences
- `system_config` - System configuration

### Sync System

#### Sync States
- **Enabled**: Active synchronization across workstations
- **Disabled**: Local-only operation, no sync changes recorded
- **Error**: Sync errors detected, manual intervention required

#### Configuration
- Location: Sync Settings → Advanced tab
- Setting: `[Sync] enabled=true|false`
- Runtime: `SyncManager.sync_enabled`

### Error Codes

#### Database Errors
- `database_locked` - SQLite database is locked
- `connection_failed` - Database connection failed
- `schema_mismatch` - Database schema version mismatch

#### Sync Errors
- `sync_disabled` - Synchronization is disabled
- `conflict_detected` - Data conflict detected
- `network_error` - Network communication error

#### API Errors
- `unauthorized` - Authentication required
- `forbidden` - Insufficient permissions
- `not_found` - Resource not found
- `validation_error` - Request validation failed

## Development References

### Code Architecture
- **MVC Pattern**: Model-View-Controller architecture
- **Repository Pattern**: Data access abstraction
- **Observer Pattern**: Event handling and notifications
- **Factory Pattern**: Object creation and initialization

### Key Classes
- `SyncManager` - Synchronization system management
- `DatabaseManager` - Database connection and operations
- `UserManager` - User authentication and authorization
- `ConfigManager` - Configuration file management

### File Structure
```
src/
├── data/           # Data layer and models
├── views/          # UI components and dialogs
├── controllers/    # Business logic
├── api/           # REST API endpoints
├── utils/         # Utility functions
└── tests/         # Test files
```

---

**Note**: This reference documentation is intended for developers and advanced users who need detailed technical information about the application internals.
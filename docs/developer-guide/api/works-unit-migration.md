# Works Unit Migration - API Documentation Update

## Overview

The works reference structure refactoring has been completed. The legacy `unit` string column has been removed from the works table, and all works now use `unit_id` foreign key relationships to the units table.

## API Changes

### Works Endpoints

All works-related endpoints now exclusively use `unit_id` foreign key relationships:

#### GET /api/references/works

**Enhanced Response Structure:**
- `unit_id`: Foreign key to units table (replaces legacy unit string)
- `unit_name`: Unit name from units table join
- `unit_description`: Unit description from units table
- `unit_display`: Display-friendly unit name

**Legacy Changes:**
- ❌ `unit` string field removed
- ✅ `unit_id` foreign key used exclusively
- ✅ Proper joins with units table for display

#### POST /api/references/works

**Request Body Changes:**
- `unit_id`: Required foreign key to valid unit record
- ❌ Legacy `unit` string field no longer accepted

**Validation:**
- Unit ID must reference existing unit record
- Proper foreign key constraint validation
- Circular reference prevention for parent-child relationships

#### PUT /api/references/works/{id}

**Request Body Changes:**
- `unit_id`: Foreign key to units table
- ❌ Legacy `unit` string field no longer accepted

### Migration Endpoints

#### GET /api/references/works/migration-status

**Status:** Migration Complete
- Returns historical migration statistics
- All works now use `unit_id` foreign key relationships
- Legacy unit column has been removed

#### GET /api/references/works/migration-pending

**Status:** No Pending Migrations
- Returns empty result set
- Migration process is complete

## Database Schema Changes

### Works Table

**Removed:**
```sql
unit VARCHAR(50)  -- Legacy unit column removed
```

**Current Structure:**
```sql
unit_id INTEGER REFERENCES units(id)  -- Foreign key to units table
```

### Migration Tracking

The `work_unit_migration` table contains historical migration data but is no longer actively used for new migrations.

## Frontend Integration

### API Response Format

**Before (Legacy):**
```json
{
  "id": 1,
  "name": "Concrete Work",
  "unit": "m³",
  "unit_id": null
}
```

**After (Current):**
```json
{
  "id": 1,
  "name": "Concrete Work",
  "unit_id": 5,
  "unit_name": "m³",
  "unit_description": "Cubic meter",
  "unit_display": "m³"
}
```

### Error Handling

**Invalid Unit ID:**
```json
{
  "detail": "Invalid unit_id: Unit with ID 999 does not exist"
}
```

**Missing Unit ID:**
```json
{
  "detail": "unit_id is required for work creation"
}
```

## Migration Completion Status

- ✅ **Legacy Column Removal**: Complete
- ✅ **Code References Updated**: All legacy unit references removed
- ✅ **API Endpoints Updated**: All endpoints use unit_id exclusively
- ✅ **Frontend Components Updated**: All components use proper unit display
- ✅ **Database Migration**: Complete
- ✅ **Data Integrity**: 100% maintained

## Breaking Changes

### API Clients

**Required Updates:**
1. Use `unit_id` instead of `unit` in requests
2. Handle `unit_name` from response instead of `unit`
3. Update validation to expect foreign key constraints

### Frontend Applications

**Required Updates:**
1. Update work forms to use unit selector (unit_id)
2. Display unit information from joined unit data
3. Remove any legacy unit string handling

## Backward Compatibility

**None:** This is a breaking change. The legacy `unit` column has been completely removed.

**Migration Path:**
- All existing data has been migrated to use `unit_id`
- Applications must be updated to use the new structure
- No fallback to legacy unit strings is available

## Testing

### Unit Tests
- All unit tests updated to use `unit_id` foreign keys
- Legacy unit column references removed from test data
- Foreign key constraint validation tests added

### Integration Tests
- API endpoint tests updated for new response format
- Database constraint tests for unit_id foreign keys
- Error handling tests for invalid unit references

## Support

For questions about the migration or API changes, refer to:
- Design Document: `.kiro/specs/works-reference-refactor/design.md`
- Requirements: `.kiro/specs/works-reference-refactor/requirements.md`
- Implementation Tasks: `.kiro/specs/works-reference-refactor/tasks.md`
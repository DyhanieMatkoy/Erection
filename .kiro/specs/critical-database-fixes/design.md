# Critical Database Fixes Design

## Overview

This design addresses two critical database synchronization issues that are preventing normal system operation. The primary issue is a mismatch between the database schema (which includes UUID fields added by migration) and the SQLAlchemy models (which don't include these fields). The secondary issue involves investigating and fixing work list filtering that's limiting results to test data only.

## Architecture

The solution involves updating SQLAlchemy models to match the current database schema and investigating the data filtering mechanism in the work list form. The architecture maintains the existing layered approach:

- **Data Layer**: SQLAlchemy models updated to match database schema
- **Service Layer**: Data services ensure proper UUID generation and filtering
- **View Layer**: Forms display all available data without hidden filters

## Components and Interfaces

### 1. SQLAlchemy Model Updates

**Estimate Model Enhancement**
- Add UUID field with automatic generation
- Add updated_at field with automatic timestamps
- Add is_deleted field for soft deletion support
- Ensure all synchronization fields match database schema

**Other Models Verification**
- Verify all models that received UUID fields in migration 20251217_000001
- Ensure consistent field definitions across all synchronized models

### 2. Data Service Investigation

**Work List Data Service**
- Investigate current filtering logic in DataService.get_documents()
- Identify any hidden filters that limit results to test data
- Ensure proper handling of hierarchical work structures

**Generic List Controller**
- Verify filter application in ListFormController
- Check for any hardcoded test data filters

### 3. Database Migration Verification

**Schema Consistency Check**
- Verify that all tables mentioned in migration 20251217_000001 have proper UUID fields
- Ensure model definitions match actual database schema
- Validate that UUID generation works correctly

## Data Models

### Updated Estimate Model

```python
class Estimate(Base):
    __tablename__ = 'estimates'
    
    # Existing fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True)
    # ... other existing fields ...
    
    # Synchronization fields (matching database schema)
    uuid = Column(String(36), unique=True, nullable=False, 
                  default=lambda: str(uuid.uuid4()), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, 
                       default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
```

### Work Model Verification

Ensure Work model includes all synchronization fields:
- uuid (String(36), unique, not null, with default)
- updated_at (DateTime with timezone, not null, with default and onupdate)
- is_deleted (Boolean, not null, default False)

## Error Handling

### UUID Constraint Failures
- Automatic UUID generation prevents constraint violations
- Default value ensures UUIDs are always populated
- Unique constraint violations handled gracefully with retry logic

### Data Filtering Issues
- Remove any hardcoded test data filters
- Ensure proper error handling when no data is found
- Validate filter parameters before applying to queries

### Migration Consistency
- Verify model-schema alignment during application startup
- Log warnings for any detected inconsistencies
- Provide clear error messages for schema mismatches

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Property 1: UUID generation for new estimates**
*For any* new estimate creation, the system should automatically generate a UUID and save the estimate successfully without constraint errors
**Validates: Requirements 1.1**

**Property 2: UUID preservation during updates**
*For any* existing estimate, when updated, the UUID should remain unchanged and the save operation should succeed
**Validates: Requirements 1.2**

**Property 3: Required field population**
*For any* estimate save operation, all required fields including UUID should be populated before the database operation
**Validates: Requirements 1.3**

**Property 4: Automatic timestamp updates**
*For any* estimate save operation, the modified timestamp should be automatically updated to the current time
**Validates: Requirements 1.4**

**Property 5: Complete work list display**
*For any* work list query, all non-deleted works in the database should be included in the results
**Validates: Requirements 2.1**

**Property 6: No hidden test filters**
*For any* work query without explicit filters, the results should include all available works, not just test data
**Validates: Requirements 2.2**

**Property 7: Complete search coverage**
*For any* search term, the search should operate across all available works, not a subset
**Validates: Requirements 2.3**

**Property 8: Work type display completeness**
*For any* work list display, both individual works and work groups should be included in the results
**Validates: Requirements 2.4**

**Property 9: Filter transparency**
*For any* work list query, only explicitly specified filters should be applied to the database query
**Validates: Requirements 2.5**

**Property 10: Automatic field handling**
*For any* database operation using models, all required fields should be handled automatically without manual intervention
**Validates: Requirements 3.2**

**Property 11: Synchronization field management**
*For any* CRUD operation on synchronized models, synchronization fields (UUID, updated_at, is_deleted) should be correctly populated
**Validates: Requirements 3.3**

**Property 12: Automatic UUID generation**
*For any* new record creation, a UUID should be automatically generated using the model's default value mechanism
**Validates: Requirements 3.4**

## Testing Strategy

**Dual testing approach**:

### Unit Testing
- Test UUID generation in model creation
- Test estimate save operations with all required fields
- Test work list data retrieval without filters
- Test model field validation and constraints

### Property-Based Testing
- Use Hypothesis for Python property-based testing
- Configure each property test to run minimum 100 iterations
- Tag each test with corresponding design property reference

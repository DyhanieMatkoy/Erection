# Works Reference Structure Refactoring Design

## Overview

This design addresses the refactoring of the works reference structure to eliminate the legacy unit column, improve list display performance, and evaluate UUID migration for better synchronization capabilities. The refactoring will be implemented in phases to ensure data integrity and system stability throughout the transition.

## Architecture

The refactoring follows a phased approach:

1. **Phase 1: Unit Column Migration** - Migrate all works to use unit_id foreign keys
2. **Phase 2: Display Layer Updates** - Update all UI components to use proper joins
3. **Phase 3: UUID Evaluation** - Assess and potentially implement UUID migration
4. **Phase 4: Legacy Cleanup** - Remove legacy unit column and update APIs

### Current Architecture Issues

- Mixed usage of legacy `unit` string column and `unit_id` foreign key
- Inconsistent display logic across frontend and backend
- Integer IDs limiting synchronization capabilities
- Performance issues with large hierarchical datasets

### Target Architecture

- Consistent use of `unit_id` foreign key relationships
- Optimized queries with proper joins for display
- Optional UUID-based identifiers for synchronization
- Clean data model without legacy columns

## Components and Interfaces

### Database Layer

**Work Model Refactoring**
```python
class Work(Base):
    __tablename__ = 'works'
    
    # Primary identifier (evaluate UUID migration)
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    
    # Core fields
    name = Column(String(500), nullable=False)
    code = Column(String(50))
    
    # Unit relationship (remove legacy unit column)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=True)
    # unit = Column(String(50))  # TO BE REMOVED
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey('works.id'))
    is_group = Column(Boolean, default=False)
    
    # Relationships
    unit_ref = relationship("Unit", foreign_keys=[unit_id])
    parent = relationship("Work", remote_side=[id], backref="children")
```

**Migration Support Tables**
```python
class WorkUnitMigration(Base):
    """Temporary table to track unit migration progress"""
    __tablename__ = 'work_unit_migration'
    
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    legacy_unit = Column(String(50))
    matched_unit_id = Column(Integer, ForeignKey('units.id'))
    migration_status = Column(String(20))  # 'pending', 'matched', 'manual', 'completed'
    created_at = Column(DateTime, default=func.now())
```

### API Layer

**Enhanced Works Endpoints**
```python
@router.get("/works")
async def list_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000),
    include_unit_info: bool = Query(True),
    hierarchy_mode: str = Query("flat", regex="^(flat|tree|breadcrumb)$")
):
    """Enhanced works listing with proper unit joins and hierarchy options"""
```

**Migration Endpoints**
```python
@router.post("/works/migrate-units")
async def migrate_work_units():
    """Migrate legacy unit strings to unit_id foreign keys"""

@router.get("/works/migration-status")
async def get_migration_status():
    """Get status of unit migration process"""
```

### Frontend Layer

**Enhanced Work Display Components**
- `WorkListView` - Optimized hierarchical display
- `WorkUnitDisplay` - Consistent unit information display
- `WorkMigrationPanel` - Migration progress and controls

## Data Models

### Work Reference Structure

```typescript
interface Work {
  id: number
  uuid: string  // For future synchronization
  name: string
  code?: string
  
  // Unit relationship (no more legacy unit string)
  unit_id?: number
  unit?: Unit  // Populated through join
  
  // Hierarchy
  parent_id?: number
  is_group: boolean
  children?: Work[]
  
  // Display helpers
  hierarchy_path?: string[]
  level?: number
}

interface Unit {
  id: number
  uuid: string
  name: string
  description?: string
}
```

### Migration Tracking

```typescript
interface WorkUnitMigrationStatus {
  total_works: number
  migrated_count: number
  pending_count: number
  manual_review_count: number
  completion_percentage: number
  estimated_completion: string
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all identified properties, several can be consolidated:
- Properties 1.4 and 5.5 both test display completeness and can be combined
- Properties 2.3 and 4.4 both test proper join usage and can be combined  
- Properties 4.1 and 4.2 both test migration completion and can be combined
- Properties 5.1 and 1.2 both test validation and can be combined

### Core Properties

**Property 1: Unit Reference Consistency**
*For any* work record, when unit_id is set, the referenced unit must exist and the displayed unit name must match the referenced unit record
**Validates: Requirements 1.1, 1.4, 5.5**

**Property 2: Legacy Unit Migration Completeness**
*For any* work with legacy unit data, the migration process must preserve all unit information through proper unit_id mapping without data loss
**Validates: Requirements 1.3, 1.5**

**Property 3: Hierarchical Display Integrity**
*For any* hierarchical work structure, display operations must preserve parent-child relationships regardless of filtering, sorting, or pagination
**Validates: Requirements 2.1, 2.2, 2.4**

**Property 4: Query Optimization Correctness**
*For any* work data request, the system must use proper joins with the units table and return complete unit information efficiently
**Validates: Requirements 2.3, 4.4**

**Property 5: UUID Migration Consistency**
*For any* UUID migration operation, all related tables and foreign key relationships must be updated consistently while maintaining referential integrity
**Validates: Requirements 3.2, 3.4, 3.5**

**Property 6: Validation and Integrity**
*For any* work creation or update operation, all required fields and relationships must be validated, including prevention of circular references
**Validates: Requirements 1.2, 5.1, 5.2**

**Property 7: Migration Completion Verification**
*For any* completed migration, the legacy unit column can be safely removed without data loss and all API endpoints use unit_id exclusively
**Validates: Requirements 4.1, 4.2, 4.3**

**Property 8: Bulk Operation Integrity**
*For any* bulk operation on work data, referential integrity and all business constraints must be maintained throughout the operation
**Validates: Requirements 5.3, 5.4**

## Error Handling

### Migration Errors
- **Unit Matching Failures**: When legacy unit strings cannot be automatically matched to unit records
- **Circular Reference Detection**: Prevention of parent-child circular references during hierarchy updates
- **Foreign Key Violations**: Handling of invalid unit_id references during migration

### Display Errors
- **Missing Unit Information**: Graceful handling when unit_id references are invalid
- **Hierarchy Corruption**: Detection and recovery from corrupted parent-child relationships
- **Performance Degradation**: Monitoring and optimization of large dataset queries

### UUID Migration Errors
- **Duplicate UUID Generation**: Prevention of UUID collisions during migration
- **Foreign Key Update Failures**: Rollback mechanisms for failed relationship updates
- **Synchronization Conflicts**: Handling of UUID conflicts during system synchronization

## Testing Strategy

### Unit Testing
- Work model validation and constraint testing
- Unit migration logic with various legacy data scenarios
- Hierarchy manipulation and circular reference prevention
- API endpoint response validation with proper joins

### Property-Based Testing
The system will use **Hypothesis** for Python property-based testing with a minimum of 100 iterations per property test. Each property-based test will be tagged with comments explicitly referencing the correctness property from this design document using the format: `**Feature: works-reference-refactor, Property {number}: {property_text}**`

**Property Test Implementation Requirements:**
- Generate random work hierarchies with various unit configurations
- Test migration scenarios with mixed legacy and new data
- Validate display consistency across different data combinations
- Verify UUID migration with complex foreign key relationships
- Test bulk operations with large datasets and edge cases

### Integration Testing
- End-to-end migration workflow testing
- Frontend-backend integration with new display components
- Performance testing with large hierarchical datasets
- Cross-browser compatibility for enhanced UI components

### Migration Testing
- Backup and restore procedures for migration rollback
- Data integrity verification before and after migration
- Performance impact assessment during migration
- User acceptance testing for new display features
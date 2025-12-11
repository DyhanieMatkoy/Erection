# Design Document - Simplified Work Specification

## Overview

This design document outlines the implementation of a simplified work specification system that replaces the current complex cost_item_materials association model with a direct specification entry approach. The new system eliminates the need for pre-existing cost item catalogs and allows users to directly define work composition through specification entries.

## Architecture

### Current Architecture Issues
- Complex many-to-many relationship between works, cost_items, and materials
- Artificial separation between cost items and materials
- Forced dependency on pre-existing catalog entries
- Confusing user workflow requiring catalog selection

### New Architecture
- Single `work_specifications` table directly linked to works
- Direct entry of specification components without catalog dependencies
- Simplified data model with clear component typing
- Streamlined user workflow for specification management

## Components and Interfaces

### Database Layer

#### New Table: work_specifications
```sql
CREATE TABLE work_specifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    component_type VARCHAR(20) NOT NULL, -- 'Material', 'Labor', 'Equipment', 'Other'
    component_name VARCHAR(500) NOT NULL,
    unit_id INTEGER,
    consumption_rate DECIMAL(15,6) NOT NULL DEFAULT 0,
    unit_price DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_cost DECIMAL(15,2) GENERATED ALWAYS AS (consumption_rate * unit_price) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

CREATE INDEX idx_work_specifications_work_id ON work_specifications(work_id);
CREATE INDEX idx_work_specifications_component_type ON work_specifications(component_type);
```

#### Migration Strategy
1. Create new work_specifications table
2. Migrate existing cost_item_materials data to work_specifications
3. Maintain cost_item_materials table for backward compatibility during transition
4. Add feature flag to switch between old and new systems
5. Remove old tables after full migration

### API Layer

#### New Models (Pydantic)
```python
class WorkSpecificationBase(BaseModel):
    work_id: int
    component_type: str  # Material, Labor, Equipment, Other
    component_name: str
    unit_id: Optional[int] = None
    consumption_rate: float = Field(gt=0)
    unit_price: float = Field(ge=0)

class WorkSpecificationCreate(WorkSpecificationBase):
    pass

class WorkSpecificationUpdate(BaseModel):
    component_type: Optional[str] = None
    component_name: Optional[str] = None
    unit_id: Optional[int] = None
    consumption_rate: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)

class WorkSpecification(WorkSpecificationBase):
    id: int
    total_cost: float
    unit_name: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

class WorkSpecificationSummary(BaseModel):
    work_id: int
    work_name: str
    work_code: Optional[str] = None
    specifications: List[WorkSpecification] = []
    totals_by_type: Dict[str, float] = {}
    total_cost: float = 0.0
```

#### New Endpoints
```python
# GET /api/works/{work_id}/specifications
# POST /api/works/{work_id}/specifications
# PUT /api/works/{work_id}/specifications/{spec_id}
# DELETE /api/works/{work_id}/specifications/{spec_id}
# POST /api/works/{work_id}/specifications/copy-from/{source_work_id}
# GET /api/works/{work_id}/specifications/export
# POST /api/works/{work_id}/specifications/import
```

### Desktop Application (PyQt6)

#### New Components
1.106→1. **WorkSpecificationWidget**: Main specification management widget
107→2. **SpecificationEntryDialog**: Dialog for adding/editing specification entries
108→   - Integration with MaterialSelectorDialog for material picking
109→3. **ComponentTypeComboBox**: Dropdown for component types
110→4. **SpecificationTableWidget**: Enhanced table widget with inline editing
5. **SpecificationImportDialog**: Excel import functionality
6. **SpecificationExportDialog**: Excel export functionality

#### Integration Points
- Integrate into existing WorkForm as new tab
- Replace current cost_items_table and materials_table widgets
- Update WorkRepository to handle work_specifications
- Add new SpecificationRepository for CRUD operations

### Web Client (Vue 3 + TypeScript)

#### New Components
```typescript
// WorkSpecificationPanel.vue - Main specification management
// SpecificationEntryForm.vue - Add/edit specification entries
// SpecificationTable.vue - Display and inline edit specifications
// ComponentTypeSelector.vue - Component type selection
// SpecificationImportExport.vue - Import/export functionality
// SpecificationSummary.vue - Cost breakdown by component type
```

#### New Composables
```typescript
// useWorkSpecification.ts - Specification management logic
// useSpecificationValidation.ts - Validation rules
// useSpecificationImportExport.ts - Import/export functionality
```

### DBF Importer

#### New Import Logic
1. **Specification Mapping**: Map DBF work composition data to work_specifications
2. **Component Type Detection**: Automatically detect component types from DBF data
3. **Unit Mapping**: Map DBF units to system units table
4. **Validation**: Validate consumption rates and unit prices during import

## Data Models

### Work Specification Entity
```python
@dataclass
class WorkSpecification:
    id: Optional[int]
    work_id: int
    component_type: ComponentType
    component_name: str
    unit_id: Optional[int]
    consumption_rate: Decimal
    unit_price: Decimal
    total_cost: Decimal  # Calculated field
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

class ComponentType(Enum):
    MATERIAL = "Material"
    LABOR = "Labor" 
    EQUIPMENT = "Equipment"
    OTHER = "Other"
```

### Aggregated Models
```python
@dataclass
class WorkSpecificationSummary:
    work_id: int
    work_name: str
    specifications: List[WorkSpecification]
    material_total: Decimal
    labor_total: Decimal
    equipment_total: Decimal
    other_total: Decimal
    grand_total: Decimal
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Specification Entry Validation
*For any* work specification entry, the consumption rate and unit price must be positive numbers, and the total cost must equal consumption_rate × unit_price
**Validates: Requirements 1.4, 2.2, 9.2**

### Property 2: Work Specification Completeness
*For any* saved work that is not a group, it must have at least one specification entry
**Validates: Requirements 9.1**

### Property 3: Total Cost Calculation Consistency
*For any* work with specifications, the total cost must equal the sum of all specification entry total costs
**Validates: Requirements 4.1, 4.2**

### Property 4: Component Type Consistency
*For any* specification entry, the component_type must be one of: Material, Labor, Equipment, Other
**Validates: Requirements 1.3, 10.2**

### Property 5: Unit Reference Integrity
*For any* specification entry with a unit_id, the referenced unit must exist in the units table
**Validates: Requirements 11.4**

### Property 6: Specification Deletion Cascade
*For any* deleted work, all associated specification entries must be automatically deleted
**Validates: Requirements 11.3**

### Property 7: Import Data Validation
*For any* imported specification data, all entries must pass the same validation rules as manually entered data
**Validates: Requirements 7.5**

### Property 8: Export Data Completeness
*For any* exported work specification, the Excel file must contain all specification entries with correct totals
**Validates: Requirements 6.2, 6.3**

### Property 9: Template Application Consistency
*For any* template applied to a work, all template specification entries must be copied with identical values except work_id
**Validates: Requirements 13.2, 13.3**

### Property 10: Duplicate Entry Prevention
*For any* work, there should not be multiple specification entries with identical component_name and component_type
**Validates: Requirements 1.5 (implied)**

## Error Handling

### Validation Errors
- **Invalid consumption rate**: "Consumption rate must be greater than zero"
- **Invalid unit price**: "Unit price must be greater than or equal to zero"
- **Missing component name**: "Component name is required"
- **Invalid component type**: "Component type must be Material, Labor, Equipment, or Other"

### Database Errors
- **Foreign key constraint**: "Referenced work or unit does not exist"
- **Cascade deletion failure**: "Cannot delete work with specification entries"
- **Duplicate entry**: "Specification entry with this name and type already exists"

### Import/Export Errors
- **File format error**: "Invalid Excel file format or missing required columns"
- **Data validation error**: "Row {n}: {specific validation message}"
- **File access error**: "Cannot read/write file: {file path}"

## Testing Strategy

### Unit Testing
- Test specification CRUD operations
- Test validation rules for all input fields
- Test total cost calculations
- Test component type validation
- Test import/export functionality

### Property-Based Testing
- Generate random specification entries and verify total cost calculations
- Generate random work compositions and verify totals by component type
- Test import/export round-trip consistency
- Verify cascade deletion behavior
- Test template application with various work types

### Integration Testing
- Test full workflow: create work → add specifications → save → reload
- Test migration from old cost_item_materials to new work_specifications
- Test API endpoints with various data combinations
- Test desktop and web client integration

### Performance Testing
- Test specification loading performance with large numbers of entries
- Test total cost calculation performance
- Test import performance with large Excel files
- Test database query performance with proper indexing
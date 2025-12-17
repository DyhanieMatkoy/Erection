# Design Document - Estimate Hierarchy System

## Overview

The Estimate Hierarchy System introduces a two-level hierarchical structure for construction estimates, enabling better project management through the distinction between General Estimates (master project documents) and Plan Estimates (brigade execution plans). This design implements a parent-child relationship where General Estimates serve as comprehensive project scopes, and Plan Estimates represent focused work selections made by brigade leaders for execution.

The system maintains referential integrity while providing intuitive user interfaces for creating, managing, and navigating estimate hierarchies. The design ensures data consistency, prevents circular references, and supports efficient querying and reporting of hierarchical relationships.

## Architecture

The estimate hierarchy system follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   Desktop UI    │ │    Web UI       ││
│  │   (PyQt6)       │ │   (Vue.js)      ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Service Layer                │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │ Hierarchy       │ │ Validation      ││
│  │ Service         │ │ Service         ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│           Repository Layer              │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │ Estimate        │ │ Hierarchy       ││
│  │ Repository      │ │ Repository      ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│             Data Layer                  │
│           SQLite/PostgreSQL             │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Database Schema Extensions

**Estimates Table Modifications:**
```sql
ALTER TABLE estimates ADD COLUMN base_document_id INTEGER REFERENCES estimates(id);
ALTER TABLE estimates ADD COLUMN estimate_type VARCHAR(20) DEFAULT 'General' CHECK (estimate_type IN ('General', 'Plan'));
CREATE INDEX idx_estimates_base_document ON estimates(base_document_id);
CREATE INDEX idx_estimates_type ON estimates(estimate_type);
```

**Hierarchy Validation Constraints:**
- Foreign key constraint ensures base_document_id references valid estimates
- Check constraint ensures estimate_type is either 'General' or 'Plan'
- Trigger prevents circular references and enforces hierarchy rules

### 2. Repository Layer

**EstimateHierarchyRepository:**
```python
class EstimateHierarchyRepository:
    def get_general_estimates(self) -> List[Estimate]
    def get_plan_estimates_by_base(self, base_id: int) -> List[Estimate]
    def validate_hierarchy_integrity(self, estimate_id: int, base_id: int) -> bool
    def get_hierarchy_tree(self, root_id: int) -> HierarchyTree
    def update_base_document(self, estimate_id: int, base_id: Optional[int]) -> bool
```

### 3. Service Layer

**HierarchyService:**
```python
class HierarchyService:
    def create_general_estimate(self, estimate_data: EstimateData) -> Estimate
    def create_plan_estimate(self, estimate_data: EstimateData, base_id: int) -> Estimate
    def copy_works_from_base(self, plan_id: int, selected_works: List[int]) -> bool
    def validate_hierarchy_rules(self, estimate: Estimate) -> ValidationResult
    def get_hierarchy_summary(self, base_id: int) -> HierarchySummary
```

### 4. User Interface Components

**Desktop Application (PyQt6):**
- EstimateFormWidget with base document picker
- HierarchyTreeWidget for navigation
- BaseDocumentSelectorDialog
- WorkCopyDialog for selecting works from general estimates

**Web Application (Vue.js):**
- EstimateHierarchyComponent
- BaseDocumentPicker component
- HierarchyNavigationPanel
- WorkSelectionModal

## Data Models

### Enhanced Estimate Model

```python
@dataclass
class Estimate:
    id: Optional[int]
    code: str
    name: str
    base_document_id: Optional[int]
    estimate_type: EstimateType
    total_amount: Decimal
    created_date: datetime
    modified_date: datetime
    
    # Hierarchy relationships
    base_document: Optional['Estimate'] = None
    plan_estimates: List['Estimate'] = field(default_factory=list)
    
    @property
    def is_general(self) -> bool:
        return self.estimate_type == EstimateType.GENERAL
    
    @property
    def is_plan(self) -> bool:
        return self.estimate_type == EstimateType.PLAN
```

### Hierarchy Tree Model

```python
@dataclass
class HierarchyNode:
    estimate: Estimate
    children: List['HierarchyNode'] = field(default_factory=list)
    depth: int = 0
    
@dataclass
class HierarchyTree:
    root: HierarchyNode
    total_nodes: int
    max_depth: int
```

### Validation Models

```python
@dataclass
class HierarchyValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class HierarchyValidationRules:
    MAX_HIERARCHY_DEPTH = 2
    ALLOWED_BASE_TYPES = [EstimateType.GENERAL]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Estimate Classification Consistency
*For any* estimate, if base_document_id is NULL then estimate_type must be 'General', and if base_document_id is not NULL then estimate_type must be 'Plan' with the base document being a valid General Estimate
**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.5**

### Property 2: Base Document Validation
*For any* estimate being set as a base document, it must be a General Estimate (estimate_type = 'General' and base_document_id = NULL), and plan estimates or self-references should be rejected
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 3: Hierarchy Depth Limitation
*For any* estimate hierarchy, the maximum depth should not exceed 2 levels (General → Plan)
**Validates: Requirements 6.4**

### Property 4: Referential Integrity
*For any* plan estimate, the base_document_id must reference an existing estimate with estimate_type = 'General', and all plan estimates must have valid base document references
**Validates: Requirements 9.1, 9.4**

### Property 5: Deletion Constraint
*For any* general estimate that has dependent plan estimates, deletion should be prevented until all dependencies are removed
**Validates: Requirements 9.2, 9.3**

### Property 6: Base Document Selector Filtering
*For any* base document selection interface, only general estimates (estimates with base_document_id = NULL) should be available for selection
**Validates: Requirements 3.2, 1.5**

### Property 7: Automatic Type Assignment
*For any* estimate form, when the base document field is populated with a valid general estimate, the estimate type should automatically be set to "Plan", and when cleared, should allow classification as "General"
**Validates: Requirements 3.4, 3.5**

### Property 8: Display Consistency
*For any* estimate display, general estimates should show "Генеральная смета" indicator and plan estimates should show "Плановая смета" with base document reference
**Validates: Requirements 1.3, 2.3**

## Error Handling

### Validation Errors

**Hierarchy Validation:**
- `CIRCULAR_REFERENCE_ERROR`: "Невозможно создать циклическую ссылку в иерархии смет"
- `INVALID_BASE_TYPE_ERROR`: "Только генеральные сметы могут быть документами-основаниями"
- `MAX_DEPTH_EXCEEDED_ERROR`: "Превышена максимальная глубина иерархии смет"
- `SELF_REFERENCE_ERROR`: "Смета не может ссылаться сама на себя"

**Data Integrity Errors:**
- `ORPHANED_PLAN_ERROR`: "Плановая смета ссылается на несуществующий документ-основание"
- `INVALID_FOREIGN_KEY_ERROR`: "Недопустимая ссылка на документ-основание"
- `CONSTRAINT_VIOLATION_ERROR`: "Нарушение ограничений целостности данных"

### Database Errors

**Connection Errors:**
- Handle database connection failures gracefully
- Provide retry mechanisms for transient failures
- Log detailed error information for debugging

**Transaction Errors:**
- Implement proper rollback mechanisms for failed hierarchy operations
- Ensure atomic updates when modifying hierarchy relationships
- Maintain data consistency during concurrent access

### User Interface Errors

**Form Validation:**
- Real-time validation of base document selections
- Clear error messages for invalid hierarchy operations
- Visual indicators for validation states

**Permission Errors:**
- Check user permissions before allowing hierarchy operations
- Display appropriate error messages for insufficient permissions
- Graceful degradation of functionality based on user roles

## Testing Strategy

### Unit Testing Approach

Unit tests will focus on individual components and their specific behaviors:

**Repository Layer Tests:**
- Test CRUD operations for estimate hierarchy data
- Verify foreign key constraint enforcement
- Test query performance with hierarchical data

**Service Layer Tests:**
- Test hierarchy validation logic
- Verify business rule enforcement
- Test error handling scenarios

**Model Tests:**
- Test estimate classification logic
- Verify hierarchy relationship properties
- Test data validation methods

### Property-Based Testing Approach

Property-based tests will verify universal properties across all valid inputs using Hypothesis for Python components:

**Configuration:**
- Minimum 100 iterations per property test
- Custom generators for estimate hierarchies
- Edge case generation for boundary conditions

**Property Test Implementation:**
Each property-based test will be tagged with comments referencing the design document properties and will generate random estimate hierarchies to verify correctness properties hold across all valid scenarios.

**Test Data Generation:**
- Generate valid estimate hierarchies with varying depths
- Create invalid hierarchy scenarios for negative testing
- Generate large datasets for performance testing

### Integration Testing

**Database Integration:**
- Test schema migrations and data integrity
- Verify foreign key constraints and triggers
- Test concurrent access scenarios

**API Integration:**
- Test REST endpoints for hierarchy operations
- Verify request/response formats
- Test error handling in API layer

**UI Integration:**
- Test form interactions and validation
- Verify hierarchy navigation functionality
- Test responsive behavior across different screen sizes

### Performance Testing

**Query Performance:**
- Test hierarchy queries with large datasets
- Verify index effectiveness
- Monitor query execution plans

**UI Responsiveness:**
- Test form loading times with complex hierarchies
- Verify smooth navigation between hierarchy levels
- Test search and filter performance

### Security Testing

**Permission Testing:**
- Verify role-based access controls
- Test unauthorized access attempts
- Validate permission inheritance in hierarchies

**Data Validation:**
- Test input sanitization
- Verify SQL injection prevention
- Test cross-site scripting prevention
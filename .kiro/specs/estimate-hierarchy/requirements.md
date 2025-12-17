# Requirements Document

## Introduction

This specification defines the requirements for implementing hierarchical estimate structure in the construction management system. The system will support two types of estimates: General Estimates (Генеральные сметы) that serve as master documents, and Plan Estimates (Плановые сметы) that reference general estimates and represent work selections made by brigade leaders for execution.

This hierarchical structure enables better project management by allowing brigade leaders to create focused work plans based on comprehensive general estimates, while maintaining traceability and control over the overall project scope and budget.

## Glossary

- **Estimate**: A construction cost estimate document containing works, materials, and labor calculations
- **General_Estimate**: An estimate without a base document reference, serving as the master estimate for a project
- **Plan_Estimate**: An estimate that references a general estimate as its base document, containing selected works for execution
- **Base_Document**: A reference field linking a plan estimate to its parent general estimate
- **Estimate_Type**: An enumeration indicating whether an estimate is "General" or "Plan"
- **Brigade_Leader**: A construction supervisor who selects works from general estimates to create execution plans
- **Work_Selection**: The process of choosing specific works from a general estimate to include in a plan estimate
- **Estimate_Hierarchy**: The parent-child relationship structure between general and plan estimates

## Requirements

### Requirement 1

**User Story:** As a construction manager, I want to create general estimates without base document references, so that I can establish master project estimates that serve as the foundation for work planning.

#### Acceptance Criteria

1. WHEN a user creates a new estimate without selecting a base document THEN the system SHALL classify it as a General Estimate
2. WHEN a general estimate is saved THEN the system SHALL set the estimate_type field to "General" and base_document_id to NULL
3. WHEN a general estimate is displayed THEN the system SHALL show "Генеральная смета" in the estimate type indicator
4. WHEN a user views a general estimate THEN the system SHALL display all works, materials, and cost calculations as the complete project scope
5. WHEN a general estimate exists THEN the system SHALL allow it to be selected as a base document for plan estimates

### Requirement 2

**User Story:** As a brigade leader, I want to create plan estimates that reference general estimates, so that I can select specific works for execution while maintaining connection to the master project plan.

#### Acceptance Criteria

1. WHEN a user creates a new estimate and selects a base document THEN the system SHALL classify it as a Plan Estimate
2. WHEN a plan estimate is saved THEN the system SHALL set the estimate_type field to "Plan" and store the selected general estimate ID in base_document_id
3. WHEN a plan estimate is displayed THEN the system SHALL show "Плановая смета" and the base document reference in the estimate type indicator
4. WHEN a user views a plan estimate THEN the system SHALL display only the works selected from the general estimate
5. WHEN a plan estimate is created THEN the system SHALL validate that the base document is a valid general estimate

### Requirement 3

**User Story:** As a construction manager, I want to add a base document field to the estimate form, so that users can establish hierarchical relationships between estimates.

#### Acceptance Criteria

1. WHEN the estimate form is displayed THEN the system SHALL include a "Документ-основание" field with a reference picker for estimates
2. WHEN the base document picker opens THEN the system SHALL display only general estimates (estimates with base_document_id = NULL)
3. WHEN a user selects a base document THEN the system SHALL populate the field with the general estimate's code and name
4. WHEN a user clears the base document field THEN the system SHALL remove the reference and classify the estimate as general
5. WHEN the base document field is populated THEN the system SHALL automatically set the estimate type to "Plan"

### Requirement 4

**User Story:** As a construction manager, I want to see the estimate hierarchy in the estimates list, so that I can understand the relationships between general and plan estimates.

#### Acceptance Criteria

1. WHEN the estimates list is displayed THEN the system SHALL include columns for "Тип сметы" (Estimate Type) and "Документ-основание" (Base Document)
2. WHEN a general estimate is shown in the list THEN the system SHALL display "Генеральная" in the type column and empty base document
3. WHEN a plan estimate is shown in the list THEN the system SHALL display "Плановая" in the type column and the base document code/name
4. WHEN estimates are sorted THEN the system SHALL allow sorting by estimate type and base document
5. WHEN estimates are filtered THEN the system SHALL allow filtering by estimate type (General/Plan) and base document

### Requirement 5

**User Story:** As a brigade leader, I want to copy works from a general estimate to a plan estimate, so that I can quickly select the works my brigade will execute.

#### Acceptance Criteria

1. WHEN creating a plan estimate with a base document THEN the system SHALL provide an option to copy works from the general estimate
2. WHEN the copy works dialog opens THEN the system SHALL display all works from the base general estimate with checkboxes for selection
3. WHEN a user selects works and confirms THEN the system SHALL copy the selected works with their quantities, prices, and compositions to the plan estimate
4. WHEN works are copied THEN the system SHALL maintain references to the original work items from the general estimate
5. WHEN works are copied THEN the system SHALL recalculate the plan estimate totals based on the selected works

### Requirement 6

**User Story:** As a construction manager, I want to prevent circular references in estimate hierarchies, so that the system maintains data integrity and prevents infinite loops.

#### Acceptance Criteria

1. WHEN a user attempts to set a plan estimate as the base document for another estimate THEN the system SHALL prevent the operation and display an error message
2. WHEN a user attempts to set an estimate as its own base document THEN the system SHALL prevent the operation and display an error message
3. WHEN validating base document selection THEN the system SHALL ensure only general estimates can be selected as base documents
4. WHEN an estimate hierarchy is created THEN the system SHALL enforce a maximum depth of two levels (General → Plan)
5. WHEN base document validation fails THEN the system SHALL display "Только генеральные сметы могут быть документами-основаниями"

### Requirement 7

**User Story:** As a construction manager, I want to see summary information about plan estimates derived from each general estimate, so that I can track project execution progress.

#### Acceptance Criteria

1. WHEN viewing a general estimate THEN the system SHALL display a count of associated plan estimates
2. WHEN viewing a general estimate THEN the system SHALL provide a link or button to view all derived plan estimates
3. WHEN the derived estimates list opens THEN the system SHALL show all plan estimates that reference the current general estimate
4. WHEN derived estimates are displayed THEN the system SHALL show estimate codes, names, creation dates, and total values
5. WHEN no plan estimates exist for a general estimate THEN the system SHALL display "Нет плановых смет на основе данной генеральной сметы"

### Requirement 8

**User Story:** As a construction manager, I want to update general estimates and propagate changes to plan estimates, so that plan estimates remain synchronized with the master project scope.

#### Acceptance Criteria

1. WHEN a general estimate is modified THEN the system SHALL identify all dependent plan estimates
2. WHEN changes affect works that are included in plan estimates THEN the system SHALL notify users of potential impacts
3. WHEN a work is removed from a general estimate THEN the system SHALL warn if the work exists in dependent plan estimates
4. WHEN a work price is updated in a general estimate THEN the system SHALL provide an option to update prices in dependent plan estimates
5. WHEN propagating changes THEN the system SHALL require user confirmation before modifying plan estimates

### Requirement 9

**User Story:** As a construction manager, I want to validate estimate hierarchy integrity, so that the system maintains consistent relationships and prevents data corruption.

#### Acceptance Criteria

1. WHEN an estimate is saved THEN the system SHALL validate that base_document_id references an existing general estimate
2. WHEN an estimate is deleted THEN the system SHALL check if it serves as a base document for other estimates
3. IF a general estimate has dependent plan estimates THEN the system SHALL prevent deletion and display a warning message
4. WHEN database integrity is checked THEN the system SHALL ensure all plan estimates have valid base document references
5. WHEN integrity violations are found THEN the system SHALL log errors and provide repair options

### Requirement 10

**User Story:** As a construction manager, I want to generate reports showing estimate hierarchies, so that I can analyze project structure and execution planning.

#### Acceptance Criteria

1. WHEN generating estimate hierarchy reports THEN the system SHALL display general estimates with their dependent plan estimates in a tree structure
2. WHEN hierarchy reports are displayed THEN the system SHALL show estimate codes, names, types, total values, and creation dates
3. WHEN hierarchy reports are generated THEN the system SHALL calculate summary statistics (total general estimates, total plan estimates, coverage percentages)
4. WHEN exporting hierarchy reports THEN the system SHALL support Excel format with proper indentation showing the hierarchy
5. WHEN printing hierarchy reports THEN the system SHALL format the output with clear visual hierarchy indicators

### Requirement 11

**User Story:** As a database administrator, I want proper database schema changes to support estimate hierarchies, so that the system can store and retrieve hierarchical estimate data efficiently.

#### Acceptance Criteria

1. WHEN the database schema is updated THEN the system SHALL add base_document_id column to the estimates table as a foreign key
2. WHEN the database schema is updated THEN the system SHALL add estimate_type column to the estimates table with values "General" or "Plan"
3. WHEN foreign key constraints are created THEN the system SHALL ensure base_document_id references estimates.id
4. WHEN database indexes are created THEN the system SHALL add indexes on base_document_id and estimate_type for query performance
5. WHEN migration is complete THEN the system SHALL set existing estimates to "General" type with NULL base_document_id

### Requirement 12

**User Story:** As a construction manager, I want to search and filter estimates by hierarchy relationships, so that I can quickly find related estimates.

#### Acceptance Criteria

1. WHEN searching estimates THEN the system SHALL allow filtering by estimate type (General/Plan)
2. WHEN searching estimates THEN the system SHALL allow filtering by base document to find all plan estimates for a specific general estimate
3. WHEN search results are displayed THEN the system SHALL show the hierarchy relationship in the results
4. WHEN advanced search is used THEN the system SHALL allow combining hierarchy filters with other criteria (date, amount, status)
5. WHEN search filters are applied THEN the system SHALL maintain filter state when navigating between estimate records

### Requirement 13

**User Story:** As a construction manager, I want to see visual indicators of estimate types in the user interface, so that I can quickly distinguish between general and plan estimates.

#### Acceptance Criteria

1. WHEN estimates are displayed in lists THEN the system SHALL use distinct icons for general estimates (📋) and plan estimates (📝)
2. WHEN estimate forms are opened THEN the system SHALL display the estimate type prominently in the form header
3. WHEN plan estimates are displayed THEN the system SHALL show a breadcrumb or link to the base general estimate
4. WHEN estimate cards or tiles are used THEN the system SHALL use color coding (blue for general, green for plan) to distinguish types
5. WHEN estimate type indicators are displayed THEN the system SHALL include tooltips explaining the estimate type and hierarchy relationship

### Requirement 14

**User Story:** As a construction manager, I want to control permissions for estimate hierarchy operations, so that only authorized users can create and modify estimate relationships.

#### Acceptance Criteria

1. WHEN a user attempts to create a general estimate THEN the system SHALL verify the user has "create_general_estimate" permission
2. WHEN a user attempts to create a plan estimate THEN the system SHALL verify the user has "create_plan_estimate" permission
3. WHEN a user attempts to modify base document relationships THEN the system SHALL verify the user has "modify_estimate_hierarchy" permission
4. WHEN permission checks fail THEN the system SHALL display "Недостаточно прав для выполнения операции" and prevent the action
5. WHEN users view estimates THEN the system SHALL show only hierarchy operations they are authorized to perform

### Requirement 15

**User Story:** As a construction manager, I want to track changes to estimate hierarchies, so that I can maintain an audit trail of hierarchy modifications.

#### Acceptance Criteria

1. WHEN an estimate's base document is changed THEN the system SHALL log the change with user, timestamp, old value, and new value
2. WHEN an estimate type changes from general to plan or vice versa THEN the system SHALL log the type change
3. WHEN hierarchy relationships are created or deleted THEN the system SHALL record the operation in the audit log
4. WHEN viewing estimate history THEN the system SHALL display hierarchy changes alongside other estimate modifications
5. WHEN audit reports are generated THEN the system SHALL include hierarchy change events with clear descriptions of what changed
# Requirements Document

## Introduction

This specification defines the requirements for a comprehensive Work form interface that allows users to define the complete composition of construction work types. The form integrates cost items (трудозатраты в нормочасах) and materials (нормы расхода материалов) into a single unified editing interface, enabling users to specify labor requirements and material consumption rates for each work type.

The Work form is a critical component of the construction management system, as it establishes the foundation for accurate cost estimation, material planning, and labor scheduling. By defining work composition at the catalog level, the system can automatically calculate material requirements and labor costs when works are added to estimates.

## Glossary

- **Work**: A type of construction activity (e.g., "Штукатурка стен" - Wall Plastering)
- **CostItem**: A cost element or component that contributes to work execution (e.g., "Труд рабочих" - Labor, "Аренда оборудования" - Equipment rental)
- **Material**: A physical material consumed during work execution (e.g., "Цемент" - Cement, "Песок" - Sand)
- **CostItemMaterial**: An association record linking a work type to its cost items and materials
- **Unit**: A measurement unit (e.g., м, м², м³, кг, т, шт)
- **Quantity per Unit**: The amount of material consumed per unit of work (e.g., 0.015 т of cement per м² of plastering)
- **Labor Coefficient**: The number of labor hours required per unit of work
- **Work Composition**: The complete set of cost items and materials that define how a work type is executed

## Requirements

### Requirement 1

**User Story:** As a construction estimator, I want to define the basic properties of a work type, so that I can establish the foundation for cost calculations and work planning.

#### Acceptance Criteria

1. WHEN a user creates or edits a work THEN the system SHALL display input fields for code, name, unit, price, and labor rate
2. WHEN a user enters a work name THEN the system SHALL validate that the name is not empty
3. WHEN a user selects "Is Group" checkbox THEN the system SHALL disable the price and labor rate fields
4. WHEN a user selects a parent work THEN the system SHALL display only valid parent options from the works hierarchy
5. WHEN a user saves a work with valid data THEN the system SHALL persist the work record to the database

### Requirement 2

**User Story:** As a construction estimator, I want to add cost items to a work type, so that I can define the labor and overhead components required for work execution.

#### Acceptance Criteria

1. WHEN a user clicks the "Add Cost Item" button THEN the system SHALL display a full-scale cost item list form with search, filters, and pagination
2. WHEN a user searches for cost items THEN the system SHALL filter the list by code or description in real-time
3. WHEN a user selects a cost item from the list and confirms THEN the system SHALL create a CostItemMaterial association record with the current work ID
4. WHEN a cost item is added to the work THEN the system SHALL display it in the cost items table with code, description, unit, price, and labor coefficient
5. WHEN a user attempts to add a duplicate cost item THEN the system SHALL prevent the addition and display an error message

### Requirement 3

**User Story:** As a construction estimator, I want to remove cost items from a work type, so that I can correct mistakes or update work composition.

#### Acceptance Criteria

1. WHEN a user clicks the delete button for a cost item THEN the system SHALL check if the cost item has associated materials
2. IF the cost item has associated materials THEN the system SHALL display a warning message and prevent deletion
3. IF the cost item has no associated materials THEN the system SHALL display a confirmation dialog
4. WHEN the user confirms deletion THEN the system SHALL remove all CostItemMaterial records where work_id matches current work AND cost_item_id matches selected cost item AND material_id is NULL
5. WHEN deletion is complete THEN the system SHALL refresh the cost items table

### Requirement 4

**User Story:** As a construction estimator, I want to add materials to a work type and link them to specific cost items, so that I can define material consumption rates for accurate material planning.

#### Acceptance Criteria

1. WHEN a user clicks the "Add Material" button THEN the system SHALL display a multi-step material addition form with full-scale list forms
2. WHEN the material addition form opens THEN the system SHALL display a full-scale list form to select a cost item from those already added to the work
3. WHEN a user searches for materials THEN the system SHALL display a full-scale materials list form with search, filters, and pagination
4. WHEN a user selects a material and enters a quantity per unit THEN the system SHALL validate that quantity is greater than zero
5. WHEN a user confirms material addition THEN the system SHALL create a CostItemMaterial record with work_id, cost_item_id, material_id, and quantity_per_unit

### Requirement 5

**User Story:** As a construction estimator, I want to edit material quantities for a work type, so that I can adjust consumption rates based on actual experience or updated specifications.

#### Acceptance Criteria

1. WHEN a user clicks the edit button or double-clicks the quantity cell THEN the system SHALL make the quantity field editable
2. WHEN a user enters a new quantity value THEN the system SHALL validate that the value is numeric and greater than zero
3. WHEN a user confirms the quantity change THEN the system SHALL update the CostItemMaterial record with the new quantity_per_unit value
4. WHEN the quantity is updated THEN the system SHALL recalculate the total cost column for that material
5. WHEN validation fails THEN the system SHALL display an error message and revert to the previous value

### Requirement 6

**User Story:** As a construction estimator, I want to change which cost item a material is associated with, so that I can reorganize work composition as needed.

#### Acceptance Criteria

1. WHEN a user clicks the cost item field in a material row THEN the system SHALL display a full-scale list form showing only cost items that are already added to the current work
2. WHEN a user selects a different cost item from the list THEN the system SHALL validate that the new cost_item_id is valid
3. WHEN the selection is confirmed THEN the system SHALL update the CostItemMaterial record with the new cost_item_id
4. WHEN the cost item is changed THEN the system SHALL maintain the same work_id, material_id, and quantity_per_unit values
5. WHEN the update is complete THEN the system SHALL refresh the materials table to reflect the change

### Requirement 7

**User Story:** As a construction estimator, I want to remove materials from a work type, so that I can correct mistakes or update material requirements.

#### Acceptance Criteria

1. WHEN a user clicks the delete button for a material THEN the system SHALL display a confirmation dialog
2. WHEN the user confirms deletion THEN the system SHALL delete the CostItemMaterial record where work_id, cost_item_id, and material_id match
3. WHEN deletion is complete THEN the system SHALL remove the material from the materials table
4. WHEN deletion is complete THEN the system SHALL recalculate the total work cost
5. WHEN the materials table is empty THEN the system SHALL display an appropriate empty state message

### Requirement 8

**User Story:** As a construction estimator, I want to see the total cost of a work type calculated from its composition, so that I can understand the complete cost structure.

#### Acceptance Criteria

1. WHEN cost items are added to a work THEN the system SHALL include their base prices in the total cost calculation
2. WHEN materials are added to a work THEN the system SHALL calculate material cost as price multiplied by quantity_per_unit
3. WHEN any composition changes occur THEN the system SHALL recalculate the total work cost automatically
4. WHEN the total cost is displayed THEN the system SHALL show the cost per unit of work with appropriate currency formatting
5. WHEN the work has no composition THEN the system SHALL display zero or the base work price

### Requirement 9

**User Story:** As a construction estimator, I want the cost items table to display read-only information from the cost items catalog, so that I can see relevant details without navigating away from the work form.

#### Acceptance Criteria

1. WHEN cost items are displayed in the table THEN the system SHALL show code, description, unit, price, and labor coefficient columns
2. WHEN cost item data is displayed THEN the system SHALL retrieve unit names by joining with the units table
3. WHEN a user attempts to edit cost item properties in the table THEN the system SHALL prevent inline editing of catalog fields
4. WHEN cost item information needs to be updated THEN the system SHALL require users to edit the cost items catalog directly
5. WHEN cost items are displayed THEN the system SHALL format numeric values with appropriate precision and units

### Requirement 10

**User Story:** As a construction estimator, I want the materials table to display read-only information from the materials catalog with editable quantities, so that I can adjust consumption rates while viewing material details.

#### Acceptance Criteria

1. WHEN materials are displayed in the table THEN the system SHALL show cost item, code, description, unit, price, quantity per unit, and total cost columns
2. WHEN material data is displayed THEN the system SHALL retrieve unit names by joining with the units table
3. WHEN a user attempts to edit material properties other than quantity THEN the system SHALL prevent inline editing of catalog fields
4. WHEN the quantity per unit field is displayed THEN the system SHALL allow inline editing with numeric validation
5. WHEN the total cost is calculated THEN the system SHALL multiply material price by quantity_per_unit and display with currency formatting

### Requirement 11

**User Story:** As a construction estimator, I want the work form to validate all data before saving, so that I can ensure data integrity and prevent invalid work compositions.

#### Acceptance Criteria

1. WHEN a user attempts to save a work without a name THEN the system SHALL display an error message and prevent saving
2. WHEN a user saves a work marked as a group with price or labor rate values THEN the system SHALL display a validation error
3. WHEN a user saves a work with materials that have zero or negative quantities THEN the system SHALL display a validation error
4. WHEN a user saves a work with materials not linked to cost items THEN the system SHALL display a validation error
5. WHEN all validation passes THEN the system SHALL save the work and all associated CostItemMaterial records

### Requirement 12

**User Story:** As a construction estimator, I want the work form to provide clear visual feedback during operations, so that I understand the system state and can work efficiently.

#### Acceptance Criteria

1. WHEN data is being loaded or saved THEN the system SHALL display a loading indicator
2. WHEN an error occurs THEN the system SHALL display a clear error message with actionable guidance
3. WHEN a table is empty THEN the system SHALL display an appropriate empty state message with instructions
4. WHEN a user hovers over action buttons THEN the system SHALL display tooltips explaining the action
5. WHEN validation fails THEN the system SHALL highlight the invalid fields with visual indicators

### Requirement 13

**User Story:** As a system administrator, I want the work composition data to be stored with proper referential integrity, so that data consistency is maintained across the system.

#### Acceptance Criteria

1. WHEN a CostItemMaterial record is created THEN the system SHALL validate that work_id references an existing work
2. WHEN a CostItemMaterial record is created THEN the system SHALL validate that cost_item_id references an existing cost item
3. WHEN a CostItemMaterial record is created with a material THEN the system SHALL validate that material_id references an existing material
4. WHEN a work is deleted THEN the system SHALL cascade delete all associated CostItemMaterial records
5. WHEN a cost item or material is deleted THEN the system SHALL cascade delete all associated CostItemMaterial records

### Requirement 14

**User Story:** As a construction estimator, I want to search and filter cost items and materials efficiently, so that I can quickly find the items I need to add to work composition.

#### Acceptance Criteria

1. WHEN the cost item list form opens THEN the system SHALL display search and filter controls at the top of the list
2. WHEN a user types in the search field THEN the system SHALL filter cost items by code or description in real-time
3. WHEN the material list form opens THEN the system SHALL display search and filter controls including unit filter
4. WHEN a user types in the material search field THEN the system SHALL filter materials by code or description in real-time
5. WHEN search results are displayed THEN the system SHALL highlight matching text in the results and show result count

### Requirement 15

**User Story:** As a construction estimator, I want the work form to support hierarchical work structures, so that I can organize works into logical groups and categories.

#### Acceptance Criteria

1. WHEN a user opens the parent work list form THEN the system SHALL display the hierarchical path for each work in the list
2. WHEN a work is marked as a group THEN the system SHALL allow it to be selected as a parent for other works
3. WHEN a work is marked as a group THEN the system SHALL prevent circular parent-child relationships
4. WHEN displaying the parent work list form THEN the system SHALL show the hierarchical structure with indentation and expand/collapse controls
5. WHEN a work has child works THEN the system SHALL display an indicator showing the number of children in the list

### Requirement 16

**User Story:** As a construction estimator, I want to quickly find reference items by typing code or name fragments, so that I can work efficiently without browsing through long lists.

#### Acceptance Criteria

1. WHEN a user types in a reference field (cost item, material, unit, parent work) THEN the system SHALL filter results by matching the substring against both code and name fields
2. WHEN substring matches are found THEN the system SHALL display matching results in real-time as the user types
3. WHEN a user presses Enter with filtered results THEN the system SHALL select the first matching item
4. WHEN a user types a substring that matches multiple items THEN the system SHALL show all matches with the matching text highlighted
5. WHEN a user clears the search field THEN the system SHALL display the full unfiltered list

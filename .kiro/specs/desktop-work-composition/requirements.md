# Requirements Document - Desktop Work Composition

## Introduction

This specification defines the requirements for implementing work composition functionality in the desktop application (Python/Qt). The desktop application currently has a basic Work form that only includes fundamental fields (name, code, unit, price, labor_rate, parent). This spec will extend the Work form to include full composition management with cost items and materials, bringing it to feature parity with the web client.

The work composition feature is critical for construction management as it establishes the foundation for accurate cost estimation, material planning, and labor scheduling by defining labor requirements (cost items) and material consumption rates (materials) at the work catalog level.

## Glossary

- **Work**: A type of construction activity (e.g., "Штукатурка стен" - Wall Plastering)
- **CostItem**: A cost element that contributes to work execution (e.g., "Труд рабочих" - Labor)
- **Material**: A physical material consumed during work execution (e.g., "Цемент" - Cement)
- **CostItemMaterial**: An association record in the database linking works to cost items and materials
- **Unit**: A measurement unit (e.g., м, м², м³, кг, т, шт)
- **Quantity per Unit**: The amount of material consumed per unit of work
- **Labor Coefficient**: The number of labor hours required per unit of work
- **Work Composition**: The complete set of cost items and materials that define how a work type is executed
- **Qt**: The GUI framework used for the desktop application (PyQt6)
- **QTableWidget**: Qt widget for displaying tabular data
- **QDialog**: Qt widget for modal dialogs

## Requirements

### Requirement 1: Extend Work Form with Composition Tabs

**User Story:** As a construction estimator using the desktop application, I want to see cost items and materials in the work form, so that I can manage work composition without switching to the web client.

#### Acceptance Criteria

1. WHEN a user opens the work form THEN the system SHALL display a tabbed interface with "Основные данные" (Basic Info), "Статьи затрат" (Cost Items), and "Материалы" (Materials) tabs
2. WHEN a user switches between tabs THEN the system SHALL preserve unsaved changes in all tabs
3. WHEN a user saves the work THEN the system SHALL save data from all tabs atomically
4. WHEN the work form loads THEN the system SHALL load basic info, cost items, and materials from the database
5. WHEN a user closes the form with unsaved changes THEN the system SHALL prompt to save changes

### Requirement 2: Cost Items Table Widget

**User Story:** As a construction estimator, I want to view and manage cost items in a table within the work form, so that I can see all labor and overhead components for the work.

#### Acceptance Criteria

1. WHEN the cost items tab is displayed THEN the system SHALL show a QTableWidget with columns: Код (Code), Наименование (Description), Ед.изм (Unit), Цена (Price), Норма труда (Labor Coefficient)
2. WHEN cost items are displayed THEN the system SHALL retrieve unit names by joining with the units table
3. WHEN a user double-clicks a cost item row THEN the system SHALL do nothing (read-only display)
4. WHEN cost items are displayed THEN the system SHALL format numeric values with appropriate precision
5. WHEN the table is empty THEN the system SHALL display a message "Нет статей затрат. Нажмите 'Добавить' для добавления."

### Requirement 3: Add Cost Item to Work

**User Story:** As a construction estimator, I want to add cost items to a work, so that I can define the labor and overhead components.

#### Acceptance Criteria

1. WHEN a user clicks the "Добавить статью затрат" button THEN the system SHALL open a cost item selector dialog
2. WHEN the cost item selector opens THEN the system SHALL display all cost items with search and hierarchical navigation
3. WHEN a user selects a cost item and confirms THEN the system SHALL add it to the cost items table
4. WHEN a cost item is added THEN the system SHALL mark the form as modified
5. WHEN a user attempts to add a duplicate cost item THEN the system SHALL display an error message and prevent the addition

### Requirement 4: Remove Cost Item from Work

**User Story:** As a construction estimator, I want to remove cost items from a work, so that I can correct mistakes or update work composition.

#### Acceptance Criteria

1. WHEN a user selects a cost item row and clicks "Удалить" THEN the system SHALL check if the cost item has associated materials
2. IF the cost item has associated materials THEN the system SHALL display a warning "Невозможно удалить статью затрат с привязанными материалами. Сначала удалите материалы." and prevent deletion
3. IF the cost item has no associated materials THEN the system SHALL display a confirmation dialog "Удалить статью затрат?"
4. WHEN the user confirms deletion THEN the system SHALL remove the cost item from the table
5. WHEN a cost item is removed THEN the system SHALL mark the form as modified

### Requirement 5: Materials Table Widget

**User Story:** As a construction estimator, I want to view and manage materials in a table within the work form, so that I can define material consumption rates.

#### Acceptance Criteria

1. WHEN the materials tab is displayed THEN the system SHALL show a QTableWidget with columns: Статья затрат (Cost Item), Код (Code), Наименование (Description), Ед.изм (Unit), Цена (Price), Количество (Quantity), Сумма (Total)
2. WHEN materials are displayed THEN the system SHALL retrieve unit names by joining with the units table
3. WHEN materials are displayed THEN the system SHALL calculate total cost as price × quantity for each material
4. WHEN a user double-clicks the quantity cell THEN the system SHALL make it editable
5. WHEN the table is empty THEN the system SHALL display a message "Нет материалов. Нажмите 'Добавить' для добавления."

### Requirement 6: Add Material to Work

**User Story:** As a construction estimator, I want to add materials to a work and link them to cost items, so that I can define material consumption rates.

#### Acceptance Criteria

1. WHEN a user clicks the "Добавить материал" button THEN the system SHALL open a multi-step material addition dialog
2. WHEN the material addition dialog opens THEN the system SHALL first display a cost item selector showing only cost items already added to the work
3. WHEN a user selects a cost item THEN the system SHALL display a material selector dialog
4. WHEN a user selects a material THEN the system SHALL display a quantity input dialog
5. WHEN a user enters a quantity and confirms THEN the system SHALL add the material to the materials table with the specified cost item and quantity

### Requirement 7: Edit Material Quantity

**User Story:** As a construction estimator, I want to edit material quantities, so that I can adjust consumption rates based on actual experience.

#### Acceptance Criteria

1. WHEN a user double-clicks a quantity cell THEN the system SHALL make the cell editable with a QDoubleSpinBox
2. WHEN a user enters a new quantity THEN the system SHALL validate that the value is greater than zero
3. WHEN a user confirms the quantity change THEN the system SHALL update the quantity and recalculate the total cost
4. WHEN validation fails THEN the system SHALL display an error message and revert to the previous value
5. WHEN a quantity is updated THEN the system SHALL mark the form as modified

### Requirement 8: Change Material Cost Item

**User Story:** As a construction estimator, I want to change which cost item a material is associated with, so that I can reorganize work composition.

#### Acceptance Criteria

1. WHEN a user double-clicks a cost item cell in the materials table THEN the system SHALL open a cost item selector showing only cost items added to the work
2. WHEN a user selects a different cost item THEN the system SHALL update the material's cost item association
3. WHEN the cost item is changed THEN the system SHALL maintain the same material and quantity
4. WHEN the cost item is changed THEN the system SHALL mark the form as modified
5. WHEN the update is complete THEN the system SHALL refresh the materials table

### Requirement 9: Remove Material from Work

**User Story:** As a construction estimator, I want to remove materials from a work, so that I can correct mistakes or update material requirements.

#### Acceptance Criteria

1. WHEN a user selects a material row and clicks "Удалить" THEN the system SHALL display a confirmation dialog "Удалить материал?"
2. WHEN the user confirms deletion THEN the system SHALL remove the material from the table
3. WHEN a material is removed THEN the system SHALL recalculate the total work cost
4. WHEN a material is removed THEN the system SHALL mark the form as modified
5. WHEN the materials table becomes empty THEN the system SHALL display the empty state message

### Requirement 10: Total Cost Display

**User Story:** As a construction estimator, I want to see the total cost calculated from work composition, so that I can understand the complete cost structure.

#### Acceptance Criteria

1. WHEN cost items are added THEN the system SHALL include their base prices in the total cost calculation
2. WHEN materials are added THEN the system SHALL calculate material cost as price × quantity
3. WHEN any composition changes occur THEN the system SHALL recalculate the total work cost automatically
4. WHEN the total cost is displayed THEN the system SHALL show it with currency formatting (e.g., "15,234.50 руб.")
5. WHEN the work has no composition THEN the system SHALL display the base work price or zero

### Requirement 11: Data Persistence

**User Story:** As a construction estimator, I want my work composition changes to be saved to the database, so that they persist across sessions.

#### Acceptance Criteria

1. WHEN a user saves the work THEN the system SHALL save basic work data to the works table
2. WHEN a user saves the work THEN the system SHALL save all cost item associations to the cost_item_materials table with material_id=NULL
3. WHEN a user saves the work THEN the system SHALL save all material associations to the cost_item_materials table with work_id, cost_item_id, material_id, and quantity_per_unit
4. WHEN saving fails THEN the system SHALL rollback all changes and display an error message
5. WHEN saving succeeds THEN the system SHALL mark the form as unmodified and display a success message

### Requirement 12: Validation

**User Story:** As a construction estimator, I want the system to validate my input, so that I can ensure data integrity.

#### Acceptance Criteria

1. WHEN a user attempts to save without a work name THEN the system SHALL display an error "Наименование обязательно для заполнения"
2. WHEN a user saves a group work with price or labor rate THEN the system SHALL display a validation error
3. WHEN a user saves with materials that have zero or negative quantities THEN the system SHALL display a validation error
4. WHEN a user attempts to add a duplicate cost item THEN the system SHALL prevent the addition and display an error
5. WHEN all validation passes THEN the system SHALL save the work and all associations

### Requirement 13: Cost Item Selector Dialog

**User Story:** As a construction estimator, I want an efficient way to select cost items, so that I can quickly find and add them to works.

#### Acceptance Criteria

1. WHEN the cost item selector opens THEN the system SHALL display a QDialog with a search field and hierarchical tree view
2. WHEN a user types in the search field THEN the system SHALL filter cost items by code or description in real-time
3. WHEN cost items are displayed THEN the system SHALL show the hierarchical structure with folders and items
4. WHEN a user double-clicks a cost item THEN the system SHALL select it and close the dialog
5. WHEN a user clicks OK THEN the system SHALL return the selected cost item

### Requirement 14: Material Selector Dialog

**User Story:** As a construction estimator, I want an efficient way to select materials, so that I can quickly find and add them to works.

#### Acceptance Criteria

1. WHEN the material selector opens THEN the system SHALL display a QDialog with a search field and table view
2. WHEN a user types in the search field THEN the system SHALL filter materials by code or description in real-time
3. WHEN materials are displayed THEN the system SHALL show code, description, unit, and price columns
4. WHEN a user double-clicks a material THEN the system SHALL select it and close the dialog
5. WHEN a user clicks OK THEN the system SHALL return the selected material

### Requirement 15: Repository Layer

**User Story:** As a developer, I want a repository layer for cost_item_materials, so that database operations are encapsulated and testable.

#### Acceptance Criteria

1. WHEN the repository is initialized THEN the system SHALL provide methods for CRUD operations on cost_item_materials
2. WHEN get_by_work_id is called THEN the system SHALL return all cost items and materials for the work with joined data
3. WHEN add_cost_item is called THEN the system SHALL insert a record with work_id, cost_item_id, and material_id=NULL
4. WHEN add_material is called THEN the system SHALL insert a record with work_id, cost_item_id, material_id, and quantity_per_unit
5. WHEN delete operations are called THEN the system SHALL remove the appropriate records from the database

### Requirement 16: Error Handling

**User Story:** As a construction estimator, I want clear error messages when something goes wrong, so that I can understand and fix issues.

#### Acceptance Criteria

1. WHEN a database error occurs THEN the system SHALL display a user-friendly error message with the error details
2. WHEN validation fails THEN the system SHALL highlight the invalid field and display the validation message
3. WHEN a network/database connection fails THEN the system SHALL display "Ошибка подключения к базе данных"
4. WHEN an unexpected error occurs THEN the system SHALL log the error and display "Произошла непредвиденная ошибка"
5. WHEN errors are displayed THEN the system SHALL use QMessageBox with appropriate icons (Warning, Critical, Information)

### Requirement 17: User Experience

**User Story:** As a construction estimator, I want a responsive and intuitive interface, so that I can work efficiently.

#### Acceptance Criteria

1. WHEN tables are loading THEN the system SHALL display a loading indicator or disable the table
2. WHEN operations are in progress THEN the system SHALL disable action buttons to prevent double-clicks
3. WHEN tables are displayed THEN the system SHALL auto-resize columns to fit content
4. WHEN a user hovers over buttons THEN the system SHALL display tooltips explaining the action
5. WHEN keyboard shortcuts are used (Ctrl+S for save) THEN the system SHALL perform the corresponding action


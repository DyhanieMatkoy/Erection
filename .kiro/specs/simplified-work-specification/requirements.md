# Requirements Document - Simplified Work Specification

## Introduction

This specification defines requirements for simplifying the work composition functionality by eliminating unnecessary reference entities and focusing on direct specification entry. The current system forces users to select pre-existing cost items from a catalog, which doesn't match real-world use cases where adding materials and labor components should be direct specification entries.

The simplified approach treats work specification as a tabular composition where each row represents a component (material, labor, or equipment) with its consumption rate per unit of work. This eliminates the artificial separation between "cost items" and "materials" and removes the need for pre-existing catalog entries.

## Glossary

- **Work**: A type of construction activity (e.g., "Штукатурка стен" - Wall Plastering)
- **WorkSpecification**: A specification entry that defines a component required for work execution
- **ComponentType**: The type of specification component (Material, Labor, Equipment, Other)
- **Unit**: A measurement unit (e.g., м, м², м³, кг, т, шт, чел-час)
- **ConsumptionRate**: The quantity of component consumed per unit of work
- **WorkComposition**: The complete set of specification entries that define work execution requirements

## Requirements

### Requirement 1

**User Story:** As a construction estimator, I want to add specification entries directly to a work, so that I can define material and labor requirements without selecting from pre-existing catalogs.

#### Acceptance Criteria

1. WHEN a user clicks "Add Specification Entry" THEN the system SHALL display a form to enter component details directly
2. WHEN entering a specification entry THEN the system SHALL require component name, type, unit, consumption rate, and unit price
3. WHEN a user selects component type THEN the system SHALL provide options: Material, Labor, Equipment, Other
4. WHEN adding a Material component THEN the system SHALL allow selecting a material from the catalog
5. WHEN a material is selected from catalog THEN the system SHALL populate name, unit, and price fields automatically
6. WHEN a user enters component data THEN the system SHALL validate that consumption rate and unit price are positive numbers
7. WHEN a user saves a specification entry THEN the system SHALL add it to the work specification table

### Requirement 2

**User Story:** As a construction estimator, I want to edit specification entries inline, so that I can quickly adjust consumption rates and prices.

#### Acceptance Criteria

1. WHEN a user double-clicks any editable cell THEN the system SHALL make the cell editable
2. WHEN a user edits consumption rate or unit price THEN the system SHALL validate that values are positive numbers
3. WHEN a user changes consumption rate or unit price THEN the system SHALL recalculate the total cost automatically
4. WHEN a user edits component name or type THEN the system SHALL update the specification entry
5. WHEN validation fails THEN the system SHALL display an error message and revert to the previous value

### Requirement 3

**User Story:** As a construction estimator, I want to remove specification entries, so that I can correct mistakes or update work requirements.

#### Acceptance Criteria

1. WHEN a user selects a specification entry and clicks delete THEN the system SHALL display a confirmation dialog
2. WHEN the user confirms deletion THEN the system SHALL remove the entry from the specification table
3. WHEN an entry is removed THEN the system SHALL recalculate the total work cost
4. WHEN the specification table becomes empty THEN the system SHALL display an appropriate empty state message
5. WHEN deletion is complete THEN the system SHALL mark the work as modified

### Requirement 4

**User Story:** As a construction estimator, I want to see the total cost calculated from all specification entries, so that I can understand the complete cost structure.

#### Acceptance Criteria

1. WHEN specification entries are added or modified THEN the system SHALL calculate total cost as sum of (consumption_rate × unit_price) for all entries
2. WHEN the total cost changes THEN the system SHALL update the display automatically
3. WHEN the work has no specification entries THEN the system SHALL display zero total cost
4. WHEN displaying costs THEN the system SHALL format currency values with appropriate precision
5. WHEN cost calculation occurs THEN the system SHALL group totals by component type (Materials, Labor, Equipment, Other)

### Requirement 5

**User Story:** As a construction estimator, I want to copy specification entries from similar works, so that I can quickly create new work compositions based on existing templates.

#### Acceptance Criteria

1. WHEN a user clicks "Copy from Work" THEN the system SHALL display a work selector dialog
2. WHEN a user selects a source work THEN the system SHALL display its specification entries for review
3. WHEN a user confirms copying THEN the system SHALL add all specification entries from the source work to the current work
4. WHEN entries are copied THEN the system SHALL allow the user to modify them before saving
5. WHEN copying is complete THEN the system SHALL recalculate the total cost and mark the work as modified

### Requirement 6

**User Story:** As a construction estimator, I want to export work specifications to Excel, so that I can share detailed breakdowns with stakeholders.

#### Acceptance Criteria

1. WHEN a user clicks "Export to Excel" THEN the system SHALL generate an Excel file with work specification details
2. WHEN exporting THEN the system SHALL include columns: Component Type, Name, Unit, Consumption Rate, Unit Price, Total Cost
3. WHEN exporting THEN the system SHALL include summary rows with totals by component type
4. WHEN exporting THEN the system SHALL include work header information (code, name, unit, total cost)
5. WHEN export is complete THEN the system SHALL prompt the user to save or open the Excel file

### Requirement 7

**User Story:** As a construction estimator, I want to import specification entries from Excel templates, so that I can quickly populate work compositions from external sources.

#### Acceptance Criteria

1. WHEN a user clicks "Import from Excel" THEN the system SHALL display a file selection dialog
2. WHEN a user selects an Excel file THEN the system SHALL validate the file format and required columns
3. WHEN the file is valid THEN the system SHALL display a preview of entries to be imported
4. WHEN a user confirms import THEN the system SHALL add all valid entries to the work specification
5. WHEN import encounters errors THEN the system SHALL display validation messages and allow correction

### Requirement 8

**User Story:** As a construction estimator, I want to search and filter specification entries, so that I can quickly find specific components in large specifications.

#### Acceptance Criteria

1. WHEN the specification table is displayed THEN the system SHALL provide search and filter controls
2. WHEN a user types in the search field THEN the system SHALL filter entries by component name in real-time
3. WHEN a user selects a component type filter THEN the system SHALL show only entries of that type
4. WHEN filters are applied THEN the system SHALL update the total cost calculation to reflect filtered entries
5. WHEN filters are cleared THEN the system SHALL restore the full specification view

### Requirement 9

**User Story:** As a construction estimator, I want to validate specification completeness, so that I can ensure all necessary components are included.

#### Acceptance Criteria

1. WHEN a user saves a work THEN the system SHALL validate that at least one specification entry exists
2. WHEN validating THEN the system SHALL check that all entries have positive consumption rates and unit prices
3. WHEN validating THEN the system SHALL warn if no labor components are defined for non-group works
4. WHEN validation fails THEN the system SHALL display specific error messages and prevent saving
5. WHEN validation passes THEN the system SHALL save the work and all specification entries

### Requirement 10

**User Story:** As a construction estimator, I want to use common units and component types consistently, so that specifications are standardized across the system.

#### Acceptance Criteria

1. WHEN entering a unit THEN the system SHALL provide autocomplete suggestions from existing units in the system
2. WHEN selecting component type THEN the system SHALL provide a dropdown with standard types: Material, Labor, Equipment, Other
3. WHEN entering component names THEN the system SHALL provide autocomplete suggestions from previously used names
4. WHEN a new unit is entered THEN the system SHALL add it to the units reference for future use
5. WHEN displaying specifications THEN the system SHALL use consistent formatting for units and component types

### Requirement 11

**User Story:** As a system administrator, I want specification data to be stored efficiently, so that database performance is maintained as the system grows.

#### Acceptance Criteria

1. WHEN a specification entry is created THEN the system SHALL store it in a single work_specifications table
2. WHEN storing entries THEN the system SHALL include work_id, component_type, component_name, unit, consumption_rate, unit_price, and total_cost
3. WHEN a work is deleted THEN the system SHALL cascade delete all associated specification entries
4. WHEN querying specifications THEN the system SHALL use appropriate indexes for performance
5. WHEN the database grows THEN the system SHALL maintain query performance through proper indexing

### Requirement 12

**User Story:** As a construction estimator, I want to track specification changes over time, so that I can understand how work compositions evolve.

#### Acceptance Criteria

1. WHEN a specification entry is modified THEN the system SHALL update the modified_at timestamp
2. WHEN displaying specifications THEN the system SHALL show when each entry was last modified
3. WHEN a work specification is significantly changed THEN the system SHALL optionally create a version snapshot
4. WHEN viewing specification history THEN the system SHALL show what changes were made and when
5. WHEN reverting changes THEN the system SHALL allow restoration from previous versions

### Requirement 13

**User Story:** As a construction estimator, I want to use templates for common work types, so that I can quickly create specifications for standard construction activities.

#### Acceptance Criteria

1. WHEN creating a new work THEN the system SHALL offer to apply a template based on work type or category
2. WHEN a template is selected THEN the system SHALL populate the specification with standard entries
3. WHEN using templates THEN the system SHALL allow modification of template entries before saving
4. WHEN saving a work with good specifications THEN the system SHALL offer to save it as a new template
5. WHEN managing templates THEN the system SHALL allow administrators to create, modify, and delete standard templates

### Requirement 14

**User Story:** As a construction estimator, I want to see specification totals grouped by component type, so that I can understand the cost breakdown structure.

#### Acceptance Criteria

1. WHEN displaying specifications THEN the system SHALL show subtotals for Materials, Labor, Equipment, and Other components
2. WHEN calculating subtotals THEN the system SHALL sum (consumption_rate × unit_price) for each component type
3. WHEN the specification changes THEN the system SHALL update all subtotals automatically
4. WHEN displaying subtotals THEN the system SHALL use clear visual separation and formatting
5. WHEN exporting or printing THEN the system SHALL include the grouped totals in the output

### Requirement 15

**User Story:** As a construction estimator, I want to validate unit consistency, so that I can ensure consumption rates make sense for the work unit.

#### Acceptance Criteria

1. WHEN entering consumption rates THEN the system SHALL validate that units are compatible with the work unit
2. WHEN work unit is area-based (м²) THEN the system SHALL warn if material units don't make sense for area calculations
3. WHEN work unit is volume-based (м³) THEN the system SHALL warn if consumption rates seem inconsistent with volume work
4. WHEN validation detects potential issues THEN the system SHALL display warnings but allow the user to proceed
5. WHEN unit validation is performed THEN the system SHALL provide suggestions for appropriate units

### Requirement 16

**User Story:** As a construction estimator, I want to quickly duplicate specification entries, so that I can create variations of similar components efficiently.

#### Acceptance Criteria

1. WHEN a user right-clicks a specification entry THEN the system SHALL display a context menu with "Duplicate" option
2. WHEN a user selects duplicate THEN the system SHALL create a copy of the entry with "_copy" appended to the name
3. WHEN an entry is duplicated THEN the system SHALL allow immediate editing of the duplicated entry
4. WHEN duplicating THEN the system SHALL maintain all original values (type, unit, consumption rate, unit price)
5. WHEN duplication is complete THEN the system SHALL recalculate totals and mark the work as modified

# Implementation Plan - Simplified Work Specification

## Desktop Application Changes

- [ ] 1. Create new database schema and migration
  - Create work_specifications table with proper indexes
  - Create migration script from cost_item_materials to work_specifications
  - Add feature flag for switching between old and new systems
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 2. Implement WorkSpecification repository layer
  - Create WorkSpecificationRepository class with CRUD operations
  - Implement get_by_work_id, create, update, delete methods
  - Add methods for bulk operations (copy_from_work, import_from_excel)
  - _Requirements: 11.1, 5.2, 7.4_

- [ ] 3. Create WorkSpecificationWidget for desktop UI
  - Design QTableWidget with columns: Type, Name, Unit, Rate, Price, Total
  - Implement inline editing for consumption_rate and unit_price
  - Add context menu with duplicate, delete, copy options
  - _Requirements: 2.1, 2.2, 16.1_

- [ ] 4. Implement SpecificationEntryDialog
  - Create dialog for adding new specification entries
  - Add component type dropdown (Material, Labor, Equipment, Other)
26→  - Implement unit autocomplete and validation
27→  - Add "Select from Catalog" button for Material type
28→  - Integrate MaterialSelectorDialog to populate fields
29→  - _Requirements: 1.1, 1.2, 1.4, 1.5, 10.1_
30→
31→- [ ] 5. Update WorkForm to use new specification system
  - Replace cost_items_table and materials_table with WorkSpecificationWidget
  - Update save/load logic to handle work_specifications
  - Add total cost calculation and display by component type
  - _Requirements: 4.1, 14.1, 14.2_

- [ ] 6. Implement Excel import/export functionality
  - Create SpecificationImportDialog for Excel file selection and preview
  - Create SpecificationExportDialog for Excel generation
  - Add validation and error handling for import operations
  - _Requirements: 6.1, 7.1, 7.2_

- [ ] 7. Add specification templates functionality
  - Create template management dialog
  - Implement copy_from_work functionality
  - Add template application during work creation
  - _Requirements: 13.1, 13.2, 5.1_

## Web Client Changes

### Critical Implementation Notes (Lessons from Desktop)
> **Attention Web Developer:** The following points are crucial based on the Desktop implementation experience.

1.  **Material Linking (FK)**:
    - When adding a material to a specification, you **MUST** save the `material_id` in the `work_specifications` table.
    - Do not just copy the name and price. The link is required for future price updates from the material catalog.
    - **Schema**: `work_specifications.material_id` (ForeignKey to `materials.id`).

2.  **Unit Handling**:
    - The `work_specifications` table stores `unit_id`.
    - The API/Repository MUST return the resolved `unit_name` (joined from the `units` table).
    - **Do not** display raw `unit_id` to the user.
    - **Do not** rely on a `unit_name` column in `work_specifications` (it doesn't exist/is deprecated).

3.  **Computed Columns (`total_cost`)**:
    - `total_cost` is a database-side **COMPUTED** column (`consumption_rate * unit_price`).
    - The Web Client API **MUST NOT** attempt to insert or update this field. It is read-only.
    - Attempting to write to it will cause SQL errors.

4.  **DBF/External ID Compatibility**:
    - If the Web Client handles any import logic, use **deterministic hashing (CRC32)** for non-integer IDs from external systems (e.g., "A123" -> CRC32 int).
    - Do not use Python's default `hash()` as it is randomized per session.

5.  **Search Logic**:
    - Work search filters must apply to **BOTH** `name` and `code` fields (OR condition).
    - Example: Searching for "1.01-00006" must find the work with that code.

- [ ] 8. Create new API models and endpoints
  - Implement WorkSpecification Pydantic models
  - Create /api/works/{id}/specifications endpoints (GET, POST, PUT, DELETE)
  - Add copy-from and import/export endpoints
  - _Requirements: 1.1, 5.2, 6.1, 7.1_

- [ ] 9. Implement WorkSpecificationPanel Vue component
  - Create main specification management interface
  - Add specification table with inline editing
  - Implement add/edit/delete functionality
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 10. Create SpecificationEntryForm component
  - Build form for adding/editing specification entries
  - Add component type selector and unit autocomplete
  - Implement validation and error display
  - _Requirements: 1.2, 1.3, 10.1_

- [ ] 11. Implement useWorkSpecification composable
  - Create reactive specification management logic
  - Add total cost calculation by component type
  - Implement validation rules and error handling
  - _Requirements: 4.1, 14.1, 9.2_

- [ ] 12. Add specification import/export functionality
  - Create file upload component for Excel import
  - Implement Excel export with proper formatting
  - Add progress indicators and error handling
  - _Requirements: 6.1, 7.1, 7.5_

- [ ] 13. Update WorkForm to integrate new specification system
  - Replace existing cost items and materials sections
  - Add specification panel with totals by component type
  - Update work saving logic to handle specifications
  - _Requirements: 4.1, 14.1, 9.1_

## DBF Importer Changes

- [ ] 14. Update DBF import mapping for work specifications
  - Map DBF work composition data to work_specifications format
  - Implement component type detection from DBF data
  - Add unit mapping and validation during import
  - _Requirements: 11.1, 10.4_

- [ ] 15. Create specification import validation
  - Validate consumption rates and unit prices during import
  - Check component type consistency
  - Handle missing or invalid data gracefully
  - _Requirements: 7.5, 9.2_

- [ ] 16. Add DBF export functionality for specifications
  - Export work_specifications back to DBF format if needed
  - Maintain compatibility with external systems
  - Add proper error handling and logging
  - _Requirements: 6.1_

## Database Migration and Compatibility

- [ ] 17. Implement backward compatibility layer
  - Create views that map work_specifications back to cost_item_materials format
  - Ensure existing reports and queries continue to work
  - Add feature flag to switch between old and new systems
  - _Requirements: 11.2_

- [ ] 18. Create data migration scripts
  - Migrate existing cost_item_materials data to work_specifications
  - Handle edge cases and data inconsistencies
  - Create rollback procedures if needed
  - _Requirements: 11.2_

- [ ] 19. Update database indexes and performance
  - Add appropriate indexes for work_specifications queries
  - Optimize total cost calculation queries
  - Test performance with large datasets
  - _Requirements: 11.4_

## Testing and Validation

- [ ] 20. Write unit tests for specification functionality
  - Test WorkSpecificationRepository CRUD operations
  - Test validation rules and error handling
  - Test total cost calculations and component type grouping
  - _Requirements: 1.4, 4.1, 9.2_

- [ ]* 21. Write property-based tests for correctness properties
  - **Property 1: Specification Entry Validation**
  - **Property 2: Work Specification Completeness**  
  - **Property 3: Total Cost Calculation Consistency**
  - **Property 4: Component Type Consistency**
  - **Property 5: Unit Reference Integrity**
  - **Validates: Requirements 1.4, 2.2, 4.1, 9.1, 9.2**

- [ ]* 22. Write integration tests for full workflow
  - Test desktop application specification management
  - Test web client specification functionality
  - Test API endpoints with various data scenarios
  - _Requirements: 1.1, 2.1, 4.1_

- [ ] 23. Test migration and compatibility
  - Test data migration from cost_item_materials to work_specifications
  - Verify backward compatibility with existing functionality
  - Test feature flag switching between old and new systems
  - _Requirements: 11.2_

## Documentation and Deployment

- [ ] 24. Update user documentation
  - Create user guide for new specification functionality
  - Document migration process and compatibility considerations
  - Add troubleshooting guide for common issues
  - _Requirements: 13.1_

- [ ] 25. Create deployment plan
  - Plan phased rollout with feature flags
  - Create rollback procedures
  - Document database migration steps
  - _Requirements: 11.2_

- [ ] 26. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
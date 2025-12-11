# Implementation Plan

This implementation plan provides a series of discrete, incremental coding tasks to build the Work Composition Form feature. Each task builds on previous tasks and references specific requirements from the requirements document.

## Task Overview

The implementation follows this sequence:
1. Backend database and API foundation
2. Frontend components and state management
3. Integration and testing
4. Polish and optimization

---

- [x] 1. Set up backend database schema and models





  - Verify `cost_item_materials` table has `work_id` column (added in migration 20251209_100000)
  - Update SQLAlchemy models for Work and CostItemMaterial with proper relationships
  - Add indexes for performance (work_id, cost_item_id, material_id)
  - Verify UNIQUE constraint on (work_id, cost_item_id, material_id)
  - Verify CASCADE DELETE on foreign keys
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 1.1 Write property test for referential integrity
  - **Property 35: Work referential integrity**
  - **Validates: Requirements 13.1**

- [ ]* 1.2 Write property test for cascade deletion
  - **Property 38: Work deletion cascades to associations**
  - **Validates: Requirements 13.4**

- [x] 2. Implement backend API endpoints for work composition





  - Create GET /api/works/{id}/composition endpoint
  - Create POST /api/works/{id}/cost-items endpoint
  - Create DELETE /api/works/{id}/cost-items/{cost_item_id} endpoint
  - Create POST /api/works/{id}/materials endpoint
  - Create PUT /api/works/{id}/materials/{id} endpoint
  - Create DELETE /api/works/{id}/materials/{id} endpoint
  - Add validation logic for all endpoints
  - _Requirements: 2.3, 3.4, 4.5, 5.3, 6.3, 7.2_

- [ ]* 2.1 Write property test for cost item association creation
  - **Property 6: Cost item association creation**
  - **Validates: Requirements 2.3**

- [ ]* 2.2 Write property test for material association creation
  - **Property 15: Material association creation**
  - **Validates: Requirements 4.5**

- [ ]* 2.3 Write property test for material quantity update
  - **Property 16: Material quantity update**
  - **Validates: Requirements 5.3**


- [x] 3. Implement list form API endpoints with pagination and filtering




  - Update GET /api/cost-items with pagination (?page, ?limit)
  - Add search parameter (?search) for cost items
  - Add hierarchical filter (?parent_id, ?is_folder) for cost items
  - Update GET /api/materials with pagination
  - Add search parameter (?search) for materials
  - Add unit filter (?unit_id) for materials
  - Ensure all endpoints return total count for pagination
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ]* 3.1 Write property test for cost item search filtering
  - **Property 5: Cost item search filtering**
  - **Validates: Requirements 2.2, 14.2**

- [ ]* 3.2 Write property test for material search filtering
  - **Property 13: Material search filtering**
  - **Validates: Requirements 4.3, 14.4**

- [ ]* 3.3 Write property test for substring filtering
  - **Property 44: Substring filtering by code or name**
  - **Validates: Requirements 16.1, 16.2**

- [x] 4. Implement backend validation logic





  - Add work name validation (not empty, not whitespace-only)
  - Add group work validation (cannot have price or labor_rate)
  - Add quantity validation (must be > 0, must be numeric)
  - Add duplicate cost item prevention
  - Add duplicate material prevention
  - Add cost item deletion check (prevent if has materials)
  - Add circular reference prevention for parent_id
  - _Requirements: 1.2, 1.3, 2.5, 4.4, 5.2, 11.1, 11.2, 11.3, 15.3_

- [ ]* 4.1 Write property test for work name validation
  - **Property 1: Work name validation**
  - **Validates: Requirements 1.2, 11.1**

- [ ]* 4.2 Write property test for group work validation
  - **Property 3: Group works cannot have price or labor rate**
  - **Validates: Requirements 1.3, 11.2**

- [ ]* 4.3 Write property test for quantity validation
  - **Property 14: Material quantity validation**
  - **Validates: Requirements 4.4, 5.2, 11.3**

- [ ]* 4.4 Write property test for duplicate prevention
  - **Property 8: Duplicate cost item prevention**
  - **Validates: Requirements 2.5**

- [ ]* 4.5 Write property test for circular reference prevention
  - **Property 4: Parent work circular reference prevention**
  - **Validates: Requirements 1.4, 15.3**


- [x] 5. Create frontend composable for work composition state management




  - Create `composables/useWorkComposition.ts`
  - Implement reactive state for work, costItems, materials
  - Implement computed property for totalCost
  - Implement loadWork() action
  - Implement saveWork() action
  - Implement addCostItem() action
  - Implement removeCostItem() action
  - Implement addMaterial() action
  - Implement updateMaterialQuantity() action
  - Implement changeMaterialCostItem() action
  - Implement removeMaterial() action
  - _Requirements: 1.5, 2.3, 3.4, 4.5, 5.3, 6.3, 7.2_

- [ ]* 5.1 Write property test for work persistence round trip
  - **Property 2: Work persistence round trip**
  - **Validates: Requirements 1.5**

- [ ]* 5.2 Write property test for total cost calculation
  - **Property 24: Total cost includes cost items**
  - **Property 25: Total cost includes materials**
  - **Validates: Requirements 8.1, 8.2**

- [x] 6. Create reusable list form components





  - Create `components/common/ListForm.vue` (base component)
  - Add search input with real-time filtering
  - Add pagination controls
  - Add table/list display
  - Add selection state management
  - Add OK/Cancel actions
  - Create `components/common/CostItemListForm.vue` (extends ListForm)
  - Create `components/common/MaterialListForm.vue` (extends ListForm)
  - Create `components/common/UnitListForm.vue` (extends ListForm)
  - Create `components/common/WorkListForm.vue` (extends ListForm with hierarchy)
  - _Requirements: 2.1, 4.1, 14.1, 14.3_

- [ ]* 6.1 Write unit tests for ListForm component
  - Test search filtering
  - Test pagination
  - Test selection
  - Test OK/Cancel actions


- [x] 7. Implement substring entry feature for reference fields




  - Add substring matching logic (search code OR name)
  - Implement real-time filtering as user types
  - Add Enter key handler to select first match
  - Add text highlighting for matches
  - Implement clear search to show full list
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ]* 7.1 Write property test for substring filtering
  - **Property 44: Substring filtering by code or name**
  - **Validates: Requirements 16.1, 16.2**

- [ ]* 7.2 Write property test for Enter key selection
  - **Property 45: Enter key selects first match**
  - **Validates: Requirements 16.3**

- [ ]* 7.3 Write property test for clear search
  - **Property 47: Clear search shows full list**
  - **Validates: Requirements 16.5**

- [x] 8. Create WorkBasicInfo component





  - Create `components/work/WorkBasicInfo.vue`
  - Add text inputs for code and name
  - Add UnitListForm for unit selection
  - Add number inputs for price and labor_rate
  - Add checkbox for is_group
  - Add WorkListForm for parent selection
  - Implement field validation
  - Implement conditional field disabling (groups can't have price/labor_rate)
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 8.1 Write unit tests for WorkBasicInfo component
  - Test field rendering
  - Test validation
  - Test conditional disabling


- [x] 9. Create CostItemsTable component




  - Create `components/work/CostItemsTable.vue`
  - Add table with columns: code, description, unit, price, labor coefficient, actions
  - Add "Add Cost Item" button
  - Implement CostItemListForm integration
  - Add delete button with confirmation
  - Implement delete validation (check for materials)
  - Display unit names via join with units table
  - Format numeric values appropriately
  - _Requirements: 2.1, 2.4, 3.1, 3.2, 3.3, 9.1, 9.2, 9.3, 9.5_

- [ ]* 9.1 Write property test for cost item display
  - **Property 7: Cost item display completeness**
  - **Validates: Requirements 2.4, 9.1**

- [ ]* 9.2 Write property test for cost item deletion check
  - **Property 9: Cost item deletion with materials check**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 9.3 Write property test for unit name retrieval
  - **Property 28: Unit name retrieval via join**
  - **Validates: Requirements 9.2**


- [x] 10. Create MaterialsTable component




  - Create `components/work/MaterialsTable.vue`
  - Add table with columns: cost item, code, description, unit, price, quantity, total, actions
  - Add "Add Material" button
  - Implement multi-step material addition dialog
  - Add inline quantity editing
  - Add cost item reassignment via list form
  - Add delete button with confirmation
  - Calculate and display total cost per material
  - Display unit names via join with units table
  - Format numeric values and currency
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 7.1, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 10.1 Write property test for material total cost calculation
  - **Property 17: Material total cost calculation**
  - **Validates: Requirements 5.4, 8.2, 10.5**

- [ ]* 10.2 Write property test for quantity validation revert
  - **Property 18: Material quantity validation revert**
  - **Validates: Requirements 5.5**

- [ ]* 10.3 Write property test for cost item change preserves fields
  - **Property 19: Material cost item change preserves other fields**
  - **Validates: Requirements 6.3, 6.4**

- [x] 11. Create main WorkForm component





  - Create `components/work/WorkForm.vue`
  - Integrate WorkBasicInfo component
  - Integrate CostItemsTable component
  - Integrate MaterialsTable component
  - Add total cost display
  - Add Save and Cancel buttons
  - Implement form-level validation
  - Implement loading states
  - Implement error handling and display
  - _Requirements: 8.3, 8.4, 11.5, 12.1, 12.2_

- [ ]* 11.1 Write property test for total cost recalculation
  - **Property 26: Total cost automatic recalculation**
  - **Validates: Requirements 8.3**

- [ ]* 11.2 Write property test for successful save
  - **Property 34: Successful save persists all associations**
  - **Validates: Requirements 11.5**

- [x] 12. Implement hierarchical work structure support





  - Add hierarchical path display in WorkBasicInfo
  - Implement expand/collapse in WorkListForm
  - Add child count indicator
  - Implement circular reference prevention in parent selection
  - Filter parent options to show only groups
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ]* 12.1 Write property test for groups as parents
  - **Property 42: Groups can be parents**
  - **Validates: Requirements 15.2**

- [ ]* 12.2 Write property test for child count display
  - **Property 43: Child count display**
  - **Validates: Requirements 15.5**


- [x] 13. Add comprehensive error handling and user feedback



  - Implement validation error messages
  - Add loading indicators for async operations
  - Add empty state messages for tables
  - Add tooltips for action buttons
  - Add visual indicators for invalid fields
  - Implement toast notifications for success/error
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 13.1 Write unit tests for error handling
  - Test validation error display
  - Test loading states
  - Test empty states
  - Test tooltips

- [x] 14. Create API client functions





  - Create `api/work-composition.ts`
  - Implement getWorkComposition()
  - Implement addCostItemToWork()
  - Implement removeCostItemFromWork()
  - Implement addMaterialToWork()
  - Implement updateMaterialQuantity()
  - Implement changeMaterialCostItem()
  - Implement removeMaterialFromWork()
  - Add error handling and response parsing
  - _Requirements: All API-related requirements_

- [ ]* 14.1 Write unit tests for API client
  - Test all API functions
  - Test error handling
  - Mock HTTP responses

- [x] 15. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Create integration view for testing





  - Create `views/WorkCompositionView.vue`
  - Add route configuration
  - Integrate WorkForm component
  - Add navigation controls
  - Test complete workflow
  - _Requirements: All requirements_

- [ ]* 16.1 Write E2E tests for complete workflows
  - Test creating work with composition
  - Test editing work composition
  - Test deleting cost items and materials
  - Test validation scenarios
  - Test error scenarios


- [x] 17. Optimize performance




  - Add debouncing to search inputs
  - Implement virtual scrolling for large lists
  - Add caching for frequently accessed data
  - Optimize re-renders with proper memoization
  - Add loading skeletons for better UX
  - _Requirements: Performance-related aspects_

- [ ]* 17.1 Write performance tests
  - Test with large datasets (1000+ items)
  - Measure search response time
  - Measure render time


- [x] 18. Final Checkpoint - Ensure all tests pass




  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional testing tasks
- Each task references specific requirements from requirements.md
- Property-based tests should run 100+ iterations
- All tests should pass before moving to the next major section
- Integration tests should cover complete user workflows
- Performance optimization should be done after core functionality is complete


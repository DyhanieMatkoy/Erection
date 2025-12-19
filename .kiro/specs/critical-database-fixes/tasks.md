# Implementation Plan

- [ ] 1. Update SQLAlchemy Estimate model to include synchronization fields
  - Add uuid field with automatic generation using lambda: str(uuid.uuid4())
  - Add updated_at field with automatic timestamps using func.now()
  - Add is_deleted field with default False
  - Ensure all fields match the database schema from migration 20251217_000001
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1_

- [ ]* 1.1 Write property test for UUID generation
  - **Property 1: UUID generation for new estimates**
  - **Validates: Requirements 1.1**

- [ ]* 1.2 Write property test for UUID preservation
  - **Property 2: UUID preservation during updates**
  - **Validates: Requirements 1.2**

- [ ]* 1.3 Write property test for required field population
  - **Property 3: Required field population**
  - **Validates: Requirements 1.3**

- [ ]* 1.4 Write property test for automatic timestamps
  - **Property 4: Automatic timestamp updates**
  - **Validates: Requirements 1.4**

- [ ] 2. Verify and update other synchronized models
  - Check all models listed in migration 20251217_000001 (daily_reports, daily_report_lines, estimate_lines, timesheets, timesheet_lines, works, materials, cost_items, units, persons, organizations, counterparties, objects)
  - Ensure each model includes uuid, updated_at, and is_deleted fields
  - Verify field definitions match database schema
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 2.1 Write property test for automatic field handling
  - **Property 10: Automatic field handling**
  - **Validates: Requirements 3.2**

- [ ]* 2.2 Write property test for synchronization field management
  - **Property 11: Synchronization field management**
  - **Validates: Requirements 3.3**

- [ ]* 2.3 Write property test for automatic UUID generation
  - **Property 12: Automatic UUID generation**
  - **Validates: Requirements 3.4**

- [ ] 3. Investigate and fix work list filtering issue
  - Examine WorkListFormV2 and GenericListForm for hidden filters
  - Check DataService.get_documents() for test data filters
  - Verify ListFormController filter application logic
  - Identify why only test records are showing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Remove or fix problematic filters in work list
  - Remove any hardcoded test data filters
  - Ensure parent_id filter works correctly for hierarchical display
  - Verify search functionality operates on full dataset
  - Ensure both individual works and groups are displayed
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 4.1 Write property test for complete work list display
  - **Property 5: Complete work list display**
  - **Validates: Requirements 2.1**

- [ ]* 4.2 Write property test for no hidden filters
  - **Property 6: No hidden test filters**
  - **Validates: Requirements 2.2**

- [ ]* 4.3 Write property test for complete search coverage
  - **Property 7: Complete search coverage**
  - **Validates: Requirements 2.3**

- [ ]* 4.4 Write property test for work type display
  - **Property 8: Work type display completeness**
  - **Validates: Requirements 2.4**

- [ ]* 4.5 Write property test for filter transparency
  - **Property 9: Filter transparency**
  - **Validates: Requirements 2.5**

- [ ] 5. Test estimate creation and updates
  - Create new estimates and verify UUID generation
  - Update existing estimates and verify UUID preservation
  - Test with various estimate types (General, Plan)
  - Verify all synchronization fields are populated correctly
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 6. Test work list functionality
  - Open work list and verify all works are displayed
  - Test hierarchical navigation (groups and items)
  - Test search functionality across all works
  - Verify no test data filters are applied
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
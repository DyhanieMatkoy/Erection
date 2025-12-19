# Implementation Plan - Estimate Hierarchy System

## Overview
This implementation plan creates a hierarchical estimate system with General Estimates (master documents) and Plan Estimates (brigade execution plans). The current codebase has basic estimate functionality but lacks hierarchy support.

## Tasks

- [x] 1. Database Schema Implementation





  - Create Alembic migration to add hierarchy fields to estimates table
  - Add base_document_id column as foreign key to estimates.id
  - Add estimate_type column with 'General'/'Plan' values and default 'General'
  - Create indexes on base_document_id and estimate_type for performance
  - Add check constraint to ensure estimate_type is 'General' or 'Plan'
  - Set existing estimates to 'General' type with NULL base_document_id
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 1.1 Write property test for database schema constraints
  - **Property 1: Estimate Classification Consistency**
  - **Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.5**

- [ ]* 1.2 Write property test for base document validation
  - **Property 2: Base Document Validation**
  - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 2. Update Data Models





  - Extend SQLAlchemy Estimate model with base_document_id and estimate_type fields
  - Add EstimateType enum with GENERAL and PLAN values
  - Update Estimate dataclass with hierarchy fields and properties
  - Add is_general and is_plan convenience properties
  - Add base_document and plan_estimates relationship properties
  - _Requirements: 1.2, 2.2, 1.3, 2.3_

- [ ]* 2.1 Write property test for model hierarchy validation
  - **Property 4: Referential Integrity**
  - **Validates: Requirements 9.1, 9.4**

- [x] 3. Create Hierarchy Repository Layer
  - Implement EstimateHierarchyRepository class
  - Add get_general_estimates() method to fetch estimates with base_document_id = NULL
  - Add get_plan_estimates_by_base(base_id) method for finding child estimates
  - Add validate_hierarchy_integrity(estimate_id, base_id) method
  - Add update_base_document(estimate_id, base_id) method with validation
  - _Requirements: 6.1, 6.2, 6.3, 9.1, 9.4_

- [ ]* 3.1 Write property test for hierarchy depth limitation
  - **Property 3: Hierarchy Depth Limitation**
  - **Validates: Requirements 6.4**

- [x] 4. Create Hierarchy Service Layer
  - Implement HierarchyService class for business logic
  - Add create_general_estimate(estimate_data) method
  - Add create_plan_estimate(estimate_data, base_id) method with validation
  - Add validate_hierarchy_rules(estimate) method to prevent circular references
  - Add get_hierarchy_summary(base_id) method for reporting
  - _Requirements: 1.1, 2.1, 6.1, 6.2, 6.3, 7.1, 7.2_

- [ ]* 4.1 Write property test for deletion constraints
  - **Property 5: Deletion Constraint**
  - **Validates: Requirements 9.2, 9.3**

- [x] 5. Update Desktop Estimate Document Form
  - Add "Документ-основание" field to EstimateDocumentForm
  - Implement base document picker using ReferencePickerDialog
  - Filter base document picker to show only general estimates
  - Add automatic estimate type assignment based on base document selection
  - Add visual indicators for estimate type (General/Plan)
  - Display base document reference for plan estimates
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.2, 13.3_

- [ ]* 5.1 Write property test for base document selector filtering
  - **Property 6: Base Document Selector Filtering**
  - **Validates: Requirements 3.2, 1.5**

- [ ]* 5.2 Write property test for automatic type assignment
  - **Property 7: Automatic Type Assignment**
  - **Validates: Requirements 3.4, 3.5**

- [x] 6. Update Desktop Estimate List Form
  - Add "Тип сметы" and "Документ-основание" columns to EstimateListForm
  - Display "Генеральная" for general estimates and "Плановая" for plan estimates
  - Show base document code/name for plan estimates
  - Add filtering by estimate type (General/Plan)
  - Add filtering by base document
  - Add visual indicators (icons) for estimate types
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 13.1, 13.4_

- [ ]* 6.1 Write property test for display consistency
  - **Property 8: Display Consistency**
  - **Validates: Requirements 1.3, 2.3**

- [x] 7. Implement Work Copy Functionality
  - Create WorkCopyDialog for selecting works from general estimates
  - Add copy_works_from_base(plan_id, selected_works) method to service
  - Display all works from base general estimate with checkboxes
  - Copy selected works with quantities, prices, and compositions
  - Recalculate plan estimate totals after copying works
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 7.1 Write unit tests for work copy functionality
  - Test work selection and copying logic
  - Test total recalculation after copying
  - Test error handling for invalid selections
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Add API Endpoints for Hierarchy
  - Extend estimates API endpoints with hierarchy support
  - Add base_document_id and estimate_type to EstimateBase model
  - Update create/update endpoints to handle hierarchy fields
  - Add GET /estimates/general endpoint for base document selection
  - Add GET /estimates/{id}/plan-estimates endpoint for derived estimates
  - Add validation for hierarchy rules in API layer
  - _Requirements: 2.1, 2.2, 3.2, 7.3, 7.4_

- [ ]* 8.1 Write API integration tests for hierarchy endpoints
  - Test creating general and plan estimates via API
  - Test hierarchy validation in API endpoints
  - Test filtering and querying hierarchy relationships
  - _Requirements: 2.1, 2.2, 6.1, 6.2, 6.3_

- [x] 9. Update Web Client Components
  - Add base document picker to estimate form components
  - Update estimate list components with hierarchy columns
  - Add estimate type indicators and visual styling
  - Implement hierarchy navigation in web interface
  - Add filtering by estimate type and base document
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 13.1, 13.2, 13.4_

- [ ]* 9.1 Write web component tests for hierarchy features
  - Test base document selection in forms
  - Test hierarchy display in lists
  - Test filtering and navigation functionality
  - _Requirements: 3.1, 3.2, 4.1, 4.2_

- [x] 10. Implement Hierarchy Reporting
  - Create hierarchy tree structure for reporting
  - Add get_hierarchy_tree(root_id) method to repository
  - Implement hierarchy summary with statistics
  - Add derived estimates display for general estimates
  - Create Excel export with hierarchy indentation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 10.1 Write unit tests for hierarchy reporting
  - Test hierarchy tree generation
  - Test summary statistics calculation
  - Test Excel export formatting
  - _Requirements: 7.1, 7.2, 10.1, 10.2, 10.3_

- [x] 11. Add Permission Controls
  - Implement permission checks for hierarchy operations
  - Add create_general_estimate permission
  - Add create_plan_estimate permission
  - Add modify_estimate_hierarchy permission
  - Update UI to show/hide operations based on permissions
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ]* 11.1 Write unit tests for permission controls
  - Test permission validation for hierarchy operations
  - Test UI behavior with different permission levels
  - Test error handling for insufficient permissions
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 12. Implement Audit Logging
  - Add hierarchy change tracking to audit system
  - Log base document changes with old/new values
  - Log estimate type changes
  - Log hierarchy relationship creation/deletion
  - Add hierarchy events to audit reports
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ]* 12.1 Write unit tests for audit logging
  - Test hierarchy change event logging
  - Test audit report generation with hierarchy events
  - Test audit data integrity and completeness
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 13. Add Search and Filtering
  - Implement search by estimate type in desktop application
  - Add base document filtering in estimate lists
  - Implement hierarchy relationship search
  - Add advanced search combining hierarchy with other criteria
  - Maintain filter state during navigation
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 13.1 Write unit tests for search and filtering
  - Test estimate type filtering
  - Test base document search functionality
  - Test advanced search combinations
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 14. Final Integration and Testing
  - Ensure all tests pass, ask the user if questions arise
  - Test complete hierarchy workflows end-to-end
  - Verify data migration for existing estimates
  - Test performance with large hierarchy datasets
  - Validate all requirements are implemented
  - _Requirements: All_

- [ ]* 14.1 Write comprehensive integration tests
  - Test complete estimate hierarchy workflows
  - Test data consistency across all layers
  - Test error handling and edge cases
  - _Requirements: All_
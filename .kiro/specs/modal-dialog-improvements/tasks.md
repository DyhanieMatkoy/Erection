# Implementation Plan - Modal Dialog and List Improvements

## Task Overview

This implementation plan converts the modal dialog and list improvements design into a series of actionable coding tasks. Each task builds incrementally on previous work to deliver the three main improvements: modal dialog z-index fixes, dynamic document list loading, and column sorting functionality.

## Tasks

- [ ] 1. Set up modal dialog management infrastructure
  - Create ModalDialogManager class for PyQt6 desktop application
  - Implement z-index calculation and stacking logic
  - Add dialog registration and cleanup methods
  - _Requirements: 1.1, 1.5_

- [ ] 1.1 Implement desktop modal dialog z-index management
  - Create ModalDialogManager singleton class with dialog stack tracking
  - Implement automatic z-index assignment based on stack position
  - Add methods for dialog registration, removal, and z-index recalculation
  - _Requirements: 1.1, 1.2, 1.5_

- [ ]* 1.2 Write property test for modal dialog z-index monotonicity
  - **Property 1: Modal Dialog Z-Index Monotonicity**
  - **Validates: Requirements 1.1, 1.2, 1.5**

- [ ] 1.3 Enhance ReferencePickerDialog with proper z-index handling
  - Integrate ReferencePickerDialog with ModalDialogManager
  - Add support for modal and non-modal modes
  - Implement proper focus management when opening edit forms
  - _Requirements: 1.2, 1.3, 1.4_

- [ ]* 1.4 Write property test for edit form visibility over selector
  - **Property 2: Edit Form Visibility Over Selector**
  - **Validates: Requirements 1.2, 1.3**

- [ ]* 1.5 Write property test for focus return after dialog close
  - **Property 3: Focus Return After Dialog Close**
  - **Validates: Requirements 1.4**

- [ ] 2. Implement web client modal service
  - Create ModalService for Vue.js web client
  - Implement modal component with proper z-index management
  - Add support for modal and non-modal modes
  - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [ ] 2.1 Create Vue.js ModalService and components
  - Implement ModalService class with modal stack management
  - Create reusable Modal component with z-index handling
  - Add support for backdrop click and escape key handling
  - _Requirements: 1.1, 5.1, 7.2_

- [ ]* 2.2 Write property test for non-modal window independence
  - **Property 13: Non-Modal Window Independence**
  - **Validates: Requirements 5.2, 5.3**

- [ ] 3. Implement dynamic document list loading
  - Create InfiniteScrollList component for web client
  - Implement scroll detection and batch loading logic
  - Add loading indicators and end-of-list detection
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 3.1 Create InfiniteScrollList Vue component
  - Implement scroll event handling with Intersection Observer API
  - Add automatic batch loading when approaching bottom
  - Include loading spinner and end-of-data indicators
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 3.2 Write property test for dynamic loading no duplicates
  - **Property 4: Dynamic Loading No Duplicates**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 3.3 Write property test for scroll-triggered loading
  - **Property 5: Scroll-Triggered Loading**
  - **Validates: Requirements 2.2, 2.3**

- [ ] 3.4 Implement virtual scrolling for large datasets
  - Add virtual scrolling capability to handle thousands of items
  - Implement DOM element recycling for performance
  - Add configuration options for virtual scrolling thresholds
  - _Requirements: 2.5_

- [ ]* 3.5 Write property test for virtual scrolling DOM stability
  - **Property 6: Virtual Scrolling DOM Stability**
  - **Validates: Requirements 2.5**

- [ ] 4. Enhance desktop list forms with dynamic loading
  - Update GenericListForm to support infinite scrolling
  - Implement scroll detection for QScrollArea
  - Add batch loading logic for desktop application
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4.1 Update GenericListForm for dynamic loading
  - Modify DocumentListTable to support batch loading
  - Implement scroll event handling in QScrollArea
  - Add loading indicators for desktop interface
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 5. Implement API pagination and sorting endpoints
  - Add pagination parameters to document list endpoints
  - Implement efficient database queries with LIMIT/OFFSET
  - Add sorting parameters and database query optimization
  - _Requirements: 2.1, 4.1, 4.4_

- [ ] 5.1 Create PaginationService for API layer
  - Implement pagination logic with configurable page sizes
  - Add metadata for total counts and page information
  - Create efficient database queries with proper indexing
  - _Requirements: 2.1, 2.2_

- [ ] 5.2 Add sorting support to API endpoints
  - Implement SortingService with column validation
  - Add sorting parameters to all document list endpoints
  - Ensure sorting works correctly with pagination
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 5.3 Write property test for global sort with pagination
  - **Property 12: Global Sort with Pagination**
  - **Validates: Requirements 4.4**

- [ ] 6. Implement intelligent date filtering
  - Create DateFilterService for default date range calculation
  - Add date filter persistence using user preferences
  - Implement date range validation and error handling
  - _Requirements: 3.1, 3.2, 3.5_

- [ ] 6.1 Create DateFilterService
  - Implement logic to calculate default date range from last document
  - Add date filter application to database queries
  - Include date range validation and boundary checking
  - _Requirements: 3.1, 3.2_

- [ ]* 6.2 Write property test for default date range calculation
  - **Property 7: Default Date Range Calculation**
  - **Validates: Requirements 3.1**

- [ ]* 6.3 Write property test for date filter application
  - **Property 8: Date Filter Application**
  - **Validates: Requirements 3.2**

- [ ] 6.4 Implement date filter persistence
  - Add user preference storage for custom date ranges
  - Implement preference loading on list form initialization
  - Add preference reset functionality
  - _Requirements: 3.5_

- [ ]* 6.5 Write property test for date filter persistence
  - **Property 9: Date Filter Persistence**
  - **Validates: Requirements 3.5**

- [ ] 7. Implement column sorting functionality
  - Add sortable column headers to document lists
  - Implement sort state management and visual indicators
  - Add keyboard support for column sorting
  - _Requirements: 4.1, 4.2, 4.3, 7.3_

- [ ] 7.1 Create sortable column headers
  - Add click handlers to column headers in DocumentListTable
  - Implement sort state cycling (none → asc → desc → none)
  - Add visual indicators for current sort state
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 7.2 Write property test for column sort toggle
  - **Property 10: Column Sort Toggle**
  - **Validates: Requirements 4.1, 4.2**

- [ ]* 7.3 Write property test for sort visual indicator consistency
  - **Property 11: Sort Visual Indicator Consistency**
  - **Validates: Requirements 4.3**

- [ ] 7.4 Add keyboard support for column sorting
  - Implement Enter/Space key handling on column headers
  - Add keyboard navigation between sortable columns
  - Ensure accessibility compliance for screen readers
  - _Requirements: 7.3_

- [ ]* 7.5 Write property test for keyboard sort activation
  - **Property 18: Keyboard Sort Activation**
  - **Validates: Requirements 7.3**

- [ ] 8. Implement user preference management
  - Create settings for modal behavior preferences
  - Add configuration options for list behavior
  - Implement preference persistence and loading
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8.1 Create user preference service for modal and list settings
  - Add preference storage for modal vs non-modal behavior
  - Implement settings for default page sizes and thresholds
  - Add configuration options for date filter defaults
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 8.2 Write property test for modal preference persistence
  - **Property 15: Modal Preference Persistence**
  - **Validates: Requirements 5.5**

- [ ] 9. Enhance keyboard navigation and accessibility
  - Implement comprehensive keyboard navigation for lists
  - Add focus trapping for modal dialogs
  - Ensure all functionality is accessible via keyboard
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [ ] 9.1 Implement keyboard navigation for document lists
  - Add arrow key navigation for row selection
  - Implement Page Up/Page Down for batch navigation
  - Add Home/End keys for first/last item navigation
  - _Requirements: 7.1_

- [ ]* 9.2 Write property test for keyboard navigation completeness
  - **Property 16: Keyboard Navigation Completeness**
  - **Validates: Requirements 7.1**

- [ ] 9.3 Implement modal focus trapping
  - Add focus trap logic for modal dialogs
  - Implement Escape key handling for dialog closure
  - Ensure focus returns to correct element after modal close
  - _Requirements: 7.2_

- [ ]* 9.4 Write property test for modal focus trapping
  - **Property 17: Modal Focus Trapping**
  - **Validates: Requirements 7.2**

- [ ]* 9.5 Write property test for stacked dialog focus management
  - **Property 19: Stacked Dialog Focus Management**
  - **Validates: Requirements 7.5**

- [ ] 10. Integration and testing
  - Integrate all components and test end-to-end workflows
  - Verify cross-platform compatibility (desktop and web)
  - Test performance with large datasets
  - _Requirements: All_

- [ ] 10.1 Integrate modal dialog improvements across desktop and web
  - Test modal dialog stacking in both PyQt6 and Vue.js implementations
  - Verify consistent behavior between desktop and web clients
  - Test work selector edit form scenarios end-to-end
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 10.2 Integrate dynamic loading across all document lists
  - Test infinite scrolling in both desktop and web implementations
  - Verify performance with datasets of 1000+ items
  - Test date filtering and sorting with dynamic loading
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 10.3 Test complete sorting and filtering workflows
  - Verify column sorting works with all document types
  - Test date filter defaults and persistence across sessions
  - Ensure keyboard navigation works with all new features
  - _Requirements: 3.1, 3.2, 3.5, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3_

- [ ]* 10.4 Write property test for multiple non-modal windows
  - **Property 14: Multiple Non-Modal Windows**
  - **Validates: Requirements 5.4**

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
# Implementation Plan - Timesheet Document

## Task List

- [x] 1. Database schema and migrations
- [x] 1.1 Create timesheets table with indexes
  - Add table definition to database_manager.py
  - Include fields: id, number, date, object_id, estimate_id, foreman_id, month_year, is_posted, posted_at, marked_for_deletion, created_at, modified_at
  - Create indexes on date, foreman_id, object_id, estimate_id
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Create timesheet_lines table with day columns
  - Add table with 31 day columns (day_01 to day_31)
  - Include fields: id, timesheet_id, line_number, employee_id, hourly_rate, day_01-day_31, total_hours, total_amount
  - Create indexes on timesheet_id, employee_id
  - _Requirements: 1.3, 2.1_

- [x] 1.3 Create payroll_register table with unique constraint
  - Add table with unique key (object_id, estimate_id, employee_id, work_date)
  - Include fields: id, recorder_type, recorder_id, line_number, period, object_id, estimate_id, employee_id, work_date, hours_worked, amount
  - Create indexes on recorder, dimensions, work_date
  - _Requirements: 3.1, 4.1, 4.2_

- [x] 1.4 Add migration logic to database_manager
  - Implement _add_timesheet_tables() method
  - Call from _create_tables() or _add_posting_fields()
  - Test migration on existing database
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Data models and API models
- [x] 2.1 Create Pydantic models for API
  - Implement TimesheetLineBase, TimesheetLineCreate, TimesheetLine
  - Implement TimesheetBase, TimesheetCreate, TimesheetUpdate, Timesheet
  - Add validation for hours (0-24) and positive rates
  - _Requirements: 1.1, 2.1, 6.1, 6.2, 6.3_

- [x] 2.2 Create PayrollRecord model
  - Implement PayrollRecord with all required fields
  - Add validation for unique key fields
  - _Requirements: 3.2, 4.1_

- [x] 3. Repository layer
- [x] 3.1 Implement TimesheetRepository
  - Create find_all() with optional foreman filter
  - Create find_by_id() with lines loading
  - Create create() method
  - Create update() method with lines replacement
  - Create delete() method (soft delete)
  - Create mark_posted() and unmark_posted() methods
  - _Requirements: 1.1, 1.2, 5.1, 5.2, 8.1, 8.2, 8.3_

- [x] 3.2 Implement PayrollRegisterRepository
  - Create write_records() with batch insert
  - Create delete_by_recorder() method
  - Create check_duplicates() method
  - Create get_by_dimensions() method
  - Implement transaction handling
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 8.1_

- [x] 4. Service layer - Core functionality
- [x] 4.1 Implement TimesheetService
  - Create get_timesheets() with role-based filtering
  - Create get_by_id() method
  - Create create_timesheet() with foreman assignment
  - Create update_timesheet() with totals recalculation
  - Implement _recalculate_totals() helper
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2_

- [x] 4.2 Implement TimesheetPostingService
  - Create post_timesheet() method
  - Create unpost_timesheet() method
  - Implement _create_payroll_records() helper
  - Add duplicate checking before posting
  - Add validation for empty timesheets
  - Handle posting errors with rollback
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 6.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 4.3 Implement AutoFillService
  - Create fill_from_daily_reports() method
  - Implement period calculation from month_year
  - Aggregate hours by employee and day
  - Distribute hours among multiple executors
  - Load hourly rates from person records
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 5. API endpoints
- [x] 5.1 Create timesheet endpoints module
  - Implement GET /api/documents/timesheets (list)
  - Implement GET /api/documents/timesheets/{id} (detail)
  - Implement POST /api/documents/timesheets (create)
  - Implement PUT /api/documents/timesheets/{id} (update)
  - Implement DELETE /api/documents/timesheets/{id} (delete)
  - Add authentication and authorization
  - _Requirements: 1.1, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.2 Create posting endpoints
  - Implement POST /api/documents/timesheets/{id}/post
  - Implement POST /api/documents/timesheets/{id}/unpost
  - Add error handling for duplicate records
  - Return detailed error messages
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 8.1, 8.2_

- [x] 5.3 Create autofill endpoint
  - Implement POST /api/documents/timesheets/autofill
  - Accept object_id, estimate_id, month_year parameters
  - Return list of timesheet lines
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 6. Desktop UI - List form




- [x] 6.1 Create TimesheetListForm class


  - Implement table with columns: Number, Date, Object, Estimate, Foreman, Posted
  - Add toolbar: New, Edit, Delete, Post, Unpost, Print, Refresh
  - Add filters: Date range, Object, Posted status
  - Implement role-based data loading
  - Add double-click to open document
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6.2 Implement list form actions

  - Create new_timesheet() handler
  - Create edit_timesheet() handler
  - Create delete_timesheet() handler with confirmation
  - Create post_timesheet() handler
  - Create unpost_timesheet() handler
  - Add refresh_data() method
  - _Requirements: 1.1, 3.1, 8.1, 8.2, 8.5_

- [x] 6.3 Add list form to main window menu


  - Add "Табель" menu item under "Документы"
  - Set keyboard shortcut (e.g., Ctrl+Shift+T)
  - Register form in main window
  - _Requirements: 1.1_

- [x] 7. Desktop UI - Document form





- [x] 7.1 Create TimesheetDocumentForm class


  - Implement header fields: Number, Date, Object, Estimate
  - Add toolbar: Save, Post, Unpost, Print, Fill from Daily Reports
  - Create table widget for lines
  - Set up form layout and styling
  - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2_

- [x] 7.2 Implement dynamic day columns

  - Calculate number of days in month from date
  - Create columns: Employee, Rate, Day 1-N, Total, Amount
  - Hide unused day columns (for months < 31 days)
  - Add column headers with day numbers
  - Highlight weekend columns
  - _Requirements: 1.4, 1.5, 7.1, 7.2, 7.3_

- [x] 7.3 Implement table cell editing

  - Add cell value validation (hours: 0-24, rate: > 0)
  - Implement on_cell_changed() handler
  - Add recalculate_row_totals() method
  - Support Tab/Enter navigation
  - Show validation errors
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.3, 7.4_

- [x] 7.4 Implement employee picker integration

  - Add "Add Employee" button
  - Open EmployeePickerDialog with brigade filter
  - Add selected employees to table
  - Load hourly rate from person record
  - Prevent duplicate employees
  - _Requirements: 10.3, 10.4, 10.5, 11.1, 11.2, 11.3_

- [x] 7.5 Implement auto-fill from daily reports

  - Add "Fill from Daily Reports" button
  - Check if Object and Estimate are selected
  - Show confirmation if table has data
  - Call AutoFillService
  - Populate table with returned lines
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [x] 7.6 Implement save and load functionality

  - Create save_timesheet() method
  - Validate required fields before save
  - Create load_timesheet() method
  - Populate form fields and table from data
  - Handle save errors
  - _Requirements: 1.1, 1.2, 6.4, 6.5_

- [x] 7.7 Implement posting from form

  - Add post_document() method
  - Call TimesheetPostingService
  - Show success/error messages
  - Disable editing after posting
  - Add unpost_document() method
  - Enable editing after unposting
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 8.1, 8.2, 8.3, 8.4_

- [x] 8. Desktop UI - Employee picker with brigade filter




- [x] 8.1 Create EmployeePickerDialog class


  - Implement table with columns: Name, Position, Rate
  - Add "Show all employees" checkbox
  - Add filter logic for brigade members
  - Add OK/Cancel buttons
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 8.2 Implement brigade filtering logic


  - Load foreman's person_id from current user
  - Query persons where parent_id = foreman_id OR parent_id IS NULL
  - Query all persons if "Show all" is checked
  - Save filter preference to user settings
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 9. Print forms





- [x] 9.1 Create Excel timesheet print form


  - Implement ExcelTimesheetPrintForm class
  - Create template with header and table
  - Add day columns with proper formatting
  - Include totals row
  - Support Cyrillic characters
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_



- [x] 9.2 Integrate print form with document form
  - Add print_document() method
  - Generate Excel file
  - Open file in default application
  - Handle print errors
  - _Requirements: 9.1_

- [x] 10. Web client - Vue components





- [x] 10.1 Create TimesheetListView component


  - Implement data table with filters
  - Add action buttons
  - Implement role-based filtering
  - Add routing
  - _Requirements: 5.1, 5.2_

- [x] 10.2 Create TimesheetFormView component


  - Implement form with header fields
  - Create dynamic day columns table
  - Add auto-fill button
  - Implement save/post/unpost actions
  - _Requirements: 1.1, 1.2, 7.1, 7.2, 12.1_

- [x] 10.3 Create TimesheetLines component


  - Implement editable table with day columns
  - Add cell validation
  - Implement auto-calculation
  - Add employee picker integration
  - _Requirements: 2.1, 2.2, 6.1, 7.3_

- [x] 11. Testing





- [x] 11.1 Write unit tests for services


  - Test TimesheetService methods
  - Test TimesheetPostingService with duplicates
  - Test AutoFillService hour distribution
  - _Requirements: All_

- [x] 11.2 Write integration tests


  - Test end-to-end posting flow
  - Test duplicate prevention
  - Test unposting and cleanup
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 8.1_

- [x] 11.3 Write API tests


  - Test all endpoints
  - Test authentication and authorization
  - Test error handling
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 12. Documentation






- [x] 12.1 Update database schema documentation

  - Add timesheet tables to DATABASE_SCHEMA.md
  - Add ER diagram for timesheet relationships
  - Document payroll register structure
  - _Requirements: All_

- [x] 12.2 Create user guide for timesheet


  - Write step-by-step instructions (Russian)
  - Add screenshots
  - Document auto-fill feature
  - Explain posting and duplicate prevention
  - _Requirements: All_


- [-] 12.3 Update API documentation

  - Document timesheet endpoints
  - Add request/response examples
  - Document error codes
  - _Requirements: 5.1, 5.2, 5.3_

# Bug Fix Patchlist

This document tracks all bug fixes applied to the Construction Time Management System.

## Fix #1: start_desktop.bat not using virtual environment
**File:** `start_desktop.bat`
**Issue:** Script was calling `python main.py` directly without activating virtual environment
**Fix:** Added virtual environment activation and error checking
```batch
# Before
python main.py

# After  
call .venv\Scripts\activate.bat
python main.py
```

## Fix #2: Ambiguous column name 'marked_for_deletion' in SQL query
**File:** `src/views/reference_picker_dialog.py`
**Issue:** SQL JOIN query had ambiguous column reference when joining works and units tables
**Fix:** Added table alias qualification for WHERE clause
```python
# Before
where_clauses = ["marked_for_deletion = 0"]

# After
if self.table_name == "works":
    where_clauses = ["w.marked_for_deletion = 0"]
else:
    where_clauses = ["marked_for_deletion = 0"]
```

## Fix #3: Ambiguous column name 'name' in ORDER BY clause
**File:** `src/views/reference_picker_dialog.py`
**Issue:** ORDER BY clause had ambiguous column reference in JOIN query
**Fix:** Added table alias qualification for ORDER BY clause
```python
# Before
ORDER BY {self.display_column}

# After
if self.table_name == "works":
    order_by_clause = f"w.{self.display_column}"
else:
    order_by_clause = self.display_column
```

## Fix #4: SQLite Row object has no 'get' method
**File:** `src/views/reference_picker_dialog.py`
**Issue:** Code was using `.get()` method on sqlite3.Row objects which don't support it
**Fix:** Changed to dictionary-style access with null checking
```python
# Before
row.get('code', '') or ''

# After
row['code'] if row['code'] else ''
```

## Fix #5: Disabled automatic sync node registration
**File:** `src/services/sync_service.py`
**Issue:** Application was trying to register with sync server on startup, causing connection errors
**Fix:** Commented out automatic registration
```python
# Before
self._register_node()

# After
# self._register_node()  # Uncomment to enable automatic registration
```

## Fix #6: ValueError when converting empty string to int
**File:** `src/views/daily_report_document_form.py`
**Issue:** Code was trying to convert empty string to integer without validation
**Fix:** Added empty string check and try-catch block
```python
# Before
estimate_id = int(estimate_id_item.text())

# After
if estimate_id_item and estimate_id_item.text().strip():
    try:
        estimate_id = int(estimate_id_item.text())
        self.load_estimate(estimate_id)
        self.modified = True
    except ValueError:
        QMessageBox.warning(self, "Error", "Invalid estimate ID selected")
```

## Fix #7: Missing column 'deviation_percent' in daily_report_lines table
**File:** `src/views/daily_report_document_form.py`
**Issue:** Code was referencing old column name `deviation_percent` but database schema was updated to use `labor_deviation_percent`
**Fix:** Updated SQL query and field access to use correct column name
```python
# Before
SELECT id, line_number, work_id, planned_labor, actual_labor, deviation_percent,
line.deviation_percent = line_row['deviation_percent']

# After
SELECT id, line_number, work_id, planned_labor, actual_labor, labor_deviation_percent,
line.deviation_percent = line_row['labor_deviation_percent']
```

## Fix #8: Lambda closure variable scope issue
**File:** `src/views/estimate_list_form.py`
**Issue:** Lambda function was trying to access `form` variable that was out of scope when the lambda executed
**Fix:** Used default parameter to capture the form reference properly in the lambda closure
```python
# Before
form.destroyed.connect(lambda: self.opened_forms.remove(form) if form in self.opened_forms else None)

# After
form.destroyed.connect(lambda f=form: self.opened_forms.remove(f) if f in self.opened_forms else None)
```

## Fix #9: Missing foreman_id attribute in TimesheetDocumentForm
**File:** `src/views/timesheet_document_form.py`
**Issue:** `foreman_id` could be None when loading existing timesheets, causing AttributeError when trying to add employees
**Fix:** Added fallback to current user's person_id if foreman_id is not available from database
```python
# Before
self.foreman_id = timesheet.get('foreman_id')

# After
self.foreman_id = timesheet.get('foreman_id')

# Ensure foreman_id is set, fallback to current user if not available
if not self.foreman_id:
    from ..services.auth_service import AuthService
    auth_service = AuthService()
    self.foreman_id = auth_service.current_person_id()
```

## Fix #10: ValueError when converting empty string to int (timesheet form)
**File:** `src/views/timesheet_document_form.py`
**Issue:** Code was trying to convert empty string to integer without validation when selecting estimate
**Fix:** Added empty string check and try-catch block (same pattern as Fix #6)
```python
# Before
estimate_id = int(estimate_id_item.text())

# After
if estimate_id_item and estimate_id_item.text().strip():
    try:
        estimate_id = int(estimate_id_item.text())
        self.load_estimate(estimate_id)
        self.modified = True
    except ValueError:
        QMessageBox.warning(self, "Error", "Invalid estimate ID selected")
```

## Fix #11: Estimate references not picked in timesheet form via selector
**File:** `src/views/timesheet_document_form.py`
**Issue:** Timesheet form was trying to get estimate ID from column 0, but EstimateListForm stores ID in column 7
**Fix:** Changed column index from 0 to 7 to get the correct estimate ID
```python
# Before
estimate_id_item = list_form.table_view.item(current_row, 0)

# After
estimate_id_item = list_form.table_view.item(current_row, 7)
```

**Note:** Column 0 contains posted status ("✓"), column 7 contains the actual estimate ID (hidden column)

---
**Total Fixes Applied:** 11
**Last Updated:** December 17, 2025
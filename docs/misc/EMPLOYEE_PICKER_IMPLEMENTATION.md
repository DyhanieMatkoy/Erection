# Employee Picker Dialog Implementation

## Overview

Implemented task 8 "Desktop UI - Employee picker with brigade filter" from the timesheet document specification. This feature allows foremen to select employees for timesheet documents with intelligent filtering based on brigade membership.

## Implementation Summary

### 1. Created EmployeePickerDialog Class (Task 8.1)

**File:** `src/views/employee_picker_dialog.py`

A standalone dialog component for selecting employees with the following features:

- **Table Display**: Shows employees with columns for Name, Position, and Hourly Rate
- **Brigade Filter Checkbox**: "Показать всех сотрудников" (Show all employees)
- **Smart Filtering**: 
  - When unchecked: Shows only brigade members (where foreman is supervisor) + employees without supervisor
  - When checked: Shows all employees in the system
- **User-Friendly Interface**: 
  - Double-click to select
  - Keyboard shortcuts (Enter to select, Escape to cancel)
  - OK/Cancel buttons

### 2. Implemented Brigade Filtering Logic (Task 8.2)

**Key Features:**

#### Filter Logic
- **Brigade Members Only**: Queries `persons WHERE parent_id = foreman_id OR parent_id IS NULL`
- **All Employees**: Queries all persons without filtering
- **Foreman ID**: Passed from the current user's person_id

#### Settings Persistence
- **Storage**: Uses `user_settings` table with key `employee_picker_show_all`
- **Auto-save**: Filter preference is saved when checkbox state changes
- **Auto-load**: Preference is loaded when dialog is created (defaults to "brigade only")
- **Table Creation**: Automatically creates `user_settings` table if it doesn't exist

#### Database Migration
- **Added Field**: `hourly_rate REAL DEFAULT 0` to `persons` table
- **Migration Method**: Updated `_add_posting_fields()` in `database_manager.py`
- **Safe Migration**: Checks if field exists before adding (idempotent)

### 3. Integration with Timesheet Document Form

**File:** `src/views/timesheet_document_form.py`

**Changes:**
- Removed embedded `EmployeePickerDialog` class
- Imported standalone `EmployeePickerDialog` from `employee_picker_dialog.py`
- Updated `on_add_employee()` method to use new dialog return value (id, name, rate)
- Hourly rate is now automatically populated from the persons table

**File:** `src/views/__init__.py`

**Changes:**
- Added `EmployeePickerDialog` to imports
- Added `EmployeePickerDialog` to `__all__` exports

## Technical Details

### Database Schema Changes

#### persons Table
```sql
ALTER TABLE persons ADD COLUMN hourly_rate REAL DEFAULT 0
```

#### user_settings Table
```sql
CREATE TABLE IF NOT EXISTS user_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT
)
```

### API

#### EmployeePickerDialog Constructor
```python
EmployeePickerDialog(parent=None, foreman_id=None, show_all=None)
```

**Parameters:**
- `parent`: Parent widget (optional)
- `foreman_id`: ID of the foreman for brigade filtering (optional)
- `show_all`: Override for show all setting (None = load from settings)

#### get_selected() Method
```python
def get_selected(self) -> Tuple[int, str, float]:
    """Returns (employee_id, employee_name, hourly_rate)"""
```

### Requirements Satisfied

✅ **Requirement 11.1**: Provides filter setting with two modes
✅ **Requirement 11.2**: Shows brigade members (parent_id = foreman_id) + employees without supervisor
✅ **Requirement 11.3**: Shows all employees when filter is disabled
✅ **Requirement 11.4**: Saves filter preference for each foreman
✅ **Requirement 11.5**: Applies filtering in employee picker forms

## Testing

**Test File:** `test_employee_picker.py`

**Test Results:**
- ✅ Brigade filtering works correctly
- ✅ Show all employees works correctly
- ✅ Filter preference persistence works
- ✅ hourly_rate field exists in database
- ✅ user_settings table created successfully

**Test Output:**
```
Testing with foreman: Иванов Иван Иванович (ID: 4)

=== Test 1: Show only brigade members ===
Employees shown (brigade only): 4

=== Test 2: Show all employees ===
Employees shown (all): 4

=== Test 3: Filter preference persistence ===
✓ Filter preference persistence works!

=== Test 4: Check hourly_rate field ===
✓ hourly_rate field exists in persons table

=== Test 5: Check user_settings table ===
✓ user_settings table exists
```

## Usage Example

```python
from src.views.employee_picker_dialog import EmployeePickerDialog

# Create dialog with foreman filtering
dialog = EmployeePickerDialog(parent=self, foreman_id=current_foreman_id)

if dialog.exec():
    employee_id, employee_name, hourly_rate = dialog.get_selected()
    
    # Use selected employee
    print(f"Selected: {employee_name} (ID: {employee_id}, Rate: {hourly_rate})")
```

## Files Modified

1. **Created:**
   - `src/views/employee_picker_dialog.py` - New standalone dialog component
   - `test_employee_picker.py` - Test file for verification

2. **Modified:**
   - `src/views/timesheet_document_form.py` - Removed embedded dialog, integrated new one
   - `src/views/__init__.py` - Added exports for new dialog
   - `src/data/database_manager.py` - Added hourly_rate field migration

## Benefits

1. **Reusability**: Standalone dialog can be used in other forms
2. **User Experience**: Filter preference is remembered across sessions
3. **Data Integrity**: Hourly rate is automatically loaded from database
4. **Flexibility**: Foremen can choose to see all employees when needed
5. **Maintainability**: Clean separation of concerns with dedicated dialog class

## Future Enhancements

Possible improvements for future iterations:

1. Add search/filter functionality within the dialog
2. Support for multiple selection (if needed)
3. Display additional employee information (phone, email, etc.)
4. Sort by different columns
5. Show brigade hierarchy visually

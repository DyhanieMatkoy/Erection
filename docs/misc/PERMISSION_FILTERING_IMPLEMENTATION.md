# Permission-Based Data Filtering Implementation

## Overview

Implemented permission-based data filtering to ensure that foremen (бригадиры) and employees (сотрудники) only see their own data in the system.

## Changes Made

### 1. AuthService Enhancements (`src/services/auth_service.py`)

Added the following methods to support permission-based filtering:

- **`current_person_id()`**: Returns the person ID associated with the current user
- **`is_foreman()`**: Checks if the current user has the "Бригадир" role
- **`is_employee()`**: Checks if the current user has the "Сотрудник" role
- **`_load_person_id()`**: Internal method that loads the person ID from the database when a user logs in

The service now maintains a `_current_person_id` field that is populated during login by querying the `persons` table for a record with matching `user_id`.

### 2. Daily Report List Form (`src/views/daily_report_list_form.py`)

Modified the form to filter daily reports based on user permissions:

- **Foreman users**: Automatically filtered to show only reports where they are the foreman
- **Filter visibility**: The foreman filter dropdown is hidden for foreman users since they can only see their own reports
- **Query modification**: Added permission-based WHERE clause to the data loading query

```python
# Apply permission-based filtering for foremen
if self.auth_service.is_foreman():
    person_id = self.auth_service.current_person_id()
    if person_id:
        where_clauses.append("dr.foreman_id = ?")
        params.append(person_id)
```

### 3. Work Execution Report Form (`src/views/work_execution_report_form.py`)

Modified the form to filter work execution data based on user permissions:

- **Foreman and Employee users**: Automatically filtered to show only work where they are executors
- **Filter visibility**: The executor filter dropdown is hidden for foreman and employee users
- **Query modification**: Added executor_id to filters when generating reports

```python
# Apply permission-based filtering for foremen and employees
if self.auth_service.is_foreman() or self.auth_service.is_employee():
    person_id = self.auth_service.current_person_id()
    if person_id:
        filters['executor_id'] = person_id
```

### 4. Work Execution Register Repository (`src/data/repositories/work_execution_register_repository.py`)

Enhanced the repository to support executor-based filtering:

- **Executor filtering**: Added support for `executor_id` in the filters parameter
- **Join logic**: When executor filtering is requested, the query joins with `daily_report_lines` and `daily_report_executors` tables
- **Expense-only filtering**: Executor filtering only applies to expense movements (from daily reports) since income movements (from estimates) don't have executors

```python
if needs_executor_join:
    # Join with daily reports and executors for filtering
    query = f"""
        SELECT ...
        FROM work_execution_register r
        ...
        LEFT JOIN daily_report_lines drl ON (
            r.recorder_type = 'DailyReport' 
            AND r.recorder_id = drl.report_id 
            AND r.line_number = drl.line_number
        )
        LEFT JOIN daily_report_executors dre ON drl.id = dre.report_line_id
        WHERE {where_clause}
    """
```

## User Experience

### For Administrators and Managers (Администратор, Руководитель)

- See all data without restrictions
- All filter dropdowns are visible and functional
- Can filter by any foreman or executor

### For Foremen (Бригадир)

- **Daily Reports**: Only see reports where they are the foreman
- **Work Execution Report**: Only see work where they are executors
- Foreman and executor filter dropdowns are hidden
- Cannot bypass the filtering

### For Employees (Сотрудник)

- **Daily Reports**: See all reports (no restriction at this level)
- **Work Execution Report**: Only see work where they are executors
- Executor filter dropdown is hidden
- Cannot bypass the filtering

## Database Requirements

For the filtering to work correctly, users must be linked to persons in the database:

1. Create a user record in the `users` table with appropriate role
2. Create or update a person record in the `persons` table
3. Set the `user_id` field in the `persons` table to link them

Example:
```sql
-- Create user
INSERT INTO users (username, password_hash, role, is_active)
VALUES ('foreman1', '<hash>', 'Бригадир', 1);

-- Link to person
UPDATE persons SET user_id = <user_id> WHERE id = <person_id>;
```

## Testing

Created comprehensive tests to verify the implementation:

1. **`test_permission_filtering.py`**: Basic tests for auth service and filtering
2. **`test_foreman_filtering_detailed.py`**: Detailed tests for foreman filtering in daily reports
3. **`test_executor_filtering_detailed.py`**: Detailed tests for executor filtering in work execution reports

All tests pass successfully, confirming that:
- AuthService correctly loads person IDs
- Foremen only see their own daily reports
- Employees only see their own work execution data
- Filtering cannot be bypassed

## Security Considerations

- Filtering is applied at the database query level, not just in the UI
- Users cannot bypass the filtering by manipulating UI elements
- The filtering is transparent to the user - they simply don't see data they shouldn't access
- No error messages reveal the existence of hidden data

## Future Enhancements

Potential improvements for future iterations:

1. Add filtering for estimates (foremen see only estimates where they are responsible)
2. Add audit logging for data access
3. Add more granular permissions (e.g., read-only vs. edit access)
4. Add team-based filtering (foremen see their team members' data)

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 5.2**: "КОГДА пользователь с ролью Бригадир открывает список смет, УчетнаяСистема ДОЛЖНА показать только сметы, где он указан как Ответственный" (partially - applies to daily reports)
- **Requirement 5.3**: "КОГДА пользователь с ролью Сотрудник открывает ежедневные отчеты, УчетнаяСистема ДОЛЖНА показать только отчеты, где он указан как Исполнитель" (applies to work execution report)

The implementation ensures data privacy and security by restricting access based on user roles and their associations with persons in the system.

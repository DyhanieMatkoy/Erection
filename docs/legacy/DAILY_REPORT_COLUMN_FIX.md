# Daily Report Column Name Fix

## Issue
The application was throwing a SQLite error: `sqlite3.OperationalError: no such column: report_id` when trying to open the daily reports form.

## Root Cause
The database schema uses `daily_report_id` as the foreign key column name in the `daily_report_lines` table, but the application code was using `report_id` in SQL queries and model definitions.

## Database Schema
The actual column structure in `daily_report_lines` table:
- `id` (INTEGER) - Primary key
- `daily_report_id` (INTEGER) - Foreign key to daily_reports.id
- Other columns...

## Files Fixed

### 1. Views
- `src/views/daily_report_list_form.py` - Fixed COUNT query
- `src/views/daily_report_document_form.py` - Fixed SELECT query

### 2. Services
- `src/services/excel_daily_report_print_form.py` - Fixed SELECT query
- `src/services/document_posting_service.py` - Fixed SELECT query
- `src/services/daily_report_service.py` - Fixed SELECT, DELETE, and INSERT queries
- `src/services/daily_report_print_form.py` - Fixed SELECT query
- `src/services/auto_fill_service.py` - Fixed SELECT query
- `src/services/auth_service.py` - Fixed SELECT query

### 3. Models
- `src/data/models/sqlalchemy_models.py` - Updated column name and __repr__ method
- `src/data/models/daily_report.py` - Updated attribute name

## Changes Made

### SQL Query Changes
Changed all occurrences of:
```sql
WHERE report_id = ?
```
To:
```sql
WHERE daily_report_id = ?
```

### Model Changes
Changed attribute name from `report_id` to `daily_report_id` in:
- DailyReportLine class definitions
- SQLAlchemy column definitions
- Object attribute assignments

## Testing
Created `fix_daily_report_error.py` to verify:
- ✅ Table exists
- ✅ `daily_report_id` column exists
- ✅ Corrected queries work properly
- ✅ Returns expected data

## Result
The daily reports functionality should now work correctly without the "no such column: report_id" error.
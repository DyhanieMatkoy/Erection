# Datetime Handling Guide

This guide explains how to use the datetime handling utilities for consistent datetime operations across SQLite, PostgreSQL, and Microsoft SQL Server backends.

## Overview

The `datetime_utils` module provides two main classes:
- `DateTimeConverter`: Utilities for converting between timezone-aware and naive datetimes
- `DateQueryHelper`: Helper methods for date comparison queries across different backends

## DateTimeConverter

### Converting to UTC

```python
from src.data.datetime_utils import DateTimeConverter
from datetime import datetime, timezone, timedelta

# Convert naive datetime to UTC (assumes input is UTC)
naive_dt = datetime(2024, 1, 15, 10, 30, 0)
utc_dt = DateTimeConverter.to_utc(naive_dt)
# Result: 2024-01-15 10:30:00+00:00

# Convert timezone-aware datetime to UTC
est = timezone(timedelta(hours=-5))
est_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=est)
utc_dt = DateTimeConverter.to_utc(est_dt)
# Result: 2024-01-15 15:30:00+00:00 (converted from EST)
```

### Converting to Naive UTC

For database storage (especially SQLite), you may need naive datetimes:

```python
# Convert timezone-aware to naive UTC
aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
naive_dt = DateTimeConverter.to_naive_utc(aware_dt)
# Result: 2024-01-15 10:30:00 (no timezone info)
```

### Converting from Naive UTC

When retrieving from database, convert back to timezone-aware:

```python
# Convert naive UTC to timezone-aware
naive_dt = datetime(2024, 1, 15, 10, 30, 0)
aware_dt = DateTimeConverter.from_naive_utc(naive_dt)
# Result: 2024-01-15 10:30:00+00:00
```

### Ensuring Timezone State

```python
# Ensure datetime is naive (remove timezone info)
aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
naive_dt = DateTimeConverter.ensure_naive(aware_dt)

# Ensure datetime is timezone-aware (add UTC if missing)
naive_dt = datetime(2024, 1, 15, 10, 30, 0)
aware_dt = DateTimeConverter.ensure_aware(naive_dt)
```

### Date/Datetime Conversion

```python
from datetime import date

# Convert date to datetime at midnight UTC
d = date(2024, 1, 15)
dt = DateTimeConverter.date_to_datetime(d)
# Result: 2024-01-15 00:00:00+00:00

# Convert datetime to date
dt = datetime(2024, 1, 15, 10, 30, 0)
d = DateTimeConverter.datetime_to_date(dt)
# Result: 2024-01-15
```

## DateQueryHelper

### Date Equality

```python
from src.data.datetime_utils import DateQueryHelper
from src.data.models.sqlalchemy_models import Estimate
from datetime import date

# Query for specific date
target_date = date(2024, 1, 15)
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_equals(Estimate.date, target_date)
).all()

# Also works with datetime input
target_datetime = datetime(2024, 1, 15, 12, 0, 0)
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_equals(Estimate.date, target_datetime)
).all()
```

### Date Comparisons

```python
# Greater than
start_date = date(2024, 1, 1)
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_greater_than(Estimate.date, start_date)
).all()

# Greater than or equal
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_greater_or_equal(Estimate.date, start_date)
).all()

# Less than
end_date = date(2024, 12, 31)
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_less_than(Estimate.date, end_date)
).all()

# Less than or equal
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_less_or_equal(Estimate.date, end_date)
).all()
```

### Date Ranges

```python
# Between two dates (inclusive)
start_date = date(2024, 1, 1)
end_date = date(2024, 3, 31)
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_between(Estimate.date, start_date, end_date)
).all()

# Specific month
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_in_month(Estimate.date, 2024, 2)
).all()

# Specific year
estimates = session.query(Estimate).filter(
    DateQueryHelper.date_in_year(Estimate.date, 2024)
).all()
```

### Datetime Ranges

```python
# Between two datetimes (inclusive)
start_dt = datetime(2024, 1, 1, 0, 0, 0)
end_dt = datetime(2024, 3, 31, 23, 59, 59)
estimates = session.query(Estimate).filter(
    DateQueryHelper.datetime_between(Estimate.created_at, start_dt, end_dt)
).all()

# Works with timezone-aware datetimes
start_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
end_dt = datetime(2024, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
estimates = session.query(Estimate).filter(
    DateQueryHelper.datetime_between(Estimate.created_at, start_dt, end_dt)
).all()
```

### Date Part Extraction

```python
# Extract year
estimates = session.query(Estimate).filter(
    DateQueryHelper.extract_year(Estimate.date) == 2024
).all()

# Extract month
estimates = session.query(Estimate).filter(
    DateQueryHelper.extract_month(Estimate.date) == 2
).all()

# Extract day
estimates = session.query(Estimate).filter(
    DateQueryHelper.extract_day(Estimate.date) == 15
).all()
```

## Best Practices

### Storing Datetimes

1. **Always store datetimes as naive UTC in the database**:
   ```python
   # Before storing
   aware_dt = datetime.now(timezone.utc)
   naive_dt = DateTimeConverter.to_naive_utc(aware_dt)
   estimate.created_at = naive_dt
   ```

2. **Convert back to timezone-aware when retrieving**:
   ```python
   # After retrieving
   estimate = session.query(Estimate).first()
   aware_dt = DateTimeConverter.from_naive_utc(estimate.created_at)
   ```

### Querying Dates

1. **Use DateQueryHelper for all date comparisons**:
   ```python
   # Good - works across all backends
   DateQueryHelper.date_equals(Estimate.date, target_date)
   
   # Avoid - may not work consistently across backends
   Estimate.date == target_date
   ```

2. **Use date_between for ranges**:
   ```python
   # Good - clear and consistent
   DateQueryHelper.date_between(Estimate.date, start_date, end_date)
   
   # Avoid - more verbose and error-prone
   and_(Estimate.date >= start_date, Estimate.date <= end_date)
   ```

### Timezone Handling

1. **Always be explicit about timezones**:
   ```python
   # Good - explicit UTC
   datetime.now(timezone.utc)
   
   # Avoid - ambiguous
   datetime.now()
   ```

2. **Convert at boundaries**:
   - Convert to naive UTC when storing
   - Convert to timezone-aware when retrieving
   - Keep timezone-aware in application logic

### Cross-Backend Compatibility

The utilities handle differences between database backends:

- **SQLite**: Stores datetimes as strings, no native timezone support
- **PostgreSQL**: Native TIMESTAMP and TIMESTAMPTZ types
- **MSSQL**: DATETIME2 type with timezone support

By using these utilities, your code works consistently across all backends.

## Examples

### Complete Round-Trip Example

```python
from src.data.datetime_utils import DateTimeConverter
from src.data.models.sqlalchemy_models import Estimate
from datetime import datetime, timezone

# Create estimate with current time
now = datetime.now(timezone.utc)
estimate = Estimate(
    number="EST-001",
    date=now.date(),
    created_at=DateTimeConverter.to_naive_utc(now)
)

# Save to database
session.add(estimate)
session.commit()

# Retrieve and convert back
retrieved = session.query(Estimate).filter_by(number="EST-001").first()
created_at_aware = DateTimeConverter.from_naive_utc(retrieved.created_at)

# Now you have timezone-aware datetime for application logic
print(f"Created at: {created_at_aware.isoformat()}")
```

### Query Example with Date Range

```python
from src.data.datetime_utils import DateQueryHelper
from src.data.models.sqlalchemy_models import Estimate
from datetime import date

# Get all estimates for Q1 2024
start_date = date(2024, 1, 1)
end_date = date(2024, 3, 31)

q1_estimates = session.query(Estimate).filter(
    DateQueryHelper.date_between(Estimate.date, start_date, end_date)
).order_by(Estimate.date).all()

for estimate in q1_estimates:
    print(f"{estimate.number}: {estimate.date}")
```

## Requirements Validation

This implementation satisfies the following requirements:

- **10.1**: Datetime conversion utilities for timezone handling ✓
- **10.2**: Models properly handle timezone-aware and naive datetimes ✓
- **10.3**: Date comparison query helpers ✓
- **10.4**: Date functions work across backends ✓
- **10.5**: Consistent timezone handling ✓

## Testing

The datetime utilities include comprehensive tests:

```bash
# Run datetime utility tests
python -m pytest test/test_datetime_utils.py -v
```

Tests cover:
- Timezone conversions (naive ↔ aware)
- UTC conversions
- Date/datetime conversions
- Query helpers with actual database
- Round-trip storage and retrieval

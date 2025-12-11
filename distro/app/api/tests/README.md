# API Integration Tests

This directory contains integration tests for the Construction Time Management API.

## Test Files

- `conftest.py` - Shared pytest fixtures
- `test_auth.py` - Authentication endpoint tests
- `test_references.py` - Reference data endpoint tests (counterparties, objects, works, persons, organizations)
- `test_estimates.py` - Estimate document endpoint tests
- `test_daily_reports.py` - Daily report document endpoint tests
- `test_document_posting.py` - Document posting/unposting tests
- `test_registers.py` - Register endpoint tests (work execution register)
- `test_error_cases.py` - Error case tests (401, 404, 422, 500)

## Running Tests

### Run all tests
```bash
pytest api/tests/ -v
```

### Run specific test file
```bash
pytest api/tests/test_auth.py -v
```

### Run with coverage
```bash
pytest api/tests/ --cov=api --cov-report=html
```

### Run specific test
```bash
pytest api/tests/test_auth.py::test_login_success -v
```

## Test Database

Tests use the existing `construction.db` database. Make sure it's initialized before running tests.

## Test Coverage

The integration tests cover:
- ✅ Authentication (login, token validation, current user)
- ✅ Reference endpoints (CRUD operations for all references)
- ✅ Document endpoints (estimates and daily reports)
- ✅ Document posting/unposting
- ✅ Register queries (work execution register)
- ✅ Error cases (401, 404, 422, 500)
- ✅ Pagination, filtering, sorting
- ✅ Authorization checks

## Requirements

- pytest
- fastapi
- All dependencies from requirements.txt

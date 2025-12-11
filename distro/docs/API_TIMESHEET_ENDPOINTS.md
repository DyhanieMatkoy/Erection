# Timesheet API Documentation

## Overview

The Timesheet API provides endpoints for managing employee time tracking documents. Timesheets record working hours for employees by day of the month, with automatic calculation of totals and integration with the payroll register.

**Base URL:** `/api/documents/timesheets`

**Authentication:** All endpoints require JWT authentication via Bearer token.

## Table of Contents

1. [Data Models](#data-models)
2. [Endpoints](#endpoints)
3. [Error Codes](#error-codes)
4. [Examples](#examples)

## Data Models

### TimesheetLineBase

Base model for timesheet lines.

```json
{
  "line_number": 1,
  "employee_id": 5,
  "hourly_rate": 250.0,
  "days": {
    "1": 8.0,
    "2": 8.0,
    "3": 7.5,
    "15": 8.0
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_number` | integer | Yes | Line number in the document (≥ 1) |
| `employee_id` | integer | Yes | Employee ID (FK to persons) |
| `hourly_rate` | float | No | Hourly rate (≥ 0, default: 0) |
| `days` | object | No | Dictionary of day numbers (1-31) to hours worked |

### TimesheetLine

Full timesheet line model with calculated fields.

```json
{
  "id": 1,
  "timesheet_id": 10,
  "line_number": 1,
  "employee_id": 5,
  "hourly_rate": 250.0,
  "days": {
    "1": 8.0,
    "2": 8.0,
    "3": 7.5
  },
  "total_hours": 23.5,
  "total_amount": 5875.0,
  "employee_name": "Иванов Иван Иванович"
}
```

**Additional Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Line ID |
| `timesheet_id` | integer | Parent timesheet ID |
| `total_hours` | float | Sum of all hours (calculated) |
| `total_amount` | float | total_hours × hourly_rate (calculated) |
| `employee_name` | string | Employee full name (joined) |

### TimesheetBase

Base model for timesheet documents.

```json
{
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | string | Yes | Document number (1-100 chars) |
| `date` | date | Yes | Document date (ISO 8601) |
| `object_id` | integer | No | Construction object ID |
| `estimate_id` | integer | No | Estimate ID |
| `foreman_id` | integer | No | Foreman ID (FK to persons) |
| `month_year` | string | Yes | Month in format "YYYY-MM" |

### TimesheetCreate

Model for creating a new timesheet.

```json
{
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "lines": [
    {
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0
      }
    }
  ]
}
```

**Fields:** Same as `TimesheetBase` plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lines` | array | No | Array of `TimesheetLineCreate` objects |

### TimesheetUpdate

Model for updating an existing timesheet.

Same structure as `TimesheetCreate`.

### Timesheet

Full timesheet model with metadata.

```json
{
  "id": 10,
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "is_posted": false,
  "posted_at": null,
  "marked_for_deletion": false,
  "created_at": "2024-03-15T10:30:00",
  "modified_at": "2024-03-15T14:20:00",
  "lines": [...],
  "object_name": "Жилой дом",
  "estimate_number": "СМ-001",
  "foreman_name": "Петров Петр Петрович"
}
```

**Additional Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Timesheet ID |
| `is_posted` | boolean | Posted status |
| `posted_at` | datetime | Posted timestamp (ISO 8601) |
| `marked_for_deletion` | boolean | Deletion mark |
| `created_at` | datetime | Creation timestamp |
| `modified_at` | datetime | Last modification timestamp |
| `lines` | array | Array of `TimesheetLine` objects |
| `object_name` | string | Object name (joined) |
| `estimate_number` | string | Estimate number (joined) |
| `foreman_name` | string | Foreman name (joined) |

### AutoFillRequest

Model for auto-fill request.

```json
{
  "object_id": 3,
  "estimate_id": 7,
  "month_year": "2024-03"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `object_id` | integer | Yes | Construction object ID |
| `estimate_id` | integer | Yes | Estimate ID |
| `month_year` | string | Yes | Month in format "YYYY-MM" |

### AutoFillResponse

Model for auto-fill response.

```json
{
  "lines": [
    {
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0,
        "15": 7.5
      }
    }
  ]
}
```

## Endpoints

### 1. List Timesheets

Get a list of timesheets for the current user.

**Endpoint:** `GET /api/documents/timesheets`

**Authentication:** Required

**Authorization:**
- **Admin:** Returns all timesheets
- **Foreman:** Returns only timesheets where user is the foreman

**Request:**

```http
GET /api/documents/timesheets HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
[
  {
    "id": 10,
    "number": "ТБ-001",
    "date": "2024-03-15",
    "object_id": 3,
    "estimate_id": 7,
    "foreman_id": 2,
    "month_year": "2024-03",
    "is_posted": false,
    "posted_at": null,
    "marked_for_deletion": false,
    "created_at": "2024-03-15T10:30:00",
    "modified_at": "2024-03-15T14:20:00",
    "lines": [],
    "object_name": "Жилой дом",
    "estimate_number": "СМ-001",
    "foreman_name": "Петров Петр Петрович"
  }
]
```

**Error Responses:**

- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

---

### 2. Get Timesheet by ID

Get a specific timesheet with all lines.

**Endpoint:** `GET /api/documents/timesheets/{id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Timesheet ID |

**Request:**

```http
GET /api/documents/timesheets/10 HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "id": 10,
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "is_posted": false,
  "posted_at": null,
  "marked_for_deletion": false,
  "created_at": "2024-03-15T10:30:00",
  "modified_at": "2024-03-15T14:20:00",
  "lines": [
    {
      "id": 1,
      "timesheet_id": 10,
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0,
        "3": 7.5
      },
      "total_hours": 23.5,
      "total_amount": 5875.0,
      "employee_name": "Иванов Иван Иванович"
    }
  ],
  "object_name": "Жилой дом",
  "estimate_number": "СМ-001",
  "foreman_name": "Петров Петр Петрович"
}
```

**Error Responses:**

- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Timesheet not found
- `500 Internal Server Error` - Server error

---

### 3. Create Timesheet

Create a new timesheet document.

**Endpoint:** `POST /api/documents/timesheets`

**Authentication:** Required

**Request Body:** `TimesheetCreate`

**Request:**

```http
POST /api/documents/timesheets HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json

{
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "lines": [
    {
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0
      }
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "id": 10,
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "is_posted": false,
  "posted_at": null,
  "marked_for_deletion": false,
  "created_at": "2024-03-15T10:30:00",
  "modified_at": "2024-03-15T10:30:00",
  "lines": [
    {
      "id": 1,
      "timesheet_id": 10,
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0
      },
      "total_hours": 16.0,
      "total_amount": 4000.0,
      "employee_name": "Иванов Иван Иванович"
    }
  ],
  "object_name": "Жилой дом",
  "estimate_number": "СМ-001",
  "foreman_name": "Петров Петр Петрович"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Validation Rules:**

- `number`: 1-100 characters, required
- `date`: Valid ISO 8601 date, required
- `month_year`: Format "YYYY-MM", required
- `hourly_rate`: ≥ 0
- `days`: Keys must be 1-31, values must be 0-24

---

### 4. Update Timesheet

Update an existing timesheet document.

**Endpoint:** `PUT /api/documents/timesheets/{id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Timesheet ID |

**Request Body:** `TimesheetUpdate`

**Request:**

```http
PUT /api/documents/timesheets/10 HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json

{
  "number": "ТБ-001",
  "date": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "foreman_id": 2,
  "month_year": "2024-03",
  "lines": [
    {
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0,
        "3": 7.5
      }
    }
  ]
}
```

**Response:** `200 OK`

Returns updated `Timesheet` object (same structure as Create response).

**Error Responses:**

- `400 Bad Request` - Invalid request data or timesheet is posted
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Timesheet not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Notes:**

- Cannot update a posted timesheet (must unpost first)
- All lines are replaced (not merged)

---

### 5. Delete Timesheet

Mark a timesheet for deletion (soft delete).

**Endpoint:** `DELETE /api/documents/timesheets/{id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Timesheet ID |

**Request:**

```http
DELETE /api/documents/timesheets/10 HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Timesheet marked for deletion"
}
```

**Error Responses:**

- `400 Bad Request` - Timesheet is posted (must unpost first)
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Timesheet not found
- `500 Internal Server Error` - Server error

**Notes:**

- Cannot delete a posted timesheet
- This is a soft delete (sets `marked_for_deletion = true`)

---

### 6. Post Timesheet

Post a timesheet to create payroll register records.

**Endpoint:** `POST /api/documents/timesheets/{id}/post`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Timesheet ID |

**Request:**

```http
POST /api/documents/timesheets/10/post HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Timesheet posted successfully"
}
```

**Error Responses:**

- `400 Bad Request` - Validation error or duplicate records
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Timesheet not found
- `500 Internal Server Error` - Server error

**Validation:**

- Timesheet must not be already posted
- Timesheet must have at least one line with non-zero hours
- No duplicate records in payroll register (same object, estimate, employee, date)

**Duplicate Error Response:** `400 Bad Request`

```json
{
  "detail": "Cannot post: duplicate records found for Иванов И.И. on 2024-03-15. Existing document: Табель №5 от 01.03.2024"
}
```

**What Happens:**

1. System checks for duplicate records in payroll register
2. Creates one payroll record for each employee/day with non-zero hours
3. Sets `is_posted = true` and `posted_at = current_timestamp`
4. Locks the document for editing

**Payroll Record Structure:**

```json
{
  "recorder_type": "timesheet",
  "recorder_id": 10,
  "line_number": 1,
  "period": "2024-03-15",
  "object_id": 3,
  "estimate_id": 7,
  "employee_id": 5,
  "work_date": "2024-03-15",
  "hours_worked": 8.0,
  "amount": 2000.0
}
```

---

### 7. Unpost Timesheet

Unpost a timesheet and delete payroll register records.

**Endpoint:** `POST /api/documents/timesheets/{id}/unpost`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Timesheet ID |

**Request:**

```http
POST /api/documents/timesheets/10/unpost HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Timesheet unposted successfully"
}
```

**Error Responses:**

- `400 Bad Request` - Timesheet is not posted
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Timesheet not found
- `500 Internal Server Error` - Server error

**What Happens:**

1. Deletes all payroll records created by this timesheet
2. Sets `is_posted = false` and `posted_at = null`
3. Unlocks the document for editing

---

### 8. Auto-fill from Daily Reports

Get timesheet lines auto-filled from daily reports.

**Endpoint:** `POST /api/documents/timesheets/autofill`

**Authentication:** Required

**Request Body:** `AutoFillRequest`

**Request:**

```http
POST /api/documents/timesheets/autofill HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json

{
  "object_id": 3,
  "estimate_id": 7,
  "month_year": "2024-03"
}
```

**Response:** `200 OK`

```json
{
  "lines": [
    {
      "line_number": 1,
      "employee_id": 5,
      "hourly_rate": 250.0,
      "days": {
        "1": 8.0,
        "2": 8.0,
        "15": 7.5,
        "16": 8.0
      }
    },
    {
      "line_number": 2,
      "employee_id": 8,
      "hourly_rate": 300.0,
      "days": {
        "1": 8.0,
        "2": 8.0
      }
    }
  ]
}
```

**Error Responses:**

- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**How It Works:**

1. Finds all daily reports for the specified object, estimate, and month
2. Extracts unique list of employees (executors)
3. Aggregates actual labor hours by employee and day
4. If multiple executors on one work, distributes hours proportionally
5. Loads hourly rates from person records
6. Returns ready-to-use timesheet lines

**Example Scenario:**

Daily Report 2024-03-15:
- Work: Bricklaying
- Actual labor: 16 hours
- Executors: Ivanov, Petrov

Result:
- Ivanov, day 15: 8 hours
- Petrov, day 15: 8 hours

---

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request - Invalid data or business rule violation |
| `401` | Unauthorized - Missing or invalid authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error |

### Business Error Messages

| Error | HTTP Code | Message |
|-------|-----------|---------|
| Already Posted | 400 | "Timesheet is already posted" |
| Not Posted | 400 | "Timesheet is not posted" |
| Empty Timesheet | 400 | "Cannot post: timesheet has no working hours" |
| Duplicate Records | 400 | "Cannot post: duplicate records found for {employee} on {date}" |
| Cannot Edit Posted | 400 | "Cannot update posted timesheet" |
| Cannot Delete Posted | 400 | "Cannot delete posted timesheet" |
| Invalid Hours | 422 | "Hours must be between 0 and 24" |
| Invalid Rate | 422 | "Hourly rate must be positive" |
| Not Found | 404 | "Timesheet not found" |

## Examples

### Complete Workflow Example

#### 1. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "foreman1", "password": "password123"}'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "foreman1",
    "role": "foreman"
  }
}
```

#### 2. Create Timesheet

```bash
curl -X POST http://localhost:8000/api/documents/timesheets \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "number": "ТБ-001",
    "date": "2024-03-15",
    "object_id": 3,
    "estimate_id": 7,
    "foreman_id": 2,
    "month_year": "2024-03",
    "lines": []
  }'
```

#### 3. Auto-fill from Daily Reports

```bash
curl -X POST http://localhost:8000/api/documents/timesheets/autofill \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "object_id": 3,
    "estimate_id": 7,
    "month_year": "2024-03"
  }'
```

#### 4. Update Timesheet with Auto-filled Lines

```bash
curl -X PUT http://localhost:8000/api/documents/timesheets/10 \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "number": "ТБ-001",
    "date": "2024-03-15",
    "object_id": 3,
    "estimate_id": 7,
    "foreman_id": 2,
    "month_year": "2024-03",
    "lines": [
      {
        "line_number": 1,
        "employee_id": 5,
        "hourly_rate": 250.0,
        "days": {
          "1": 8.0,
          "2": 8.0,
          "15": 7.5
        }
      }
    ]
  }'
```

#### 5. Post Timesheet

```bash
curl -X POST http://localhost:8000/api/documents/timesheets/10/post \
  -H "Authorization: Bearer eyJhbGc..."
```

#### 6. Get Posted Timesheet

```bash
curl -X GET http://localhost:8000/api/documents/timesheets/10 \
  -H "Authorization: Bearer eyJhbGc..."
```

#### 7. Unpost Timesheet (if needed)

```bash
curl -X POST http://localhost:8000/api/documents/timesheets/10/unpost \
  -H "Authorization: Bearer eyJhbGc..."
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "foreman1",
    "password": "password123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create timesheet
timesheet_data = {
    "number": "ТБ-001",
    "date": "2024-03-15",
    "object_id": 3,
    "estimate_id": 7,
    "foreman_id": 2,
    "month_year": "2024-03",
    "lines": [
        {
            "line_number": 1,
            "employee_id": 5,
            "hourly_rate": 250.0,
            "days": {
                "1": 8.0,
                "2": 8.0,
                "3": 7.5
            }
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/documents/timesheets",
    headers=headers,
    json=timesheet_data
)
timesheet = response.json()
timesheet_id = timesheet["id"]

# Post timesheet
response = requests.post(
    f"{BASE_URL}/api/documents/timesheets/{timesheet_id}/post",
    headers=headers
)
print(response.json())  # {"success": true, "message": "Timesheet posted successfully"}
```

### JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8000';

// Login
const loginResponse = await fetch(`${BASE_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'foreman1',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// Create timesheet
const timesheetData = {
  number: 'ТБ-001',
  date: '2024-03-15',
  object_id: 3,
  estimate_id: 7,
  foreman_id: 2,
  month_year: '2024-03',
  lines: [
    {
      line_number: 1,
      employee_id: 5,
      hourly_rate: 250.0,
      days: {
        1: 8.0,
        2: 8.0,
        3: 7.5
      }
    }
  ]
};

const createResponse = await fetch(`${BASE_URL}/api/documents/timesheets`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(timesheetData)
});
const timesheet = await createResponse.json();

// Post timesheet
const postResponse = await fetch(
  `${BASE_URL}/api/documents/timesheets/${timesheet.id}/post`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);
const result = await postResponse.json();
console.log(result); // {success: true, message: "Timesheet posted successfully"}
```

## Testing with Swagger UI

1. Start the API server:
   ```bash
   uvicorn api.main:app --reload
   ```

2. Open Swagger UI:
   ```
   http://localhost:8000/docs
   ```

3. Authenticate:
   - Click "Authorize" button
   - Login via `/api/auth/login` endpoint
   - Copy the `access_token`
   - Enter `Bearer <token>` in the authorization dialog

4. Test endpoints:
   - Expand any endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"

## Notes

- All datetime fields use ISO 8601 format with timezone
- The `days` dictionary uses integer keys (1-31) for day numbers
- Hours validation: 0 ≤ hours ≤ 24
- Hourly rate validation: rate ≥ 0
- Posted timesheets cannot be edited or deleted
- Duplicate prevention is enforced at the database level with unique constraint
- Auto-fill aggregates data from all daily reports in the specified period
- Role-based filtering applies automatically based on JWT token

## Support

For issues or questions, contact the development team or refer to the main API documentation.

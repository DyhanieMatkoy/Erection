# Web Client Access Design Document

## Overview

This document describes the design for a web-based client that provides browser access to the construction time management system. The web client will offer an alternative interface to the existing PyQt6 desktop application while maintaining full compatibility with the shared SQLite database and business logic.

### Design Goals

- **Reuse existing business logic**: Leverage current repositories, services, and database schema without modification
- **Maintain data compatibility**: Ensure seamless interoperability between desktop and web clients
- **Mobile-first approach**: Prioritize responsive design for field workers using mobile devices
- **Minimal infrastructure**: Use lightweight technologies suitable for small construction companies
- **Progressive enhancement**: Start with core features and expand based on user feedback

### Technology Stack Rationale

**Backend: FastAPI**
- Lightweight and modern Python web framework
- Automatic OpenAPI documentation generation
- Native async support for better performance
- Easy integration with existing SQLite and services
- Minimal learning curve for Python developers

**Frontend: Vue.js 3 with Composition API**
- Progressive framework suitable for both simple and complex UIs
- Excellent mobile support and performance
- Component-based architecture matches desktop form structure
- Strong TypeScript support for type safety
- Smaller bundle size compared to alternatives

**Authentication: JWT (JSON Web Tokens)**
- Stateless authentication suitable for REST APIs
- Works well with mobile and web clients
- Easy to implement and validate
- Industry standard approach

## Architecture

### High-Level Architecture


```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Browser    │  │   Mobile     │  │   Tablet     │      │
│  │   (Vue.js)   │  │   Browser    │  │   Browser    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTPS / REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                   API Server Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                      │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │   Auth     │  │  Document  │  │  Reference │    │   │
│  │  │  Endpoints │  │  Endpoints │  │  Endpoints │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Middleware Layer                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │    JWT     │  │   CORS     │  │ Validation │    │   │
│  │  │   Auth     │  │  Handler   │  │  Handler   │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Existing Services (Reused)                    │   │
│  │  ┌────────────────┐  ┌──────────────────────┐       │   │
│  │  │ Document       │  │  Print Form          │       │   │
│  │  │ Posting        │  │  Service             │       │   │
│  │  │ Service        │  └──────────────────────┘       │   │
│  │  └────────────────┘                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Existing Repositories (Reused)                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ Estimate   │  │ Reference  │  │   User     │    │   │
│  │  │ Repository │  │ Repository │  │ Repository │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Database Manager (Reused)                     │   │
│  │              SQLite Connection                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                  construction.db (SQLite)                    │
│         (Shared with Desktop Client)                         │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Authentication Flow:**
1. User enters credentials in Vue.js login form
2. Frontend sends POST to `/api/auth/login`
3. API validates credentials via UserRepository
4. API generates JWT token with 8-hour expiration
5. Frontend stores token in localStorage
6. All subsequent requests include token in Authorization header

**Data Access Flow:**
1. Frontend makes authenticated API request
2. JWT middleware validates token
3. API endpoint calls existing repository/service
4. Repository queries SQLite database
5. API returns JSON response
6. Frontend updates Vue.js reactive state
7. UI re-renders with new data



## Components and Interfaces

### Backend Components

#### 1. API Server (FastAPI Application)

**Purpose**: Expose REST endpoints for web client access to system functionality

**Key Responsibilities**:
- Route HTTP requests to appropriate handlers
- Validate request data using Pydantic models
- Enforce authentication and authorization
- Handle CORS for browser security
- Return standardized JSON responses

**Configuration**:
```python
# api/main.py structure
- CORS middleware (allow specific origins)
- JWT authentication middleware
- Request validation middleware
- Error handling middleware
- Static file serving for Vue.js build
```

#### 2. Authentication Service

**Purpose**: Manage user authentication and session tokens

**Key Methods**:
```python
authenticate_user(username: str, password: str) -> Optional[User]
create_access_token(user_id: int, expires_delta: timedelta) -> str
verify_token(token: str) -> Optional[dict]
hash_password(password: str) -> str
verify_password(plain: str, hashed: str) -> bool
```

**Token Structure**:
```json
{
  "sub": "user_id",
  "username": "username",
  "role": "admin|user",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Design Decisions**:
- Use bcrypt for password hashing (already in requirements.txt)
- JWT tokens expire after 8 hours (Requirement 1.4)
- Refresh tokens not implemented in MVP (can add later)
- Session timeout after 30 minutes of inactivity (Requirement 11.5)

#### 3. API Endpoints

**Authentication Endpoints** (`/api/auth`):
```
POST   /login          - Authenticate user, return JWT token
POST   /logout         - Invalidate token (client-side)
GET    /me             - Get current user info
```

**Reference Endpoints** (`/api/references`):
```
GET    /counterparties          - List counterparties
POST   /counterparties          - Create counterparty
GET    /counterparties/{id}     - Get counterparty details
PUT    /counterparties/{id}     - Update counterparty
DELETE /counterparties/{id}     - Mark for deletion

GET    /objects                 - List objects
POST   /objects                 - Create object
GET    /objects/{id}            - Get object details
PUT    /objects/{id}            - Update object
DELETE /objects/{id}            - Mark for deletion

GET    /works                   - List works
POST   /works                   - Create work
GET    /works/{id}              - Get work details
PUT    /works/{id}              - Update work
DELETE /works/{id}              - Mark for deletion

GET    /persons                 - List persons
POST   /persons                 - Create person
GET    /persons/{id}            - Get person details
PUT    /persons/{id}            - Update person
DELETE /persons/{id}            - Mark for deletion

GET    /organizations           - List organizations
POST   /organizations           - Create organization
GET    /organizations/{id}      - Get organization details
PUT    /organizations/{id}      - Update organization
DELETE /organizations/{id}      - Mark for deletion
```

**Document Endpoints** (`/api/documents`):
```
GET    /estimates               - List estimates (paginated)
POST   /estimates               - Create estimate
GET    /estimates/{id}          - Get estimate with lines
PUT    /estimates/{id}          - Update estimate header
DELETE /estimates/{id}          - Delete estimate
POST   /estimates/{id}/post     - Post estimate document
POST   /estimates/{id}/unpost   - Unpost estimate document
GET    /estimates/{id}/print    - Generate print form

GET    /daily-reports           - List daily reports (paginated)
POST   /daily-reports           - Create daily report
GET    /daily-reports/{id}      - Get report with lines
PUT    /daily-reports/{id}      - Update report header
DELETE /daily-reports/{id}      - Delete report
POST   /daily-reports/{id}/post - Post report document
POST   /daily-reports/{id}/unpost - Unpost report document
GET    /daily-reports/{id}/print - Generate print form
```

**Register Endpoints** (`/api/registers`):
```
GET    /work-execution          - Query work execution register
                                  Query params: period_from, period_to,
                                  object_id, estimate_id, work_id
```

**Query Parameters for Lists**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `search`: Search term for filtering
- `sort_by`: Field to sort by
- `sort_order`: asc|desc

**Standard Response Format**:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 150,
    "pages": 3
  }
}
```



### Frontend Components

#### 1. Vue.js Application Structure

```
web-client/
├── src/
│   ├── main.ts                 # Application entry point
│   ├── App.vue                 # Root component
│   ├── router/
│   │   └── index.ts            # Vue Router configuration
│   ├── stores/                 # Pinia state management
│   │   ├── auth.ts             # Authentication state
│   │   ├── references.ts       # Reference data cache
│   │   └── documents.ts        # Document state
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios instance with interceptors
│   │   ├── auth.ts             # Auth API calls
│   │   ├── references.ts       # Reference API calls
│   │   └── documents.ts        # Document API calls
│   ├── components/             # Reusable components
│   │   ├── common/
│   │   │   ├── DataTable.vue   # Generic table component
│   │   │   ├── FormField.vue   # Form input wrapper
│   │   │   ├── Modal.vue       # Modal dialog
│   │   │   └── Picker.vue      # Reference picker
│   │   ├── layout/
│   │   │   ├── AppHeader.vue   # Top navigation
│   │   │   ├── AppSidebar.vue  # Side menu
│   │   │   └── AppLayout.vue   # Main layout wrapper
│   │   └── documents/
│   │       ├── EstimateLines.vue
│   │       └── DailyReportLines.vue
│   ├── views/                  # Page components
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── references/
│   │   │   ├── CounterpartiesView.vue
│   │   │   ├── ObjectsView.vue
│   │   │   ├── WorksView.vue
│   │   │   ├── PersonsView.vue
│   │   │   └── OrganizationsView.vue
│   │   ├── documents/
│   │   │   ├── EstimateListView.vue
│   │   │   ├── EstimateFormView.vue
│   │   │   ├── DailyReportListView.vue
│   │   │   └── DailyReportFormView.vue
│   │   └── registers/
│   │       └── WorkExecutionView.vue
│   ├── composables/            # Reusable composition functions
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useTable.ts
│   └── types/                  # TypeScript type definitions
│       ├── api.ts
│       ├── models.ts
│       └── forms.ts
├── public/
│   └── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

#### 2. Key Frontend Components

**Authentication Components**:
- `LoginView.vue`: Login form with username/password fields
- `useAuth` composable: Manages authentication state and token storage

**Reference Management Components**:
- `DataTable.vue`: Generic table with search, sort, pagination
- `ReferenceFormModal.vue`: Generic form for creating/editing references
- `ReferencePicker.vue`: Searchable dropdown for selecting references
- Hierarchical tree view for references with parent-child relationships

**Document Components**:
- `EstimateFormView.vue`: Estimate header and lines editor
- `EstimateLines.vue`: Editable table for estimate lines with grouping
- `DailyReportFormView.vue`: Daily report header and lines editor
- `DailyReportLines.vue`: Editable table for report lines with executors

**Responsive Design Strategy**:
- Desktop (>1024px): Full table view with all columns
- Tablet (768-1024px): Condensed table with essential columns
- Mobile (<768px): Card-based layout instead of tables
- Touch-friendly controls (larger buttons, swipe gestures)



## Data Models

### API Request/Response Models (Pydantic)

#### Authentication Models

```python
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo

class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
```

#### Reference Models

```python
class CounterpartyBase(BaseModel):
    name: str
    inn: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    parent_id: Optional[int] = None

class CounterpartyCreate(CounterpartyBase):
    pass

class CounterpartyUpdate(CounterpartyBase):
    pass

class Counterparty(CounterpartyBase):
    id: int
    marked_for_deletion: bool = False
    
    class Config:
        from_attributes = True

# Similar models for: Object, Work, Person, Organization
```

#### Document Models

```python
class EstimateLineBase(BaseModel):
    line_number: int
    work_id: Optional[int] = None
    quantity: float = 0
    unit: Optional[str] = None
    price: float = 0
    labor_rate: float = 0
    sum: float = 0
    planned_labor: float = 0
    is_group: bool = False
    group_name: Optional[str] = None
    parent_group_id: Optional[int] = None

class EstimateLineCreate(EstimateLineBase):
    pass

class EstimateLine(EstimateLineBase):
    id: int
    estimate_id: int
    work_name: Optional[str] = None  # Joined from works table
    
    class Config:
        from_attributes = True

class EstimateBase(BaseModel):
    number: str
    date: date
    customer_id: Optional[int] = None
    object_id: Optional[int] = None
    contractor_id: Optional[int] = None
    responsible_id: Optional[int] = None

class EstimateCreate(EstimateBase):
    lines: List[EstimateLineCreate] = []

class EstimateUpdate(EstimateBase):
    lines: Optional[List[EstimateLineCreate]] = None

class Estimate(EstimateBase):
    id: int
    total_sum: float = 0
    total_labor: float = 0
    is_posted: bool = False
    posted_at: Optional[datetime] = None
    created_at: datetime
    modified_at: datetime
    lines: List[EstimateLine] = []
    
    # Joined fields for display
    customer_name: Optional[str] = None
    object_name: Optional[str] = None
    contractor_name: Optional[str] = None
    responsible_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Similar models for: DailyReport, DailyReportLine
```

#### Register Models

```python
class WorkExecutionMovement(BaseModel):
    id: int
    recorder_type: str
    recorder_id: int
    line_number: int
    period: date
    object_id: Optional[int] = None
    estimate_id: Optional[int] = None
    work_id: Optional[int] = None
    quantity_income: float = 0
    quantity_expense: float = 0
    sum_income: float = 0
    sum_expense: float = 0
    created_at: datetime
    
    # Joined fields
    object_name: Optional[str] = None
    estimate_number: Optional[str] = None
    work_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class WorkExecutionQuery(BaseModel):
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    object_id: Optional[int] = None
    estimate_id: Optional[int] = None
    work_id: Optional[int] = None
    group_by: Optional[List[str]] = None  # ['object', 'estimate', 'work']
```

### Frontend TypeScript Types

```typescript
// types/models.ts
export interface User {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
}

export interface Counterparty {
  id: number;
  name: string;
  inn?: string;
  contact_person?: string;
  phone?: string;
  parent_id?: number;
  marked_for_deletion: boolean;
}

export interface Estimate {
  id: number;
  number: string;
  date: string;
  customer_id?: number;
  object_id?: number;
  contractor_id?: number;
  responsible_id?: number;
  total_sum: number;
  total_labor: number;
  is_posted: boolean;
  posted_at?: string;
  created_at: string;
  modified_at: string;
  lines: EstimateLine[];
  
  // Display fields
  customer_name?: string;
  object_name?: string;
  contractor_name?: string;
  responsible_name?: string;
}

export interface EstimateLine {
  id: number;
  estimate_id: number;
  line_number: number;
  work_id?: number;
  quantity: number;
  unit?: string;
  price: number;
  labor_rate: number;
  sum: number;
  planned_labor: number;
  is_group: boolean;
  group_name?: string;
  parent_group_id?: number;
  work_name?: string;
}

// Similar interfaces for other entities
```



## Error Handling

### Backend Error Handling

**HTTP Status Codes**:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Error Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "number",
        "message": "Field is required"
      }
    ]
  }
}
```

**Error Categories**:
1. **Authentication Errors**: Invalid credentials, expired token
2. **Validation Errors**: Invalid input data, missing required fields
3. **Business Logic Errors**: Document already posted, insufficient permissions
4. **Database Errors**: Constraint violations, connection issues
5. **System Errors**: Unexpected exceptions

**Error Handling Strategy**:
- Use FastAPI exception handlers for consistent error responses
- Log all errors with context for debugging
- Return user-friendly messages in Russian
- Include error codes for frontend handling
- Never expose sensitive information in error messages

### Frontend Error Handling

**Error Display**:
- Toast notifications for transient errors
- Inline validation messages for form errors
- Modal dialogs for critical errors
- Network error banner for connectivity issues

**Error Recovery**:
- Automatic token refresh on 401 errors
- Retry logic for network failures (max 3 attempts)
- Optimistic updates with rollback on failure
- Form state preservation on validation errors

**Offline Handling**:
- Detect network connectivity status
- Show offline indicator in UI
- Queue mutations for later sync (future enhancement)
- Cache reference data for offline viewing



## Security Design

### Authentication & Authorization

**Password Security**:
- Passwords hashed using bcrypt with salt (cost factor: 12)
- Never store or transmit plain text passwords
- Minimum password length: 8 characters (enforced in UI and API)

**JWT Token Security**:
- Tokens signed with HS256 algorithm
- Secret key stored in environment variable (not in code)
- Token payload includes: user_id, username, role, exp, iat
- Tokens expire after 8 hours (Requirement 1.4)
- No sensitive data in token payload

**Session Management**:
- Tokens stored in localStorage (accessible only to same origin)
- Automatic logout on token expiration
- Inactive session timeout: 30 minutes (Requirement 11.5)
- Activity tracking via API calls

**Authorization Levels**:
- `admin`: Full access to all features
- `user`: Read/write access to documents and references
- `viewer`: Read-only access (future enhancement)

**Permission Checks**:
- Backend validates permissions on every request
- Frontend hides UI elements based on user role
- Document posting restricted to admin role (Requirement 6.5)

### API Security

**HTTPS Enforcement** (Requirement 11.1):
- All production traffic over HTTPS
- HTTP Strict Transport Security (HSTS) header
- Redirect HTTP to HTTPS in production

**CORS Configuration**:
- Whitelist specific origins (no wildcard in production)
- Allow credentials for cookie/token handling
- Restrict allowed methods and headers

**Input Validation** (Requirement 11.3):
- Pydantic models validate all request data
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- File upload validation (size, type, content)

**Rate Limiting**:
- Limit login attempts: 5 per minute per IP
- API rate limit: 100 requests per minute per user
- Prevent brute force attacks

**SQL Injection Prevention**:
- Use SQLite parameterized queries exclusively
- Never concatenate user input into SQL strings
- Existing repositories already follow this pattern

**XSS Prevention**:
- Vue.js automatically escapes output
- Sanitize HTML input if rich text is needed
- Content Security Policy (CSP) headers

### Data Security

**Database Access**:
- API server has exclusive database access
- No direct database connections from web clients
- Transaction isolation for concurrent access

**Sensitive Data**:
- Password hashes never returned in API responses
- User PII protected by authentication
- Audit log for sensitive operations (future enhancement)

**Backup & Recovery**:
- Regular SQLite database backups
- Backup before schema migrations
- Point-in-time recovery capability



## Performance Optimization

### Backend Performance

**Database Optimization** (Requirement 12.5):
- Existing indices on frequently queried columns
- Additional indices for API queries:
  - `estimates(customer_id, object_id, date)`
  - `daily_reports(estimate_id, date)`
  - `work_execution_register(period, object_id, estimate_id, work_id)`
- Query optimization for joins with reference tables
- Connection pooling for concurrent requests

**Pagination** (Requirement 12.2):
- Default page size: 50 items
- Maximum page size: 100 items
- Offset-based pagination for simplicity
- Return total count for pagination UI

**Caching Strategy**:
- Reference data cached in memory (TTL: 5 minutes)
- Cache invalidation on reference updates
- ETag support for conditional requests
- Browser caching for static assets

**Response Optimization**:
- Compress responses with gzip
- Minimize JSON payload size
- Lazy load document lines (separate endpoint)
- Partial updates for large documents

### Frontend Performance

**Initial Load Optimization**:
- Code splitting by route
- Lazy load non-critical components
- Minimize bundle size (<500KB gzipped)
- Preload critical resources

**Runtime Performance**:
- Virtual scrolling for large tables (>100 rows)
- Debounced search input (300ms delay) (Requirement 12.4)
- Throttled scroll/resize handlers
- Memoized computed properties

**Data Management** (Requirement 12.3):
- Cache reference data in Pinia store
- Invalidate cache on updates
- Optimistic UI updates
- Background data refresh

**Mobile Performance**:
- Reduce network requests on mobile
- Compress images and assets
- Use native mobile inputs
- Minimize JavaScript execution

**Performance Targets** (Requirement 12.1):
- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- API response time: <500ms (p95)
- List view render: <2s for 50 items



## Testing Strategy

### Backend Testing

**Unit Tests**:
- Test API endpoints with mock repositories
- Test authentication service (token generation, validation)
- Test Pydantic model validation
- Test error handling and edge cases
- Coverage target: >80%

**Integration Tests**:
- Test API endpoints with real database
- Test document posting workflow
- Test concurrent access scenarios
- Test print form generation

**Test Tools**:
- pytest for test framework
- pytest-asyncio for async tests
- httpx for API client testing
- SQLite in-memory database for tests

**Test Data**:
- Fixtures for common test scenarios
- Factory functions for model creation
- Separate test database

### Frontend Testing

**Unit Tests**:
- Test composables and utilities
- Test Pinia stores
- Test API client functions
- Coverage target: >70%

**Component Tests**:
- Test Vue components in isolation
- Test user interactions
- Test form validation
- Test responsive behavior

**E2E Tests**:
- Test critical user flows:
  - Login and authentication
  - Create and edit estimate
  - Create and edit daily report
  - Document posting
  - Print form generation
- Test on multiple browsers
- Test on mobile viewport

**Test Tools**:
- Vitest for unit tests
- Vue Test Utils for component tests
- Playwright for E2E tests
- Mock Service Worker for API mocking

### Manual Testing

**Browser Compatibility**:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

**Device Testing**:
- Desktop (1920x1080, 1366x768)
- Tablet (iPad, Android tablet)
- Mobile (iPhone, Android phone)
- Test portrait and landscape orientations

**Accessibility Testing**:
- Keyboard navigation
- Screen reader compatibility
- Color contrast (WCAG AA)
- Focus indicators



## Deployment Architecture

### Development Environment

**Backend**:
```bash
# Run FastAPI with hot reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
# Run Vite dev server with hot reload
npm run dev
# Proxy API requests to backend
```

**Database**:
- Use existing `construction.db` SQLite file
- Shared with desktop client for testing compatibility

### Production Deployment

**Deployment Options**:

**Option 1: Single Server (Recommended for MVP)**
```
┌─────────────────────────────────────┐
│         Single Server               │
│  ┌──────────────────────────────┐  │
│  │   Nginx (Reverse Proxy)      │  │
│  │   - Serve static files       │  │
│  │   - Proxy /api to FastAPI    │  │
│  │   - SSL termination          │  │
│  └──────────────────────────────┘  │
│              │                      │
│  ┌──────────────────────────────┐  │
│  │   FastAPI (Uvicorn)          │  │
│  │   - Multiple workers         │  │
│  │   - Process manager (systemd)│  │
│  └──────────────────────────────┘  │
│              │                      │
│  ┌──────────────────────────────┐  │
│  │   SQLite Database            │  │
│  │   - File-based storage       │  │
│  │   - Regular backups          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Option 2: Cloud Deployment (Future)**
- Frontend: Static hosting (Netlify, Vercel, S3+CloudFront)
- Backend: Container service (AWS ECS, Google Cloud Run)
- Database: Migrate to PostgreSQL for better concurrency

**Server Requirements**:
- OS: Ubuntu 20.04+ or Windows Server 2019+
- CPU: 2 cores minimum
- RAM: 4GB minimum
- Storage: 20GB minimum (SSD recommended)
- Network: Static IP, open ports 80/443

**Process Management**:
- systemd service for FastAPI
- Automatic restart on failure
- Log rotation
- Health check endpoint

**SSL Certificate**:
- Let's Encrypt for free SSL
- Automatic renewal
- HTTPS redirect

**Backup Strategy**:
- Daily SQLite database backup
- Retain backups for 30 days
- Backup before updates
- Test restore procedure

### Configuration Management

**Environment Variables**:
```bash
# .env file (not committed to git)
DATABASE_PATH=/path/to/construction.db
JWT_SECRET_KEY=<random-secret-key>
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
```

**Configuration Files**:
- `api/config.py`: Backend configuration
- `web-client/.env.production`: Frontend build config
- `nginx.conf`: Web server configuration



## Desktop-Web Compatibility

### Shared Database Design

**Concurrent Access Strategy**:
- SQLite WAL (Write-Ahead Logging) mode enabled
- Supports multiple readers and one writer
- Desktop and web clients can read simultaneously
- Writes are serialized automatically by SQLite

**Transaction Management**:
- Use explicit transactions for multi-statement operations
- Keep transactions short to minimize lock contention
- Retry logic for SQLITE_BUSY errors
- Timeout: 5 seconds for lock acquisition

**Schema Compatibility**:
- No schema changes required for web client
- Existing tables and columns used as-is
- Database migrations handled by DatabaseManager
- Both clients use same migration logic

**Data Synchronization**:
- No real-time sync in MVP
- Desktop client: Manual refresh to see web changes
- Web client: Automatic refresh on page load
- Future: WebSocket notifications for real-time updates

### Code Reuse Strategy

**Reused Components**:
- `DatabaseManager`: Database connection and schema management
- All repositories: `EstimateRepository`, `ReferenceRepository`, `UserRepository`, etc.
- All services: `DocumentPostingService`, `PrintFormService`, etc.
- Business logic: Validation, calculations, posting rules

**API Integration Layer**:
```python
# api/dependencies.py
def get_db():
    """Dependency for database access"""
    return DatabaseManager().get_connection()

def get_estimate_repository():
    """Dependency for estimate repository"""
    return EstimateRepository()

# api/endpoints/estimates.py
@router.get("/estimates/{id}")
async def get_estimate(
    id: int,
    repo: EstimateRepository = Depends(get_estimate_repository)
):
    estimate = repo.get_by_id(id)
    if not estimate:
        raise HTTPException(404, "Estimate not found")
    return estimate
```

**No Modifications Required**:
- Existing repositories return dict/Row objects
- Pydantic models convert to JSON automatically
- No changes to business logic
- No changes to database schema

### Migration Path

**Phase 1: MVP (Web Client Basics)**
- Authentication and session management
- Reference management (view, create, edit)
- Estimate management (view, create, edit)
- Daily report management (view, create, edit)
- Basic responsive design

**Phase 2: Feature Parity**
- Document posting
- Print forms (PDF and Excel)
- Register views
- Advanced search and filtering
- Full mobile optimization

**Phase 3: Web-Specific Features**
- Real-time collaboration
- Offline support with sync
- Mobile app (PWA or native)
- Advanced analytics dashboard
- Bulk operations

**Phase 4: Migration (Optional)**
- Migrate to PostgreSQL for better concurrency
- Deprecate desktop client (if desired)
- Cloud deployment
- Multi-tenant support



## Responsive Design Specifications

### Breakpoints

```css
/* Mobile First Approach */
$mobile: 320px;      /* Small phones */
$mobile-lg: 480px;   /* Large phones */
$tablet: 768px;      /* Tablets */
$desktop: 1024px;    /* Small desktops */
$desktop-lg: 1440px; /* Large desktops */
```

### Layout Adaptations

**Mobile (<768px)** (Requirement 8.2, 8.3):
- Single column layout
- Hamburger menu for navigation
- Card-based list views instead of tables
- Full-width forms
- Bottom navigation bar for primary actions
- Collapsible sections to save space
- Touch-friendly buttons (min 44x44px)

**Tablet (768-1024px)**:
- Two-column layout where appropriate
- Sidebar navigation (collapsible)
- Condensed table views
- Side-by-side forms for related fields
- Floating action button for primary actions

**Desktop (>1024px)**:
- Multi-column layout
- Persistent sidebar navigation
- Full table views with all columns
- Multi-column forms
- Toolbar with all actions visible

### Touch Optimization (Requirement 8.4)

**Gestures**:
- Swipe left/right: Navigate between tabs
- Pull down: Refresh list
- Long press: Show context menu
- Pinch zoom: Zoom tables (if needed)

**Controls**:
- Minimum touch target: 44x44px
- Adequate spacing between controls (8px minimum)
- Large, easy-to-tap buttons
- Swipeable list items for actions

**Input Types** (Requirement 8.5):
```html
<!-- Numeric keyboard for numbers -->
<input type="number" inputmode="numeric" />

<!-- Date picker for dates -->
<input type="date" />

<!-- Telephone keyboard for phones -->
<input type="tel" />

<!-- Email keyboard for emails -->
<input type="email" />

<!-- Search keyboard with search button -->
<input type="search" />
```

### Component Responsive Behavior

**DataTable Component**:
- Desktop: Full table with all columns
- Tablet: Hide less important columns
- Mobile: Card layout with key information

**Form Components**:
- Desktop: Multi-column layout
- Tablet: Two-column layout
- Mobile: Single column, full width

**Navigation**:
- Desktop: Persistent sidebar
- Tablet: Collapsible sidebar
- Mobile: Drawer menu with overlay

**Modals**:
- Desktop: Centered modal (max-width: 800px)
- Tablet: Centered modal (max-width: 90%)
- Mobile: Full-screen modal

### Performance on Mobile

**Network Optimization**:
- Reduce image sizes for mobile
- Lazy load images
- Compress API responses
- Minimize API calls

**Rendering Optimization**:
- Virtual scrolling for long lists
- Debounced input handlers
- Throttled scroll handlers
- Minimize DOM updates

**Battery Optimization**:
- Reduce animation on low battery
- Pause background tasks when inactive
- Minimize network polling



## Print Form Integration

### Print Form Architecture

**Backend Integration**:
- Reuse existing `PrintFormService` class
- Reuse existing print form generators:
  - `EstimatePrintForm` (PDF/АРСД)
  - `DailyReportPrintForm` (PDF/АРСД)
  - `ExcelEstimatePrintForm` (Excel)
  - `ExcelDailyReportPrintForm` (Excel)

**API Endpoints**:
```python
@router.get("/estimates/{id}/print")
async def print_estimate(
    id: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    print_service: PrintFormService = Depends(get_print_service)
):
    """Generate estimate print form"""
    if format == "excel":
        result = print_service.generate_estimate_excel(id)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"estimate_{id}.xlsx"
    else:
        result = print_service.generate_estimate_pdf(id)
        media_type = "application/pdf"
        filename = f"estimate_{id}.pdf"
    
    if not result:
        raise HTTPException(404, "Failed to generate print form")
    
    return Response(
        content=result,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

**Frontend Implementation**:
```typescript
// api/documents.ts
export async function printEstimate(id: number, format: 'pdf' | 'excel') {
  const response = await apiClient.get(
    `/api/documents/estimates/${id}/print`,
    {
      params: { format },
      responseType: 'blob'
    }
  );
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `estimate_${id}.${format === 'excel' ? 'xlsx' : 'pdf'}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
```

**Format Selection UI** (Requirement 7.4):
- Dropdown or radio buttons for format selection
- Remember user's last choice
- Show preview option (open in new tab for PDF)
- Download option for both formats

**Cyrillic Support** (Requirement 7.5):
- Existing print forms already support Cyrillic
- Use DejaVu Sans font for PDF
- Excel uses system fonts (automatic Cyrillic support)

### Print Form Features

**Estimate Print Form**:
- Header: Number, date, customer, object, contractor, responsible
- Lines: Work name, unit, quantity, price, sum, labor
- Groups: Hierarchical structure with subtotals
- Footer: Total sum, total labor
- АРСД format compliance

**Daily Report Print Form**:
- Header: Date, estimate, foreman
- Lines: Work name, planned labor, actual labor, deviation
- Executors: List of workers per line
- Groups: Hierarchical structure
- Footer: Total labor

**Print Settings**:
- Page size: A4
- Orientation: Portrait (default) or Landscape
- Margins: Configurable
- Font size: Configurable
- Logo: Optional company logo



## Register and Reporting

### Work Execution Register

**Data Model**:
- Accumulation register with income/expense movements
- Dimensions: period, object, estimate, work
- Resources: quantity, sum
- Recorder: estimate or daily_report

**Query API**:
```python
@router.get("/registers/work-execution")
async def query_work_execution(
    period_from: Optional[date] = None,
    period_to: Optional[date] = None,
    object_id: Optional[int] = None,
    estimate_id: Optional[int] = None,
    work_id: Optional[int] = None,
    group_by: Optional[str] = None,  # comma-separated: object,estimate,work
    page: int = 1,
    page_size: int = 50,
    repo: WorkExecutionRegisterRepository = Depends(get_register_repo)
):
    """Query work execution register with filtering and grouping"""
    movements = repo.query(
        period_from=period_from,
        period_to=period_to,
        object_id=object_id,
        estimate_id=estimate_id,
        work_id=work_id
    )
    
    if group_by:
        movements = repo.group_by(movements, group_by.split(','))
    
    # Paginate
    total = len(movements)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "success": True,
        "data": movements[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }
```

**Frontend Register View** (Requirement 9):
- Filter panel: Date range, object, estimate, work
- Grouping options: By object, by estimate, by work
- Table view with columns:
  - Period
  - Object
  - Estimate
  - Work
  - Quantity Income
  - Quantity Expense
  - Sum Income
  - Sum Expense
  - Balance (Income - Expense)
- Totals row at bottom
- Export to Excel option

**Grouping Logic** (Requirement 9.3):
```typescript
// Group by dimensions
interface GroupedMovement {
  object_name?: string;
  estimate_number?: string;
  work_name?: string;
  quantity_income: number;
  quantity_expense: number;
  sum_income: number;
  sum_expense: number;
  balance_quantity: number;
  balance_sum: number;
}

// Frontend aggregation
function groupMovements(
  movements: Movement[],
  groupBy: ('object' | 'estimate' | 'work')[]
): GroupedMovement[] {
  // Group and sum by selected dimensions
  // Calculate balances
}
```

### Analytical Reports (Future Enhancement)

**Planned Reports**:
1. Work execution by object (plan vs actual)
2. Labor efficiency by foreman
3. Cost analysis by work type
4. Timeline analysis (Gantt chart)
5. Resource utilization

**Report Features**:
- Interactive charts (Chart.js or similar)
- Drill-down capability
- Export to PDF/Excel
- Scheduled email delivery



## Development Workflow

### Project Setup

**Backend Setup**:
```bash
# Create API directory structure
mkdir -p api/{endpoints,models,services,middleware,dependencies}

# Install dependencies
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart

# Create main application
# api/main.py - FastAPI app with CORS, auth middleware

# Run development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup**:
```bash
# Create Vue.js project with TypeScript
npm create vue@latest web-client
# Select: TypeScript, Router, Pinia, ESLint, Prettier

cd web-client
npm install

# Install additional dependencies
npm install axios @vueuse/core

# Configure Vite proxy for API
# vite.config.ts - proxy /api to http://localhost:8000

# Run development server
npm run dev
```

### Development Process

**Backend Development**:
1. Define Pydantic models for request/response
2. Create endpoint in appropriate router
3. Add dependency injection for repositories/services
4. Implement business logic (reuse existing services)
5. Add error handling
6. Write unit tests
7. Test with Swagger UI (auto-generated)

**Frontend Development**:
1. Define TypeScript types for models
2. Create API client functions
3. Create/update Pinia store if needed
4. Create Vue component
5. Add routing if new page
6. Implement responsive design
7. Add error handling
8. Write component tests

**Integration Testing**:
1. Start backend server
2. Start frontend dev server
3. Test full user flows
4. Test on different devices/browsers
5. Test with desktop client (database compatibility)

### Code Organization

**Backend Structure**:
```
api/
├── main.py                 # FastAPI app initialization
├── config.py               # Configuration management
├── dependencies.py         # Dependency injection
├── models/                 # Pydantic models
│   ├── auth.py
│   ├── references.py
│   └── documents.py
├── endpoints/              # API endpoints
│   ├── auth.py
│   ├── references.py
│   ├── documents.py
│   └── registers.py
├── services/               # Business logic (reuse existing)
│   └── auth_service.py     # New authentication service
├── middleware/             # Custom middleware
│   ├── auth.py
│   └── error_handler.py
└── tests/                  # Backend tests
    ├── test_auth.py
    ├── test_references.py
    └── test_documents.py
```

**Frontend Structure** (already defined in Components section)

### Version Control

**Git Workflow**:
- `main` branch: Production-ready code
- `develop` branch: Integration branch
- Feature branches: `feature/web-client-auth`, `feature/web-client-estimates`
- Commit messages: Conventional commits format

**Code Review**:
- Pull requests required for all changes
- At least one approval required
- Automated tests must pass
- Code coverage must not decrease



## Design Decisions and Rationales

### Key Design Decisions

#### 1. FastAPI vs Flask vs Django

**Decision**: Use FastAPI

**Rationale**:
- Modern async support for better performance
- Automatic API documentation (OpenAPI/Swagger)
- Built-in request validation with Pydantic
- Better type hints and IDE support
- Smaller and faster than Django
- More structured than Flask for APIs

#### 2. Vue.js vs React vs Angular

**Decision**: Use Vue.js 3

**Rationale**:
- Easier learning curve for team
- Excellent documentation in multiple languages
- Great mobile performance
- Smaller bundle size than Angular
- More opinionated than React (faster development)
- Strong TypeScript support
- Composition API similar to React hooks

#### 3. JWT vs Session-based Authentication

**Decision**: Use JWT tokens

**Rationale**:
- Stateless authentication (no server-side session storage)
- Works well with mobile apps
- Easy to scale horizontally
- Standard approach for REST APIs
- Can include user info in token payload
- No database lookup on every request

#### 4. SQLite vs PostgreSQL

**Decision**: Keep SQLite for MVP, plan PostgreSQL migration

**Rationale**:
- **SQLite Advantages**:
  - Zero configuration
  - File-based (easy backup)
  - Compatible with desktop client
  - Sufficient for small teams (<10 concurrent users)
  - No additional infrastructure
  
- **PostgreSQL for Future**:
  - Better concurrent write performance
  - More robust for production
  - Better for cloud deployment
  - Advanced features (full-text search, JSON)

#### 5. Monorepo vs Separate Repositories

**Decision**: Separate directories in same repo

**Rationale**:
- Easier to manage related changes
- Shared documentation
- Single version control
- Simpler deployment
- Can split later if needed

#### 6. Server-Side Rendering vs Client-Side Rendering

**Decision**: Client-Side Rendering (SPA)

**Rationale**:
- Better user experience (no page reloads)
- Easier to make responsive
- Simpler deployment (static files)
- Better for mobile app conversion (PWA)
- API can be used by other clients

#### 7. Real-time Updates vs Polling vs Manual Refresh

**Decision**: Manual refresh for MVP, WebSocket for future

**Rationale**:
- Simpler implementation for MVP
- Lower server resource usage
- Sufficient for current use case
- Can add WebSocket later for real-time collaboration

#### 8. Optimistic Updates vs Pessimistic Updates

**Decision**: Optimistic updates with rollback

**Rationale**:
- Better perceived performance
- Immediate UI feedback
- Better mobile experience
- Rollback on error maintains consistency

#### 9. Inline Editing vs Modal Forms

**Decision**: Modal forms for complex entities, inline for simple fields

**Rationale**:
- Modals provide focus and context
- Inline editing for quick changes (e.g., quantity)
- Consistent with desktop client patterns
- Better mobile experience with modals

#### 10. Custom UI Components vs Component Library

**Decision**: Custom components with Tailwind CSS

**Rationale**:
- Full control over styling
- Smaller bundle size
- Easier to make responsive
- Match desktop client look and feel
- No learning curve for third-party library

### Trade-offs and Limitations

**SQLite Limitations**:
- Limited concurrent writes (one writer at a time)
- No built-in replication
- File-based (harder to scale horizontally)
- **Mitigation**: Plan PostgreSQL migration for growth

**JWT Limitations**:
- Cannot revoke tokens before expiration
- Token size larger than session ID
- **Mitigation**: Short expiration time (8 hours), token blacklist for future

**Client-Side Rendering Limitations**:
- Slower initial page load
- SEO challenges (not relevant for this app)
- **Mitigation**: Code splitting, lazy loading

**No Real-time Updates**:
- Users must refresh to see changes from other clients
- **Mitigation**: Auto-refresh on focus, WebSocket for future

**No Offline Support**:
- Requires internet connection
- **Mitigation**: PWA with service worker for future



## Future Enhancements

### Phase 1 Enhancements (Post-MVP)

**Real-time Collaboration**:
- WebSocket connection for live updates
- Show who is editing what document
- Conflict resolution for concurrent edits
- Presence indicators

**Offline Support**:
- Progressive Web App (PWA)
- Service worker for offline caching
- IndexedDB for local data storage
- Sync queue for offline changes
- Background sync when online

**Advanced Search**:
- Full-text search across all entities
- Saved search filters
- Recent searches
- Search suggestions

**Bulk Operations**:
- Multi-select in tables
- Bulk edit
- Bulk delete
- Bulk export

### Phase 2 Enhancements

**Mobile Native App**:
- React Native or Flutter app
- Native mobile features (camera, GPS)
- Push notifications
- Offline-first architecture

**Advanced Analytics**:
- Interactive dashboards
- Custom report builder
- Data visualization (charts, graphs)
- Export to various formats

**Workflow Automation**:
- Document approval workflows
- Email notifications
- Scheduled reports
- Automated backups

**Multi-language Support**:
- Internationalization (i18n)
- Support for English, Russian, others
- User language preference

### Phase 3 Enhancements

**Multi-tenant Support**:
- Separate data per organization
- Organization management
- User invitations
- Role-based access control per organization

**API for Third-party Integration**:
- Public API documentation
- API keys for external access
- Webhooks for events
- OAuth2 for third-party apps

**Advanced Document Features**:
- Document templates
- Document versioning
- Document comparison
- Audit trail

**Performance Monitoring**:
- Application performance monitoring (APM)
- Error tracking (Sentry)
- User analytics
- Performance metrics dashboard

## Conclusion

This design provides a solid foundation for a web-based client that complements the existing desktop application. The architecture prioritizes:

1. **Reusability**: Leveraging existing business logic and database schema
2. **Compatibility**: Seamless interoperability with desktop client
3. **Scalability**: Clear migration path to more robust infrastructure
4. **User Experience**: Mobile-first responsive design
5. **Security**: Industry-standard authentication and authorization
6. **Performance**: Optimized for fast load times and smooth interactions

The phased approach allows for incremental development and validation, starting with core features and expanding based on user feedback and business needs.


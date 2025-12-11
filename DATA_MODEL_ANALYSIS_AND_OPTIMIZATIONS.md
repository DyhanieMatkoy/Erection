# Data Model Analysis & Optimization Recommendations

## Executive Summary

This document analyzes the data model architecture for both desktop (Qt6/Python) and mobile (Vue.js/TypeScript) versions of the construction management system, identifying optimization opportunities for performance, scalability, and maintainability.

---

## 1. Current Architecture Overview

### 1.1 Three-Tier Architecture

**Desktop Application (Qt6/Python)**
- **Data Layer**: SQLAlchemy ORM models (`src/data/models/`)
- **Business Logic**: Services layer (`src/services/`)
- **Presentation**: ViewModels + Qt Views (`src/viewmodels/`, `src/views/`)

**Web Application (Vue.js/TypeScript)**
- **Backend API**: FastAPI with Pydantic models (`api/models/`)
- **Frontend**: Vue 3 + TypeScript with Pinia stores (`web-client/src/`)
- **Communication**: REST API with JSON serialization

### 1.2 Database Support
- SQLite (development/single-user)
- PostgreSQL (production/multi-user)
- Microsoft SQL Server (enterprise)

---

## 2. Data Model Structure

### 2.1 Core Entities

#### Reference Data (Справочники)
```
├── Person (employees, foremen)
├── Organization (contractors, companies)
├── Counterparty (customers, suppliers)
├── Object (construction sites)
├── Work (work types)
├── CostItem (cost elements) - NEW
├── Material (materials catalog) - NEW
└── Unit (measurement units) - NEW
```

#### Documents (Документы)
```
├── Estimate (сметы)
│   └── EstimateLine[]
├── DailyReport (ежедневные отчеты)
│   └── DailyReportLine[]
│       └── DailyReportExecutor[] (many-to-many)
└── Timesheet (табели)
    └── TimesheetLine[]
```

#### Registers (Регистры накопления)
```
├── WorkExecutionRegister (выполнение работ)
└── PayrollRegister (начисления зарплаты)
```

---

## 3. Data Model Issues & Optimization Opportunities

### 3.1 🔴 CRITICAL: Timesheet Day Columns Anti-Pattern

**Current Implementation:**
```python
class TimesheetLine(Base):
    day_01 = Column(Float, default=0.0)
    day_02 = Column(Float, default=0.0)
    # ... 31 columns total
    day_31 = Column(Float, default=0.0)
```

**Problems:**
- ❌ Violates database normalization (1NF)
- ❌ Inflexible schema (always 31 columns regardless of month)
- ❌ Difficult to query (e.g., "find all days with >8 hours")
- ❌ Poor indexing performance
- ❌ Wastes storage space
- ❌ Complex aggregation queries

**Recommended Solution:**
```python
class TimesheetDayEntry(Base):
    """Normalized timesheet day entries"""
    __tablename__ = 'timesheet_day_entries'
    
    id = Column(Integer, primary_key=True)
    timesheet_line_id = Column(Integer, ForeignKey('timesheet_lines.id'))
    day_number = Column(Integer, nullable=False)  # 1-31
    hours_worked = Column(Float, default=0.0)
    
    __table_args__ = (
        Index('idx_timesheet_day', 'timesheet_line_id', 'day_number'),
        UniqueConstraint('timesheet_line_id', 'day_number'),
    )
```

**Benefits:**
- ✅ Proper normalization
- ✅ Flexible for any month length
- ✅ Easy to query and aggregate
- ✅ Better indexing
- ✅ Reduced storage for partial months

**Migration Strategy:**
1. Create new `timesheet_day_entries` table
2. Migrate existing data: `INSERT INTO timesheet_day_entries SELECT ...`
3. Update application code to use new structure
4. Drop old day_XX columns after validation

---

### 3.2 🟡 MEDIUM: Duplicate Data in API Models

**Issue:** Frontend TypeScript models duplicate backend Pydantic models

**Current State:**
- `api/models/documents.py` (Pydantic)
- `web-client/src/types/models.ts` (TypeScript)
- Manual synchronization required
- Risk of inconsistency

**Recommended Solution:**

**Option A: Code Generation**
```bash
# Generate TypeScript from Pydantic models
pip install pydantic-to-typescript
pydantic2ts --module api.models --output web-client/src/types/generated.ts
```

**Option B: OpenAPI/JSON Schema**
```python
# FastAPI automatically generates OpenAPI schema
# Use openapi-typescript to generate types
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api-schema.ts
```

**Benefits:**
- ✅ Single source of truth
- ✅ Automatic synchronization
- ✅ Reduced maintenance
- ✅ Type safety guaranteed

---

### 3.3 🟡 MEDIUM: Missing Indexes

**Current Issues:**
- Some foreign keys lack indexes
- Composite queries not optimized
- Register queries can be slow

**Recommended Indexes:**

```python
# Add to EstimateLine
__table_args__ = (
    Index('idx_estimate_work', 'estimate_id', 'work_id'),
    Index('idx_estimate_line_number', 'estimate_id', 'line_number'),
)

# Add to DailyReportLine
__table_args__ = (
    Index('idx_report_work', 'report_id', 'work_id'),
    Index('idx_report_line_number', 'report_id', 'line_number'),
)

# Add to Person
__table_args__ = (
    Index('idx_person_user', 'user_id'),
    Index('idx_person_parent', 'parent_id'),
)

# Add to Object
__table_args__ = (
    Index('idx_object_owner', 'owner_id'),
)
```

---

### 3.4 🟢 LOW: Soft Delete Inconsistency

**Issue:** Mixed naming conventions
- `marked_for_deletion` (most tables)
- `is_deleted` (some reference tables)

**Recommendation:**
Standardize on `marked_for_deletion` everywhere for consistency.

```sql
-- Migration
ALTER TABLE counterparties RENAME COLUMN is_deleted TO marked_for_deletion;
ALTER TABLE objects RENAME COLUMN is_deleted TO marked_for_deletion;
ALTER TABLE persons RENAME COLUMN is_deleted TO marked_for_deletion;
```

---

### 3.5 🟡 MEDIUM: Missing Audit Trail

**Current State:**
- `created_at` and `modified_at` exist
- No tracking of WHO made changes
- No change history

**Recommended Enhancement:**

```python
class AuditMixin:
    """Mixin for audit trail"""
    created_at = Column(DateTime, default=func.now())
    created_by_id = Column(Integer, ForeignKey('users.id'))
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by_id = Column(Integer, ForeignKey('users.id'))
    
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

# Optional: Full audit log table
class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=func.now())
    old_values = Column(JSON)
    new_values = Column(JSON)
```

---

### 3.6 🟢 LOW: Redundant Computed Fields

**Issue:** Some computed fields stored in database
- `total_sum` in Estimate (can be calculated from lines)
- `total_labor` in Estimate
- `total_hours` in TimesheetLine
- `total_amount` in TimesheetLine

**Options:**

**Option A: Remove and compute on-the-fly**
```python
@property
def total_sum(self):
    return sum(line.sum for line in self.lines)
```

**Option B: Keep but use database triggers**
```sql
CREATE TRIGGER update_estimate_totals
AFTER INSERT OR UPDATE OR DELETE ON estimate_lines
FOR EACH ROW
BEGIN
    UPDATE estimates
    SET total_sum = (SELECT SUM(sum) FROM estimate_lines WHERE estimate_id = NEW.estimate_id),
        total_labor = (SELECT SUM(planned_labor) FROM estimate_lines WHERE estimate_id = NEW.estimate_id)
    WHERE id = NEW.estimate_id;
END;
```

**Recommendation:** Keep stored values for performance, but ensure consistency with triggers or application-level updates.

---

## 4. Mobile-Specific Optimizations

### 4.1 🔴 CRITICAL: Reduce Payload Size

**Current Issue:** Full document objects with all nested data

**Recommendations:**

#### A. Implement Field Selection
```typescript
// API endpoint
GET /api/estimates?fields=id,number,date,total_sum

// Response
{
  "data": [
    {"id": 1, "number": "EST-001", "date": "2024-01-15", "total_sum": 50000}
  ]
}
```

#### B. Pagination for Large Lists
```typescript
// Already implemented, but ensure consistent usage
interface PaginationParams {
  page: number
  page_size: number  // Recommend: 20 for mobile, 50 for desktop
  search?: string
}
```

#### C. Lazy Loading for Document Lines
```typescript
// Don't load lines by default
GET /api/estimates/123  // Returns estimate without lines
GET /api/estimates/123/lines  // Separate endpoint for lines
```

---

### 4.2 🟡 MEDIUM: Implement Caching Strategy

**Recommendations:**

#### A. Backend Caching (Redis)
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Cache reference data (rarely changes)
@cache(expire=3600)  # 1 hour
async def get_works():
    return await work_repository.get_all()
```

#### B. Frontend Caching (Pinia)
```typescript
// Store reference data in Pinia with TTL
export const useReferenceStore = defineStore('reference', {
  state: () => ({
    works: [] as Work[],
    worksLastFetched: null as Date | null,
  }),
  actions: {
    async fetchWorks(force = false) {
      const cacheValid = this.worksLastFetched && 
        (Date.now() - this.worksLastFetched.getTime()) < 3600000
      
      if (!force && cacheValid) return
      
      this.works = await api.getWorks()
      this.worksLastFetched = new Date()
    }
  }
})
```

#### C. HTTP Caching Headers
```python
from fastapi import Response

@app.get("/api/works")
async def get_works(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return await work_repository.get_all()
```

---

### 4.3 🟡 MEDIUM: Offline Support

**Recommendation:** Implement Progressive Web App (PWA) with IndexedDB

```typescript
// Service Worker for offline caching
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request)
    })
  )
})

// IndexedDB for offline data storage
import { openDB } from 'idb'

const db = await openDB('construction-db', 1, {
  upgrade(db) {
    db.createObjectStore('estimates', { keyPath: 'id' })
    db.createObjectStore('daily_reports', { keyPath: 'id' })
  }
})

// Sync when online
window.addEventListener('online', async () => {
  const pendingChanges = await db.getAll('pending_changes')
  for (const change of pendingChanges) {
    await api.sync(change)
  }
})
```

---

### 4.4 🟢 LOW: Optimize Images and Assets

**Recommendations:**
- Use WebP format for images
- Implement lazy loading for images
- Use SVG for icons (already using?)
- Enable gzip/brotli compression

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'ui': ['primevue']
        }
      }
    }
  }
})
```

---

## 5. Desktop-Specific Optimizations

### 5.1 🟡 MEDIUM: Connection Pooling

**Current:** SQLAlchemy with default settings

**Recommendation:**
```python
# src/data/database_manager.py
engine = create_engine(
    connection_string,
    pool_size=10,  # Increase for desktop
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600,  # Recycle after 1 hour
    echo=False  # Disable in production
)
```

---

### 5.2 🟢 LOW: Eager Loading for Related Data

**Issue:** N+1 query problem

**Current:**
```python
estimates = session.query(Estimate).all()
for estimate in estimates:
    print(estimate.customer.name)  # N additional queries!
```

**Optimized:**
```python
from sqlalchemy.orm import joinedload

estimates = session.query(Estimate)\
    .options(
        joinedload(Estimate.customer),
        joinedload(Estimate.object),
        joinedload(Estimate.contractor),
        joinedload(Estimate.responsible)
    )\
    .all()
```

---

### 5.3 🟡 MEDIUM: Batch Operations

**Recommendation:** Implement bulk insert/update

```python
# Instead of:
for line in lines:
    session.add(EstimateLine(**line))
session.commit()

# Use:
session.bulk_insert_mappings(EstimateLine, lines)
session.commit()
```

---

## 6. Cross-Platform Optimizations

### 6.1 🔴 CRITICAL: API Response Standardization

**Current:** Inconsistent response formats

**Recommendation:** Standardize all responses

```python
# api/models/common.py
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[list] = None

class PaginatedResponse(ApiResponse[T], Generic[T]):
    pagination: PaginationInfo

# Usage
@app.get("/api/estimates", response_model=PaginatedResponse[List[Estimate]])
async def get_estimates():
    ...
```

---

### 6.2 🟡 MEDIUM: Validation Consistency

**Issue:** Different validation rules in desktop vs web

**Recommendation:** Share validation logic

```python
# shared/validators.py
class EstimateValidator:
    @staticmethod
    def validate_number(number: str) -> bool:
        return len(number) > 0 and len(number) <= 50
    
    @staticmethod
    def validate_date(date: date) -> bool:
        return date <= date.today()

# Use in both Pydantic and desktop models
```

---

### 6.3 🟢 LOW: Error Handling Standardization

**Recommendation:**

```python
# api/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

class NotFoundException(AppException):
    def __init__(self, resource: str, id: int):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND",
            status_code=404
        )

# Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "code": exc.code}
    )
```

---

## 7. Performance Monitoring Recommendations

### 7.1 Add Query Performance Logging

```python
# Slow query logging
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger('sqlalchemy.performance')

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 0.1:  # Log queries > 100ms
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

### 7.2 API Performance Monitoring

```python
# Middleware for request timing
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    if process_time > 1.0:  # Log slow requests
        logger.warning(f"Slow request ({process_time:.2f}s): {request.url}")
    
    return response
```

---

## 8. Implementation Priority

### Phase 1: Critical (Immediate)
1. ✅ Fix timesheet day columns normalization
2. ✅ Add missing database indexes
3. ✅ Implement API response standardization
4. ✅ Add field selection for mobile

### Phase 2: High Priority (1-2 weeks)
1. ✅ Implement caching strategy (Redis + Pinia)
2. ✅ Add audit trail (created_by, modified_by)
3. ✅ Optimize eager loading in desktop app
4. ✅ Implement code generation for TypeScript types

### Phase 3: Medium Priority (1 month)
1. ✅ Implement offline support (PWA + IndexedDB)
2. ✅ Add performance monitoring
3. ✅ Standardize soft delete naming
4. ✅ Implement batch operations

### Phase 4: Low Priority (Ongoing)
1. ✅ Optimize assets and images
2. ✅ Review and optimize computed fields
3. ✅ Continuous performance tuning

---

## 9. Estimated Impact

### Performance Improvements
- **Mobile API calls**: 40-60% reduction in payload size
- **Desktop queries**: 30-50% faster with proper indexing
- **Cache hit rate**: 70-80% for reference data
- **Offline capability**: 100% for read operations

### Development Efficiency
- **Type safety**: 90% reduction in type-related bugs
- **Code generation**: 50% less manual synchronization
- **Maintenance**: 30% reduction in time spent on data model changes

---

## 10. Conclusion

The current data model is well-structured but has several optimization opportunities:

**Strengths:**
- ✅ Clean separation of concerns
- ✅ Proper use of ORM patterns
- ✅ Support for multiple databases
- ✅ Hierarchical reference data

**Key Improvements Needed:**
- 🔴 Normalize timesheet day columns
- 🟡 Add comprehensive indexing
- 🟡 Implement caching strategy
- 🟡 Reduce mobile payload sizes
- 🟢 Standardize naming conventions

Implementing these recommendations will significantly improve performance, maintainability, and user experience across both desktop and mobile platforms.

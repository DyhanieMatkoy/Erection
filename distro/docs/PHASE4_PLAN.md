# Phase 4: Testing and Quality Assurance - Plan

## Overview
Phase 4 focuses on comprehensive testing to ensure code quality, reliability, and correctness before production deployment.

## Current Status

### ✅ Completed Tasks
- **Task 4.2**: Backend Integration Tests - COMPLETE
  - All API endpoints tested
  - Error cases covered
  - 100% endpoint coverage

### 🔄 Remaining Tasks
- **Task 4.1**: Backend Unit Tests - NOT STARTED
- **Task 4.3**: Frontend Unit Tests - NOT STARTED
- **Task 4.4**: Frontend Component Tests - NOT STARTED
- **Task 4.5**: E2E Tests - NOT STARTED
- **Task 4.6**: Manual Testing - NOT STARTED

---

## Task 4.1: Backend Unit Tests

### Scope
Write unit tests for backend services, models, and utilities in isolation.

### Components to Test

#### 1. AuthService (`api/services/auth_service.py`)
**Methods to test**:
- `authenticate_user(username, password)` - Success and failure cases
- `create_access_token(user_id, expires_delta)` - Token generation
- `verify_token(token)` - Valid, expired, invalid tokens
- `hash_password(password)` - Password hashing
- `verify_password(plain, hashed)` - Password verification

**Test cases**: ~15-20 tests

#### 2. Pydantic Models
**Models to test**:
- `api/models/auth.py` - LoginRequest, LoginResponse, UserInfo
- `api/models/references.py` - All reference models
- `api/models/documents.py` - Estimate and DailyReport models

**Test cases**: ~30-40 tests (validation, serialization)

#### 3. Middleware & Dependencies
**Components to test**:
- JWT token validation
- Error handlers
- CORS configuration

**Test cases**: ~10-15 tests

### Estimated Time: 4-6 hours
### Priority: HIGH

---

## Task 4.3: Frontend Unit Tests

### Scope
Write unit tests for composables, stores, and utility functions.

### Components to Test

#### 1. Composables
**Files to test**:
- `useAuth.ts` - Login, logout, token management
- `useTable.ts` - Pagination, sorting, search
- `usePrint.ts` - Print dialog logic
- `useReferenceView.ts` - CRUD operations

**Test cases**: ~25-30 tests

#### 2. Pinia Stores
**Stores to test**:
- `auth.ts` - Authentication state management
- `references.ts` - Reference data caching
- `documents.ts` - Document state management

**Test cases**: ~20-25 tests

#### 3. API Client Functions
**Files to test**:
- `api/client.ts` - Axios interceptors
- `api/auth.ts` - Auth API calls
- `api/references.ts` - Reference API calls
- `api/documents.ts` - Document API calls
- `api/registers.ts` - Register API calls

**Test cases**: ~30-35 tests

### Estimated Time: 6-8 hours
### Priority: MEDIUM

---

## Task 4.4: Frontend Component Tests

### Scope
Write tests for Vue components using Vue Test Utils.

### Components to Test

#### 1. Common Components
**Files to test**:
- `DataTable.vue` - Rendering, sorting, pagination, search
- `Modal.vue` - Open/close, backdrop, keyboard events
- `FormField.vue` - Input types, validation, errors
- `Picker.vue` - Search, selection, dropdown
- `MultiPicker.vue` - Multi-select, checkboxes

**Test cases**: ~40-50 tests

#### 2. Layout Components
**Files to test**:
- `AppLayout.vue` - Sidebar state management
- `AppHeader.vue` - User menu, logout
- `AppSidebar.vue` - Navigation, drawer behavior

**Test cases**: ~15-20 tests

#### 3. Document Components
**Files to test**:
- `EstimateLines.vue` - Add/remove lines, calculations
- `DailyReportLines.vue` - Auto-fill, executors, deviations
- `PrintDialog.vue` - Format selection, print actions

**Test cases**: ~20-25 tests

### Estimated Time: 8-10 hours
### Priority: MEDIUM

---

## Task 4.5: E2E Tests

### Scope
Write end-to-end tests for critical user flows using Playwright.

### User Flows to Test

#### 1. Authentication Flow
- Login with valid credentials
- Login with invalid credentials
- Logout
- Token expiration handling

**Test cases**: ~4-5 tests

#### 2. Reference Management Flow
- Create counterparty
- Edit counterparty
- Delete counterparty
- Search and pagination

**Test cases**: ~4-5 tests

#### 3. Estimate Flow
- Create estimate
- Add estimate lines
- Calculate totals
- Save estimate
- Post estimate
- Print estimate

**Test cases**: ~6-8 tests

#### 4. Daily Report Flow
- Create daily report
- Select estimate (auto-fill)
- Enter actual labor
- Select executors
- Save report
- Post report

**Test cases**: ~6-8 tests

#### 5. Register Flow
- Apply filters
- View movements
- Check totals
- Export (if implemented)

**Test cases**: ~3-4 tests

### Estimated Time: 10-12 hours
### Priority: MEDIUM

---

## Task 4.6: Manual Testing

### Scope
Comprehensive manual testing on different browsers and devices.

### Testing Areas

#### 1. Desktop Browsers
- Chrome (latest)
- Firefox (latest)
- Edge (latest)
- Safari (if available)

**Time**: 2-3 hours

#### 2. Mobile Devices
- iPhone (Safari)
- Android (Chrome)
- Different screen sizes

**Time**: 2-3 hours

#### 3. Tablet Devices
- iPad (Safari)
- Android tablet (Chrome)

**Time**: 1-2 hours

#### 4. Accessibility Testing
- Keyboard navigation
- Screen reader (basic)
- High contrast mode

**Time**: 1-2 hours

#### 5. Performance Testing
- Lighthouse audits
- Network throttling
- Large datasets

**Time**: 1-2 hours

### Estimated Time: 8-12 hours
### Priority: HIGH

---

## Total Estimates

### Time Required:
- Task 4.1: 4-6 hours
- Task 4.3: 6-8 hours
- Task 4.4: 8-10 hours
- Task 4.5: 10-12 hours
- Task 4.6: 8-12 hours

**Total**: 36-48 hours (5-6 working days)

### Priority Order:
1. Task 4.1 (Backend Unit Tests) - HIGH
2. Task 4.6 (Manual Testing) - HIGH
3. Task 4.3 (Frontend Unit Tests) - MEDIUM
4. Task 4.4 (Frontend Component Tests) - MEDIUM
5. Task 4.5 (E2E Tests) - MEDIUM

---

## Recommended Approach

### Week 1: Backend & Manual Testing
- **Day 1-2**: Task 4.1 (Backend Unit Tests)
- **Day 3-4**: Task 4.6 (Manual Testing)
- **Day 5**: Fix issues found in manual testing

### Week 2: Frontend Testing
- **Day 1-2**: Task 4.3 (Frontend Unit Tests)
- **Day 3-4**: Task 4.4 (Frontend Component Tests)
- **Day 5**: Task 4.5 (E2E Tests - critical flows only)

---

## Success Criteria

### Code Coverage Targets:
- Backend: >80%
- Frontend: >70%
- Overall: >75%

### Quality Metrics:
- All tests passing
- No critical bugs
- Performance acceptable
- Accessibility baseline met

### Documentation:
- Test documentation complete
- Known issues documented
- Test reports generated

---

## Tools & Setup

### Backend Testing:
```bash
# Install pytest
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest api/tests/ -v --cov=api --cov-report=html
```

### Frontend Testing:
```bash
# Install Vitest and Vue Test Utils
npm install -D vitest @vue/test-utils @vitest/ui

# Run tests
npm run test:unit
npm run test:coverage
```

### E2E Testing:
```bash
# Install Playwright
npm install -D @playwright/test

# Run tests
npx playwright test
```

---

## Next Steps

1. ✅ Phase 3 complete
2. ➡️ Start Task 4.1 (Backend Unit Tests)
3. ➡️ Continue with remaining Phase 4 tasks
4. ➡️ Proceed to Phase 5 (Deployment)

---

## Notes

- Task 4.2 (Backend Integration Tests) already complete ✅
- Focus on high-priority tasks first
- Manual testing is critical before production
- E2E tests can be limited to critical flows for MVP
- Full test suite can be expanded post-MVP


# Desktop Application - Work Composition Gap Analysis

## Overview

The work composition form specification (`.kiro/specs/work-composition-form/`) was implemented for the **web client only**. The desktop application (Python/Qt in `src/` directory) has NOT been updated to support the new work composition requirements.

## Current State

### Desktop Work Form (`src/views/work_form.py`)

**What it HAS:**
- ✅ Basic work fields (name, code, unit, price, labor_rate)
- ✅ Parent work selection (hierarchical structure)
- ✅ Group work support (is_group flag)
- ✅ Save/load functionality

**What it's MISSING:**
- ❌ Cost Items table (трудозатраты в нормочасах)
- ❌ Materials table (нормы расхода материалов)
- ❌ Ability to add/remove cost items to works
- ❌ Ability to add/remove materials to works with quantities
- ❌ Total cost calculation from composition
- ❌ Validation for work composition
- ❌ UI for managing work composition

### Database Schema

**Status: ✅ COMPLETE**
- The database schema has been updated with the `cost_item_materials` table
- The `work_id` column was added via migration `20251209_100000_add_work_to_cost_item_materials.py`
- The `unit_id` column was added to works via migration `20251209_120000_add_unit_id_to_works.py`
- All foreign keys and constraints are in place

### Backend API

**Status: ✅ COMPLETE**
- All API endpoints for work composition are implemented
- Validation logic is complete
- Tests are passing

## Gap Analysis

### 1. Work Form UI Components Missing

The desktop work form needs these additional UI components:

#### Cost Items Section
```
┌─────────────────────────────────────────────────────────────┐
│ Статьи затрат (Cost Items)                                  │
├─────────────────────────────────────────────────────────────┤
│ [Добавить статью затрат]                                    │
│                                                              │
│ Код    │ Наименование        │ Ед.изм │ Цена  │ Норма труда│
│────────┼─────────────────────┼────────┼───────┼────────────│
│ 1.01   │ Труд рабочих        │ час    │ 500   │ 2.5        │
│ 1.02   │ Аренда оборудования │ час    │ 200   │ 0.5        │
│        │                     │        │       │            │
└─────────────────────────────────────────────────────────────┘
```

#### Materials Section
```
┌─────────────────────────────────────────────────────────────┐
│ Материалы (Materials)                                        │
├─────────────────────────────────────────────────────────────┤
│ [Добавить материал]                                         │
│                                                              │
│ Статья  │ Код  │ Наименование │ Ед.изм │ Цена │ Кол-во │ Σ │
│─────────┼──────┼──────────────┼────────┼──────┼────────┼───│
│ 1.03    │ M001 │ Цемент М400  │ т      │ 5000 │ 0.015  │75 │
│ 1.03    │ M002 │ Песок речной │ т      │ 800  │ 0.05   │40 │
│         │      │              │        │      │        │   │
└─────────────────────────────────────────────────────────────┘
```

#### Total Cost Display
```
┌─────────────────────────────────────────────────────────────┐
│ Итого стоимость работы: 815.00 руб.                         │
└─────────────────────────────────────────────────────────────┘
```

### 2. Required Desktop Components

To implement work composition in the desktop app, we need:

#### New/Modified Files:

1. **`src/views/work_form.py`** (MODIFY)
   - Add cost items table widget
   - Add materials table widget
   - Add total cost display
   - Add buttons for adding/removing items
   - Implement composition save/load logic

2. **`src/views/cost_item_selector_dialog.py`** (NEW)
   - Dialog for selecting cost items from catalog
   - Search and filter functionality
   - Hierarchical display

3. **`src/views/material_selector_dialog.py`** (NEW)
   - Dialog for selecting materials from catalog
   - Search and filter functionality
   - Unit filter

4. **`src/data/repositories/cost_item_material_repository.py`** (NEW)
   - Repository for managing cost_item_materials table
   - CRUD operations for work composition

5. **`src/services/work_composition_service.py`** (NEW)
   - Business logic for work composition
   - Validation (duplicates, circular references, etc.)
   - Total cost calculation

### 3. Timesheet Form Considerations

The timesheet form (`src/views/timesheet_document_form.py`) currently works with works but doesn't need immediate changes because:
- It references works by ID
- The work composition is used for cost calculation in the background
- The timesheet UI doesn't display work composition details

**However**, if users want to see work composition details in timesheets, we would need:
- Tooltip or detail view showing cost items and materials for selected work
- Automatic material consumption calculation based on work quantities

### 4. Other Forms That May Need Updates

#### Estimate Form
- May want to show work composition when adding works to estimates
- Could display material requirements automatically

#### Daily Report Form
- Similar to timesheet, may want to show work composition details

## Requirements Mapping

### From Specification to Desktop Implementation

| Requirement | Web Client | Desktop App | Status |
|-------------|-----------|-------------|--------|
| 1. Basic work properties | ✅ | ✅ | Complete |
| 2. Add cost items to work | ✅ | ❌ | **Missing** |
| 3. Remove cost items | ✅ | ❌ | **Missing** |
| 4. Add materials to work | ✅ | ❌ | **Missing** |
| 5. Edit material quantities | ✅ | ❌ | **Missing** |
| 6. Change material cost item | ✅ | ❌ | **Missing** |
| 7. Remove materials | ✅ | ❌ | **Missing** |
| 8. Total cost calculation | ✅ | ❌ | **Missing** |
| 9. Cost items table display | ✅ | ❌ | **Missing** |
| 10. Materials table display | ✅ | ❌ | **Missing** |
| 11. Validation | ✅ | ❌ | **Missing** |
| 12. Visual feedback | ✅ | ❌ | **Missing** |
| 13. Referential integrity | ✅ | ✅ | Complete (DB) |
| 14. Search and filter | ✅ | ❌ | **Missing** |
| 15. Hierarchical structure | ✅ | ✅ | Complete |
| 16. Substring entry | ✅ | ❌ | **Missing** |

## Implementation Priority

### High Priority (Core Functionality)
1. ✅ Database schema (DONE)
2. ✅ Backend API (DONE)
3. ❌ Desktop Work Form - Cost Items table
4. ❌ Desktop Work Form - Materials table
5. ❌ Cost Item Selector Dialog
6. ❌ Material Selector Dialog

### Medium Priority (Enhanced UX)
7. ❌ Total cost calculation display
8. ❌ Validation in desktop UI
9. ❌ Search/filter in selector dialogs

### Low Priority (Nice to Have)
10. ❌ Work composition display in Timesheet
11. ❌ Work composition display in Estimates
12. ❌ Material requirements calculation

## Recommended Approach

### Option 1: Full Desktop Implementation (Recommended)
Implement complete work composition functionality in desktop app to match web client.

**Pros:**
- Feature parity between web and desktop
- Users can manage work composition from either interface
- Consistent user experience

**Cons:**
- Significant development effort
- Need to implement Qt widgets and dialogs

**Estimated Effort:** 3-5 days

### Option 2: Read-Only Desktop Display
Show work composition in desktop app but require web client for editing.

**Pros:**
- Less development effort
- Users can view composition details
- Editing happens in one place (web)

**Cons:**
- Inconsistent experience
- Users must switch to web for editing
- Desktop app feels incomplete

**Estimated Effort:** 1-2 days

### Option 3: Web-Only (Current State)
Keep work composition as web-only feature.

**Pros:**
- No additional work needed
- Web client is modern and feature-rich

**Cons:**
- Desktop users can't access this functionality
- May confuse users who primarily use desktop
- Data exists but can't be managed from desktop

**Estimated Effort:** 0 days (current state)

## Recommendation

**Implement Option 1: Full Desktop Implementation**

**Reasoning:**
1. The desktop application is the primary interface for many users
2. Work composition is a core feature for construction management
3. Users expect feature parity between interfaces
4. The database and API are already complete
5. The implementation pattern is clear from the web client

## Next Steps

If proceeding with desktop implementation:

1. Create new spec for desktop work composition implementation
2. Design Qt UI components (tables, dialogs, buttons)
3. Implement repository layer for cost_item_materials
4. Implement service layer for business logic
5. Update work form with composition UI
6. Create selector dialogs
7. Add validation
8. Test thoroughly
9. Update user documentation

## Questions for User

1. **Which option do you prefer?** (Full implementation, read-only, or web-only)
2. **What is the priority?** (Can this wait or is it urgent?)
3. **Who are the primary users?** (Desktop or web client?)
4. **Are there specific workflows** that require desktop work composition?

---

**Document Created:** December 9, 2025
**Status:** Gap identified, awaiting decision on implementation approach

# Schema Changes Summary
## Work-CostItem-Material Relationship Update

**Date:** December 9, 2025  
**Change Type:** Schema Enhancement  
**Priority:** 🔴 CRITICAL

---

## Overview

Updated the `cost_item_materials` association table to include a parent `work_id` reference, creating a three-way relationship between Work, CostItem, and Material entities.

---

## Changes Made

### 1. Database Schema Change

**Before:**
```sql
CREATE TABLE cost_item_materials (
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity_per_unit FLOAT DEFAULT 0.0,
    PRIMARY KEY (cost_item_id, material_id)
);
```

**After:**
```sql
CREATE TABLE cost_item_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,              -- NEW: Parent work reference
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity_per_unit FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    
    UNIQUE (work_id, cost_item_id, material_id)  -- NEW: Prevents duplicates
);
```

### 2. Relationship Changes

**Old Relationship:**
```
CostItem ←→ Material (many-to-many)
```

**New Relationship:**
```
Work → CostItem
Work → Material
Work → (CostItem + Material) via CostItemMaterial
```

### 3. Data Model Updates

**Python:**
```python
@dataclass
class CostItemMaterial:
    id: int = 0
    work_id: int = 0              # NEW
    cost_item_id: int = 0
    material_id: int = 0
    quantity_per_unit: float = 0.0
```

**TypeScript:**
```typescript
interface CostItemMaterial {
  id: number
  work_id: number               // NEW
  cost_item_id: number
  material_id: number
  quantity_per_unit: number
  work?: Work                   // NEW
  cost_item?: CostItem
  material?: Material
}
```

---

## Business Logic Changes

### Before
- Cost items and materials were associated independently
- No context about which work type uses which combination
- Difficult to define work composition

### After
- Each work type has its own cost items and materials
- Clear composition: "Work X uses Cost Item Y and Material Z"
- Example: "Wall Plastering" uses "Labor" + "Cement" (0.015 т per м²)

---

## UI Changes Required

### New Work Form Features

**Two Tables Added:**

1. **Cost Items Table**
   - Shows cost items for this work
   - Add/Remove cost items
   - Read-only display of cost item properties

2. **Materials Table**
   - Shows materials for this work
   - Must select which cost item each material belongs to
   - Editable quantity per unit
   - Auto-calculates total cost

**Example:**
```
Work: "Штукатурка стен" (Wall Plastering)

Cost Items:
  - Труд рабочих (Labor)
  - Аренда оборудования (Equipment rental)

Materials:
  - Cost Item: Труд рабочих → Material: Цемент (0.015 т)
  - Cost Item: Труд рабочих → Material: Песок (0.045 т)
  - Cost Item: Аренда → Material: Штукатурная машина (1 шт)
```

---

## API Changes

### New Endpoints

```
GET    /api/works/{id}/composition          - Get full work composition
GET    /api/works/{id}/cost-items           - Get cost items for work
GET    /api/works/{id}/materials            - Get materials for work
POST   /api/works/{id}/cost-items           - Add cost item to work
POST   /api/works/{id}/materials            - Add material to work
PUT    /api/works/{id}/materials/{mid}      - Update material quantity
DELETE /api/works/{id}/cost-items/{cid}     - Remove cost item
DELETE /api/works/{id}/materials/{mid}      - Remove material
```

### Updated Response Models

```typescript
interface WorkComposition {
  work: Work
  cost_items: CostItemMaterial[]
  materials: CostItemMaterial[]
  total_cost: number
}
```

---

## Migration Strategy

### Step 1: Add Column
```sql
ALTER TABLE cost_item_materials ADD COLUMN work_id INTEGER;
```

### Step 2: Migrate Data
```python
# Option 1: Create default work for existing associations
default_work = Work(name="Общие работы (миграция)")
session.add(default_work)
session.flush()

session.query(CostItemMaterial)\
    .update({CostItemMaterial.work_id: default_work.id})

# Option 2: Manual data entry required
# Review existing associations and assign to appropriate works
```

### Step 3: Make Required
```sql
ALTER TABLE cost_item_materials ALTER COLUMN work_id SET NOT NULL;
```

### Step 4: Update Constraints
```sql
ALTER TABLE cost_item_materials ADD COLUMN id INTEGER PRIMARY KEY;
ALTER TABLE cost_item_materials ADD CONSTRAINT uq_work_cost_item_material 
    UNIQUE (work_id, cost_item_id, material_id);
```

---

## Impact Analysis

### Affected Components

**Backend:**
- ✅ Database schema
- ✅ SQLAlchemy models
- ✅ Pydantic models
- ✅ CostItemMaterialRepository
- ✅ WorkRepository
- ✅ API endpoints

**Frontend:**
- ✅ TypeScript models
- ⚠️ Work form (NEW UI required)
- ⚠️ Work list (may need updates)
- ⚠️ Estimate form (may use work composition)

**Documentation:**
- ✅ COMPLETE_DATA_LAYER_SPECIFICATION.md
- ✅ WORK_FORM_UI_SPECIFICATION.md
- ✅ SCHEMA_CHANGES_SUMMARY.md

---

## Benefits

1. **Clear Work Composition**
   - Each work type has defined cost items and materials
   - Easy to understand what goes into each work

2. **Better Cost Estimation**
   - Automatic material calculation based on work type
   - Consistent pricing across estimates

3. **Improved Data Integrity**
   - UNIQUE constraint prevents duplicate associations
   - Foreign key constraints ensure referential integrity

4. **Enhanced Reporting**
   - Can analyze material usage by work type
   - Better cost breakdown in estimates

---

## Risks & Mitigation

### Risk 1: Data Migration Complexity
**Impact:** Existing cost_item_materials records need work_id  
**Mitigation:** 
- Create default "General Work" for migration
- Provide admin interface to reassign associations
- Document manual steps required

### Risk 2: Breaking Changes
**Impact:** Existing API calls will fail  
**Mitigation:**
- Version API endpoints (v1 → v2)
- Provide migration guide for API consumers
- Maintain backward compatibility temporarily

### Risk 3: UI Complexity
**Impact:** Work form becomes more complex  
**Mitigation:**
- Provide clear UI/UX design
- Add tooltips and help text
- Implement step-by-step wizard for first-time users

---

## Testing Requirements

### Unit Tests
- [ ] CostItemMaterial model validation
- [ ] Repository CRUD operations
- [ ] Unique constraint enforcement
- [ ] Cascade delete behavior

### Integration Tests
- [ ] API endpoint responses
- [ ] Work composition retrieval
- [ ] Cost item and material associations
- [ ] Total cost calculations

### E2E Tests
- [ ] Work form: add cost item
- [ ] Work form: add material
- [ ] Work form: edit quantity
- [ ] Work form: delete associations
- [ ] Work form: save and reload

---

## Rollout Plan

### Phase 1: Database (Week 1)
- [ ] Create migration script
- [ ] Test on development database
- [ ] Backup production database
- [ ] Run migration on production
- [ ] Verify data integrity

### Phase 2: Backend (Week 2)
- [ ] Update models
- [ ] Update repositories
- [ ] Create new API endpoints
- [ ] Write unit tests
- [ ] Deploy to staging

### Phase 3: Frontend (Week 3-4)
- [ ] Update TypeScript models
- [ ] Create Work form UI
- [ ] Implement cost items table
- [ ] Implement materials table
- [ ] Write E2E tests
- [ ] Deploy to staging

### Phase 4: Testing & Deployment (Week 5)
- [ ] Full regression testing
- [ ] User acceptance testing
- [ ] Performance testing
- [ ] Deploy to production
- [ ] Monitor for issues

---

## Success Criteria

✅ All existing works can be edited without errors  
✅ New works can be created with cost items and materials  
✅ Material quantities can be edited inline  
✅ Total cost calculations are accurate  
✅ No data loss during migration  
✅ API response times remain acceptable (<200ms)  
✅ Users can complete work composition in <5 minutes  

---

## Related Documents

- [COMPLETE_DATA_LAYER_SPECIFICATION.md](./COMPLETE_DATA_LAYER_SPECIFICATION.md) - Full schema documentation
- [WORK_FORM_UI_SPECIFICATION.md](./WORK_FORM_UI_SPECIFICATION.md) - Detailed UI design
- [DATA_MODEL_ANALYSIS_AND_OPTIMIZATIONS.md](./DATA_MODEL_ANALYSIS_AND_OPTIMIZATIONS.md) - Performance considerations

---

**Status:** ✅ Specification Complete - Ready for Implementation  
**Next Step:** Begin Phase 1 - Database Migration

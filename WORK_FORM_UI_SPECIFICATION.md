# Work Form UI Specification
## Construction Management System - Work Composition Interface

**Version:** 1.0  
**Date:** December 9, 2025  
**Purpose:** Detailed UI specification for Work form with cost items and materials tables

---

## 1. Overview

The Work form allows users to define the composition of construction work types by associating:
1. **Cost Items** - Components like labor, equipment, overhead
2. **Materials** - Physical materials needed, linked to specific cost items

This creates a three-way relationship: **Work → CostItem → Material**

---

## 2. Form Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Work Form: Штукатурка стен (Wall Plastering)          [X]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Basic Information                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Code:        [1.01.001                    ]               │ │
│  │ Name:        [Штукатурка стен             ]               │ │
│  │ Unit:        [м²          ▼]                              │ │
│  │ Price:       [1250.00     ] руб.                          │ │
│  │ Labor Rate:  [2.5         ] hours                         │ │
│  │ □ Is Group                                                │ │
│  │ Parent:      [(None)      ▼]                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Cost Items                                    [+ Add]    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Code    │ Description        │ Unit │ Price │ Labor │ ⚙ │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 1.01    │ Труд рабочих       │ час  │ 500   │ 2.5   │ ✎🗑│   │
│  │ 1.02    │ Аренда оборудования│ час  │ 200   │ 0.5   │ ✎🗑│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Materials                                     [+ Add]    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Cost Item │ Code │ Material    │ Unit │ Price │ Qty │ ⚙ │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Труд      │ M001 │ Цемент      │ т    │ 5000  │0.015│✎🗑│   │
│  │ Труд      │ M002 │ Песок       │ т    │ 800   │0.045│✎🗑│   │
│  │ Аренда    │ E001 │ Штукат.маш. │ шт   │ 0     │ 1.0 │✎🗑│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Total Cost: 1,250.00 руб. per м²                              │
│                                                                 │
│  [Save]  [Cancel]                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Basic Information Section

### 3.1 Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Code | Text | No | Work code (e.g., "1.01.001") |
| Name | Text | Yes | Work name (e.g., "Штукатурка стен") |
| Unit | Dropdown | No | Measurement unit (from Units table) |
| Price | Number | No | Base price per unit |
| Labor Rate | Number | No | Labor hours per unit |
| Is Group | Checkbox | No | Whether this is a folder/group |
| Parent | Dropdown | No | Parent work (for hierarchical structure) |

### 3.2 Validation Rules

- Name is required
- If "Is Group" is checked, disable Price and Labor Rate fields
- Price and Labor Rate must be >= 0
- Unit should be selected from Units table

---

## 4. Cost Items Table

### 4.1 Table Structure

**Columns:**
1. **Code** (read-only) - From CostItem.code
2. **Description** (read-only) - From CostItem.description
3. **Unit** (read-only) - From CostItem.unit_name (via Unit table)
4. **Price** (read-only) - From CostItem.price
5. **Labor** (read-only) - From CostItem.labor_coefficient
6. **Actions** - Edit (✎) and Delete (🗑) buttons

### 4.2 Add Cost Item Flow

```
User clicks [+ Add] button
    ↓
Opens "Select Cost Item" dialog
    ↓
Dialog shows:
  - Search box (filter by code or description)
  - Tree view of cost items (hierarchical)
  - Only non-folder items are selectable
  - Shows: Code, Description, Unit, Price
    ↓
User selects cost item and clicks [OK]
    ↓
System creates CostItemMaterial record:
  - work_id = current work ID
  - cost_item_id = selected cost item ID
  - material_id = NULL (no material yet)
  - quantity_per_unit = 0
    ↓
Cost item appears in table
```

### 4.3 Delete Cost Item Flow

```
User clicks delete (🗑) button
    ↓
System checks if cost item has associated materials
    ↓
If materials exist:
  Show warning: "This cost item has associated materials. 
                 Delete materials first."
  Cancel deletion
    ↓
If no materials:
  Show confirmation: "Delete cost item [Name]?"
    ↓
  User confirms
    ↓
  Delete all CostItemMaterial records where:
    work_id = current work AND
    cost_item_id = selected cost item AND
    material_id IS NULL
    ↓
  Remove from table
```

### 4.4 Business Rules

- Cannot add same cost item twice to same work
- Cannot delete cost item if it has associated materials
- Cost items are read-only (edit in Cost Items catalog)
- Folders cannot be added (only leaf items)

---

## 5. Materials Table

### 5.1 Table Structure

**Columns:**
1. **Cost Item** (dropdown) - Which cost item this material belongs to
2. **Code** (read-only) - From Material.code
3. **Material** (read-only) - From Material.description
4. **Unit** (read-only) - From Material.unit_name (via Unit table)
5. **Price** (read-only) - From Material.price
6. **Qty** (editable) - quantity_per_unit (how much per work unit)
7. **Total** (calculated) - Price × Qty
8. **Actions** - Edit (✎) and Delete (🗑) buttons

### 5.2 Add Material Flow

```
User clicks [+ Add] button
    ↓
Opens "Add Material" dialog
    ↓
Dialog shows:
  Step 1: Select Cost Item
    - Dropdown with cost items already added to work
    - Required field
    ↓
  Step 2: Select Material
    - Search box (filter by code or description)
    - List of materials
    - Shows: Code, Description, Unit, Price
    ↓
  Step 3: Enter Quantity
    - Quantity per unit input
    - Default: 1.0
    - Must be > 0
    ↓
User clicks [OK]
    ↓
System creates CostItemMaterial record:
  - work_id = current work ID
  - cost_item_id = selected cost item ID
  - material_id = selected material ID
  - quantity_per_unit = entered quantity
    ↓
Material appears in table
```

### 5.3 Edit Material Quantity Flow

```
User clicks edit (✎) button OR double-clicks Qty cell
    ↓
Qty cell becomes editable
    ↓
User enters new quantity
    ↓
User presses Enter or clicks outside
    ↓
System validates:
  - Quantity must be > 0
  - Quantity must be numeric
    ↓
If valid:
  Update CostItemMaterial.quantity_per_unit
  Recalculate Total column
  Update total work cost
    ↓
If invalid:
  Show error message
  Revert to previous value
```

### 5.4 Change Cost Item for Material Flow

```
User clicks Cost Item dropdown in row
    ↓
Dropdown shows only cost items added to this work
    ↓
User selects different cost item
    ↓
System updates CostItemMaterial record:
  - cost_item_id = new cost item ID
  - Keep same work_id, material_id, quantity_per_unit
    ↓
Table refreshes
```

### 5.5 Delete Material Flow

```
User clicks delete (🗑) button
    ↓
Show confirmation: "Delete material [Name]?"
    ↓
User confirms
    ↓
Delete CostItemMaterial record where:
  work_id = current work AND
  cost_item_id = selected cost item AND
  material_id = selected material
    ↓
Remove from table
Recalculate total work cost
```

### 5.6 Business Rules

- Material must be linked to a cost item
- Cost item must already exist in Cost Items table
- Cannot add same material twice to same cost item in same work
- Quantity per unit must be > 0
- Materials are read-only except for quantity (edit in Materials catalog)

---

## 6. Calculations

### 6.1 Total Cost Calculation

```typescript
function calculateWorkTotalCost(work: Work): number {
  let total = 0
  
  // Add cost items base cost
  for (const costItem of work.cost_items) {
    total += costItem.price
  }
  
  // Add materials cost
  for (const material of work.materials) {
    total += material.material.price * material.quantity_per_unit
  }
  
  return total
}
```

### 6.2 Material Total Cost

```typescript
function calculateMaterialTotal(material: CostItemMaterial): number {
  return material.material.price * material.quantity_per_unit
}
```

---

## 7. Data Model

### 7.1 Work Object Structure

```typescript
interface Work {
  id: number
  code: string
  name: string
  unit_id: number
  unit_name: string
  price: number
  labor_rate: number
  is_group: boolean
  parent_id: number | null
  marked_for_deletion: boolean
  
  // Composition
  cost_items: CostItemMaterial[]  // Where material_id IS NULL
  materials: CostItemMaterial[]   // Where material_id IS NOT NULL
}

interface CostItemMaterial {
  id: number
  work_id: number
  cost_item_id: number
  material_id: number | null
  quantity_per_unit: number
  
  // Joined data
  cost_item?: CostItem
  material?: Material
}
```

### 7.2 API Endpoints

```typescript
// Get work with composition
GET /api/works/{id}/composition
Response: {
  work: Work,
  cost_items: CostItemMaterial[],
  materials: CostItemMaterial[],
  total_cost: number
}

// Add cost item to work
POST /api/works/{id}/cost-items
Body: { cost_item_id: number }
Response: CostItemMaterial

// Add material to work
POST /api/works/{id}/materials
Body: {
  cost_item_id: number,
  material_id: number,
  quantity_per_unit: number
}
Response: CostItemMaterial

// Update material quantity
PUT /api/works/{work_id}/materials/{id}
Body: { quantity_per_unit: number }
Response: CostItemMaterial

// Delete cost item from work
DELETE /api/works/{work_id}/cost-items/{cost_item_id}
Response: { success: boolean }

// Delete material from work
DELETE /api/works/{work_id}/materials/{id}
Response: { success: boolean }
```

---

## 8. Example Data

### 8.1 Work: "Штукатурка стен" (Wall Plastering)

**Basic Info:**
- Code: 1.01.001
- Name: Штукатурка стен
- Unit: м² (square meter)
- Price: 1,250 руб.
- Labor Rate: 2.5 hours

**Cost Items:**
1. Code: 1.01, Description: "Труд рабочих", Price: 500 руб., Labor: 2.5 hours
2. Code: 1.02, Description: "Аренда оборудования", Price: 200 руб., Labor: 0.5 hours

**Materials:**
1. Cost Item: "Труд рабочих" → Material: "Цемент" (M001), Qty: 0.015 т, Price: 5,000 руб./т
2. Cost Item: "Труд рабочих" → Material: "Песок" (M002), Qty: 0.045 т, Price: 800 руб./т
3. Cost Item: "Аренда оборудования" → Material: "Штукатурная машина" (E001), Qty: 1.0 шт, Price: 0 руб.

**Total Cost Calculation:**
```
Cost Items:
  Труд рабочих: 500 руб.
  Аренда оборудования: 200 руб.
  
Materials:
  Цемент: 5,000 × 0.015 = 75 руб.
  Песок: 800 × 0.045 = 36 руб.
  Штукатурная машина: 0 × 1.0 = 0 руб.
  
Total: 500 + 200 + 75 + 36 + 0 = 811 руб. per м²
```

---

## 9. UI Components

### 9.1 Component Hierarchy

```
WorkForm
├── BasicInfoSection
│   ├── TextInput (code)
│   ├── TextInput (name)
│   ├── UnitSelector (unit_id)
│   ├── NumberInput (price)
│   ├── NumberInput (labor_rate)
│   ├── Checkbox (is_group)
│   └── WorkSelector (parent_id)
├── CostItemsTable
│   ├── TableHeader
│   ├── TableBody
│   │   └── CostItemRow[]
│   │       ├── ReadOnlyCell (code)
│   │       ├── ReadOnlyCell (description)
│   │       ├── ReadOnlyCell (unit)
│   │       ├── ReadOnlyCell (price)
│   │       ├── ReadOnlyCell (labor)
│   │       └── ActionButtons (edit, delete)
│   └── AddButton
│       └── CostItemSelectorDialog
├── MaterialsTable
│   ├── TableHeader
│   ├── TableBody
│   │   └── MaterialRow[]
│   │       ├── CostItemDropdown (cost_item_id)
│   │       ├── ReadOnlyCell (code)
│   │       ├── ReadOnlyCell (description)
│   │       ├── ReadOnlyCell (unit)
│   │       ├── ReadOnlyCell (price)
│   │       ├── EditableCell (quantity_per_unit)
│   │       ├── CalculatedCell (total)
│   │       └── ActionButtons (edit, delete)
│   └── AddButton
│       └── MaterialSelectorDialog
├── TotalCostDisplay
└── FormActions
    ├── SaveButton
    └── CancelButton
```

### 9.2 Dialogs

**CostItemSelectorDialog:**
- Search input
- Hierarchical tree view
- Filter: only non-folder items
- OK/Cancel buttons

**MaterialSelectorDialog:**
- Step 1: Cost Item dropdown (required)
- Step 2: Material search and list
- Step 3: Quantity input (default: 1.0)
- OK/Cancel buttons

---

## 10. Validation & Error Handling

### 10.1 Form Validation

**On Save:**
1. Name is required
2. If not a group, at least one cost item recommended (warning)
3. All materials must have quantity > 0
4. All materials must be linked to existing cost items
5. No duplicate cost items
6. No duplicate materials per cost item

### 10.2 Error Messages

```typescript
const ERROR_MESSAGES = {
  NAME_REQUIRED: "Work name is required",
  NO_COST_ITEMS: "Consider adding at least one cost item",
  INVALID_QUANTITY: "Quantity must be greater than 0",
  DUPLICATE_COST_ITEM: "This cost item is already added",
  DUPLICATE_MATERIAL: "This material is already added to this cost item",
  COST_ITEM_HAS_MATERIALS: "Cannot delete cost item with associated materials",
  MATERIAL_REQUIRES_COST_ITEM: "Material must be linked to a cost item"
}
```

---

## 11. Implementation Checklist

**Backend:**
- [ ] Add work_id column to cost_item_materials table
- [ ] Create migration script
- [ ] Update CostItemMaterial model
- [ ] Update CostItemMaterialRepository
- [ ] Create API endpoints for work composition
- [ ] Add validation logic
- [ ] Write unit tests

**Frontend:**
- [ ] Create WorkForm component
- [ ] Create CostItemsTable component
- [ ] Create MaterialsTable component
- [ ] Create CostItemSelectorDialog
- [ ] Create MaterialSelectorDialog
- [ ] Implement inline editing for quantity
- [ ] Implement total cost calculation
- [ ] Add validation and error handling
- [ ] Write E2E tests

---

**Document Version:** 1.0  
**Last Updated:** December 9, 2025  
**Status:** Ready for Implementation

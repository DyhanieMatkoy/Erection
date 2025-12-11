# Tasks Document - Desktop Work Composition

## Overview

This document outlines the implementation tasks for adding work composition functionality to the desktop application. Tasks are organized in dependency order and should be completed sequentially.

## Task List

### Phase 1: Selector Dialogs

<task title="1. Create CostItemSelectorDialog" status="not started">

**Requirements**: REQ-3, REQ-13

**Description**: Create a dialog for selecting cost items from a hierarchical list with search functionality.

**Implementation**:
1. Create `src/views/dialogs/cost_item_selector_dialog.py`
2. Implement QDialog with:
   - QLineEdit for search
   - QTreeWidget for hierarchical display
   - OK/Cancel buttons
3. Load cost items from CostItemRepository
4. Build hierarchical tree structure
5. Implement search filtering by code or description
6. Support filtering by work (show only cost items in work)
7. Handle double-click to select and close
8. Return selected cost_item_id

**Acceptance Criteria**:
- Dialog displays all cost items in hierarchical tree
- Search filters by code or description (case-insensitive)
- Double-click selects item and closes dialog
- Can filter to show only cost items in specific work
- Returns selected cost_item_id or None

**Files to modify**:
- Create: `src/views/dialogs/cost_item_selector_dialog.py`

</task>

<task title="2. Create MaterialSelectorDialog" status="not started">

**Requirements**: REQ-6, REQ-14

**Description**: Create a dialog for selecting materials from a searchable list.

**Implementation**:
1. Create `src/views/dialogs/material_selector_dialog.py`
2. Implement QDialog with:
   - QLineEdit for search
   - QTableWidget for materials list
   - OK/Cancel buttons
3. Load materials from MaterialRepository
4. Display columns: Код, Наименование, Ед.изм, Цена
5. Implement search filtering by code or description
6. Handle double-click to select and close
7. Return selected material_id

**Acceptance Criteria**:
- Dialog displays all materials in table
- Search filters by code or description (case-insensitive)
- Double-click selects item and closes dialog
- Returns selected material_id or None

**Files to modify**:
- Create: `src/views/dialogs/material_selector_dialog.py`

</task>

<task title="3. Create MaterialAddDialog" status="not started">

**Requirements**: REQ-6

**Description**: Create a multi-step dialog for adding materials to works.

**Implementation**:
1. Create `src/views/dialogs/material_add_dialog.py`
2. Implement multi-step workflow:
   - Step 1: Select cost item (using CostItemSelectorDialog filtered to work)
   - Step 2: Select material (using MaterialSelectorDialog)
   - Step 3: Enter quantity (using QInputDialog)
3. Return tuple of (cost_item_id, material_id, quantity)
4. Handle cancellation at any step

**Acceptance Criteria**:
- Step 1 shows only cost items in the work
- Step 2 shows all materials
- Step 3 validates quantity > 0
- Returns complete tuple or None if cancelled
- Can cancel at any step

**Files to modify**:
- Create: `src/views/dialogs/material_add_dialog.py`

**Dependencies**: Task 1, Task 2

</task>


### Phase 2: Table Widgets

<task title="4. Create CostItemsTable Widget" status="not started">

**Requirements**: REQ-2

**Description**: Create a table widget for displaying cost items in the work form.

**Implementation**:
1. Create `src/views/widgets/cost_items_table.py`
2. Extend QTableWidget
3. Setup columns: Код, Наименование, Ед.изм, Цена, Норма труда
4. Implement `load_cost_items(cost_items)` method
5. Format numeric values with appropriate precision
6. Make table read-only (no editing)
7. Support row selection
8. Implement `get_selected_cost_item_id()` method

**Acceptance Criteria**:
- Table displays 5 columns correctly
- Numeric values formatted with 2 decimal places
- Table is read-only
- Can select rows
- Returns selected cost_item_id

**Files to modify**:
- Create: `src/views/widgets/cost_items_table.py`

</task>

<task title="5. Create MaterialsTable Widget" status="not started">

**Requirements**: REQ-5, REQ-7

**Description**: Create a table widget for displaying materials with editable quantities.

**Implementation**:
1. Create `src/views/widgets/materials_table.py`
2. Extend QTableWidget
3. Setup columns: Статья затрат, Код, Наименование, Ед.изм, Цена, Количество, Сумма
4. Implement `load_materials(materials)` method
5. Make quantity column editable
6. Make all other columns read-only
7. Calculate and display total (price × quantity)
8. Emit signal when quantity changes
9. Implement `get_selected_material_id()` method

**Acceptance Criteria**:
- Table displays 7 columns correctly
- Quantity column is editable
- Other columns are read-only
- Total calculated automatically
- Emits signal on quantity change
- Returns selected material_id

**Files to modify**:
- Create: `src/views/widgets/materials_table.py`

</task>

### Phase 3: WorkForm Extension

<task title="6. Add Tab Widget to WorkForm" status="not started">

**Requirements**: REQ-1

**Description**: Extend WorkForm to use tabbed interface.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Replace single layout with QTabWidget
3. Move existing basic info fields to first tab
4. Create empty second tab (Статьи затрат)
5. Create empty third tab (Материалы)
6. Preserve existing save/close button bar
7. Ensure tab switching preserves unsaved changes

**Acceptance Criteria**:
- Form displays 3 tabs
- Basic info tab contains existing fields
- Tab switching works smoothly
- Unsaved changes preserved across tabs
- Existing functionality still works

**Files to modify**:
- Modify: `src/views/work_form.py`

</task>

<task title="7. Implement Cost Items Tab" status="not started">

**Requirements**: REQ-2, REQ-3, REQ-4

**Description**: Implement cost items management in second tab.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Add CostItemsTable to second tab
3. Add "Добавить статью затрат" button
4. Add "Удалить" button
5. Implement `on_add_cost_item()`:
   - Open CostItemSelectorDialog
   - Check for duplicates
   - Add to local list
   - Refresh table
6. Implement `on_remove_cost_item()`:
   - Check if cost item has materials
   - Show confirmation dialog
   - Remove from local list
   - Refresh table
7. Implement `load_cost_items()`:
   - Load from CostItemMaterialRepository
   - Populate local list
   - Refresh table
8. Add instance variables:
   - `self.cost_items = []`
   - `self.cost_item_material_repo`

**Acceptance Criteria**:
- Can add cost items to work
- Can remove cost items without materials
- Cannot remove cost items with materials
- Duplicate cost items prevented
- Cost items persist across tab switches
- Cost items loaded on form open

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 1, Task 4, Task 6

</task>


<task title="8. Implement Materials Tab" status="not started">

**Requirements**: REQ-5, REQ-6, REQ-7, REQ-8, REQ-9

**Description**: Implement materials management in third tab.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Add MaterialsTable to third tab
3. Add "Добавить материал" button
4. Add "Удалить" button
5. Implement `on_add_material()`:
   - Check if work has cost items
   - Open MaterialAddDialog
   - Check for duplicates
   - Add to local list
   - Refresh table
6. Implement `on_remove_material()`:
   - Show confirmation dialog
   - Remove from local list
   - Refresh table
   - Update total cost
7. Implement `on_material_quantity_changed()`:
   - Validate quantity > 0
   - Update local list
   - Recalculate total
   - Handle validation errors
8. Implement `on_material_cost_item_changed()`:
   - Open CostItemSelectorDialog (filtered to work)
   - Update local list
   - Refresh table
9. Implement `load_materials()`:
   - Load from CostItemMaterialRepository
   - Populate local list
   - Refresh table
10. Add instance variables:
    - `self.materials = []`
11. Add total cost label below table

**Acceptance Criteria**:
- Can add materials to work
- Can remove materials from work
- Can edit material quantities
- Can change material cost item
- Duplicate materials prevented
- Quantity validation works
- Total cost updates automatically
- Materials persist across tab switches
- Materials loaded on form open

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 2, Task 3, Task 5, Task 6, Task 7

</task>

<task title="9. Implement Data Persistence" status="not started">

**Requirements**: REQ-11

**Description**: Implement saving and loading of work composition.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Extend `load_data()`:
   - Call existing basic info loading
   - Load cost items using `load_cost_items()`
   - Load materials using `load_materials()`
3. Extend `save_data()`:
   - Call existing basic info saving
   - Save cost items using `save_cost_items()`
   - Save materials using `save_materials()`
4. Implement `save_cost_items()`:
   - Get existing associations from database
   - Compare with current local list
   - Remove deleted associations
   - Add new associations
5. Implement `save_materials()`:
   - Get existing associations from database
   - Compare with current local list
   - Remove deleted associations
   - Add or update associations with quantities
6. Handle database errors with user-friendly messages

**Acceptance Criteria**:
- Cost items saved to database
- Materials saved to database
- Quantities saved correctly
- Deletions persisted
- Database errors handled gracefully
- Data loads correctly on form open
- Changes persist across form reopens

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 7, Task 8

</task>

<task title="10. Implement Validation" status="not started">

**Requirements**: REQ-12, REQ-16

**Description**: Implement validation for work composition.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Extend `save_data()` validation:
   - Existing: Check work name required
   - Existing: Check group works can't have price/labor
   - New: Validate all material quantities > 0
   - New: Validate all materials linked to cost items
3. Implement `is_cost_item_in_work()`:
   - Check if cost item already in local list
4. Implement `is_material_in_cost_item()`:
   - Check if material already in cost item
5. Implement `cost_item_has_materials()`:
   - Check if cost item has materials in local list
6. Display validation errors with QMessageBox
7. Prevent save if validation fails

**Acceptance Criteria**:
- Work name required validation works
- Group work validation works
- Material quantity validation works
- Duplicate prevention works
- Cost item with materials cannot be deleted
- Clear error messages displayed
- Save prevented on validation failure

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 9

</task>


<task title="11. Implement Total Cost Calculation" status="not started">

**Requirements**: REQ-10

**Description**: Implement automatic total cost calculation and display.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Implement `calculate_total_cost()`:
   - Sum all cost item prices
   - Sum all material costs (price × quantity)
   - Return total
3. Implement `update_total_cost_display()`:
   - Calculate total
   - Format with currency (руб.)
   - Update label
4. Call `update_total_cost_display()` after:
   - Adding cost item
   - Removing cost item
   - Adding material
   - Removing material
   - Changing material quantity
5. Add total cost label to materials tab

**Acceptance Criteria**:
- Total cost calculated correctly
- Total includes cost items and materials
- Total updates automatically on changes
- Total formatted with currency
- Total displayed in materials tab

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 7, Task 8

</task>

<task title="12. Implement Error Handling" status="not started">

**Requirements**: REQ-16

**Description**: Implement comprehensive error handling.

**Implementation**:
1. Modify `src/views/work_form.py`
2. Wrap database operations in try-except blocks
3. Catch SQLAlchemy exceptions
4. Translate to user-friendly Russian messages
5. Use appropriate QMessageBox types:
   - QMessageBox.warning() for validation errors
   - QMessageBox.critical() for database errors
   - QMessageBox.question() for confirmations
   - QMessageBox.information() for success
6. Log detailed errors for debugging
7. Ensure form remains in consistent state after errors

**Acceptance Criteria**:
- Database errors show user-friendly messages
- Validation errors show clear messages
- Confirmations use question dialogs
- Success messages use information dialogs
- Errors logged for debugging
- Form state consistent after errors

**Files to modify**:
- Modify: `src/views/work_form.py`

**Dependencies**: Task 9, Task 10

</task>

### Phase 4: Testing and Polish

<task title="13. Manual Testing" status="not started">

**Requirements**: All

**Description**: Perform comprehensive manual testing.

**Testing Checklist**:

**Basic Functionality:**
- [ ] Create new work with cost items and materials
- [ ] Edit existing work composition
- [ ] Add cost items to work
- [ ] Remove cost items from work
- [ ] Add materials to work
- [ ] Remove materials from work
- [ ] Edit material quantities
- [ ] Save work with composition
- [ ] Load work with composition

**Validation:**
- [ ] Prevent saving work without name
- [ ] Prevent adding duplicate cost items
- [ ] Prevent adding duplicate materials
- [ ] Prevent deleting cost item with materials
- [ ] Validate material quantity > 0

**UI/UX:**
- [ ] Tab switching preserves changes
- [ ] Tables display correct data
- [ ] Search filters work in dialogs
- [ ] Double-click selects in dialogs
- [ ] Keyboard shortcuts work
- [ ] Total cost updates automatically
- [ ] Confirmation dialogs appear
- [ ] Error messages clear and in Russian

**Data Persistence:**
- [ ] Cost items persist after save
- [ ] Materials persist after save
- [ ] Quantities persist correctly
- [ ] Deletions persist after save
- [ ] Changes persist across reopens

**Acceptance Criteria**:
- All checklist items pass
- No critical bugs found
- UI responsive and intuitive
- Data integrity maintained

**Dependencies**: All previous tasks

</task>

<task title="14. Bug Fixes and Polish" status="not started">

**Requirements**: REQ-17

**Description**: Fix bugs found during testing and polish UI/UX.

**Implementation**:
1. Fix any bugs found in Task 13
2. Improve UI responsiveness:
   - Add loading indicators
   - Disable buttons during operations
   - Auto-resize table columns
3. Add tooltips to buttons
4. Improve keyboard navigation
5. Optimize performance for large datasets
6. Add any missing error handling

**Acceptance Criteria**:
- All bugs from testing fixed
- UI responsive and polished
- Tooltips added to buttons
- Keyboard navigation smooth
- Performance acceptable with large data
- No known issues remaining

**Dependencies**: Task 13

</task>


## Task Summary

### Phase 1: Selector Dialogs (Tasks 1-3)
- Create CostItemSelectorDialog
- Create MaterialSelectorDialog
- Create MaterialAddDialog

**Estimated Time**: 4-6 hours

### Phase 2: Table Widgets (Tasks 4-5)
- Create CostItemsTable
- Create MaterialsTable

**Estimated Time**: 3-4 hours

### Phase 3: WorkForm Extension (Tasks 6-12)
- Add tab widget
- Implement cost items tab
- Implement materials tab
- Implement data persistence
- Implement validation
- Implement total cost calculation
- Implement error handling

**Estimated Time**: 10-14 hours

### Phase 4: Testing and Polish (Tasks 13-14)
- Manual testing
- Bug fixes and polish

**Estimated Time**: 4-6 hours

**Total Estimated Time**: 21-30 hours

## Dependencies Graph

```
Task 1 (CostItemSelectorDialog)
  ├─> Task 3 (MaterialAddDialog)
  └─> Task 7 (Cost Items Tab)

Task 2 (MaterialSelectorDialog)
  └─> Task 3 (MaterialAddDialog)

Task 3 (MaterialAddDialog)
  └─> Task 8 (Materials Tab)

Task 4 (CostItemsTable)
  └─> Task 7 (Cost Items Tab)

Task 5 (MaterialsTable)
  └─> Task 8 (Materials Tab)

Task 6 (Tab Widget)
  ├─> Task 7 (Cost Items Tab)
  └─> Task 8 (Materials Tab)

Task 7 (Cost Items Tab)
  ├─> Task 8 (Materials Tab)
  ├─> Task 9 (Data Persistence)
  └─> Task 11 (Total Cost)

Task 8 (Materials Tab)
  ├─> Task 9 (Data Persistence)
  └─> Task 11 (Total Cost)

Task 9 (Data Persistence)
  └─> Task 10 (Validation)

Task 10 (Validation)
  └─> Task 12 (Error Handling)

Task 11 (Total Cost)
  └─> Task 13 (Testing)

Task 12 (Error Handling)
  └─> Task 13 (Testing)

Task 13 (Testing)
  └─> Task 14 (Bug Fixes)
```

## Implementation Order

1. Task 1: CostItemSelectorDialog
2. Task 2: MaterialSelectorDialog
3. Task 3: MaterialAddDialog
4. Task 4: CostItemsTable
5. Task 5: MaterialsTable
6. Task 6: Tab Widget
7. Task 7: Cost Items Tab
8. Task 8: Materials Tab
9. Task 11: Total Cost Calculation
10. Task 9: Data Persistence
11. Task 10: Validation
12. Task 12: Error Handling
13. Task 13: Manual Testing
14. Task 14: Bug Fixes and Polish

## Notes

- All UI text must be in Russian to match existing desktop app
- Reuse existing ReferencePickerDialog pattern for consistency
- Follow existing code style and patterns in desktop app
- Test with real data from existing database
- Ensure backward compatibility with existing work forms
- Repository layer already complete - no changes needed
- Database schema already complete - no migrations needed


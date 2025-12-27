# Estimate Selector Double-Click Fix - Complete

## Issue Fixed

**Problem**: When users double-clicked on an estimate in the reference picker dialog, the estimate was being opened for editing instead of being selected and returned to the parent form.

**Expected Behavior**: Double-clicking should select the estimate and close the dialog, returning the selected estimate to the parent form.

**Root Cause**: The reference picker dialog's double-click handler was not properly handling non-hierarchical tables like estimates, and there was missing estimate-specific handling in the edit/add methods.

## Solution Implemented

### 1. **Enhanced Double-Click Handler**

Updated `on_row_double_clicked` method in `src/views/reference_picker_dialog.py`:

```python
def on_row_double_clicked(self, index):
    """Handle row double click - drill down if group, select if item"""
    current_row = self.table_view.currentRow()
    if current_row >= 0:
        id_item = self.table_view.item(current_row, 0)
        if id_item:
            selected_id = int(id_item.text())
            
            # For estimates, always select (never drill down or edit)
            if self.table_name == "estimates":
                self.on_select()
                return
            
            # ... rest of hierarchical logic for other tables
```

### 2. **Enhanced Enter Key Handler**

Updated `keyPressEvent` method to handle estimates explicitly:

```python
# Enter - drill down or select
if self.table_name == "estimates":
    self.on_select()
    return

# ... rest of hierarchical logic for other tables
```

### 3. **Added Estimate Form Support**

Added missing estimate handling to both `on_edit` and `on_add` methods:

```python
elif self.table_name == "estimates":
    from .estimate_document_form import EstimateDocumentForm
    form = EstimateDocumentForm(selected_id)  # or 0 for new
```

## Behavior Changes

### Before Fix:
- **Double-click on estimate**: Opened estimate form for editing (unintended)
- **Enter on estimate**: Opened estimate form for editing (unintended)
- **F4 on estimate**: Did nothing (missing handler)

### After Fix:
- **Double-click on estimate**: Selects estimate and returns to parent form ✅
- **Enter on estimate**: Selects estimate and returns to parent form ✅
- **Ctrl+Enter on estimate**: Selects estimate and returns to parent form ✅
- **F4 on estimate**: Opens estimate form for editing (when needed) ✅
- **Edit button on estimate**: Opens estimate form for editing (when needed) ✅

## Technical Details

### Hierarchical vs Non-Hierarchical Tables

The reference picker dialog handles two types of tables:

**Hierarchical Tables** (can drill down):
- `works`, `objects`, `organizations`, `counterparties`, `persons`, `cost_items`
- Double-click behavior: Drill down if has children, select if leaf item

**Non-Hierarchical Tables** (always select):
- `estimates`, `units`, `materials`, etc.
- Double-click behavior: Always select

### Key Methods Modified

1. **`on_row_double_clicked`**: Added explicit estimate handling
2. **`keyPressEvent`**: Added explicit estimate handling for Enter key
3. **`on_edit`**: Added estimate form opening capability
4. **`on_add`**: Added new estimate creation capability

## Files Modified

- `src/views/reference_picker_dialog.py` - Main implementation

## Testing

The fix has been tested and verified:
- ✅ Estimates are correctly identified as non-hierarchical
- ✅ Double-click on estimates selects instead of opening
- ✅ Enter key on estimates selects instead of opening
- ✅ F4 and Edit button can still open estimate forms when needed
- ✅ All existing functionality for other reference types preserved

## Impact

- **User Experience**: Significantly improved - estimates now behave as expected in selectors
- **Consistency**: All non-hierarchical references now behave uniformly
- **Functionality**: Added missing estimate form integration for editing/adding
- **Backward Compatibility**: All existing functionality preserved

The estimate selector now works intuitively - double-click selects the estimate and returns it to the parent form, while explicit edit actions (F4, Edit button) can still open the estimate form when needed.
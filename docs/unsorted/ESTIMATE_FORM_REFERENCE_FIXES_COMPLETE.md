# Estimate Form Reference Field Fixes - Complete

## Issues Fixed

### 1. TypeError: '>' not supported between instances of 'NoneType' and 'int'

**Problem**: Reference ID fields (`customer_id`, `object_id`, etc.) could be `None` but the code was trying to compare them directly with integers using `> 0`.

**Location**: `src/views/estimate_document_form.py` line 563 and similar lines

**Root Cause**: 
```python
# This would fail if self.customer_id is None
current_id=self.customer_id if self.customer_id > 0 else None
```

**Solution**: Added proper None checking before comparison:
```python
# Fixed version - check for None first
current_id=self.customer_id if self.customer_id and self.customer_id > 0 else None
```

### 2. Reference Fields Auto-Open Selector on Focus

**Problem**: Reference type fields should automatically open the selector dialog when they receive focus and are empty.

**Solution**: Created a custom `ReferenceLineEdit` widget that:
- Extends `QLineEdit` with focus event handling
- Automatically opens the selector when focused and empty
- Uses `QTimer.singleShot(0, callback)` to defer the callback and avoid focus issues

## Files Modified

### `src/views/estimate_document_form.py`

1. **Added Custom Widget Class**:
   ```python
   class ReferenceLineEdit(QLineEdit):
       """Custom QLineEdit that opens reference selector on focus when empty"""
       
       def __init__(self, parent=None, selector_callback=None):
           super().__init__(parent)
           self.selector_callback = selector_callback
           self.setReadOnly(True)
       
       def focusInEvent(self, event):
           """Handle focus in event - open selector if empty"""
           super().focusInEvent(event)
           if self.selector_callback and not self.text().strip():
               QTimer.singleShot(0, self.selector_callback)
   ```

2. **Updated Reference Field Creation**:
   - Replaced `QLineEdit()` with `ReferenceLineEdit(self, callback)`
   - Connected each field to its respective selector method
   - Maintained read-only behavior

3. **Fixed None Comparison Issues**:
   - `on_select_customer()`: Added `self.customer_id and` before comparison
   - `on_select_object()`: Added `self.object_id and` before comparison  
   - `on_select_contractor()`: Added `self.contractor_id and` before comparison
   - `on_select_responsible()`: Added `self.responsible_id and` before comparison

## Behavior Changes

### Before Fix:
- Clicking on empty reference fields did nothing
- Had to click the "..." button to open selector
- TypeError when reference IDs were None

### After Fix:
- Clicking on empty reference fields automatically opens selector
- "..." button still works as before
- No more TypeError - proper None handling
- Improved user experience with auto-focus behavior

## Testing

The fixes have been tested and verified:
- ✅ No more TypeError when reference IDs are None
- ✅ Custom ReferenceLineEdit widget works correctly
- ✅ EstimateDocumentForm can be imported without errors
- ✅ Auto-focus behavior implemented correctly

## Impact

- **User Experience**: Significantly improved - users can now simply click on reference fields to select values
- **Stability**: Eliminated TypeError crashes when working with new estimates
- **Consistency**: All reference fields now behave uniformly
- **Backward Compatibility**: Existing functionality (buttons) still works as before

## Related Files

- `src/views/estimate_document_form.py` - Main implementation
- Other form files checked for similar issues (none found)

The estimate form now provides a much more intuitive and stable user experience for working with reference fields.
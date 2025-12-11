# Web Works Reference - Integration with Work Composition Form

## Problem

The Works reference view in the web client was using the old simple form modal (from `useReferenceView` composable) instead of the new comprehensive Work Composition Form that includes cost items and materials tables.

## Solution

Updated `web-client/src/views/references/WorksView.vue` to navigate to the Work Composition View instead of opening the simple modal.

### Changes Made

1. **Added Router Import:**
```typescript
import { useRouter } from 'vue-router'
const router = useRouter()
```

2. **Created Custom Edit Handler:**
```typescript
// Custom handler to navigate to work composition view instead of modal
function handleEditWork(work: Work) {
  router.push({ name: 'work-composition', params: { id: work.id } })
}
```

3. **Updated DataTable Event Handler:**
```vue
<!-- Before -->
@row-click="view.handleEdit"

<!-- After -->
@row-click="handleEditWork"
```

## Result

Now when users click on a work in the References > Works view, they will be navigated to the full Work Composition Form (`/works/:id/composition`) which includes:

✅ Basic work information (name, code, unit, price, labor_rate, parent)
✅ Cost Items table with add/remove functionality
✅ Materials table with add/remove/edit functionality  
✅ Total cost calculation
✅ Full validation
✅ Hierarchical structure support

## User Experience

### Before:
1. Click on work in list
2. Simple modal opens with only basic fields
3. No way to edit cost items or materials

### After:
1. Click on work in list
2. Navigate to dedicated Work Composition page
3. Full form with all composition features
4. Can add/edit cost items and materials
5. See total cost calculation
6. Better UX with more space

## Routes

The work composition form is available at:
- **Edit existing work:** `/works/:id/composition`
- **Demo view:** `/demo/work-composition`

## Integration Points

The Work Composition View integrates with:
- `WorkForm` component (main form with all features)
- `WorkBasicInfo` component (basic fields)
- `CostItemsTable` component (cost items management)
- `MaterialsTable` component (materials management)
- `useWorkComposition` composable (state management)
- Work composition API endpoints

## Testing

To test the integration:
1. Login to web client at http://localhost:5174/ctm/
2. Navigate to References > Works
3. Click on any work in the list
4. Should navigate to `/works/{id}/composition`
5. Should see full work composition form with cost items and materials tables

## Future Enhancements

Consider adding:
- Quick edit button in list for basic fields only
- Composition preview in list (show count of cost items/materials)
- Bulk operations for multiple works
- Import/export with composition data

---

**Issue Resolved:** December 9, 2025
**File Modified:** `web-client/src/views/references/WorksView.vue`
**Status:** Works reference now uses full work composition form

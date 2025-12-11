# Bug Fix: Unable to Add Cost Items or Materials to Work

## Issue
Users were unable to add new cost items or materials to works in the web application.

## Root Cause
The frontend API client was sending the `cost_item_id` parameter incorrectly when adding cost items to works.

**Backend Expected:**
```python
# POST /works/{work_id}/cost-items
# Request body: {"cost_item_id": int}
```

**Frontend Was Sending:**
```typescript
// Sending as query parameter instead of request body
apiClient.post(`/works/${workId}/cost-items`, null, { params: { cost_item_id: costItemId } })
```

This mismatch caused the backend to receive `null` for the `cost_item_id`, which failed validation with the error "cost_item_id is required".

## Files Fixed

### 1. `web-client/src/api/costs-materials.ts`
Changed the `addCostItem` function to send `cost_item_id` in the request body:

**Before:**
```typescript
async addCostItem(workId: number, costItemId: number): Promise<CostItemMaterial> {
  const response = await apiClient.post<CostItemMaterial>(
    `/works/${workId}/cost-items`,
    null,
    { params: { cost_item_id: costItemId } }
  )
  return response.data
}
```

**After:**
```typescript
async addCostItem(workId: number, costItemId: number): Promise<CostItemMaterial> {
  const response = await apiClient.post<CostItemMaterial>(
    `/works/${workId}/cost-items`,
    { cost_item_id: costItemId }
  )
  return response.data
}
```

### 2. `web-client/src/api/work-composition.ts`
Applied the same fix to the `addCostItemToWork` function for consistency.

## Impact
- **Cost Items:** Users can now successfully add cost items to works
- **Materials:** Materials can be added once cost items are added (materials require a cost item association)

## Testing
To verify the fix:
1. Open a work in the work form
2. Click "Add Cost Item" button
3. Select a cost item from the dialog
4. Verify the cost item is added to the table
5. Click "Add Material" button
6. Select a cost item, then a material, and enter quantity
7. Verify the material is added to the table

## Related Components
- `web-client/src/components/work/WorkForm.vue` - Main work form
- `web-client/src/components/work/CostItemsTable.vue` - Cost items table
- `web-client/src/components/work/MaterialsTable.vue` - Materials table
- `web-client/src/composables/useWorkComposition.ts` - Work composition state management
- `api/endpoints/costs_materials.py` - Backend API endpoints

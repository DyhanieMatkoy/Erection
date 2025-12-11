# Bulk Operations and User-Person Linking Implementation

## Summary of Changes

### 1. Fixed "User has no associated person record" Error

**Backend Changes** (`api/endpoints/documents.py`):
- Made person record optional for admin users when creating timesheets
- Non-admin users still require an associated person record
- Improved error message to guide users

### 2. User-Person Linking (Admin Only)

**Backend API** (`api/endpoints/references.py`):
- Added `/references/persons/link-user` endpoint to link/unlink users to persons
- Added `/references/persons/available-for-user/{user_id}` endpoint to get available persons
- Only admins can manage user-person links

**Frontend API** (`web-client/src/api/references.ts`):
- Added `linkUserToPerson(userId, personId?)` function
- Added `getPersonsAvailableForUser(userId)` function
- Added `PersonWithUser` interface

**Usage**:
```typescript
// Link user to person
await linkUserToPerson(userId, personId)

// Unlink user from person
await linkUserToPerson(userId, null)

// Get available persons for user
const persons = await getPersonsAvailableForUser(userId)
```

### 3. Bulk Operations for References

**Backend API** (`api/endpoints/references.py`):
Added bulk delete endpoints for all reference types:
- `/references/counterparties/bulk-delete`
- `/references/objects/bulk-delete`
- `/references/works/bulk-delete`
- `/references/persons/bulk-delete`
- `/references/organizations/bulk-delete`

**Frontend API** (`web-client/src/api/references.ts`):
- Added `bulkDeleteCounterparties(ids)`
- Added `bulkDeleteObjects(ids)`
- Added `bulkDeleteWorks(ids)`
- Added `bulkDeletePersons(ids)`
- Added `bulkDeleteOrganizations(ids)`
- Added `BulkOperationResult` interface

**Frontend UI** (`web-client/src/views/references/CounterpartiesView.vue`):
- Added checkbox selection to DataTable
- Added bulk delete button that appears when items are selected
- Shows count of selected items
- Displays operation results with error details

**Example Implementation**:
```vue
<DataTable
  ref="tableRef"
  :selectable="true"
  @selection-change="handleSelectionChange"
>
  <template #bulk-actions="{ selected }">
    <button v-if="selected.length > 0" @click="handleBulkDelete">
      Удалить ({{ selected.length }})
    </button>
  </template>
</DataTable>
```

### 4. Fixed Estimate Loading in Timesheets

**Changes** (`web-client/src/views/documents/TimesheetFormView.vue`):
- Increased page size to 10000 to load all estimates
- Added filtering to exclude deleted estimates
- Added console logging for debugging
- Fallback logic shows all estimates with object names when filtered list is empty

## API Endpoints

### Bulk Delete
```
POST /api/references/{type}/bulk-delete
Body: { "ids": [1, 2, 3] }
Response: {
  "success": true,
  "message": "Processed 3 of 3 items",
  "processed": 3,
  "errors": []
}
```

### User-Person Linking
```
POST /api/references/persons/link-user
Body: { "user_id": 1, "person_id": 5 }
Response: {
  "success": true,
  "message": "User 'admin' linked to person 'John Doe'"
}
```

```
GET /api/references/persons/available-for-user/1
Response: {
  "success": true,
  "data": [
    { "id": 5, "full_name": "John Doe", "position": "Foreman", "user_id": null },
    ...
  ]
}
```

## Next Steps

To apply bulk operations to other reference views:
1. Add `ref="tableRef"` and `:selectable="true"` to DataTable
2. Add `@selection-change="handleSelectionChange"` handler
3. Add `#bulk-actions` template slot with delete button
4. Implement `handleBulkDelete()` function using the appropriate API call

To implement user management UI:
1. Create a user management view
2. Add person picker for each user
3. Use `linkUserToPerson()` API to link/unlink
4. Use `getPersonsAvailableForUser()` to show available persons

## Testing

1. **Test bulk delete**:
   - Select multiple items in any reference view
   - Click bulk delete button
   - Verify all items are marked as deleted

2. **Test user-person linking**:
   - Call API to link user to person
   - Verify timesheet creation works
   - Test unlinking

3. **Test estimate loading**:
   - Open timesheet form
   - Verify all estimates are available in dropdown
   - Test filtering by object
   - Test fallback when no estimates match filter

## Security

- All bulk operations require admin role
- User-person linking requires admin role
- Non-admin users must have associated person record for timesheet creation
- Admin users can create timesheets without person record

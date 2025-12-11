# Work Composition View - Usage Guide

## Overview

The Work Composition View (`WorkCompositionView.vue`) is an integration view that provides a complete interface for editing work compositions. It integrates all the components built in previous tasks into a single, cohesive workflow.

## Accessing the View

### Route
```
/works/:id/composition
```

### Examples
- Edit work with ID 1: `/works/1/composition`
- Edit work with ID 42: `/works/42/composition`

### Programmatic Navigation

```typescript
// From Vue component
import { useRouter } from 'vue-router'

const router = useRouter()

// Navigate to edit work composition
router.push({ name: 'work-composition', params: { id: 123 } })

// Or using path
router.push(`/works/${workId}/composition`)
```

## Features

### 1. Header Navigation
- **Back Button**: Returns to works list (`/references/works`)
- **Refresh Button**: Reloads work data from server
- **Dynamic Title**: Shows "Create New Work" or "Edit Work Composition"

### 2. Breadcrumb Trail
```
Home > Works > Work #123
```
Provides clear navigation context and allows quick navigation to parent pages.

### 3. Work Form Integration
The view embeds the complete `WorkForm` component which includes:
- **Work Basic Info**: Code, name, unit, price, labor rate, parent, is_group
- **Cost Items Table**: Add, view, and remove cost items
- **Materials Table**: Add, edit quantities, change cost items, remove materials
- **Total Cost Display**: Real-time calculation of total work cost

### 4. Save/Cancel Actions
- **Save**: Persists all changes to the database
- **Cancel**: Prompts for confirmation if there are unsaved changes

### 5. Success Modal
After successful save, displays a modal with options to:
- **Continue Editing**: Stay on the page
- **View Works List**: Navigate back to works list

## Complete Workflow Example

### 1. Navigate to Work
```typescript
// From works list, click on a work or use:
router.push({ name: 'work-composition', params: { id: 123 } })
```

### 2. Edit Work Basic Info
- Update work name, code, unit
- Set price and labor rate
- Select parent work (if applicable)
- Toggle "Is Group" checkbox

### 3. Add Cost Items
- Click "Add Cost Item" button
- Search and filter cost items in the list form
- Select cost item and click OK
- Cost item appears in the table

### 4. Add Materials
- Click "Add Material" button
- Step 1: Select cost item from dropdown
- Step 2: Search and select material
- Step 3: Enter quantity per unit
- Click OK to add material

### 5. Edit Material Quantities
- Click on quantity cell in materials table
- Enter new quantity
- Press Enter or click outside to save

### 6. Change Material Cost Item
- Click on cost item cell in materials table
- Select different cost item from dropdown
- Material is reassigned to new cost item

### 7. Remove Items
- Click delete button (🗑️) on cost item or material row
- Confirm deletion in dialog
- Item is removed from table

### 8. Save Changes
- Review total cost calculation
- Click "Save" button
- Wait for success confirmation
- Choose to continue editing or return to list

## Integration with Existing Features

### Works List Integration
The view is designed to be accessed from the works list view:

```vue
<!-- In WorksView.vue -->
<button @click="editComposition(work.id)">
  Edit Composition
</button>

<script setup>
const editComposition = (workId: number) => {
  router.push({ name: 'work-composition', params: { id: workId } })
}
</script>
```

### Navigation Guards
The route requires authentication:
```typescript
meta: { requiresAuth: true }
```

Users must be logged in to access the view.

## Error Handling

The view handles various error scenarios:

### 1. Work Not Found
If the work ID doesn't exist, the WorkForm will display an error message.

### 2. Network Errors
Network failures are caught and displayed in error banners.

### 3. Validation Errors
Validation errors are shown inline and prevent saving until resolved.

### 4. Unsaved Changes
When clicking Cancel or Back with unsaved changes, a confirmation dialog appears.

## Responsive Design

The view is fully responsive:
- **Desktop**: Full layout with side-by-side sections
- **Tablet**: Stacked layout with adjusted spacing
- **Mobile**: Single column layout with touch-friendly controls

## Accessibility

The view includes accessibility features:
- ARIA labels for navigation
- Keyboard navigation support
- Focus management
- Screen reader friendly
- Semantic HTML structure

## Testing the View

### Manual Testing Steps

1. **Start Development Server**
   ```bash
   cd web-client
   npm run dev
   ```

2. **Login to Application**
   Navigate to `/login` and authenticate

3. **Navigate to Works List**
   Go to `/references/works`

4. **Select a Work**
   Click on a work or manually navigate to `/works/1/composition`

5. **Test All Features**
   - Edit basic info
   - Add cost items
   - Add materials
   - Edit quantities
   - Remove items
   - Save changes
   - Test navigation

### Automated Testing

```typescript
// Example E2E test
describe('Work Composition View', () => {
  it('should load work composition', () => {
    cy.visit('/works/1/composition')
    cy.contains('Edit Work Composition')
    cy.get('[data-testid="work-form"]').should('be.visible')
  })

  it('should navigate back to works list', () => {
    cy.visit('/works/1/composition')
    cy.get('.back-button').click()
    cy.url().should('include', '/references/works')
  })

  it('should save work composition', () => {
    cy.visit('/works/1/composition')
    cy.get('[data-testid="work-name"]').clear().type('Updated Work Name')
    cy.get('.btn-primary').contains('Save').click()
    cy.contains('Success').should('be.visible')
  })
})
```

## Troubleshooting

### Issue: Route Not Found
**Solution**: Ensure the router configuration includes the route and the server is restarted.

### Issue: Work Form Not Loading
**Solution**: Check that the work ID exists in the database and the API is accessible.

### Issue: Save Button Disabled
**Solution**: Check for validation errors. The save button is disabled when:
- Work name is empty
- Group work has price or labor rate
- Materials have invalid quantities

### Issue: TypeScript Errors
**Solution**: The TypeScript language server may show false positives. Run the app to verify it works correctly.

## Related Documentation

- [Task 16 Implementation](./TASK16_INTEGRATION_VIEW_IMPLEMENTATION.md)
- [Work Form Implementation](./TASK11_WORK_FORM_IMPLEMENTATION.md)
- [Requirements Document](./.kiro/specs/work-composition-form/requirements.md)
- [Design Document](./.kiro/specs/work-composition-form/design.md)

## Conclusion

The Work Composition View provides a complete, production-ready interface for managing work compositions. It integrates all previously built components into a cohesive workflow with proper navigation, error handling, and user feedback.

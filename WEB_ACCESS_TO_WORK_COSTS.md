# Web Access to Work Costs - Implementation Guide

**Issue:** Web version cannot access cost information from works catalog  
**Date:** December 9, 2025

---

## Problem Analysis

The web version cannot directly access cost items and materials from the works catalog because:

### 1. Authentication Barrier
- `/api/references/works` requires authentication
- Demo view bypasses this by using direct work IDs
- Need to integrate with auth system

### 2. Separate Endpoints
- Works list: `/api/references/works` (basic work info only)
- Work composition: `/api/works/{id}/composition` (cost items + materials)
- These are intentionally separate for performance

### 3. Missing Integration
- Works view doesn't show composition button/link
- No UI to navigate from work to its composition
- Need to add composition access to works catalog

---

## Solution: Add Composition Access to Works View

### Option 1: Add Composition Button to Works Table

Update `web-client/src/views/references/WorksView.vue`:

```vue
<template>
  <div class="works-view">
    <!-- Existing works table -->
    <table class="table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Name</th>
          <th>Unit</th>
          <th>Price</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="work in works" :key="work.id">
          <td>{{ work.code }}</td>
          <td>{{ work.name }}</td>
          <td>{{ work.unit }}</td>
          <td>{{ work.price }}</td>
          <td>
            <button @click="editWork(work)">Edit</button>
            <button @click="viewComposition(work.id)">Composition</button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <!-- Composition Modal -->
    <div v-if="showCompositionModal" class="modal">
      <WorkCompositionPanel :work-id="selectedWorkId" />
      <button @click="closeComposition">Close</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import WorkCompositionPanel from '@/components/common/WorkCompositionPanel.vue'

const showCompositionModal = ref(false)
const selectedWorkId = ref<number | null>(null)

function viewComposition(workId: number) {
  selectedWorkId.value = workId
  showCompositionModal.value = true
}

function closeComposition() {
  showCompositionModal.value = false
  selectedWorkId.value = null
}
</script>
```

### Option 2: Add Composition Tab to Work Form

Update work form to include composition as a tab:

```vue
<template>
  <div class="work-form">
    <div class="tabs">
      <button @click="activeTab = 'basic'" :class="{ active: activeTab === 'basic' }">
        Basic Info
      </button>
      <button @click="activeTab = 'composition'" :class="{ active: activeTab === 'composition' }">
        Composition
      </button>
    </div>
    
    <div v-if="activeTab === 'basic'" class="tab-content">
      <!-- Basic work fields -->
    </div>
    
    <div v-if="activeTab === 'composition'" class="tab-content">
      <WorkCompositionPanel :work-id="workId" />
    </div>
  </div>
</template>
```

### Option 3: Dedicated Composition Route

Add a dedicated route for work composition:

```typescript
// router/index.ts
{
  path: '/references/works/:id/composition',
  name: 'work-composition',
  component: () => import('@/views/references/WorkCompositionView.vue'),
  meta: { requiresAuth: true },
}
```

Then create `WorkCompositionView.vue`:

```vue
<template>
  <div class="work-composition-view">
    <div class="page-header">
      <button @click="goBack">← Back to Works</button>
      <h1>Work Composition: {{ workName }}</h1>
    </div>
    
    <WorkCompositionPanel :work-id="workId" />
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import WorkCompositionPanel from '@/components/common/WorkCompositionPanel.vue'

const route = useRoute()
const router = useRouter()
const workId = parseInt(route.params.id as string)
const workName = ref('')

function goBack() {
  router.push({ name: 'works' })
}
</script>
```

---

## Recommended Approach

**Use Option 3 (Dedicated Route)** because:

1. ✅ Clean separation of concerns
2. ✅ Better URL structure
3. ✅ Easier to bookmark/share
4. ✅ Better performance (lazy loading)
5. ✅ Consistent with existing patterns

---

## Implementation Steps

### Step 1: Create WorkCompositionView.vue

```bash
# Create the view file
touch web-client/src/views/references/WorkCompositionView.vue
```

### Step 2: Add Route

Update `web-client/src/router/index.ts`:

```typescript
{
  path: '/references/works/:id/composition',
  name: 'work-composition',
  component: () => import('@/views/references/WorkCompositionView.vue'),
  meta: { requiresAuth: true },
}
```

### Step 3: Add Button to Works Table

Update `web-client/src/views/references/WorksView.vue` to add composition button in actions column.

### Step 4: Test

1. Navigate to works catalog
2. Click "Composition" button on any work
3. Verify composition loads correctly
4. Test all CRUD operations

---

## Authentication Handling

The composition endpoint doesn't require auth, but the works list does. To handle this:

```typescript
// In WorkCompositionView.vue
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  
  // Load composition
})
```

---

## Alternative: Make Composition Public

If you want composition accessible without auth:

```python
# api/endpoints/costs_materials.py

@router.get("/works/{work_id}/composition", response_model=WorkCompositionDetail)
async def get_work_composition(
    work_id: int, 
    db: Session = Depends(get_db)
    # Remove: current_user: UserInfo = Depends(get_current_user)
):
    """Get complete work composition - PUBLIC ACCESS"""
    # ... existing code
```

---

## Summary

**Current State:**
- ❌ No direct access from works catalog
- ❌ Composition only accessible via demo
- ❌ No integration with auth system

**After Implementation:**
- ✅ Composition button in works table
- ✅ Dedicated composition view
- ✅ Proper authentication handling
- ✅ Clean URL structure
- ✅ Full CRUD operations available

---

**Next Steps:**
1. Create WorkCompositionView.vue
2. Add route configuration
3. Update WorksView.vue with composition button
4. Test with authenticated user
5. Document for users


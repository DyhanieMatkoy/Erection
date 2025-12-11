import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory('/ctm/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    // References
    {
      path: '/references/counterparties',
      name: 'counterparties',
      component: () => import('@/views/references/CounterpartiesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/references/objects',
      name: 'objects',
      component: () => import('@/views/references/ObjectsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/references/works',
      name: 'works',
      component: () => import('@/views/references/WorksView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/references/persons',
      name: 'persons',
      component: () => import('@/views/references/PersonsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/references/organizations',
      name: 'organizations',
      component: () => import('@/views/references/OrganizationsView.vue'),
      meta: { requiresAuth: true },
    },
    // Documents - Estimates
    {
      path: '/documents/estimates',
      name: 'estimates',
      component: () => import('@/views/documents/EstimateListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/documents/estimates/:id',
      name: 'estimate-form',
      component: () => import('@/views/documents/EstimateFormView.vue'),
      meta: { requiresAuth: true },
    },
    // Documents - Daily Reports
    {
      path: '/documents/daily-reports',
      name: 'daily-reports',
      component: () => import('@/views/documents/DailyReportListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/documents/daily-reports/:id',
      name: 'daily-report-form',
      component: () => import('@/views/documents/DailyReportFormView.vue'),
      meta: { requiresAuth: true },
    },
    // Documents - Timesheets
    {
      path: '/documents/timesheets',
      name: 'timesheets',
      component: () => import('@/views/documents/TimesheetListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/documents/timesheets/:id',
      name: 'timesheet-form',
      component: () => import('@/views/documents/TimesheetFormView.vue'),
      meta: { requiresAuth: true },
    },
    // Registers
    {
      path: '/registers/work-execution',
      name: 'work-execution-register',
      component: () => import('@/views/registers/WorkExecutionView.vue'),
      meta: { requiresAuth: true },
    },
    // Demo - Work Composition
    {
      path: '/demo/work-composition',
      name: 'work-composition-demo',
      component: () => import('@/views/WorkCompositionDemo.vue'),
      meta: { requiresAuth: true },
    },
    // Demo - Cost Items Table
    {
      path: '/demo/cost-items-table',
      name: 'cost-items-table-demo',
      component: () => import('@/views/CostItemsTableDemo.vue'),
      meta: { requiresAuth: true },
    },
    // Demo - Work Basic Info
    {
      path: '/demo/work-basic-info',
      name: 'work-basic-info-demo',
      component: () => import('@/views/WorkBasicInfoDemo.vue'),
      meta: { requiresAuth: true },
    },
    // Demo - Materials Table
    {
      path: '/demo/materials-table',
      name: 'materials-table-demo',
      component: () => import('@/views/MaterialsTableDemo.vue'),
      meta: { requiresAuth: true },
    },
    // Demo - Work Form
    {
      path: '/demo/work-form',
      name: 'work-form-demo',
      component: () => import('@/views/WorkFormDemo.vue'),
      meta: { requiresAuth: true },
    },
    // Work Composition - Integration View
    {
      path: '/works/:id/composition',
      name: 'work-composition',
      component: () => import('@/views/WorkCompositionView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth) {
    // Check if user is authenticated
    if (!authStore.isAuthenticated) {
      // Try to restore auth from localStorage
      const isAuthenticated = await authStore.checkAuth()
      
      if (!isAuthenticated) {
        // Redirect to login
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
    }
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    // Already logged in, redirect to home
    next({ name: 'home' })
    return
  }

  next()
})

export default router

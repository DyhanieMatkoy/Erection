import { test, expect } from '@playwright/test'

/**
 * E2E Test: Create and Edit Counterparty
 * 
 * Tests the complete CRUD flow for counterparties including:
 * - Navigate to counterparties list
 * - Create a new counterparty
 * - Verify counterparty appears in list
 * - Edit the counterparty
 * - Verify changes are saved
 * - Delete the counterparty
 * 
 * Prerequisites:
 * 1. Backend API must be running on http://localhost:8000
 *    Start with: python -m uvicorn api.main:app --reload
 * 2. Test database must be set up with admin user
 *    Run: python api/tests/setup_test_db.py
 * 3. User must be logged in (handled in beforeEach)
 */

test.describe('Counterparty CRUD Operations', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')
    
    // Login with admin credentials
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    await page.click('button[type="submit"]')
    
    // Wait for navigation to dashboard
    await page.waitForURL('/')
    
    // Navigate to counterparties page
    await page.goto('/references/counterparties')
    
    // Wait for the page to load
    await expect(page.locator('h2:has-text("Контрагенты")')).toBeVisible()
  })

  test('should display counterparties list page', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h2')).toContainText('Контрагенты')
    
    // Verify description
    await expect(page.locator('text=Управление справочником контрагентов')).toBeVisible()
    
    // Verify create button is visible
    await expect(page.locator('button:has-text("Создать")')).toBeVisible()
    
    // Verify table is visible (DataTable component)
    await expect(page.locator('table, .space-y-4')).toBeVisible()
  })

  test('should create a new counterparty', async ({ page }) => {
    // Generate unique name for test
    const timestamp = Date.now()
    const counterpartyName = `Test Counterparty ${timestamp}`
    
    // Click create button
    await page.click('button:has-text("Создать")')
    
    // Wait for modal to open
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    
    // Fill in the form - find the input with label "Наименование"
    const nameInput = page.locator('input[type="text"]').first()
    await nameInput.fill(counterpartyName)
    
    // Click save button
    await page.click('button:has-text("Сохранить")')
    
    // Wait for modal to close (with longer timeout for API call)
    await expect(page.locator('text=Создание контрагента')).not.toBeVisible({ timeout: 10000 })
    
    // Verify the new counterparty appears in the list
    await expect(page.locator(`text=${counterpartyName}`)).toBeVisible({ timeout: 10000 })
  })

  test('should edit an existing counterparty', async ({ page }) => {
    // First, create a counterparty to edit
    const timestamp = Date.now()
    const originalName = `Original Name ${timestamp}`
    const updatedName = `Updated Name ${timestamp}`
    
    // Create counterparty
    await page.click('button:has-text("Создать")')
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    const createInput = page.locator('input[type="text"]').first()
    await createInput.fill(originalName)
    await page.click('button:has-text("Сохранить")')
    await expect(page.locator('text=Создание контрагента')).not.toBeVisible({ timeout: 10000 })
    
    // Wait for the counterparty to appear
    await expect(page.locator(`text=${originalName}`)).toBeVisible({ timeout: 10000 })
    
    // Find and click the edit button for this counterparty
    // The row should have the counterparty name and an "Изменить" button
    const row = page.locator(`tr:has-text("${originalName}"), div:has-text("${originalName}")`).first()
    await row.locator('button:has-text("Изменить"), text=Изменить').click()
    
    // Wait for edit modal to open
    await expect(page.locator('text=Редактирование контрагента')).toBeVisible()
    
    // Verify the form is pre-filled with the original name
    const nameInput = page.locator('input[type="text"]').first()
    await expect(nameInput).toHaveValue(originalName)
    
    // Update the name
    await nameInput.clear()
    await nameInput.fill(updatedName)
    
    // Save changes
    await page.click('button:has-text("Сохранить")')
    
    // Wait for modal to close
    await expect(page.locator('text=Редактирование контрагента')).not.toBeVisible({ timeout: 10000 })
    
    // Verify the updated name appears in the list
    await expect(page.locator(`text=${updatedName}`)).toBeVisible({ timeout: 10000 })
    
    // Verify the original name is no longer visible
    await expect(page.locator(`text=${originalName}`)).not.toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("Создать")')
    
    // Wait for modal to open
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    
    // Try to save without filling the name
    await page.click('button:has-text("Сохранить")')
    
    // Modal should still be open (validation failed)
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    
    // Check for validation error message
    // The FormField component should show an error
    await expect(page.locator('text=Обязательное поле')).toBeVisible()
  })

  test('should cancel creation without saving', async ({ page }) => {
    const timestamp = Date.now()
    const counterpartyName = `Cancelled Counterparty ${timestamp}`
    
    // Click create button
    await page.click('button:has-text("Создать")')
    
    // Wait for modal to open
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    
    // Fill in the form
    await page.fill('input[type="text"]', counterpartyName)
    
    // Click cancel button
    await page.click('button:has-text("Отмена")')
    
    // Wait for modal to close
    await expect(page.locator('text=Создание контрагента')).not.toBeVisible()
    
    // Verify the counterparty was NOT created
    await expect(page.locator(`text=${counterpartyName}`)).not.toBeVisible()
  })

  test('should delete a counterparty', async ({ page }) => {
    // First, create a counterparty to delete
    const timestamp = Date.now()
    const counterpartyName = `To Delete ${timestamp}`
    
    // Create counterparty
    await page.click('button:has-text("Создать")')
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    const createInput = page.locator('input[type="text"]').first()
    await createInput.fill(counterpartyName)
    await page.click('button:has-text("Сохранить")')
    await expect(page.locator('text=Создание контрагента')).not.toBeVisible({ timeout: 10000 })
    
    // Wait for the counterparty to appear
    await expect(page.locator(`text=${counterpartyName}`)).toBeVisible({ timeout: 10000 })
    
    // Set up dialog handler to accept the confirmation
    page.on('dialog', dialog => dialog.accept())
    
    // Find and click the delete button for this counterparty
    const row = page.locator(`tr:has-text("${counterpartyName}"), div:has-text("${counterpartyName}")`).first()
    await row.locator('button:has-text("Удалить"), text=Удалить').click()
    
    // Wait a moment for the deletion to process
    await page.waitForTimeout(2000)
    
    // Reload the page to verify deletion
    await page.reload()
    await expect(page.locator('h2:has-text("Контрагенты")')).toBeVisible()
    
    // The counterparty should either be gone or marked as deleted
    // Check if it's still visible - if so, it should show "Удален" status
    const deletedRow = page.locator(`text=${counterpartyName}`)
    const isVisible = await deletedRow.isVisible().catch(() => false)
    
    if (isVisible) {
      // If still visible, verify it's marked as deleted
      await expect(page.locator(`text=Удален`)).toBeVisible()
    }
  })

  test('should search for counterparties', async ({ page }) => {
    // Create a unique counterparty for searching
    const timestamp = Date.now()
    const searchableName = `Searchable ${timestamp}`
    
    // Create counterparty
    await page.click('button:has-text("Создать")')
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    const createInput = page.locator('input[type="text"]').first()
    await createInput.fill(searchableName)
    await page.click('button:has-text("Сохранить")')
    await expect(page.locator('text=Создание контрагента')).not.toBeVisible({ timeout: 10000 })
    
    // Wait for the counterparty to appear
    await expect(page.locator(`text=${searchableName}`)).toBeVisible({ timeout: 10000 })
    
    // Find the search input (should be in the DataTable component)
    const searchInput = page.locator('input[type="search"], input[placeholder*="Поиск"], input[placeholder*="поиск"]').first()
    
    // If search input exists, test search functionality
    const searchExists = await searchInput.isVisible().catch(() => false)
    
    if (searchExists) {
      // Type in search
      await searchInput.fill(searchableName)
      
      // Wait for search results
      await page.waitForTimeout(500)
      
      // Verify the searchable counterparty is visible
      await expect(page.locator(`text=${searchableName}`)).toBeVisible()
    }
  })

  test('should handle network errors gracefully', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("Создать")')
    
    // Wait for modal to open
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
    
    // Simulate network error by blocking API requests
    await page.route('**/api/references/counterparties', route => {
      route.abort()
    })
    
    // Fill in the form
    const nameInput = page.locator('input[type="text"]').first()
    await nameInput.fill('Network Error Test')
    
    // Try to save
    await page.click('button:has-text("Сохранить")')
    
    // Wait for error message to appear (either in red background or containing "Ошибка")
    await expect(page.locator('.bg-red-50').or(page.locator('text=Ошибка'))).toBeVisible({ timeout: 5000 })
    
    // Modal should still be open
    await expect(page.locator('text=Создание контрагента')).toBeVisible()
  })
})

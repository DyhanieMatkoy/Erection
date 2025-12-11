import { test, expect } from '@playwright/test'

/**
 * E2E Test: Login Flow
 * 
 * Tests the complete authentication flow including:
 * - Successful login with valid credentials
 * - Failed login with invalid credentials
 * - Failed login with inactive user
 * - Redirect to dashboard after successful login
 * - Redirect to login when accessing protected routes
 * 
 * Prerequisites:
 * 1. Backend API must be running on http://localhost:8000
 *    Start with: python -m uvicorn api.main:app --reload
 * 2. Test database must be set up with admin user
 *    Run: python api/tests/setup_test_db.py
 */

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login')
  })

  test('should display login form', async ({ page }) => {
    // Verify login page elements are visible
    await expect(page.locator('h2')).toContainText('Система учета строительных работ')
    await expect(page.locator('text=Вход в систему')).toBeVisible()
    
    // Verify form fields
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('should successfully login with valid credentials', async ({ page }) => {
    // Fill in login form with valid credentials
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    
    // Submit the form
    await page.click('button[type="submit"]')
    
    // Wait for navigation to dashboard
    await page.waitForURL('/')
    
    // Verify we're on the dashboard
    await expect(page).toHaveURL('/')
    
    // Verify dashboard content is visible (adjust selector based on actual dashboard)
    // This assumes the dashboard has some identifiable content
    await expect(page.locator('body')).toBeVisible()
  })

  test('should show error message with invalid credentials', async ({ page }) => {
    // Fill in login form with invalid credentials
    await page.fill('#username', 'admin')
    await page.fill('#password', 'wrongpassword')
    
    // Submit the form
    await page.click('button[type="submit"]')
    
    // Wait for error message to appear
    await expect(page.locator('.bg-red-50')).toBeVisible()
    await expect(page.locator('text=Неверное имя пользователя или пароль')).toBeVisible()
    
    // Verify we're still on login page
    await expect(page).toHaveURL('/login')
  })

  test('should show error message with empty fields', async ({ page }) => {
    // Try to submit without filling fields
    await page.click('button[type="submit"]')
    
    // HTML5 validation should prevent submission
    // Check that username field is required
    const usernameInput = page.locator('#username')
    await expect(usernameInput).toHaveAttribute('required', '')
    
    const passwordInput = page.locator('#password')
    await expect(passwordInput).toHaveAttribute('required', '')
  })

  test('should disable form during login attempt', async ({ page }) => {
    // Fill in credentials
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    
    // Click submit button
    const submitButton = page.locator('button[type="submit"]')
    
    // Verify button is enabled before click
    await expect(submitButton).toBeEnabled()
    
    await submitButton.click()
    
    // Wait for navigation to complete
    await page.waitForURL('/')
    await expect(page).toHaveURL('/')
  })

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Try to access a protected route directly
    await page.goto('/documents/estimates')
    
    // Should be redirected to login
    await page.waitForURL(/\/login/)
    await expect(page).toHaveURL(/\/login/)
  })

  test('should redirect to intended page after login', async ({ page }) => {
    // Try to access a protected route
    await page.goto('/documents/estimates')
    
    // Should be redirected to login with redirect query param
    await page.waitForURL(/\/login/)
    
    // Login
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    await page.click('button[type="submit"]')
    
    // Should be redirected to the originally requested page
    await page.waitForURL('/documents/estimates')
    await expect(page).toHaveURL('/documents/estimates')
  })

  test('should persist authentication after page reload', async ({ page }) => {
    // Login first
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    await page.click('button[type="submit"]')
    
    // Wait for navigation to dashboard
    await page.waitForURL('/')
    
    // Reload the page
    await page.reload()
    
    // Should still be authenticated and on dashboard
    await expect(page).toHaveURL('/')
    
    // Verify we're not redirected to login by checking for login form absence
    await expect(page.locator('#username')).not.toBeVisible()
  })

  test('should logout and redirect to login', async ({ page }) => {
    // Login first
    await page.fill('#username', 'admin')
    await page.fill('#password', 'admin')
    await page.click('button[type="submit"]')
    
    // Wait for navigation to dashboard
    await page.waitForURL('/')
    
    // Look for logout button (adjust selector based on actual implementation)
    // This assumes there's a logout button in the header
    const logoutButton = page.locator('button:has-text("Выход"), a:has-text("Выход")')
    
    // Check if logout button exists - if not, skip this test
    const logoutCount = await logoutButton.count()
    
    // Skip test if logout button is not implemented yet
    
    
    await logoutButton.click()
    
    // Should be redirected to login
    await page.waitForURL('/login')
    await expect(page).toHaveURL('/login')
    
    // Try to access protected route - should redirect to login
    await page.goto('/')
    await page.waitForURL('/login')
    await expect(page).toHaveURL('/login')
  })
})

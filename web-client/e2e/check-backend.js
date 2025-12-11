/**
 * Check if backend API is running before E2E tests
 */

async function checkBackend() {
  const maxRetries = 3
  const retryDelay = 2000
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('http://localhost:8000/api/health')
      if (response.ok) {
        console.log('✓ Backend API is running on http://localhost:8000')
        return true
      }
    } catch (error) {
      if (i < maxRetries - 1) {
        console.log(`Waiting for backend API... (attempt ${i + 1}/${maxRetries})`)
        await new Promise(resolve => setTimeout(resolve, retryDelay))
      }
    }
  }
  
  console.error('\n❌ Backend API is not running!')
  console.error('\nPlease start the backend API server:')
  console.error('  cd ..')
  console.error('  python -m uvicorn api.main:app --reload\n')
  console.error('Or use the helper script:')
  console.error('  start-e2e-servers.bat\n')
  return false
}

checkBackend().then(isRunning => {
  process.exit(isRunning ? 0 : 1)
})

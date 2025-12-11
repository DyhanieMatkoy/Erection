/**
 * Setup test database for E2E tests
 * This script ensures the test database has the required test users
 */

import { spawn } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const rootDir = join(__dirname, '..', '..')

console.log('Setting up test database...')

// Run the Python setup script
const pythonProcess = spawn('python', [
  join(rootDir, 'api', 'tests', 'setup_test_db.py')
], {
  cwd: rootDir,
  stdio: 'inherit'
})

pythonProcess.on('close', (code) => {
  if (code === 0) {
    console.log('Test database setup complete')
    process.exit(0)
  } else {
    console.error(`Test database setup failed with code ${code}`)
    process.exit(code)
  }
})

pythonProcess.on('error', (err) => {
  console.error('Failed to start Python process:', err)
  process.exit(1)
})

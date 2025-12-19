# Testing Rules and Guidelines

## Vitest/Jest Testing Commands

### Running Tests in CI Mode (Non-Interactive)

**Problem:** When running tests with `npm test` or `npm run test:unit`, Vitest may enter watch mode and wait for user input, blocking automated processes.

**Solution:** Use direct Vitest commands to run tests in CI mode:

```bash
# For web-client directory (Vitest)
npx vitest run

# Alternative approaches that also work:
npm run test:unit -- --run
```

**Key Points:**
- `npx vitest run` is the most reliable way to run Vitest in non-interactive CI mode
- This bypasses any npm script configuration that might force watch mode
- The command will complete and exit cleanly without waiting for user input
- Use this approach in automated scripts, CI/CD pipelines, and when you need tests to run once and exit

### Directory Structure
- **Frontend tests:** `web-client/` directory uses Vitest
- **Backend tests:** Root directory uses pytest for Python tests

### Test Execution Examples
```bash
# Frontend tests (from web-client directory)
cd web-client
npx vitest run

# Backend tests (from root directory)
pytest
```

This ensures tests run in a non-interactive mode suitable for automation and CI/CD environments.
# Database and Configuration Guide

## Database Usage

### Desktop Version (PyQt6)
- **Database file**: `construction.db` (hardcoded in `main.py`)
- **Location**: Project root directory
- **Configuration**: Hardcoded in `main.py` line 18:
  ```python
  db_manager.initialize("construction.db")
  ```

### Web Version (API + Vue.js)
- **Database file**: `construction.db` (same as desktop by default)
- **Location**: Project root directory
- **Configuration**: Set in `.env` or `.env.production` files:
  ```
  DATABASE_PATH=construction.db
  ```

### Can Desktop and Web Share the Same Database?

**YES**, both versions can share the same database file (`construction.db`).

**Important considerations:**
- ✅ Both use SQLite with the same schema
- ✅ Data will be synchronized automatically (same file)
- ⚠️ **Concurrent access**: SQLite handles multiple readers, but only one writer at a time
- ⚠️ **File locking**: If desktop app is running, web API might experience delays
- ⚠️ **Recommended**: Use separate databases for production web deployment

## Configuration Files

### Desktop Version Settings

**File**: `env.ini`
```ini
[Auth]
login = admin
password = admin

[PrintForms]
format = EXCEL
templates_path = PrnForms
```

**Database**: Hardcoded in `main.py` - to change, edit line 18:
```python
db_manager.initialize("your_database.db")
```

### Web API Settings (Backend)

**Development**: `.env`
```bash
DATABASE_PATH=construction.db
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
```

**Production**: `.env.production`
```bash
DATABASE_PATH=construction.db
JWT_SECRET_KEY=CHANGE-THIS-TO-SECURE-RANDOM-KEY
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com
```

### Web Client Settings (Frontend)

**Development**: `web-client/.env.development`
```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

**Production**: `web-client/.env.production`
```bash
VITE_API_BASE_URL=http://servut.npksarmat.ru:65002/api
```

**Current Default**: `web-client/.env`
```bash
VITE_API_BASE_URL=http://servut.npksarmat.ru:65002/api
```

## How to Change Production API Address

### Method 1: Edit `.env.production` (Recommended)

1. Open `web-client/.env.production`
2. Change the API URL:
   ```bash
   VITE_API_BASE_URL=http://your-server.com:port/api
   ```
3. Rebuild the web client:
   ```bash
   build_web.bat
   ```

### Method 2: Edit `.env` (Quick Change)

1. Open `web-client/.env`
2. Change the API URL:
   ```bash
   VITE_API_BASE_URL=http://your-server.com:port/api
   ```
3. Rebuild:
   ```bash
   build_web.bat
   ```

### Method 3: Use Relative Path (Same Server)

If API and web client are on the same server:

1. Edit `web-client/.env.production`:
   ```bash
   VITE_API_BASE_URL=/api
   ```
2. Rebuild:
   ```bash
   build_web.bat
   ```

## Common Scenarios

### Scenario 1: Local Development
- Desktop: Uses `construction.db`
- Web API: Uses `construction.db` (same file)
- Web Client: Points to `http://localhost:8000/api`

**Setup:**
```bash
# No changes needed - default configuration
run.bat              # Start desktop
start_dev.bat        # Start web (API + client)
```

### Scenario 2: Production Deployment
- Desktop: Uses `construction.db` (local)
- Web API: Uses `construction.db` (on server)
- Web Client: Points to production server

**Setup:**
1. Edit `web-client/.env.production`:
   ```bash
   VITE_API_BASE_URL=http://your-production-server.com:65002/api
   ```
2. Build and deploy:
   ```bash
   build_web.bat
   start_api_production.bat
   ```

### Scenario 3: Separate Databases
- Desktop: Uses `construction.db`
- Web API: Uses `web_construction.db`

**Setup:**
1. Edit `.env.production`:
   ```bash
   DATABASE_PATH=web_construction.db
   ```
2. Copy database:
   ```bash
   copy construction.db web_construction.db
   ```
3. Start API:
   ```bash
   start_api_production.bat
   ```

## Quick Reference

| Component | Config File | Setting | Default Value |
|-----------|------------|---------|---------------|
| Desktop DB | `main.py` | Hardcoded | `construction.db` |
| API DB | `.env` | `DATABASE_PATH` | `construction.db` |
| Web Client API | `web-client/.env.production` | `VITE_API_BASE_URL` | `http://servut.npksarmat.ru:65002/api` |
| Desktop Auth | `env.ini` | `[Auth]` section | admin/admin |
| API JWT | `.env` | `JWT_SECRET_KEY` | dev key |

## Build Commands

```bash
# Build web client only
build_web.bat

# Build production API (creates executable)
build_production_api.bat

# Build desktop app
build.bat
```

## Troubleshooting

### Web client can't connect to API
- Check `web-client/.env.production` has correct URL
- Rebuild web client: `build_web.bat`
- Verify API is running: `http://your-server:port/api/health`

### Database locked error
- Close desktop application
- Check no other processes are using the database
- Consider using separate databases for desktop and web

### CORS errors
- Add your domain to `CORS_ORIGINS` in `.env.production`
- Restart API server

### Changes not taking effect
- Always rebuild after config changes: `build_web.bat`
- Clear browser cache
- Check you edited the correct `.env` file

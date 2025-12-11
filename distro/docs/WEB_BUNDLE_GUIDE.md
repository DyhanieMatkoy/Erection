# Web Application Bundle Guide

This guide explains how to build and run the web application bundle for the Construction Time Management System.

## Overview

The system consists of:
- **FastAPI Backend** - REST API server
- **Vue.js Frontend** - Single Page Application (SPA)
- **Unified Server** - Serves both API and static web client

## Quick Start

### Development Mode (Recommended for Development)

Run both API and web client with hot-reload:

```bash
start_dev.bat
```

This will:
- Start API server on http://localhost:8000
- Start web dev server on http://localhost:5173 (with hot-reload)
- Open two separate command windows

Access:
- Web Client: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Production Mode (Single Server)

Build and run the complete application:

```bash
# 1. Build the web client
build_web.bat

# 2. Start the unified server
start_web.bat
```

This will:
- Build the Vue.js client into static files
- Start a single server on http://localhost:8000
- Serve both API and web client from the same port

Access:
- Web Client: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Build Scripts

### build_web.bat

Builds the Vue.js web client for production:
- Installs npm dependencies (if needed)
- Runs `npm run build` in web-client directory
- Outputs to `web-client/dist/`

### start_web.bat

Starts the unified production server:
- Checks for virtual environment
- Verifies web client is built
- Starts FastAPI server with static file serving
- Serves on http://localhost:8000

### start_dev.bat

Starts development environment:
- Runs API server (Python/FastAPI)
- Runs web dev server (Vite) with hot-reload
- Opens separate windows for each server

## File Structure

```
project/
├── api/                      # FastAPI backend
│   ├── endpoints/           # API routes
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   └── main.py             # API entry point
├── web-client/              # Vue.js frontend
│   ├── src/                # Source code
│   ├── dist/               # Built files (after build)
│   ├── .env.development    # Dev environment config
│   ├── .env.production     # Prod environment config
│   └── package.json        # Dependencies
├── start_server.py          # Unified server script
├── build_web.bat           # Build script
├── start_web.bat           # Production startup
└── start_dev.bat           # Development startup
```

## Environment Configuration

### Development (.env.development)
```
VITE_API_BASE_URL=http://localhost:8000/api
```

### Production (.env.production)
```
VITE_API_BASE_URL=/api
```

The web client automatically uses the correct configuration based on the mode.

## How It Works

### Development Mode
1. API server runs on port 8000
2. Vite dev server runs on port 5173
3. Vite proxies API requests to port 8000
4. Hot-reload enabled for instant updates

### Production Mode
1. Web client is built into static files
2. FastAPI serves both API and static files
3. Single server on port 8000
4. SPA routing handled by FastAPI

## Deployment

For production deployment:

1. Build the web client:
   ```bash
   build_web.bat
   ```

2. Deploy the entire project with:
   - Python dependencies (requirements.txt)
   - Built web client (web-client/dist/)
   - API code (api/)
   - Startup script (start_server.py)

3. Run the server:
   ```bash
   python start_server.py
   ```

## Troubleshooting

### Web client not found
- Run `build_web.bat` to build the client
- Check that `web-client/dist/index.html` exists

### API connection errors
- Verify API server is running on port 8000
- Check CORS settings in `api/config.py`
- Verify environment variables are set correctly

### Build failures
- Ensure Node.js is installed (v20.19+ or v22.12+)
- Delete `web-client/node_modules` and run `npm install`
- Check for TypeScript errors with `npm run type-check`

### Port conflicts
- Change port in `start_server.py` (default: 8000)
- Change dev port in `web-client/vite.config.ts` (default: 5173)

## Additional Commands

### Web Client Only

```bash
cd web-client

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint

# Run tests
npm run test:unit
```

### API Only

```bash
# Activate virtual environment
.venv\Scripts\activate.bat

# Run API server
python api/main.py

# Or use existing script
run.bat
```

## Notes

- The unified server (start_server.py) automatically detects if the web client is built
- If not built, it only serves the API with a message to build the client
- All API routes are prefixed with `/api`
- Static files are served from `/assets`
- SPA routing is handled for all other paths

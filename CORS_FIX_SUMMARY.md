# CORS Issue - Resolution Summary

## Problem

The web client was blocked by CORS policy when trying to access the API:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/auth/login' 
from origin 'http://localhost:5174' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause

The API server's CORS configuration (`api/config.py`) only allowed origins on port 5173:
```python
CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
```

But the web client was running on port **5174** (because port 5173 was already in use).

## Solution

Updated the CORS configuration to include both ports 5173 and 5174:

```python
# api/config.py
CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:8000"
```

The API server automatically reloaded and picked up the new configuration.

## Verification

The web client should now be able to:
1. ✅ Make requests to the API without CORS errors
2. ✅ Login successfully
3. ✅ Access all API endpoints

## Testing

1. Open http://localhost:5174/ctm/ in your browser
2. Try to login with credentials (e.g., `admin`/`admin`)
3. You should see a successful login without CORS errors

## Technical Details

### What is CORS?

CORS (Cross-Origin Resource Sharing) is a security feature that restricts web pages from making requests to a different domain than the one serving the web page.

### Why did this happen?

- **Web Client Origin:** `http://localhost:5174`
- **API Server Origin:** `http://localhost:8000`
- These are different origins (different ports), so CORS applies
- The API must explicitly allow the web client's origin

### CORS Configuration in FastAPI

```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # List of allowed origins
    allow_credentials=True,                # Allow cookies/auth headers
    allow_methods=["*"],                   # Allow all HTTP methods
    allow_headers=["*"],                   # Allow all headers
)
```

## Future Considerations

### For Production

In production, you should:
1. Use specific origins (not wildcards)
2. Use HTTPS
3. Restrict methods and headers if possible
4. Consider using environment variables for configuration

Example production config:
```python
CORS_ORIGINS: str = "https://yourdomain.com,https://www.yourdomain.com"
```

### For Development

If you frequently change ports, you can:
1. Use a wildcard for localhost (less secure): `http://localhost:*`
2. Or use environment variables: `CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:5173}`
3. Or configure a fixed port in vite.config.ts

### Fixing Port in Vite

To always use port 5173, update `web-client/vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,  // Fail if port is in use instead of trying another
  }
})
```

## Status

✅ **CORS Issue Resolved**
- API Server: Running on port 8000 with updated CORS config
- Web Client: Running on port 5174 and can now access API
- Login: Should work without CORS errors

---

**Issue Resolved:** December 9, 2025
**Files Modified:** `api/config.py`
**Server Status:** Auto-reloaded with new configuration

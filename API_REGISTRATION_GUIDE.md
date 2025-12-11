# API Registration Guide
## How to Register New Costs & Materials Endpoints

**Status:** ⚠️ ACTION REQUIRED

---

## Quick Start

Add these lines to your `api/main.py` file:

```python
# Import the new router
from .endpoints import costs_materials

# Register the router
app.include_router(
    costs_materials.router,
    prefix="/api",
    tags=["costs-materials"]
)
```

---

## Detailed Steps

### Step 1: Open `api/main.py`

### Step 2: Add Import

Find the imports section and add:

```python
from .endpoints import costs_materials
```

### Step 3: Register Router

Find where other routers are registered (look for `app.include_router`) and add:

```python
app.include_router(
    costs_materials.router,
    prefix="/api",
    tags=["costs-materials"]
)
```

### Step 4: Test Endpoints

Start the server and visit:
- http://localhost:8000/docs

You should see new endpoints under "costs-materials" tag:
- GET /api/units
- POST /api/units
- GET /api/cost-items
- POST /api/cost-items
- GET /api/materials
- POST /api/materials
- GET /api/works/{work_id}/composition
- POST /api/works/{work_id}/cost-items
- POST /api/works/{work_id}/materials
- etc.

---

## Example `api/main.py` Structure

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from .endpoints import auth, documents, references, registers
from .endpoints import costs_materials  # NEW

app = FastAPI(title="Construction Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(references.router, prefix="/api", tags=["references"])
app.include_router(registers.router, prefix="/api", tags=["registers"])

# NEW: Register costs & materials router
app.include_router(
    costs_materials.router,
    prefix="/api",
    tags=["costs-materials"]
)

@app.get("/")
async def root():
    return {"message": "Construction Management API"}
```

---

## Testing the API

### Test Units Endpoint

```bash
# Get all units
curl http://localhost:8000/api/units

# Create a unit
curl -X POST http://localhost:8000/api/units \
  -H "Content-Type: application/json" \
  -d '{"name": "м", "description": "Метр"}'
```

### Test Work Composition

```bash
# Get work composition
curl http://localhost:8000/api/works/1/composition

# Add cost item to work
curl -X POST http://localhost:8000/api/works/1/cost-items?cost_item_id=1

# Add material to work
curl -X POST http://localhost:8000/api/works/1/materials \
  -H "Content-Type: application/json" \
  -d '{
    "work_id": 1,
    "cost_item_id": 1,
    "material_id": 1,
    "quantity_per_unit": 0.015
  }'
```

---

## Troubleshooting

### Issue: Import Error

**Error:** `ModuleNotFoundError: No module named 'api.endpoints.costs_materials'`

**Solution:** Make sure the file exists at `api/endpoints/costs_materials.py`

### Issue: Database Connection Error

**Error:** `No module named 'src.data.database_manager'`

**Solution:** Update the import in `api/endpoints/costs_materials.py`:

```python
# Change from:
from ...src.data.database_manager import DatabaseManager

# To:
from src.data.database_manager import DatabaseManager
```

### Issue: Circular Import

**Error:** `ImportError: cannot import name 'X' from partially initialized module`

**Solution:** Check import order in `api/main.py`. Import routers after app creation.

---

## Next Steps After Registration

1. ✅ Test all endpoints in Swagger UI (http://localhost:8000/docs)
2. ✅ Test with Postman or curl
3. ✅ Update frontend to use new endpoints
4. ✅ Implement Work form UI
5. ✅ Add authentication/authorization to endpoints

---

**Status:** Ready for registration  
**Priority:** HIGH - Required for new functionality

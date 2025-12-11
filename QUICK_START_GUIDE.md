# Quick Start Guide
## Using the New Costs & Materials Features

**Last Updated:** December 9, 2025

---

## 🚀 Start the Server

```bash
# Start the API server
python start_server.py

# Server will be available at:
# http://localhost:8000
```

---

## 📖 Access Documentation

### Swagger UI (Interactive API Docs)
```
http://localhost:8000/docs
```

### ReDoc (Alternative Docs)
```
http://localhost:8000/redoc
```

---

## 🎯 Quick API Examples

### 1. Get All Units

```bash
curl http://localhost:8000/api/units
```

**Response:**
```json
[
  {"id": 1, "name": "м", "description": "Метр"},
  {"id": 2, "name": "м²", "description": "Квадратный метр"},
  ...
]
```

### 2. Create a Cost Item

```bash
curl -X POST http://localhost:8000/api/cost-items \
  -H "Content-Type: application/json" \
  -d '{
    "code": "1.01",
    "description": "Труд рабочих",
    "is_folder": false,
    "price": 500.0,
    "unit_id": 9,
    "labor_coefficient": 2.5
  }'
```

### 3. Create a Material

```bash
curl -X POST http://localhost:8000/api/materials \
  -H "Content-Type: application/json" \
  -d '{
    "code": "M001",
    "description": "Цемент",
    "price": 5000.0,
    "unit_id": 5
  }'
```

### 4. Get Work Composition

```bash
curl http://localhost:8000/api/works/1/composition
```

**Response:**
```json
{
  "work_id": 1,
  "work_name": "Штукатурка стен",
  "cost_items": [...],
  "materials": [...],
  "total_cost": 1250.0
}
```

### 5. Add Cost Item to Work

```bash
curl -X POST "http://localhost:8000/api/works/1/cost-items?cost_item_id=1"
```

### 6. Add Material to Work

```bash
curl -X POST http://localhost:8000/api/works/1/materials \
  -H "Content-Type: application/json" \
  -d '{
    "work_id": 1,
    "cost_item_id": 1,
    "material_id": 1,
    "quantity_per_unit": 0.015
  }'
```

### 7. Update Material Quantity

```bash
curl -X PUT http://localhost:8000/api/works/1/materials/1 \
  -H "Content-Type: application/json" \
  -d '{
    "quantity_per_unit": 0.020
  }'
```

---

## 🗄️ Database Quick Check

### Check Migration Status

```bash
python -m alembic current
```

**Expected Output:**
```
20251209_100000 (head)
```

### Check Tables

```bash
python check_db_state.py
```

**Expected Output:**
```
Units table exists: True
cost_item_materials columns:
  - id (INTEGER)
  - work_id (INTEGER)
  - cost_item_id (INTEGER)
  - material_id (INTEGER)
  - quantity_per_unit (FLOAT)
Has work_id column: True
```

---

## 🔍 Common Queries

### Get All Cost Items with Units

```sql
SELECT 
    ci.id,
    ci.code,
    ci.description,
    ci.price,
    u.name as unit_name
FROM cost_items ci
LEFT JOIN units u ON ci.unit_id = u.id
WHERE ci.marked_for_deletion = 0;
```

### Get Work Composition

```sql
SELECT 
    w.name as work_name,
    ci.description as cost_item,
    m.description as material,
    cim.quantity_per_unit
FROM cost_item_materials cim
JOIN works w ON cim.work_id = w.id
JOIN cost_items ci ON cim.cost_item_id = ci.id
LEFT JOIN materials m ON cim.material_id = m.id
WHERE w.id = 1;
```

### Get Materials for Work

```sql
SELECT 
    m.code,
    m.description,
    m.price,
    u.name as unit,
    cim.quantity_per_unit,
    (m.price * cim.quantity_per_unit) as total_cost
FROM cost_item_materials cim
JOIN materials m ON cim.material_id = m.id
LEFT JOIN units u ON m.unit_id = u.id
WHERE cim.work_id = 1 
  AND cim.material_id IS NOT NULL;
```

---

## 🐛 Troubleshooting

### Issue: API Won't Start

**Check:**
```bash
python -c "from api.main import app; print('OK')"
```

**If error, check:**
- Python virtual environment activated
- All dependencies installed: `pip install -r requirements.txt`
- Database file exists: `construction.db`

### Issue: Migration Not Applied

**Check current version:**
```bash
python -m alembic current
```

**Apply migration:**
```bash
python -m alembic upgrade head
```

### Issue: Import Errors

**Verify paths:**
```bash
python -c "import sys; print('\n'.join(sys.path))"
```

**Should include project root directory**

### Issue: Database Locked

**Solution:**
```bash
# Close all connections to database
# Restart server
python start_server.py
```

---

## 📚 Documentation Links

- **Full Schema:** `COMPLETE_DATA_LAYER_SPECIFICATION.md`
- **UI Design:** `WORK_FORM_UI_SPECIFICATION.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`
- **Completion Report:** `COMPLETION_REPORT.md`

---

## 🎓 Example Workflow

### Creating a Complete Work

```bash
# 1. Create cost items
curl -X POST http://localhost:8000/api/cost-items \
  -H "Content-Type: application/json" \
  -d '{"code": "1.01", "description": "Труд рабочих", "price": 500, "unit_id": 9}'

curl -X POST http://localhost:8000/api/cost-items \
  -H "Content-Type: application/json" \
  -d '{"code": "1.02", "description": "Аренда оборудования", "price": 200, "unit_id": 9}'

# 2. Create materials
curl -X POST http://localhost:8000/api/materials \
  -H "Content-Type: application/json" \
  -d '{"code": "M001", "description": "Цемент", "price": 5000, "unit_id": 5}'

curl -X POST http://localhost:8000/api/materials \
  -H "Content-Type: application/json" \
  -d '{"code": "M002", "description": "Песок", "price": 800, "unit_id": 5}'

# 3. Add cost items to work (assuming work_id=1)
curl -X POST "http://localhost:8000/api/works/1/cost-items?cost_item_id=1"
curl -X POST "http://localhost:8000/api/works/1/cost-items?cost_item_id=2"

# 4. Add materials to work
curl -X POST http://localhost:8000/api/works/1/materials \
  -H "Content-Type: application/json" \
  -d '{"work_id": 1, "cost_item_id": 1, "material_id": 1, "quantity_per_unit": 0.015}'

curl -X POST http://localhost:8000/api/works/1/materials \
  -H "Content-Type: application/json" \
  -d '{"work_id": 1, "cost_item_id": 1, "material_id": 2, "quantity_per_unit": 0.045}'

# 5. Get complete composition
curl http://localhost:8000/api/works/1/composition
```

---

## ✅ Health Check

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

---

## 🔐 Authentication

If authentication is enabled, add token to requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/units
```

---

**Quick Start Guide Version:** 1.0  
**Last Updated:** December 9, 2025  
**Status:** Ready for Use

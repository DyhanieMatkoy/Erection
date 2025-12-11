# Costs & Materials Integration Guide

This guide explains how to integrate the new Costs & Materials functionality into the Erection project.

## Overview

The Erection project has been enhanced to support Costs (Затраты) and Materials (Материалы) based on the 1C DBF schema. This integration allows for:

1. Hierarchical cost items structure
2. Materials catalog with pricing
3. Material consumption tracking in estimates and daily reports
4. Cost calculation with material components

## Database Schema Changes

### New Tables

1. **cost_items** - Hierarchical structure of cost items (from SC12.DBF)
   - Fields: id, parent_id, code, description, is_folder, price, unit, labor_coefficient
   - Supports nested structure with parent_id references

2. **materials** - Materials catalog (from SC25.DBF)
   - Fields: id, code, description, price, unit
   - Complete materials database with pricing

3. **cost_item_materials** - Association table linking cost items to materials
   - Fields: cost_item_id, material_id, quantity_per_unit
   - Defines material requirements for each cost item

### Enhanced Tables

1. **estimate_lines** - Added material tracking
   - New fields: material_id, material_quantity, material_price, material_sum
   - Allows specifying materials for each estimate line

2. **daily_report_lines** - Added material consumption tracking
   - New fields: material_id, planned_material_quantity, actual_material_quantity, material_deviation_percent
   - Tracks material usage in daily reports

## Migration Process

### 1. Database Migration

Run the Alembic migration to create the new tables:

```bash
cd f:\traeRepo\Vibe1Co\Erection\Erection
python -m alembic upgrade head
```

### 2. Data Migration

Import data from the 1C DBF files:

```bash
python scripts\database\migrate_costs_materials.py
```

This script will:
- Read SC12.DBF and import cost items into the cost_items table
- Read SC25.DBF and import materials into the materials table
- Maintain hierarchical relationships between cost items

## Usage Examples

### Working with Cost Items

```python
from src.data.models.sqlalchemy_models import CostItem
from src.data.database_manager import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize("construction.db")

# Get all root cost items (no parent)
with db_manager.session_scope() as session:
    root_items = session.query(CostItem).filter(CostItem.parent_id.is_(None)).all()
    
    for item in root_items:
        print(f"{item.code}: {item.description}")
        
        # Get child items
        children = session.query(CostItem).filter(CostItem.parent_id == item.id).all()
        for child in children:
            print(f"  {child.code}: {child.description}")
```

### Working with Materials

```python
from src.data.models.sqlalchemy_models import Material

# Search for materials
with db_manager.session_scope() as session:
    # Find materials by description
    materials = session.query(Material).filter(
        Material.description.like("%контейнер%")
    ).all()
    
    for material in materials:
        print(f"{material.code}: {material.description} - {material.price} {material.unit}")
```

### Creating Estimates with Materials

```python
from src.data.models.sqlalchemy_models import Estimate, EstimateLine, Material

# Create a new estimate with material tracking
with db_manager.session_scope() as session:
    # Create estimate
    estimate = Estimate(
        number="EST-2023-001",
        date=date.today(),
        customer_id=1,
        object_id=1,
        contractor_id=1,
        responsible_id=1
    )
    session.add(estimate)
    session.flush()  # Get the ID
    
    # Add estimate line with material
    material = session.query(Material).filter(Material.code == "MAT-001").first()
    
    line = EstimateLine(
        estimate_id=estimate.id,
        line_number=1,
        work_id=1,
        quantity=10,
        price=100.0,
        sum=1000.0,
        material_id=material.id if material else None,
        material_quantity=5.0,
        material_price=material.price if material else 0.0,
        material_sum=5.0 * (material.price if material else 0.0)
    )
    session.add(line)
```

### Tracking Material Consumption in Daily Reports

```python
from src.data.models.sqlalchemy_models import DailyReport, DailyReportLine, Material

# Create a daily report with material tracking
with db_manager.session_scope() as session:
    # Create daily report
    report = DailyReport(
        date=date.today(),
        estimate_id=1,
        foreman_id=1
    )
    session.add(report)
    session.flush()
    
    # Add report line with material consumption
    material = session.query(Material).filter(Material.code == "MAT-001").first()
    
    line = DailyReportLine(
        report_id=report.id,
        line_number=1,
        work_id=1,
        planned_labor=8.0,
        actual_labor=7.5,
        deviation_percent=-6.25,
        material_id=material.id if material else None,
        planned_material_quantity=5.0,
        actual_material_quantity=4.8,
        material_deviation_percent=-4.0
    )
    session.add(line)
```

## Repository Classes

For easier data access, you can use the repository pattern:

```python
from src.data.repositories.cost_item_repository import CostItemRepository
from src.data.repositories.material_repository import MaterialRepository

# Using repositories
cost_repo = CostItemRepository(db_manager)
material_repo = MaterialRepository(db_manager)

# Get cost items by code
cost_items = cost_repo.get_by_code_pattern("1.01%")

# Get materials by description
materials = material_repo.search_by_description("контейнер")
```

## UI Integration

To integrate the new functionality into the UI:

1. Add cost items selection to estimate forms
2. Add materials selection to estimate and daily report lines
3. Create cost items and materials management forms
4. Add material consumption reports

## Reporting

The new schema enables enhanced reporting:

1. Material consumption reports by project/date
2. Cost analysis with material breakdown
3. Material price variance reports
4. Inventory usage tracking

## Troubleshooting

### Migration Issues

If the migration fails:
1. Check that the DBF files exist at the specified paths
2. Verify database permissions
3. Check for encoding issues with Cyrillic text

### Performance Considerations

For large databases:
1. Add indexes on frequently queried fields (code, description)
2. Consider materializing hierarchical cost item views
3. Implement caching for material price lookups

## Future Enhancements

Potential future improvements:
1. Material inventory tracking
2. Supplier management for materials
3. Material price history
4. Automated material requirement calculations
5. Integration with procurement systems
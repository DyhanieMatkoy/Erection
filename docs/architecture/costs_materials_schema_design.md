# Costs & Materials Schema Design for Erection Project

## Analysis of DBF Structure

Based on the analysis of the DBF files from the 1C system:

### SC12 (Затраты - Costs)
- **Records**: 3,713
- **Purpose**: Project and estimate work types
- **Key Fields**:
  - ID: Unique identifier
  - PARENTID: Hierarchical structure support
  - CODE: Work code (e.g., "1.01.", "1.01-00006")
  - DESCR: Description in Russian (e.g., "ПРОЕКТНО СМЕТНЫЕ РАБОТЫ")
  - ISFOLDER: Flag indicating if item is a folder/group
  - SP15: Price/rate value
  - SP17: Unit of measurement
  - SP31: Labor coefficient

### SC25 (Материалы - Materials)
- **Records**: 1,596
- **Purpose**: Materials catalog
- **Key Fields**:
  - ID: Unique identifier
  - CODE: Material code
  - DESCR: Description in Russian (e.g., "Контейнер для мусора")
  - SP27: Price (Цена)
  - SP43: Unit of measurement (Ед. изм.)

## Proposed Schema Changes

### 1. New Tables

#### 1.1. CostItems Table (based on SC12)
```sql
CREATE TABLE cost_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NULL,
    code VARCHAR(50) NULL,
    description VARCHAR(500) NULL,
    is_folder BOOLEAN DEFAULT FALSE,
    price FLOAT DEFAULT 0.0,
    unit VARCHAR(50) NULL,
    labor_coefficient FLOAT DEFAULT 0.0,
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES cost_items(id)
);
```

#### 1.2. Materials Table (based on SC25)
```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NULL,
    description VARCHAR(500) NULL,
    price FLOAT DEFAULT 0.0,
    unit VARCHAR(50) NULL,
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Enhanced Existing Tables

#### 2.1. Enhanced EstimateLines
Add support for materials:
```sql
ALTER TABLE estimate_lines ADD COLUMN material_id INTEGER NULL;
ALTER TABLE estimate_lines ADD COLUMN material_quantity FLOAT DEFAULT 0.0;
ALTER TABLE estimate_lines ADD COLUMN material_price FLOAT DEFAULT 0.0;
ALTER TABLE estimate_lines ADD COLUMN material_sum FLOAT DEFAULT 0.0;

FOREIGN KEY (material_id) REFERENCES materials(id)
```

#### 2.2. Enhanced DailyReportLines
Add material consumption tracking:
```sql
ALTER TABLE daily_report_lines ADD COLUMN material_id INTEGER NULL;
ALTER TABLE daily_report_lines ADD COLUMN planned_material_quantity FLOAT DEFAULT 0.0;
ALTER TABLE daily_report_lines ADD COLUMN actual_material_quantity FLOAT DEFAULT 0.0;
ALTER TABLE daily_report_lines ADD COLUMN material_deviation_percent FLOAT DEFAULT 0.0;

FOREIGN KEY (material_id) REFERENCES materials(id)
```

### 3. New Association Tables

#### 3.1. CostItemMaterials (Many-to-Many)
```sql
CREATE TABLE cost_item_materials (
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity_per_unit FLOAT DEFAULT 0.0,
    PRIMARY KEY (cost_item_id, material_id),
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
```

### 4. SQLAlchemy Models

#### 4.1. CostItem Model
```python
class CostItem(Base):
    __tablename__ = 'cost_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('cost_items.id'))
    code = Column(String(50))
    description = Column(String(500))
    is_folder = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    unit = Column(String(50))
    labor_coefficient = Column(Float, default=0.0)
    marked_for_deletion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("CostItem", remote_side=[id], backref="children")
    materials = relationship("Material", secondary="cost_item_materials", backref="cost_items")
```

#### 4.2. Material Model
```python
class Material(Base):
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50))
    description = Column(String(500))
    price = Column(Float, default=0.0)
    unit = Column(String(50))
    marked_for_deletion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    estimate_lines = relationship("EstimateLine", backref="material")
    daily_report_lines = relationship("DailyReportLine", backref="material")
```

## Migration Strategy

1. Create new tables (cost_items, materials, cost_item_materials)
2. Migrate data from DBF files to new tables
3. Add new columns to existing tables
4. Update existing models and relationships
5. Create repository classes for new entities
6. Update UI components to support materials and costs

## Benefits

1. **Hierarchical Structure**: Support for nested cost items
2. **Material Tracking**: Complete material catalog with pricing
3. **Cost Estimation**: Better cost calculation with material components
4. **Reporting**: Enhanced reporting capabilities for material consumption
5. **Integration**: Seamless integration with existing estimate and daily report workflows
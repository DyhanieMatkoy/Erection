# Complete Data Layer Specification
## Construction Management System - Full Schema Documentation

**Version:** 2.0  
**Date:** December 9, 2025  
**Purpose:** Comprehensive data model specification for new project generation

---

## Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Entity Relationship Diagram](#entity-relationship-diagram)
4. [Core Entities](#core-entities)
5. [Costs & Materials Module](#costs--materials-module)
6. [Document Entities](#document-entities)
7. [Register Entities](#register-entities)
8. [API Models](#api-models)
9. [Business Rules](#business-rules)
10. [Migration Strategy](#migration-strategy)

---

## 1. Overview

### 1.1 System Architecture

The system follows a three-tier architecture:

**Desktop Application (Qt6/Python)**
- Data Layer: SQLAlchemy ORM
- Business Logic: Service Layer
- Presentation: ViewModels + Qt Views

**Web Application (Vue.js/TypeScript)**
- Backend API: FastAPI + Pydantic
- Frontend: Vue 3 + TypeScript + Pinia
- Communication: REST API with JSON

### 1.2 Database Support

- **SQLite**: Development, single-user deployments
- **PostgreSQL**: Production, multi-user deployments
- **Microsoft SQL Server**: Enterprise deployments

### 1.3 Key Design Principles

1. **Soft Delete**: All entities use `marked_for_deletion` flag
2. **Audit Trail**: `created_at`, `modified_at` timestamps
3. **Hierarchical Data**: Support for parent-child relationships
4. **Normalization**: Proper 3NF with strategic denormalization
5. **Indexing**: Comprehensive indexes for performance

---

## 2. Database Architecture

### 2.1 Schema Categories

```
┌─────────────────────────────────────────────────────────┐
│                   DATABASE SCHEMA                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │   REFERENCES     │  │   DOCUMENTS      │            │
│  │  (Справочники)   │  │   (Документы)    │            │
│  ├──────────────────┤  ├──────────────────┤            │
│  │ • Person         │  │ • Estimate       │            │
│  │ • Organization   │  │ • DailyReport    │            │
│  │ • Counterparty   │  │ • Timesheet      │            │
│  │ • Object         │  │                  │            │
│  │ • Work           │  └──────────────────┘            │
│  │ • CostItem       │                                   │
│  │ • Material       │  ┌──────────────────┐            │
│  │ • Unit           │  │   REGISTERS      │            │
│  └──────────────────┘  │   (Регистры)     │            │
│                        ├──────────────────┤            │
│  ┌──────────────────┐  │ • WorkExecution  │            │
│  │   SYSTEM         │  │ • Payroll        │            │
│  ├──────────────────┤  └──────────────────┘            │
│  │ • User           │                                   │
│  │ • UserSetting    │                                   │
│  │ • Constant       │                                   │
│  └──────────────────┘                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Entity Relationship Diagram

### 3.1 Core Relationships

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│     User     │────────>│    Person    │<────────│ Organization │
└──────────────┘         └──────────────┘         └──────────────┘
                                │                          │
                                │                          │
                                ▼                          ▼
                         ┌──────────────┐         ┌──────────────┐
                         │   Estimate   │<────────│ Counterparty │
                         └──────────────┘         └──────────────┘
                                │                          │
                                │                          │
                                ▼                          ▼
                         ┌──────────────┐         ┌──────────────┐
                         │EstimateLine  │         │    Object    │
                         └──────────────┘         └──────────────┘
                                │
                                │
                                ▼
                         ┌──────────────┐
                         │     Work     │
                         └──────────────┘
```

### 3.2 Costs & Materials Relationships

```
                         ┌──────────────┐
                         │     Work     │
                         └──────────────┘
                                │
                                │ (parent)
                                ▼
┌──────────────┐         ┌──────────────────────┐         ┌──────────────┐
│   CostItem   │<───────>│ CostItemMaterial     │<───────>│   Material   │
│              │         │ (Association Table)   │         │              │
└──────────────┘         └──────────────────────┘         └──────────────┘
       │                                                           │
       │                                                           │
       ▼                                                           ▼
┌──────────────┐                                          ┌──────────────┐
│     Unit     │                                          │     Unit     │
└──────────────┘                                          └──────────────┘
       ▲                                                           ▲
       │                                                           │
       └───────────────────────────────────────────────────────────┘
```

---

## 4. Core Entities

### 4.1 User (Authentication & Authorization)

**Table:** `users`

**Purpose:** User authentication and role-based access control

**Schema:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'admin', 'manager', 'foreman'
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    INDEX idx_username (username)
);
```

**Python Model:**
```python
@dataclass
class User:
    id: int = 0
    username: str = ""
    password_hash: str = ""
    role: str = ""
    is_active: bool = True
```

**TypeScript Model:**
```typescript
interface User {
  id: number
  username: string
  role: string
  is_active: boolean
}
```

**Business Rules:**
- Username must be unique
- Password must be hashed (bcrypt)
- Roles: admin, manager, foreman
- Soft delete not applicable (use is_active)

---

### 4.2 Person (Employees, Foremen)

**Table:** `persons`

**Purpose:** Physical persons (employees, foremen, responsible persons)

**Schema:**
```sql
CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    phone VARCHAR(50),
    hourly_rate FLOAT DEFAULT 0.0,
    user_id INTEGER,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES persons(id),
    
    INDEX idx_person_user (user_id),
    INDEX idx_person_parent (parent_id),
    INDEX idx_person_name (full_name)
);
```

**Relationships:**
- One-to-One with User (optional)
- Self-referencing (hierarchical structure)
- One-to-Many with Estimate (as responsible)
- One-to-Many with DailyReport (as foreman)
- One-to-Many with Timesheet (as foreman)
- One-to-Many with TimesheetLine (as employee)

**Business Rules:**
- full_name is required
- hourly_rate used for payroll calculations
- Hierarchical structure for organizational units
- Can be linked to a User account

---

### 4.3 Organization (Contractors, Companies)

**Table:** `organizations`

**Purpose:** Legal entities (contractors, construction companies)

**Schema:**
```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    inn VARCHAR(50),  -- Tax ID
    default_responsible_id INTEGER,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    
    FOREIGN KEY (default_responsible_id) REFERENCES persons(id),
    FOREIGN KEY (parent_id) REFERENCES organizations(id),
    
    INDEX idx_org_parent (parent_id),
    INDEX idx_org_name (name)
);
```

**Relationships:**
- Many-to-One with Person (default responsible)
- Self-referencing (hierarchical structure)
- One-to-Many with Estimate (as contractor)

---

### 4.4 Counterparty (Customers, Suppliers)

**Table:** `counterparties`

**Purpose:** Business partners (customers, suppliers)

**Schema:**
```sql
CREATE TABLE counterparties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    inn VARCHAR(50),
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    
    FOREIGN KEY (parent_id) REFERENCES counterparties(id),
    
    INDEX idx_counterparty_parent (parent_id),
    INDEX idx_counterparty_name (name)
);
```

**Relationships:**
- Self-referencing (hierarchical structure)
- One-to-Many with Estimate (as customer)
- One-to-Many with Object (as owner)

---

### 4.5 Object (Construction Sites)

**Table:** `objects`

**Purpose:** Construction sites/objects

**Schema:**
```sql
CREATE TABLE objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER,
    address TEXT,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    
    FOREIGN KEY (owner_id) REFERENCES counterparties(id),
    FOREIGN KEY (parent_id) REFERENCES objects(id),
    
    INDEX idx_object_owner (owner_id),
    INDEX idx_object_parent (parent_id),
    INDEX idx_object_name (name)
);
```

**Relationships:**
- Many-to-One with Counterparty (owner)
- Self-referencing (hierarchical structure)
- One-to-Many with Estimate
- One-to-Many with Timesheet
- One-to-Many with WorkExecutionRegister
- One-to-Many with PayrollRegister

---

### 4.6 Work (Work Types)

**Table:** `works`

**Purpose:** Types of construction work

**Schema:**
```sql
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(500) NOT NULL,
    code VARCHAR(50),
    unit VARCHAR(50),
    price FLOAT DEFAULT 0.0,
    labor_rate FLOAT DEFAULT 0.0,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    
    FOREIGN KEY (parent_id) REFERENCES works(id),
    
    INDEX idx_work_parent (parent_id),
    INDEX idx_work_name (name),
    INDEX idx_work_code (code)
);
```

**Relationships:**
- Self-referencing (hierarchical structure)
- One-to-Many with EstimateLine
- One-to-Many with DailyReportLine
- One-to-Many with WorkExecutionRegister
- One-to-Many with CostItemMaterial (cost items and materials composition)

**Business Rules:**
- name is required
- price and labor_rate used for cost calculations
- Hierarchical structure for work classification
- Each work type can have associated cost items and materials that define its composition

---

## 5. Costs & Materials Module

### 5.1 Unit (Measurement Units)

**Table:** `units`

**Purpose:** Standardized measurement units (м, м², м³, кг, т, шт, etc.)

**Schema:**
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_unit_name (name)
);
```

**Python Model:**
```python
@dataclass
class Unit:
    id: int = 0
    name: str = ""
    description: str = ""
    marked_for_deletion: bool = False
```

**TypeScript Model:**
```typescript
interface Unit {
  id: number
  name: string
  description?: string
  marked_for_deletion: boolean
}
```

**Business Rules:**
- name must be unique
- Common units: м (meter), м² (square meter), м³ (cubic meter), кг (kilogram), т (ton), шт (piece)
- Used by both CostItem and Material

**Sample Data:**
```sql
INSERT INTO units (name, description) VALUES
('м', 'Метр'),
('м²', 'Квадратный метр'),
('м³', 'Кубический метр'),
('кг', 'Килограмм'),
('т', 'Тонна'),
('шт', 'Штука'),
('л', 'Литр'),
('компл', 'Комплект');
```

---

### 5.2 CostItem (Cost Elements)

**Table:** `cost_items`

**Purpose:** Hierarchical catalog of cost elements/work types from 1C system

**Schema:**
```sql
CREATE TABLE cost_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    code VARCHAR(50),
    description VARCHAR(500),
    is_folder BOOLEAN DEFAULT FALSE,
    price FLOAT DEFAULT 0.0,
    unit VARCHAR(50),  -- Legacy field for backward compatibility
    unit_id INTEGER,   -- Foreign key to units table
    labor_coefficient FLOAT DEFAULT 0.0,
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES cost_items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    
    INDEX idx_cost_item_parent (parent_id),
    INDEX idx_cost_item_code (code),
    INDEX idx_cost_item_description (description)
);
```

**Python Model:**
```python
@dataclass
class CostItem:
    id: int = 0
    parent_id: int = None
    code: str = ""
    description: str = ""
    is_folder: bool = False
    price: float = 0.0
    unit: str = ""  # Legacy
    unit_id: int = None
    labor_coefficient: float = 0.0
    marked_for_deletion: bool = False
```

**TypeScript Model:**
```typescript
interface CostItem {
  id: number
  parent_id: number | null
  code: string
  description: string
  is_folder: boolean
  price: number
  unit?: string  // Legacy
  unit_id?: number
  unit_name?: string  // Joined from units
  labor_coefficient: number
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
  materials?: CostItemMaterial[]  // Associated materials
}
```

**Relationships:**
- Self-referencing (hierarchical structure)
- Many-to-One with Unit
- Many-to-Many with Work and Material (through CostItemMaterial)

**Business Rules:**
- Hierarchical structure (folders and items)
- Folders (is_folder=true) cannot have price, unit, or labor_coefficient
- Non-folder items can be associated with work types and materials
- code format: "1.01.", "1.01-00006", etc.
- Imported from 1C DBF files (SC12 table)
- Used to define work composition (e.g., "Labor", "Equipment rental")

**Repository Methods:**
```python
class CostItemRepository:
    def find_by_id(cost_item_id: int) -> CostItem
    def find_by_code(code: str) -> CostItem
    def find_all(include_deleted: bool = False) -> List[CostItem]
    def find_root_items() -> List[CostItem]
    def find_by_parent(parent_id: int) -> List[CostItem]
    def find_folders() -> List[CostItem]
    def find_non_folders() -> List[CostItem]
    def save(cost_item: CostItem) -> CostItem
    def delete(cost_item_id: int) -> bool
    def add_material(cost_item_id: int, material_id: int, quantity: float) -> bool
    def remove_material(cost_item_id: int, material_id: int) -> bool
    def get_materials(cost_item_id: int) -> List[Material]
    def save_materials(cost_item_id: int, materials: List[Dict]) -> bool
```

---

### 5.3 Material (Materials Catalog)

**Table:** `materials`

**Purpose:** Catalog of construction materials

**Schema:**
```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50),
    description VARCHAR(500),
    price FLOAT DEFAULT 0.0,
    unit VARCHAR(50),  -- Legacy field for backward compatibility
    unit_id INTEGER,   -- Foreign key to units table
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (unit_id) REFERENCES units(id),
    
    INDEX idx_material_code (code),
    INDEX idx_material_description (description)
);
```

**Python Model:**
```python
@dataclass
class Material:
    id: int = 0
    code: str = ""
    description: str = ""
    price: float = 0.0
    unit: str = ""  # Legacy
    unit_id: int = None
    marked_for_deletion: bool = False
```

**TypeScript Model:**
```typescript
interface Material {
  id: number
  code: string
  description: string
  price: number
  unit?: string  // Legacy
  unit_id?: number
  unit_name?: string  // Joined from units
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
}
```

**Relationships:**
- Many-to-One with Unit
- Many-to-Many with Work and CostItem (through CostItemMaterial)
- One-to-Many with EstimateLine
- One-to-Many with DailyReportLine

**Business Rules:**
- description is required
- price is per unit
- Imported from 1C DBF files (SC25 table)
- Used to define material consumption for work types

**Repository Methods:**
```python
class MaterialRepository:
    def find_by_id(material_id: int) -> Material
    def find_by_code(code: str) -> Material
    def find_all(include_deleted: bool = False) -> List[Material]
    def search_by_description(search_term: str) -> List[Material]
    def find_by_unit(unit: str) -> List[Material]
    def find_by_price_range(min_price: float, max_price: float) -> List[Material]
    def get_unique_units() -> List[str]
    def save(material: Material) -> Material
    def delete(material_id: int) -> bool
    def get_cost_items(material_id: int) -> List[CostItem]
    def get_material_consumption(material_id: int) -> float
```

---

### 5.4 CostItemMaterial (Association Table)

**Table:** `cost_item_materials`

**Purpose:** Many-to-many relationship between cost items and materials, linked to work types

**Schema:**
```sql
CREATE TABLE cost_item_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity_per_unit FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    
    INDEX idx_cost_item_material_work (work_id),
    INDEX idx_cost_item_material_cost_item (cost_item_id),
    INDEX idx_cost_item_material_material (material_id),
    UNIQUE (work_id, cost_item_id, material_id)
);
```

**Python Model:**
```python
@dataclass
class CostItemMaterial:
    id: int = 0
    work_id: int = 0
    cost_item_id: int = 0
    material_id: int = 0
    quantity_per_unit: float = 0.0
```

**TypeScript Model:**
```typescript
interface CostItemMaterial {
  id: number
  work_id: number
  cost_item_id: number
  material_id: number
  quantity_per_unit: number
  work?: Work  // Populated when joined
  cost_item?: CostItem  // Populated when joined
  material?: Material  // Populated when joined
}
```

**Relationships:**
- Many-to-One with Work (parent)
- Many-to-One with CostItem
- Many-to-One with Material

**Business Rules:**
- work_id is required - all cost items and materials must be associated with a work type
- quantity_per_unit: how much material is needed per unit of cost item for this work
- Example: Work "Plastering" uses CostItem "Labor" + Material "Cement" (0.015 т per м²)
- UNIQUE constraint prevents duplicate associations for same work/cost_item/material combination
- Used for automatic material calculation in estimates based on work type

**Repository Methods:**
```python
class CostItemMaterialRepository:
    def find_by_id(id: int) -> CostItemMaterial
    def find_association(work_id: int, cost_item_id: int, material_id: int) -> CostItemMaterial
    def get_all_associations() -> List[CostItemMaterial]
    def get_associations_for_work(work_id: int) -> List[CostItemMaterial]
    def get_associations_for_cost_item(cost_item_id: int) -> List[CostItemMaterial]
    def get_associations_for_material(material_id: int) -> List[CostItemMaterial]
    def create_or_update_association(work_id: int, cost_item_id: int, material_id: int, quantity: float) -> CostItemMaterial
    def remove_association(id: int) -> bool
    def get_cost_items_for_work(work_id: int) -> List[Tuple[CostItem, float]]
    def get_materials_for_work(work_id: int) -> List[Tuple[Material, float]]
    def calculate_total_cost_for_work(work_id: int) -> float
    def find_cost_items_not_in_work(work_id: int) -> List[CostItem]
    def find_materials_not_in_work(work_id: int) -> List[Material]
```

---

## 6. Document Entities

### 6.1 Estimate (Смета)

**Table:** `estimates`

**Purpose:** Construction estimate/budget document

**Schema:**
```sql
CREATE TABLE estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    customer_id INTEGER,
    object_id INTEGER,
    contractor_id INTEGER,
    responsible_id INTEGER,
    total_sum FLOAT DEFAULT 0.0,
    total_labor FLOAT DEFAULT 0.0,
    is_posted BOOLEAN DEFAULT FALSE,
    posted_at DATETIME,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES counterparties(id),
    FOREIGN KEY (object_id) REFERENCES objects(id),
    FOREIGN KEY (contractor_id) REFERENCES organizations(id),
    FOREIGN KEY (responsible_id) REFERENCES persons(id),
    
    INDEX idx_estimate_date (date),
    INDEX idx_estimate_responsible (responsible_id),
    INDEX idx_estimate_number (number)
);
```

**Relationships:**
- Many-to-One with Counterparty (customer)
- Many-to-One with Object
- Many-to-One with Organization (contractor)
- Many-to-One with Person (responsible)
- One-to-Many with EstimateLine
- One-to-Many with DailyReport
- One-to-Many with Timesheet

**Business Rules:**
- number must be unique
- total_sum and total_labor are calculated from lines
- is_posted: document is finalized and creates register entries
- posted_at: timestamp when document was posted

---

### 6.2 EstimateLine (Estimate Line Items)

**Table:** `estimate_lines`

**Purpose:** Line items in estimate document

**Schema:**
```sql
CREATE TABLE estimate_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    work_id INTEGER,
    quantity FLOAT DEFAULT 0.0,
    unit VARCHAR(50),
    price FLOAT DEFAULT 0.0,
    labor_rate FLOAT DEFAULT 0.0,
    sum FLOAT DEFAULT 0.0,
    planned_labor FLOAT DEFAULT 0.0,
    is_group BOOLEAN DEFAULT FALSE,
    group_name VARCHAR(500),
    parent_group_id INTEGER,
    is_collapsed BOOLEAN DEFAULT FALSE,
    material_id INTEGER,
    material_quantity FLOAT DEFAULT 0.0,
    material_price FLOAT DEFAULT 0.0,
    material_sum FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (parent_group_id) REFERENCES estimate_lines(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    
    INDEX idx_estimate_line_estimate (estimate_id),
    INDEX idx_estimate_line_work (work_id),
    INDEX idx_estimate_line_number (estimate_id, line_number)
);
```

**Business Rules:**
- line_number: sequential number within estimate
- is_group: true for group headers (folders)
- Groups can have child lines (parent_group_id)
- sum = quantity * price
- planned_labor = quantity * labor_rate
- material_sum = material_quantity * material_price
- Material tracking is optional per line

**Calculations:**
```python
# Line calculations
sum = quantity * price
planned_labor = quantity * labor_rate
material_sum = material_quantity * material_price

# Estimate totals
total_sum = SUM(sum) for all non-group lines
total_labor = SUM(planned_labor) for all non-group lines
```

---

### 6.3 DailyReport (Ежедневный отчет)

**Table:** `daily_reports`

**Purpose:** Daily work execution report

**Schema:**
```sql
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(50),
    date DATE NOT NULL,
    estimate_id INTEGER,
    foreman_id INTEGER,
    is_posted BOOLEAN DEFAULT FALSE,
    posted_at DATETIME,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (foreman_id) REFERENCES persons(id),
    
    INDEX idx_daily_report_date (date),
    INDEX idx_daily_report_estimate (estimate_id)
);
```

**Relationships:**
- Many-to-One with Estimate
- Many-to-One with Person (foreman)
- One-to-Many with DailyReportLine

**Business Rules:**
- date: work execution date
- estimate_id: links to estimate being executed
- foreman_id: person responsible for the work
- When posted, creates WorkExecutionRegister entries

---

### 6.4 DailyReportLine (Daily Report Line Items)

**Table:** `daily_report_lines`

**Purpose:** Line items in daily report

**Schema:**
```sql
CREATE TABLE daily_report_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    work_id INTEGER,
    planned_labor FLOAT DEFAULT 0.0,
    actual_labor FLOAT DEFAULT 0.0,
    deviation_percent FLOAT DEFAULT 0.0,
    is_group BOOLEAN DEFAULT FALSE,
    group_name VARCHAR(500),
    parent_group_id INTEGER,
    is_collapsed BOOLEAN DEFAULT FALSE,
    material_id INTEGER,
    planned_material_quantity FLOAT DEFAULT 0.0,
    actual_material_quantity FLOAT DEFAULT 0.0,
    material_deviation_percent FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (report_id) REFERENCES daily_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (parent_group_id) REFERENCES daily_report_lines(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    
    INDEX idx_daily_report_line_report (report_id),
    INDEX idx_daily_report_line_work (work_id),
    INDEX idx_daily_report_line_number (report_id, line_number)
);
```

**Relationships:**
- Many-to-One with DailyReport
- Many-to-One with Work
- Self-referencing (parent_group_id for grouping)
- Many-to-One with Material
- Many-to-Many with Person (through DailyReportExecutor)

**Business Rules:**
- planned_labor: from estimate
- actual_labor: actual hours worked
- deviation_percent = ((actual_labor - planned_labor) / planned_labor) * 100
- material_deviation_percent = ((actual_material_quantity - planned_material_quantity) / planned_material_quantity) * 100

---

### 6.5 DailyReportExecutor (Association Table)

**Table:** `daily_report_executors`

**Purpose:** Many-to-many relationship between report lines and executors

**Schema:**
```sql
CREATE TABLE daily_report_executors (
    report_line_id INTEGER NOT NULL,
    executor_id INTEGER NOT NULL,
    
    PRIMARY KEY (report_line_id, executor_id),
    FOREIGN KEY (report_line_id) REFERENCES daily_report_lines(id) ON DELETE CASCADE,
    FOREIGN KEY (executor_id) REFERENCES persons(id)
);
```

**Business Rules:**
- Tracks which employees worked on which tasks
- Multiple executors can work on same task
- Used for payroll calculations

---

### 6.6 Timesheet (Табель учета рабочего времени)

**Table:** `timesheets`

**Purpose:** Monthly timesheet for tracking employee hours

**Schema:**
```sql
CREATE TABLE timesheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    object_id INTEGER,
    estimate_id INTEGER,
    foreman_id INTEGER,
    month_year VARCHAR(20) NOT NULL,  -- "YYYY-MM"
    is_posted BOOLEAN DEFAULT FALSE,
    posted_at DATETIME,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES objects(id),
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (foreman_id) REFERENCES persons(id),
    
    INDEX idx_timesheet_date (date),
    INDEX idx_timesheet_object (object_id),
    INDEX idx_timesheet_estimate (estimate_id),
    INDEX idx_timesheet_foreman (foreman_id)
);
```

**Relationships:**
- Many-to-One with Object
- Many-to-One with Estimate
- Many-to-One with Person (foreman)
- One-to-Many with TimesheetLine

**Business Rules:**
- month_year format: "YYYY-MM" (e.g., "2025-12")
- One timesheet per object/estimate per month
- When posted, creates PayrollRegister entries

---

### 6.7 TimesheetLine (Timesheet Line Items)

**Table:** `timesheet_lines`

**Purpose:** Employee hours for each day of the month

**Current Schema (NEEDS REFACTORING):**
```sql
CREATE TABLE timesheet_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    employee_id INTEGER,
    hourly_rate FLOAT DEFAULT 0.0,
    day_01 FLOAT DEFAULT 0.0,
    day_02 FLOAT DEFAULT 0.0,
    -- ... 31 columns total
    day_31 FLOAT DEFAULT 0.0,
    total_hours FLOAT DEFAULT 0.0,
    total_amount FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (timesheet_id) REFERENCES timesheets(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES persons(id),
    
    INDEX idx_timesheet_line_timesheet (timesheet_id),
    INDEX idx_timesheet_line_employee (employee_id)
);
```

**⚠️ CRITICAL ISSUE:** The day_01 through day_31 columns violate database normalization.

**RECOMMENDED REFACTORED SCHEMA:**

**Table 1:** `timesheet_lines` (simplified)
```sql
CREATE TABLE timesheet_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    hourly_rate FLOAT DEFAULT 0.0,
    total_hours FLOAT DEFAULT 0.0,  -- Computed from day entries
    total_amount FLOAT DEFAULT 0.0,  -- Computed: total_hours * hourly_rate
    
    FOREIGN KEY (timesheet_id) REFERENCES timesheets(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES persons(id),
    
    INDEX idx_timesheet_line_timesheet (timesheet_id),
    INDEX idx_timesheet_line_employee (employee_id),
    UNIQUE (timesheet_id, employee_id)
);
```

**Table 2:** `timesheet_day_entries` (NEW)
```sql
CREATE TABLE timesheet_day_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_line_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,  -- 1-31
    hours_worked FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (timesheet_line_id) REFERENCES timesheet_lines(id) ON DELETE CASCADE,
    
    INDEX idx_timesheet_day_line (timesheet_line_id),
    INDEX idx_timesheet_day_number (timesheet_line_id, day_number),
    UNIQUE (timesheet_line_id, day_number)
);
```

**Benefits of Refactored Schema:**
- ✅ Proper normalization (1NF)
- ✅ Flexible for any month length
- ✅ Easy to query specific days
- ✅ Better indexing performance
- ✅ Reduced storage for partial months

**TypeScript Models (Refactored):**
```typescript
interface TimesheetLine {
  id: number
  timesheet_id: number
  line_number: number
  employee_id: number
  employee_name?: string
  hourly_rate: number
  total_hours: number
  total_amount: number
  days: Record<number, number>  // {1: 8.0, 2: 7.5, ...}
}

interface TimesheetDayEntry {
  id: number
  timesheet_line_id: number
  day_number: number
  hours_worked: number
}
```

---

## 7. Register Entities

### 7.1 WorkExecutionRegister (Регистр выполнения работ)

**Table:** `work_execution_register`

**Purpose:** Accumulation register for tracking work execution (income/expense)

**Schema:**
```sql
CREATE TABLE work_execution_register (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorder_type VARCHAR(50) NOT NULL,  -- 'Estimate', 'DailyReport'
    recorder_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    period DATE NOT NULL,
    object_id INTEGER,
    estimate_id INTEGER,
    work_id INTEGER,
    quantity_income FLOAT DEFAULT 0.0,
    quantity_expense FLOAT DEFAULT 0.0,
    sum_income FLOAT DEFAULT 0.0,
    sum_expense FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES objects(id),
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (work_id) REFERENCES works(id),
    
    INDEX idx_register_recorder (recorder_type, recorder_id),
    INDEX idx_register_dimensions (period, object_id, estimate_id, work_id),
    INDEX idx_register_period (period)
);
```

**Business Rules:**
- **Income movements**: Created when Estimate is posted (planned work)
  - quantity_income = estimate line quantity
  - sum_income = estimate line sum
- **Expense movements**: Created when DailyReport is posted (actual work)
  - quantity_expense = actual quantity completed
  - sum_expense = actual cost
- **Balance**: income - expense = remaining work
- recorder_type + recorder_id: identifies source document

**Query Examples:**
```sql
-- Get work balance for an estimate
SELECT 
    work_id,
    SUM(quantity_income) - SUM(quantity_expense) as balance_quantity,
    SUM(sum_income) - SUM(sum_expense) as balance_sum
FROM work_execution_register
WHERE estimate_id = ?
GROUP BY work_id;

-- Get work execution for a period
SELECT 
    period,
    object_id,
    work_id,
    SUM(quantity_expense) as completed_quantity,
    SUM(sum_expense) as completed_sum
FROM work_execution_register
WHERE period BETWEEN ? AND ?
GROUP BY period, object_id, work_id;
```

---

### 7.2 PayrollRegister (Регистр начислений зарплаты)

**Table:** `payroll_register`

**Purpose:** Accumulation register for tracking employee payroll

**Schema:**
```sql
CREATE TABLE payroll_register (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorder_type VARCHAR(50) NOT NULL,  -- 'Timesheet'
    recorder_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    period DATE NOT NULL,
    object_id INTEGER,
    estimate_id INTEGER,
    employee_id INTEGER,
    work_date DATE NOT NULL,
    hours_worked FLOAT DEFAULT 0.0,
    amount FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES objects(id),
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (employee_id) REFERENCES persons(id),
    
    INDEX idx_payroll_recorder (recorder_type, recorder_id),
    INDEX idx_payroll_dimensions (period, object_id, estimate_id, employee_id),
    INDEX idx_payroll_period (period),
    INDEX idx_payroll_employee (employee_id),
    UNIQUE (object_id, estimate_id, employee_id, work_date)
);
```

**Business Rules:**
- Created when Timesheet is posted
- period: month of the timesheet
- work_date: specific day worked
- amount = hours_worked * hourly_rate
- UNIQUE constraint prevents duplicate entries for same employee/date

**Query Examples:**
```sql
-- Get employee payroll for a month
SELECT 
    employee_id,
    SUM(hours_worked) as total_hours,
    SUM(amount) as total_amount
FROM payroll_register
WHERE period = ?
GROUP BY employee_id;

-- Get payroll by object
SELECT 
    object_id,
    employee_id,
    SUM(hours_worked) as total_hours,
    SUM(amount) as total_amount
FROM payroll_register
WHERE period BETWEEN ? AND ?
GROUP BY object_id, employee_id;
```

---

## 8. API Models

### 8.1 Pydantic Models (Backend)

**Authentication Models:**
```python
class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
```

**Reference Models:**
```python
class ReferenceBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    is_deleted: bool = False

class Reference(ReferenceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Cost & Material Models:**
```python
class UnitBase(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(UnitBase):
    id: int
    marked_for_deletion: bool = False

class CostItemBase(BaseModel):
    parent_id: Optional[int] = None
    code: Optional[str] = None
    description: str
    is_folder: bool = False
    price: float = 0.0
    unit_id: Optional[int] = None
    labor_coefficient: float = 0.0

class CostItem(CostItemBase):
    id: int
    unit_name: Optional[str] = None
    marked_for_deletion: bool = False
    materials: List[CostItemMaterial] = []

class MaterialBase(BaseModel):
    code: Optional[str] = None
    description: str
    price: float = 0.0
    unit_id: Optional[int] = None

class Material(MaterialBase):
    id: int
    unit_name: Optional[str] = None
    marked_for_deletion: bool = False

class CostItemMaterialBase(BaseModel):
    work_id: int
    cost_item_id: int
    material_id: int
    quantity_per_unit: float = 0.0

class CostItemMaterialCreate(CostItemMaterialBase):
    pass

class CostItemMaterial(CostItemMaterialBase):
    id: int
    work: Optional[Work] = None
    cost_item: Optional[CostItem] = None
    material: Optional[Material] = None

class WorkComposition(BaseModel):
    """Complete work composition with cost items and materials"""
    work: Work
    cost_items: List[CostItemMaterial] = []
    materials: List[CostItemMaterial] = []
    total_cost: float = 0.0
```

**Document Models:**
```python
class EstimateLineBase(BaseModel):
    line_number: int
    work_id: Optional[int] = None
    quantity: float = 0.0
    unit: Optional[str] = None
    price: float = 0.0
    labor_rate: float = 0.0
    sum: float = 0.0
    planned_labor: float = 0.0
    is_group: bool = False
    group_name: Optional[str] = None
    parent_group_id: Optional[int] = None
    material_id: Optional[int] = None
    material_quantity: float = 0.0
    material_price: float = 0.0
    material_sum: float = 0.0

class EstimateLine(EstimateLineBase):
    id: int
    estimate_id: int
    work_name: Optional[str] = None
    material_name: Optional[str] = None

class EstimateBase(BaseModel):
    number: str
    date: date
    customer_id: Optional[int] = None
    object_id: Optional[int] = None
    contractor_id: Optional[int] = None
    responsible_id: Optional[int] = None

class Estimate(EstimateBase):
    id: int
    total_sum: float = 0.0
    total_labor: float = 0.0
    is_posted: bool = False
    posted_at: Optional[datetime] = None
    marked_for_deletion: bool = False
    lines: List[EstimateLine] = []
    # Joined fields
    customer_name: Optional[str] = None
    object_name: Optional[str] = None
    contractor_name: Optional[str] = None
    responsible_name: Optional[str] = None
```

---

### 8.2 TypeScript Models (Frontend)

**Complete TypeScript Type Definitions:**

```typescript
// ============================================================================
// Reference Types
// ============================================================================

export interface Unit {
  id: number
  name: string
  description?: string
  marked_for_deletion: boolean
}

export interface Counterparty {
  id: number
  name: string
  inn?: string
  contact_person?: string
  phone?: string
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Object {
  id: number
  name: string
  address?: string
  owner_id?: number | null
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Work {
  id: number
  name: string
  code?: string
  unit?: string
  price?: number
  labor_rate?: number
  parent_id: number | null
  is_group: boolean
  marked_for_deletion: boolean
  created_at: string
  updated_at: string
  cost_items?: CostItemMaterial[]  // Associated cost items
  materials?: CostItemMaterial[]   // Associated materials
}

export interface Person {
  id: number
  full_name: string
  position?: string
  phone?: string
  hourly_rate?: number
  user_id?: number
  parent_id: number | null
  is_group: boolean
  marked_for_deletion: boolean
  created_at: string
  updated_at: string
}

export interface Organization {
  id: number
  name: string
  inn?: string
  default_responsible_id?: number
  parent_id: number | null
  is_group: boolean
  marked_for_deletion: boolean
  created_at: string
  updated_at: string
}

// ============================================================================
// Costs & Materials Types
// ============================================================================

export interface CostItem {
  id: number
  parent_id: number | null
  code?: string
  description: string
  is_folder: boolean
  price: number
  unit?: string  // Legacy
  unit_id?: number
  unit_name?: string
  labor_coefficient: number
  marked_for_deletion: boolean
  created_at: string
  modified_at: string
  materials?: CostItemMaterial[]
}

export interface Material {
  id: number
  code?: string
  description: string
  price: number
  unit?: string  // Legacy
  unit_id?: number
  unit_name?: string
  marked_for_deletion: boolean
  created_at: string
  modified_at: string
}

export interface CostItemMaterial {
  id: number
  work_id: number
  cost_item_id: number
  material_id: number
  quantity_per_unit: number
  work?: Work
  cost_item?: CostItem
  material?: Material
}

// ============================================================================
// Document Types
// ============================================================================

export interface EstimateLine {
  id?: number
  estimate_id?: number
  line_number: number
  work_id: number | null
  work_name?: string
  quantity: number
  unit?: string
  price: number
  labor_rate: number
  sum: number
  planned_labor: number
  is_group: boolean
  group_name?: string
  parent_group_id: number | null
  is_collapsed: boolean
  material_id?: number
  material_name?: string
  material_quantity: number
  material_price: number
  material_sum: number
}

export interface Estimate {
  id?: number
  number: string
  date: string
  customer_id: number
  customer_name?: string
  object_id: number
  object_name?: string
  contractor_id: number
  contractor_name?: string
  responsible_id: number
  responsible_name?: string
  total_sum: number
  total_labor: number
  is_posted: boolean
  posted_at: string | null
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
  lines?: EstimateLine[]
}

export interface DailyReportLine {
  id?: number
  report_id?: number
  line_number: number
  work_id?: number
  work_name?: string
  planned_labor: number
  actual_labor: number
  deviation_percent: number
  is_group: boolean
  group_name?: string
  parent_group_id: number | null
  is_collapsed: boolean
  material_id?: number
  material_name?: string
  planned_material_quantity: number
  actual_material_quantity: number
  material_deviation_percent: number
  executors?: number[]
  executor_names?: string[]
}

export interface DailyReport {
  id?: number
  number?: string
  date: string
  estimate_id: number
  estimate_number?: string
  foreman_id: number
  foreman_name?: string
  is_posted: boolean
  posted_at: string | null
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
  lines?: DailyReportLine[]
}

export interface TimesheetLine {
  id?: number
  timesheet_id?: number
  line_number: number
  employee_id: number
  employee_name?: string
  hourly_rate: number
  days: Record<number, number>  // {1: 8.0, 2: 7.5, ...}
  total_hours: number
  total_amount: number
}

export interface Timesheet {
  id?: number
  number: string
  date: string
  object_id: number
  object_name?: string
  estimate_id: number
  estimate_number?: string
  foreman_id: number
  foreman_name?: string
  month_year: string  // "YYYY-MM"
  is_posted: boolean
  posted_at: string | null
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
  lines?: TimesheetLine[]
}

// ============================================================================
// Register Types
// ============================================================================

export interface WorkExecutionMovement {
  id: number
  recorder_type: string
  recorder_id: number
  period: string
  object_id: number
  object_name: string
  estimate_id: number
  estimate_number: string
  work_id: number
  work_name: string
  quantity_income: number
  quantity_expense: number
  sum_income: number
  sum_expense: number
  balance_quantity: number
  balance_sum: number
}

export interface PayrollMovement {
  id: number
  recorder_type: string
  recorder_id: number
  period: string
  object_id: number
  object_name: string
  estimate_id: number
  estimate_number: string
  employee_id: number
  employee_name: string
  work_date: string
  hours_worked: number
  amount: number
}
```

---

## 9. Business Rules

### 9.1 Document Posting Rules

**Estimate Posting:**
1. Validate all required fields
2. Calculate totals from lines
3. Create WorkExecutionRegister entries (income movements)
4. Set is_posted = true, posted_at = now()
5. Lock document for editing

**DailyReport Posting:**
1. Validate estimate_id exists and is posted
2. Validate all work_ids match estimate
3. Create WorkExecutionRegister entries (expense movements)
4. Set is_posted = true, posted_at = now()
5. Lock document for editing

**Timesheet Posting:**
1. Validate all employee_ids exist
2. Calculate totals for each line
3. Create PayrollRegister entries for each day
4. Set is_posted = true, posted_at = now()
5. Lock document for editing

**Unposting:**
1. Delete all register entries where recorder_type + recorder_id match
2. Set is_posted = false, posted_at = null
3. Unlock document for editing

---

### 9.2 Calculation Rules

**Estimate Line Calculations:**
```python
# Basic calculations
sum = quantity * price
planned_labor = quantity * labor_rate

# Material calculations (if material_id is set)
material_sum = material_quantity * material_price

# Estimate totals (sum of all non-group lines)
total_sum = SUM(sum WHERE is_group = false)
total_labor = SUM(planned_labor WHERE is_group = false)
```

**Daily Report Line Calculations:**
```python
# Deviation calculations
deviation_percent = ((actual_labor - planned_labor) / planned_labor) * 100

# Material deviation (if material tracking enabled)
material_deviation_percent = (
    (actual_material_quantity - planned_material_quantity) / 
    planned_material_quantity
) * 100
```

**Timesheet Line Calculations:**
```python
# Total hours (sum of all days)
total_hours = SUM(day_01, day_02, ..., day_31)

# Total amount
total_amount = total_hours * hourly_rate
```

---

### 9.3 Validation Rules

**Estimate Validation:**
- number: required, max 50 chars
- date: required, cannot be future date
- customer_id: required, must exist
- object_id: required, must exist
- contractor_id: required, must exist
- responsible_id: required, must exist
- lines: at least one non-group line required

**EstimateLine Validation:**
- line_number: required, must be unique within estimate
- work_id: required for non-group lines
- quantity: must be >= 0
- price: must be >= 0
- Groups (is_group=true) cannot have work_id, quantity, price

**DailyReport Validation:**
- date: required
- estimate_id: required, estimate must be posted
- foreman_id: required, must exist
- lines: at least one line required

**DailyReportLine Validation:**
- work_id: must match work in estimate
- planned_labor: must match estimate line
- actual_labor: must be >= 0
- At least one executor required

**Timesheet Validation:**
- number: required, max 50 chars
- date: required
- month_year: required, format "YYYY-MM"
- object_id: required, must exist
- estimate_id: required, must exist
- foreman_id: required, must exist
- lines: at least one line required

**TimesheetLine Validation:**
- employee_id: required, must exist
- hourly_rate: must be >= 0
- day values: must be >= 0, typically 0-24

---

### 9.4 Soft Delete Rules

**All reference and document entities use soft delete:**
- Set `marked_for_deletion = true` instead of DELETE
- Queries should filter `WHERE marked_for_deletion = false` by default
- Admin interface can show deleted items with option to restore
- Posted documents cannot be deleted (must unpost first)

**Cascade Rules:**
- When parent is soft-deleted, children remain accessible
- When document is soft-deleted, lines are also soft-deleted
- Register entries are NOT soft-deleted (they are hard-deleted on unpost)

---

### 9.5 Hierarchical Data Rules

**Entities with hierarchical structure:**
- Person (organizational units)
- Organization (company structure)
- Counterparty (customer groups)
- Object (object groups)
- Work (work classification)
- CostItem (cost classification)

**Rules:**
- parent_id can be null (root items)
- is_group/is_folder indicates folder items
- Folders cannot have certain fields (price, quantity, etc.)
- Circular references must be prevented
- Deletion of parent should not cascade to children

---

### 9.6 Material Tracking Rules

**EstimateLine Material Tracking:**
- material_id is optional
- If set, material_quantity and material_price should be populated
- material_sum = material_quantity * material_price
- Material can be auto-populated from CostItem associations

**DailyReportLine Material Tracking:**
- material_id is optional
- If set, track planned vs actual material consumption
- material_deviation_percent shows over/under consumption
- Used for material cost control

**Work-CostItem-Material Associations:**
- work_id is required - defines which work type this composition belongs to
- quantity_per_unit defines material consumption rate per cost item
- Example: Work "Plastering" → CostItem "Labor" + Material "Cement" (0.015 т per м²)
- Used to auto-calculate material requirements in estimates based on work type
- UNIQUE constraint ensures no duplicate associations

---

### 9.7 Work Form Composition Rules

**Work Form UI Requirements:**

The Work form must include two tables for defining work composition:

**Table 1: Cost Items Table**
- Displays all cost items associated with this work
- Columns:
  - Code (from CostItem)
  - Description (from CostItem)
  - Unit (from CostItem via Unit table)
  - Price (from CostItem)
  - Labor Coefficient (from CostItem)
  - Actions (Edit, Delete)
- Features:
  - Add button to select cost items from catalog
  - Inline editing of cost item properties
  - Remove button to delete association
  - Filter/search by code or description

**Table 2: Materials Table**
- Displays all materials associated with this work
- Columns:
  - Cost Item (dropdown/selector)
  - Material Code (from Material)
  - Material Description (from Material)
  - Unit (from Material via Unit table)
  - Price (from Material)
  - Quantity per Unit (editable)
  - Total Cost (calculated: price * quantity_per_unit)
  - Actions (Edit, Delete)
- Features:
  - Add button to select materials from catalog
  - Cost Item selector (required) - links material to specific cost item
  - Inline editing of quantity_per_unit
  - Remove button to delete association
  - Filter/search by code or description
  - Auto-calculation of total cost

**Business Logic:**
1. When adding a cost item to work:
   - Create CostItemMaterial record with work_id, cost_item_id
   - material_id can be null initially
   
2. When adding a material to work:
   - Must select which cost item it belongs to
   - Create CostItemMaterial record with work_id, cost_item_id, material_id, quantity_per_unit
   
3. When saving work:
   - Validate all CostItemMaterial records have valid work_id
   - Validate quantity_per_unit > 0 for material associations
   - Calculate total work cost from all cost items and materials

**Example Work Composition:**

Work: "Штукатурка стен" (Wall Plastering)
- Cost Items:
  - "Труд рабочих" (Labor) - 2.5 hours per м²
  - "Аренда оборудования" (Equipment rental) - 0.5 hours per м²
- Materials:
  - Cost Item: "Труд рабочих" → Material: "Цемент" (Cement) - 0.015 т per м²
  - Cost Item: "Труд рабочих" → Material: "Песок" (Sand) - 0.045 т per м²
  - Cost Item: "Аренда оборудования" → Material: "Штукатурная машина" (Plastering machine) - 1 шт per м²

**Form Validation:**
- Work name is required
- At least one cost item should be added (warning, not error)
- Materials must be linked to existing cost items
- Quantity per unit must be > 0
- Cannot delete cost item if it has associated materials (must delete materials first)

---

## 10. Migration Strategy

### 10.1 Database Initialization

**For New Projects:**
```sql
-- 1. Create all tables in order (respecting foreign keys)
-- 2. Create indexes
-- 3. Insert default data (units, admin user)
-- 4. Run Alembic migrations
```

**Alembic Migration Files:**
1. `201f5ef24462_initial_schema.py` - Core tables
2. `20251208_001234_add_costs_and_materials_sqlite.py` - Costs & materials

---

### 10.2 Data Import from 1C

**Import CostItems from SC12.DBF:**
```python
def import_cost_items_from_dbf():
    """Import cost items from 1C DBF file"""
    # Read SC12.DBF
    # Map fields:
    #   ID -> id
    #   PARENTID -> parent_id
    #   CODE -> code
    #   DESCR -> description
    #   ISFOLDER -> is_folder
    #   SP15 -> price
    #   SP17 -> unit
    #   SP31 -> labor_coefficient
    # Insert into cost_items table
```

**Import Materials from SC25.DBF:**
```python
def import_materials_from_dbf():
    """Import materials from 1C DBF file"""
    # Read SC25.DBF
    # Map fields:
    #   ID -> id
    #   CODE -> code
    #   DESCR -> description
    #   SP27 -> price
    #   SP43 -> unit
    # Insert into materials table
```

---

### 10.3 Timesheet Schema Migration

**⚠️ CRITICAL: Migrate from day_XX columns to normalized structure**

**Step 1: Create new table**
```sql
CREATE TABLE timesheet_day_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_line_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    hours_worked FLOAT DEFAULT 0.0,
    FOREIGN KEY (timesheet_line_id) REFERENCES timesheet_lines(id) ON DELETE CASCADE,
    UNIQUE (timesheet_line_id, day_number)
);
```

**Step 2: Migrate data**
```python
def migrate_timesheet_data():
    """Migrate from day_XX columns to timesheet_day_entries"""
    for line in session.query(TimesheetLine).all():
        for day in range(1, 32):
            hours = getattr(line, f'day_{day:02d}')
            if hours > 0:
                entry = TimesheetDayEntry(
                    timesheet_line_id=line.id,
                    day_number=day,
                    hours_worked=hours
                )
                session.add(entry)
    session.commit()
```

**Step 3: Update application code**
```python
# Old code
line.day_01 = 8.0

# New code
entry = TimesheetDayEntry(
    timesheet_line_id=line.id,
    day_number=1,
    hours_worked=8.0
)
```

**Step 4: Drop old columns (after validation)**
```sql
-- SQLite requires table recreation
-- PostgreSQL/MSSQL can use ALTER TABLE DROP COLUMN
```

---

### 10.4 CostItemMaterial Work Association Migration

**⚠️ CRITICAL: Add work_id to cost_item_materials table**

**Step 1: Add work_id column**
```sql
-- Add work_id column (nullable initially for migration)
ALTER TABLE cost_item_materials ADD COLUMN work_id INTEGER;
ALTER TABLE cost_item_materials ADD CONSTRAINT fk_cost_item_material_work 
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE;
```

**Step 2: Migrate existing data**
```python
def migrate_cost_item_materials_to_work():
    """
    Migrate existing cost_item_materials to be associated with works.
    Strategy: For each cost_item, find works that use it and create associations.
    """
    # This migration depends on your business logic
    # Option 1: If you have existing work-cost_item relationships elsewhere
    # Option 2: Create a default work for orphaned associations
    # Option 3: Manual data entry required
    
    # Example: Create a default "General Work" for migration
    default_work = Work(
        name="Общие работы (миграция)",
        code="MIGRATION",
        is_group=False
    )
    session.add(default_work)
    session.flush()
    
    # Update all existing associations to use default work
    session.query(CostItemMaterial)\
        .update({CostItemMaterial.work_id: default_work.id})
    session.commit()
```

**Step 3: Make work_id NOT NULL**
```sql
-- After migration, make work_id required
ALTER TABLE cost_item_materials ALTER COLUMN work_id SET NOT NULL;
```

**Step 4: Update primary key/unique constraint**
```sql
-- Drop old primary key
ALTER TABLE cost_item_materials DROP CONSTRAINT cost_item_materials_pkey;

-- Add new primary key with id
ALTER TABLE cost_item_materials ADD COLUMN id INTEGER PRIMARY KEY AUTOINCREMENT;

-- Add unique constraint
ALTER TABLE cost_item_materials ADD CONSTRAINT uq_work_cost_item_material 
    UNIQUE (work_id, cost_item_id, material_id);
```

**Step 5: Add indexes**
```sql
CREATE INDEX idx_cost_item_material_work ON cost_item_materials(work_id);
CREATE INDEX idx_cost_item_material_cost_item ON cost_item_materials(cost_item_id);
CREATE INDEX idx_cost_item_material_material ON cost_item_materials(material_id);
```

---

### 10.5 Unit Normalization Migration

**⚠️ RECOMMENDED: Migrate from string units to unit_id references**

**Step 1: Create units table and populate**
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert common units
INSERT INTO units (name, description) VALUES
('м', 'Метр'),
('м²', 'Квадратный метр'),
('м³', 'Кубический метр'),
('кг', 'Килограмм'),
('т', 'Тонна'),
('шт', 'Штука'),
('л', 'Литр'),
('компл', 'Комплект');
```

**Step 2: Add unit_id columns**
```sql
ALTER TABLE cost_items ADD COLUMN unit_id INTEGER REFERENCES units(id);
ALTER TABLE materials ADD COLUMN unit_id INTEGER REFERENCES units(id);
```

**Step 3: Migrate existing unit strings to unit_id**
```python
def migrate_units():
    """Migrate string units to unit_id references"""
    # Get all unique units from cost_items and materials
    unique_units = set()
    for item in session.query(CostItem).all():
        if item.unit:
            unique_units.add(item.unit)
    for material in session.query(Material).all():
        if material.unit:
            unique_units.add(material.unit)
    
    # Create Unit records for any missing units
    for unit_name in unique_units:
        existing = session.query(Unit).filter(Unit.name == unit_name).first()
        if not existing:
            unit = Unit(name=unit_name)
            session.add(unit)
    session.commit()
    
    # Update cost_items with unit_id
    for item in session.query(CostItem).all():
        if item.unit:
            unit = session.query(Unit).filter(Unit.name == item.unit).first()
            if unit:
                item.unit_id = unit.id
    
    # Update materials with unit_id
    for material in session.query(Material).all():
        if material.unit:
            unit = session.query(Unit).filter(Unit.name == material.unit).first()
            if unit:
                material.unit_id = unit.id
    
    session.commit()
```

**Step 4: Keep unit string for backward compatibility**
- Don't drop the `unit` column immediately
- Application can use unit_id when available, fall back to unit string
- Eventually deprecate unit string column

---

## 11. API Endpoints Specification

### 11.1 Authentication Endpoints

```
POST   /api/auth/login          - User login
POST   /api/auth/logout         - User logout
GET    /api/auth/me             - Get current user info
POST   /api/auth/refresh        - Refresh access token
```

### 11.2 Reference Endpoints

```
# Counterparties
GET    /api/counterparties                    - List all
GET    /api/counterparties/{id}               - Get by ID
POST   /api/counterparties                    - Create
PUT    /api/counterparties/{id}               - Update
DELETE /api/counterparties/{id}               - Soft delete

# Objects
GET    /api/objects                           - List all
GET    /api/objects/{id}                      - Get by ID
POST   /api/objects                           - Create
PUT    /api/objects/{id}                      - Update
DELETE /api/objects/{id}                      - Soft delete

# Works
GET    /api/works                             - List all
GET    /api/works/{id}                        - Get by ID
GET    /api/works/{id}/cost-items             - Get cost items for work
GET    /api/works/{id}/materials              - Get materials for work
GET    /api/works/{id}/composition            - Get full composition (cost items + materials)
POST   /api/works                             - Create
PUT    /api/works/{id}                        - Update
DELETE /api/works/{id}                        - Soft delete
POST   /api/works/{id}/cost-items             - Add cost item to work
DELETE /api/works/{id}/cost-items/{cid}       - Remove cost item from work
POST   /api/works/{id}/materials              - Add material to work (with cost_item_id)
PUT    /api/works/{id}/materials/{mid}        - Update material quantity
DELETE /api/works/{id}/materials/{mid}        - Remove material from work

# Persons
GET    /api/persons                           - List all
GET    /api/persons/{id}                      - Get by ID
POST   /api/persons                           - Create
PUT    /api/persons/{id}                      - Update
DELETE /api/persons/{id}                      - Soft delete

# Organizations
GET    /api/organizations                     - List all
GET    /api/organizations/{id}                - Get by ID
POST   /api/organizations                     - Create
PUT    /api/organizations/{id}                - Update
DELETE /api/organizations/{id}                - Soft delete
```

### 11.3 Costs & Materials Endpoints

```
# Units
GET    /api/units                             - List all units
GET    /api/units/{id}                        - Get unit by ID
POST   /api/units                             - Create unit
PUT    /api/units/{id}                        - Update unit
DELETE /api/units/{id}                        - Soft delete unit

# Cost Items
GET    /api/cost-items                        - List all cost items
GET    /api/cost-items/{id}                   - Get cost item by ID
GET    /api/cost-items/{id}/materials         - Get materials for cost item
POST   /api/cost-items                        - Create cost item
PUT    /api/cost-items/{id}                   - Update cost item
DELETE /api/cost-items/{id}                   - Soft delete cost item
POST   /api/cost-items/{id}/materials         - Add material to cost item
DELETE /api/cost-items/{id}/materials/{mid}   - Remove material from cost item

# Materials
GET    /api/materials                         - List all materials
GET    /api/materials/{id}                    - Get material by ID
GET    /api/materials/{id}/cost-items         - Get cost items using material
POST   /api/materials                         - Create material
PUT    /api/materials/{id}                    - Update material
DELETE /api/materials/{id}                    - Soft delete material
```

### 11.4 Document Endpoints

```
# Estimates
GET    /api/estimates                         - List all estimates
GET    /api/estimates/{id}                    - Get estimate by ID
POST   /api/estimates                         - Create estimate
PUT    /api/estimates/{id}                    - Update estimate
DELETE /api/estimates/{id}                    - Soft delete estimate
POST   /api/estimates/{id}/post               - Post estimate
POST   /api/estimates/{id}/unpost             - Unpost estimate
GET    /api/estimates/{id}/print              - Generate print form

# Daily Reports
GET    /api/daily-reports                     - List all daily reports
GET    /api/daily-reports/{id}                - Get daily report by ID
POST   /api/daily-reports                     - Create daily report
PUT    /api/daily-reports/{id}                - Update daily report
DELETE /api/daily-reports/{id}                - Soft delete daily report
POST   /api/daily-reports/{id}/post           - Post daily report
POST   /api/daily-reports/{id}/unpost         - Unpost daily report
GET    /api/daily-reports/{id}/print          - Generate print form

# Timesheets
GET    /api/timesheets                        - List all timesheets
GET    /api/timesheets/{id}                   - Get timesheet by ID
POST   /api/timesheets                        - Create timesheet
PUT    /api/timesheets/{id}                   - Update timesheet
DELETE /api/timesheets/{id}                   - Soft delete timesheet
POST   /api/timesheets/{id}/post              - Post timesheet
POST   /api/timesheets/{id}/unpost            - Unpost timesheet
GET    /api/timesheets/{id}/print             - Generate print form
```

### 11.5 Register Endpoints

```
# Work Execution Register
GET    /api/registers/work-execution          - Query work execution movements
GET    /api/registers/work-execution/balance  - Get work balance

# Payroll Register
GET    /api/registers/payroll                 - Query payroll movements
GET    /api/registers/payroll/summary         - Get payroll summary
```

---

## 12. Repository Pattern Implementation

### 12.1 Base Repository Interface

```python
from typing import TypeVar, Generic, List, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    def find_all(self, include_deleted: bool = False) -> List[T]:
        """Find all entities"""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> Optional[T]:
        """Save entity (create or update)"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Soft delete entity"""
        pass
```

### 12.2 Example Repository Implementation

```python
class CostItemRepository(BaseRepository[CostItem]):
    """Repository for CostItem entities"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_by_id(self, cost_item_id: int) -> Optional[CostItem]:
        """Find cost item by ID"""
        with self.db_manager.session_scope() as session:
            return session.query(CostItem)\
                .options(joinedload(CostItem.materials))\
                .filter(CostItem.id == cost_item_id)\
                .first()
    
    def find_all(self, include_deleted: bool = False) -> List[CostItem]:
        """Find all cost items"""
        with self.db_manager.session_scope() as session:
            query = session.query(CostItem)
            if not include_deleted:
                query = query.filter(CostItem.marked_for_deletion == False)
            return query.order_by(CostItem.code).all()
    
    def save(self, cost_item: CostItem) -> Optional[CostItem]:
        """Save cost item (create or update)"""
        with self.db_manager.session_scope() as session:
            if cost_item.id is None:
                session.add(cost_item)
            else:
                existing = session.query(CostItem)\
                    .filter(CostItem.id == cost_item.id).first()
                if existing:
                    for key, value in cost_item.__dict__.items():
                        if not key.startswith('_'):
                            setattr(existing, key, value)
            session.flush()
            return cost_item
    
    def delete(self, cost_item_id: int) -> bool:
        """Soft delete cost item"""
        with self.db_manager.session_scope() as session:
            cost_item = session.query(CostItem)\
                .filter(CostItem.id == cost_item_id).first()
            if cost_item:
                cost_item.marked_for_deletion = True
                return True
            return False
```

---

## 13. Performance Optimization Guidelines

### 13.1 Database Indexes

**Critical Indexes:**
```sql
-- Foreign key indexes
CREATE INDEX idx_estimate_customer ON estimates(customer_id);
CREATE INDEX idx_estimate_object ON estimates(object_id);
CREATE INDEX idx_estimate_contractor ON estimates(contractor_id);
CREATE INDEX idx_estimate_responsible ON estimates(responsible_id);

-- Date indexes for time-based queries
CREATE INDEX idx_estimate_date ON estimates(date);
CREATE INDEX idx_daily_report_date ON daily_reports(date);
CREATE INDEX idx_timesheet_date ON timesheets(date);

-- Composite indexes for common queries
CREATE INDEX idx_estimate_line_estimate_work ON estimate_lines(estimate_id, work_id);
CREATE INDEX idx_daily_report_line_report_work ON daily_report_lines(report_id, work_id);

-- Register indexes
CREATE INDEX idx_work_execution_period ON work_execution_register(period);
CREATE INDEX idx_work_execution_dimensions ON work_execution_register(period, object_id, estimate_id, work_id);
CREATE INDEX idx_payroll_period ON payroll_register(period);
CREATE INDEX idx_payroll_employee ON payroll_register(employee_id);

-- Text search indexes
CREATE INDEX idx_cost_item_description ON cost_items(description);
CREATE INDEX idx_material_description ON materials(description);
CREATE INDEX idx_work_name ON works(name);
```

### 13.2 Query Optimization

**Use Eager Loading:**
```python
# Bad: N+1 queries
estimates = session.query(Estimate).all()
for estimate in estimates:
    print(estimate.customer.name)  # Additional query per estimate!

# Good: Single query with join
estimates = session.query(Estimate)\
    .options(
        joinedload(Estimate.customer),
        joinedload(Estimate.object),
        joinedload(Estimate.contractor),
        joinedload(Estimate.responsible)
    )\
    .all()
```

**Use Pagination:**
```python
# API endpoint with pagination
@app.get("/api/estimates")
async def get_estimates(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None
):
    offset = (page - 1) * page_size
    query = session.query(Estimate)
    
    if search:
        query = query.filter(Estimate.number.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.offset(offset).limit(page_size).all()
    
    return {
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
```

**Use Batch Operations:**
```python
# Bad: Individual inserts
for line in lines:
    session.add(EstimateLine(**line))
    session.commit()  # Commit per line!

# Good: Bulk insert
session.bulk_insert_mappings(EstimateLine, lines)
session.commit()  # Single commit
```

### 13.3 Caching Strategy

**Backend Caching (Redis):**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

# Cache reference data (rarely changes)
@cache(expire=3600)  # 1 hour
async def get_works():
    return await work_repository.find_all()

@cache(expire=3600)
async def get_units():
    return await unit_repository.find_all()
```

**Frontend Caching (Pinia):**
```typescript
export const useReferenceStore = defineStore('reference', {
  state: () => ({
    works: [] as Work[],
    worksLastFetched: null as Date | null,
    units: [] as Unit[],
    unitsLastFetched: null as Date | null,
  }),
  
  actions: {
    async fetchWorks(force = false) {
      const cacheValid = this.worksLastFetched && 
        (Date.now() - this.worksLastFetched.getTime()) < 3600000
      
      if (!force && cacheValid) return
      
      this.works = await api.getWorks()
      this.worksLastFetched = new Date()
    }
  }
})
```

---

## 14. Security Considerations

### 14.1 Authentication & Authorization

**JWT Token-Based Authentication:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401)
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=401)
```

**Role-Based Access Control:**
```python
def require_role(*roles: str):
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/api/estimates/{id}/post")
@require_role("admin", "manager")
async def post_estimate(id: int, current_user: User):
    # Only admin and manager can post estimates
    pass
```

### 14.2 Input Validation

**Pydantic Validation:**
```python
from pydantic import BaseModel, Field, validator

class EstimateCreate(BaseModel):
    number: str = Field(..., min_length=1, max_length=50)
    date: date
    customer_id: int = Field(..., gt=0)
    
    @validator('date')
    def date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Date cannot be in the future')
        return v
    
    @validator('number')
    def number_format(cls, v):
        if not v.strip():
            raise ValueError('Number cannot be empty')
        return v.strip()
```

### 14.3 SQL Injection Prevention

**Always use parameterized queries:**
```python
# Bad: SQL injection vulnerable
query = f"SELECT * FROM users WHERE username = '{username}'"

# Good: Parameterized query
query = session.query(User).filter(User.username == username)
```

---

## 15. Testing Strategy

### 15.1 Unit Tests

**Repository Tests:**
```python
import pytest
from src.data.repositories.cost_item_repository import CostItemRepository
from src.data.models.sqlalchemy_models import CostItem

class TestCostItemRepository:
    @pytest.fixture
    def repository(self):
        return CostItemRepository()
    
    def test_find_by_id(self, repository):
        # Arrange
        cost_item = CostItem(code="1.01", description="Test Item")
        saved = repository.save(cost_item)
        
        # Act
        found = repository.find_by_id(saved.id)
        
        # Assert
        assert found is not None
        assert found.code == "1.01"
        assert found.description == "Test Item"
    
    def test_soft_delete(self, repository):
        # Arrange
        cost_item = CostItem(code="1.02", description="Delete Test")
        saved = repository.save(cost_item)
        
        # Act
        repository.delete(saved.id)
        
        # Assert
        found = repository.find_by_id(saved.id)
        assert found.marked_for_deletion == True
```

### 15.2 Integration Tests

**API Endpoint Tests:**
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_cost_item():
    # Arrange
    payload = {
        "code": "1.01",
        "description": "Test Cost Item",
        "price": 100.0,
        "unit_id": 1,
        "labor_coefficient": 0.5
    }
    
    # Act
    response = client.post("/api/cost-items", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "1.01"
    assert data["price"] == 100.0

def test_get_cost_items():
    # Act
    response = client.get("/api/cost-items")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
```

### 15.3 E2E Tests

**Frontend E2E Tests (Playwright):**
```typescript
import { test, expect } from '@playwright/test'

test('create cost item', async ({ page }) => {
  // Navigate to cost items page
  await page.goto('/cost-items')
  
  // Click create button
  await page.click('button:has-text("Создать")')
  
  // Fill form
  await page.fill('input[name="code"]', '1.01')
  await page.fill('input[name="description"]', 'Test Cost Item')
  await page.fill('input[name="price"]', '100')
  
  // Submit
  await page.click('button:has-text("Сохранить")')
  
  // Verify
  await expect(page.locator('text=Test Cost Item')).toBeVisible()
})
```

---

## 16. Deployment Considerations

### 16.1 Environment Configuration

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/construction_db
DATABASE_TYPE=postgresql  # sqlite, postgresql, mssql

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Logging
LOG_LEVEL=INFO
```

### 16.2 Database Connection Pooling

**PostgreSQL Configuration:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### 16.3 Backup Strategy

**Automated Backups:**
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="construction_db"

# PostgreSQL backup
pg_dump -U postgres $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Compress
gzip $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Keep only last 30 days
find $BACKUP_DIR -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete
```

---

## 17. Summary & Next Steps

### 17.1 Complete Entity List

**Reference Entities (8):**
1. User
2. Person
3. Organization
4. Counterparty
5. Object
6. Work
7. CostItem ✨ NEW
8. Material ✨ NEW
9. Unit ✨ NEW

**Document Entities (6):**
1. Estimate
2. EstimateLine
3. DailyReport
4. DailyReportLine
5. Timesheet
6. TimesheetLine

**Register Entities (2):**
1. WorkExecutionRegister
2. PayrollRegister

**Association Tables (2):**
1. DailyReportExecutor
2. CostItemMaterial ✨ NEW

**System Tables (2):**
1. UserSetting
2. Constant

**Total Tables: 21**

---

### 17.2 Critical Improvements Needed

1. **🔴 CRITICAL: Add work_id to CostItemMaterial**
   - Add work_id column to cost_item_materials table
   - Migrate existing data (may require manual work)
   - Update primary key to include id
   - Add UNIQUE constraint (work_id, cost_item_id, material_id)
   - Update all repositories and API endpoints

2. **🔴 CRITICAL: Normalize Timesheet Day Columns**
   - Create `timesheet_day_entries` table
   - Migrate data from day_01-day_31 columns
   - Update application code

3. **🟡 MEDIUM: Implement Work Form UI**
   - Create Work form with two tables (Cost Items and Materials)
   - Implement cost item selection and association
   - Implement material selection with cost item linkage
   - Add inline editing for quantity_per_unit
   - Implement validation rules

4. **🟡 MEDIUM: Add Unit Normalization**
   - Create `units` table (DONE in models)
   - Add migration to create table
   - Migrate string units to unit_id references

5. **🟡 MEDIUM: Add Missing Indexes**
   - Add composite indexes for common queries
   - Add text search indexes

6. **🟡 MEDIUM: Implement Audit Trail**
   - Add created_by_id, modified_by_id columns
   - Track user actions

7. **🟢 LOW: Standardize Soft Delete**
   - Rename is_deleted to marked_for_deletion everywhere

---

### 17.3 Implementation Checklist

**Phase 1: Core Setup**
- [ ] Create database schema (Alembic migrations)
- [ ] Implement base repository pattern
- [ ] Create SQLAlchemy models
- [ ] Create Pydantic API models
- [ ] Create TypeScript type definitions

**Phase 2: Costs & Materials**
- [ ] Create Unit table and migration
- [ ] Create CostItem table and migration
- [ ] Create Material table and migration
- [ ] Create CostItemMaterial association table
- [ ] Implement repositories
- [ ] Create API endpoints
- [ ] Create frontend components

**Phase 3: Timesheet Refactoring**
- [ ] Create timesheet_day_entries table
- [ ] Write data migration script
- [ ] Update TimesheetLine model
- [ ] Update repositories
- [ ] Update API endpoints
- [ ] Update frontend components
- [ ] Test thoroughly
- [ ] Deploy migration

**Phase 4: Optimization**
- [ ] Add all recommended indexes
- [ ] Implement caching (Redis + Pinia)
- [ ] Add performance monitoring
- [ ] Optimize slow queries
- [ ] Add pagination everywhere

**Phase 5: Testing & Documentation**
- [ ] Write unit tests for repositories
- [ ] Write integration tests for API
- [ ] Write E2E tests for frontend
- [ ] Document API endpoints (OpenAPI)
- [ ] Create user documentation

---

## 18. Conclusion

This specification provides a complete blueprint for the construction management system's data layer, including:

✅ **Complete schema definitions** for all 21 tables  
✅ **Detailed entity relationships** and business rules  
✅ **Python, Pydantic, and TypeScript models** for all entities  
✅ **Repository pattern** implementation guidelines  
✅ **API endpoint specifications** for all operations  
✅ **Migration strategies** for schema improvements  
✅ **Performance optimization** recommendations  
✅ **Security best practices** for authentication and authorization  
✅ **Testing strategies** for all layers  
✅ **Deployment considerations** for production environments  

**Key Innovations:**
- ✨ Comprehensive Costs & Materials module with hierarchical structure
- ✨ Unit normalization for standardized measurements
- ✨ Material tracking in estimates and daily reports
- ✨ CostItem-Material associations for automatic calculations

**Critical Improvements:**
- 🔴 Timesheet day columns normalization (highest priority)
- 🟡 Unit table implementation and migration
- 🟡 Comprehensive indexing strategy
- 🟡 Audit trail implementation

This specification is ready for use in generating detailed implementation specs for a new project or refactoring the existing system.

---

**Document Version:** 2.0  
**Last Updated:** December 9, 2025  
**Status:** Complete and Ready for Implementation

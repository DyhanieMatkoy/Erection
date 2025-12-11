# Design Document - Desktop Work Composition

## Overview

This design document specifies the implementation of work composition functionality in the desktop application (Python/PyQt6). The desktop application currently has a basic Work form (`src/views/work_form.py`) that only includes fundamental fields. This implementation will extend the Work form to include full composition management with cost items and materials, bringing it to feature parity with the web client.

The work composition feature enables users to:
- Define labor requirements (cost items) for each work type
- Specify material consumption rates for each work type
- Link materials to specific cost items
- Calculate total work costs automatically
- Manage work composition in a tabbed interface

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                Desktop Work Form (PyQt6)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Основные   │  │    Статьи    │  │  Материалы   │     │
│  │    данные    │  │   затрат     │  │              │     │
│  │   (Tab 1)    │  │   (Tab 2)    │  │   (Tab 3)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
├─────────────────────────────────────────────────────────────┤
│  WorkRepository                                              │
│  CostItemMaterialRepository (existing)                       │
│  CostItemRepository                                          │
│  MaterialRepository                                          │
│  UnitRepository                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        Database                              │
├─────────────────────────────────────────────────────────────┤
│  works                                                       │
│  cost_items                                                  │
│  materials                                                   │
│  cost_item_materials (association table)                    │
│  units                                                       │
└─────────────────────────────────────────────────────────────┘
```


### Component Architecture

The desktop form follows a tabbed interface pattern using PyQt6:

```
WorkForm (QWidget)
├── QTabWidget (main container)
│   ├── Tab 1: Основные данные (Basic Info)
│   │   ├── QLineEdit (code, name)
│   │   ├── ReferencePickerDialog (unit_id)
│   │   ├── QDoubleSpinBox (price, labor_rate)
│   │   ├── QCheckBox (is_group)
│   │   └── ReferencePickerDialog (parent_id)
│   │
│   ├── Tab 2: Статьи затрат (Cost Items)
│   │   ├── QTableWidget (cost items display)
│   │   │   └── Columns: Код, Наименование, Ед.изм, Цена, Норма труда
│   │   ├── QPushButton (Добавить статью затрат)
│   │   ├── QPushButton (Удалить)
│   │   └── CostItemSelectorDialog
│   │       ├── QLineEdit (search)
│   │       ├── QTreeWidget (hierarchical display)
│   │       └── QPushButton (OK/Cancel)
│   │
│   └── Tab 3: Материалы (Materials)
│       ├── QTableWidget (materials display)
│       │   └── Columns: Статья затрат, Код, Наименование, Ед.изм, Цена, Количество, Сумма
│       ├── QPushButton (Добавить материал)
│       ├── QPushButton (Удалить)
│       └── MaterialAddDialog (multi-step)
│           ├── Step 1: CostItemSelectorDialog (select from work's cost items)
│           ├── Step 2: MaterialSelectorDialog (select material)
│           │   ├── QLineEdit (search)
│           │   ├── QTableWidget (materials list)
│           │   └── QPushButton (OK/Cancel)
│           └── Step 3: QInputDialog (quantity input)
│
└── Button Bar
    ├── QPushButton (Сохранить - Ctrl+S)
    ├── QPushButton (Сохранить и закрыть - Ctrl+Shift+S)
    └── QPushButton (Закрыть - Esc)
```

### State Management

The form maintains state using instance variables:

```python
class WorkForm(QWidget):
    def __init__(self, work_id=0, is_group=False):
        # Core state
        self.work_id = work_id
        self.is_group = is_group
        self.is_modified = False
        
        # Repositories
        self.work_repo = WorkRepository(db_manager)
        self.cost_item_material_repo = CostItemMaterialRepository()
        self.cost_item_repo = CostItemRepository(db_manager)
        self.material_repo = MaterialRepository(db_manager)
        self.unit_repo = UnitRepository(db_manager)
        
        # Composition data (loaded from database)
        self.cost_items = []  # List of (CostItem, quantity) tuples
        self.materials = []   # List of (Material, quantity, CostItem) tuples
```


## Components and Interfaces

### Qt Widgets

#### WorkForm (Main Container)

```python
class WorkForm(QWidget):
    """Main work form with tabbed interface"""
    
    def __init__(self, work_id=0, is_group=False):
        """Initialize form
        
        Args:
            work_id: ID of work to edit (0 for new work)
            is_group: Whether this is a group work
        """
        
    def setup_ui(self):
        """Setup UI with tabs"""
        # Create tab widget
        # Add basic info tab
        # Add cost items tab
        # Add materials tab
        # Add button bar
        
    def setup_basic_info_tab(self) -> QWidget:
        """Create basic info tab"""
        # Same as current implementation
        
    def setup_cost_items_tab(self) -> QWidget:
        """Create cost items tab"""
        # QTableWidget for cost items
        # Add/Remove buttons
        
    def setup_materials_tab(self) -> QWidget:
        """Create materials tab"""
        # QTableWidget for materials
        # Add/Remove buttons
        
    def load_data(self):
        """Load work data from database"""
        # Load basic info
        # Load cost items
        # Load materials
        
    def save_data(self) -> bool:
        """Save work data to database"""
        # Validate all tabs
        # Save basic info
        # Save cost items
        # Save materials
        # Return success/failure
```

#### CostItemsTable (QTableWidget)

```python
class CostItemsTable(QTableWidget):
    """Table widget for displaying cost items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        
    def setup_table(self):
        """Setup table columns and properties"""
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Код", "Наименование", "Ед.изм", "Цена", "Норма труда"
        ])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def load_cost_items(self, cost_items: List[Tuple[CostItem, float]]):
        """Load cost items into table"""
        self.setRowCount(len(cost_items))
        for row, (cost_item, quantity) in enumerate(cost_items):
            self.setItem(row, 0, QTableWidgetItem(cost_item.code or ""))
            self.setItem(row, 1, QTableWidgetItem(cost_item.description))
            self.setItem(row, 2, QTableWidgetItem(cost_item.unit_name or ""))
            self.setItem(row, 3, QTableWidgetItem(f"{cost_item.price:.2f}"))
            self.setItem(row, 4, QTableWidgetItem(f"{cost_item.labor_coefficient:.2f}"))
            
    def get_selected_cost_item_id(self) -> Optional[int]:
        """Get ID of selected cost item"""
        # Return cost_item_id from selected row
```


#### MaterialsTable (QTableWidget)

```python
class MaterialsTable(QTableWidget):
    """Table widget for displaying materials with editable quantities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        
    def setup_table(self):
        """Setup table columns and properties"""
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "Статья затрат", "Код", "Наименование", "Ед.изм", "Цена", "Количество", "Сумма"
        ])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Allow editing only for quantity column
        
    def load_materials(self, materials: List[Tuple[Material, float, CostItem]]):
        """Load materials into table"""
        self.setRowCount(len(materials))
        for row, (material, quantity, cost_item) in enumerate(materials):
            self.setItem(row, 0, QTableWidgetItem(cost_item.description))
            self.setItem(row, 1, QTableWidgetItem(material.code or ""))
            self.setItem(row, 2, QTableWidgetItem(material.description))
            self.setItem(row, 3, QTableWidgetItem(material.unit_name or ""))
            self.setItem(row, 4, QTableWidgetItem(f"{material.price:.2f}"))
            
            # Editable quantity cell
            quantity_item = QTableWidgetItem(f"{quantity:.4f}")
            quantity_item.setFlags(quantity_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 5, quantity_item)
            
            # Calculated total
            total = material.price * quantity
            self.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
            
    def get_selected_material_id(self) -> Optional[int]:
        """Get ID of selected material"""
        # Return material_id from selected row
```

#### CostItemSelectorDialog (QDialog)

```python
class CostItemSelectorDialog(QDialog):
    """Dialog for selecting a cost item from hierarchical list"""
    
    def __init__(self, parent=None, work_id: Optional[int] = None, 
                 filter_by_work: bool = False):
        """Initialize dialog
        
        Args:
            parent: Parent widget
            work_id: Work ID for filtering (if filter_by_work is True)
            filter_by_work: If True, show only cost items already in work
        """
        super().__init__(parent)
        self.work_id = work_id
        self.filter_by_work = filter_by_work
        self.selected_cost_item_id = None
        self.setup_ui()
        self.load_cost_items()
        
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Выбор статьи затрат")
        layout = QVBoxLayout()
        
        # Search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по коду или наименованию...")
        self.search_edit.textChanged.connect(self.on_search)
        layout.addWidget(self.search_edit)
        
        # Tree widget for hierarchical display
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Код", "Наименование", "Ед.изм", "Цена", "Норма труда"])
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("Выбрать")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_cost_items(self):
        """Load cost items into tree"""
        # Load from repository
        # Build hierarchical tree
        # Apply filter if needed
        
    def on_search(self, text: str):
        """Filter cost items by search text"""
        # Filter tree items by code or description
        
    def get_selected_cost_item_id(self) -> Optional[int]:
        """Get selected cost item ID"""
        return self.selected_cost_item_id
```


#### MaterialSelectorDialog (QDialog)

```python
class MaterialSelectorDialog(QDialog):
    """Dialog for selecting a material from list"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_material_id = None
        self.setup_ui()
        self.load_materials()
        
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("Выбор материала")
        layout = QVBoxLayout()
        
        # Search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по коду или наименованию...")
        self.search_edit.textChanged.connect(self.on_search)
        layout.addWidget(self.search_edit)
        
        # Table widget for materials
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Код", "Наименование", "Ед.изм", "Цена"])
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("Выбрать")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_materials(self):
        """Load materials into table"""
        # Load from repository
        
    def on_search(self, text: str):
        """Filter materials by search text"""
        # Filter table rows by code or description
        
    def get_selected_material_id(self) -> Optional[int]:
        """Get selected material ID"""
        return self.selected_material_id
```

#### MaterialAddDialog (QDialog)

```python
class MaterialAddDialog(QDialog):
    """Multi-step dialog for adding material to work"""
    
    def __init__(self, parent=None, work_id: int = 0):
        super().__init__(parent)
        self.work_id = work_id
        self.selected_cost_item_id = None
        self.selected_material_id = None
        self.quantity = 0.0
        self.setup_ui()
        
    def exec(self) -> int:
        """Execute multi-step dialog"""
        # Step 1: Select cost item from work's cost items
        cost_item_dialog = CostItemSelectorDialog(
            self, 
            work_id=self.work_id, 
            filter_by_work=True
        )
        if cost_item_dialog.exec() != QDialog.DialogCode.Accepted:
            return QDialog.DialogCode.Rejected
        self.selected_cost_item_id = cost_item_dialog.get_selected_cost_item_id()
        
        # Step 2: Select material
        material_dialog = MaterialSelectorDialog(self)
        if material_dialog.exec() != QDialog.DialogCode.Accepted:
            return QDialog.DialogCode.Rejected
        self.selected_material_id = material_dialog.get_selected_material_id()
        
        # Step 3: Enter quantity
        quantity, ok = QInputDialog.getDouble(
            self,
            "Количество",
            "Введите количество на единицу работы:",
            value=1.0,
            min=0.001,
            max=999999.999,
            decimals=4
        )
        if not ok:
            return QDialog.DialogCode.Rejected
        self.quantity = quantity
        
        return QDialog.DialogCode.Accepted
        
    def get_result(self) -> Tuple[int, int, float]:
        """Get selected cost item, material, and quantity"""
        return (self.selected_cost_item_id, self.selected_material_id, self.quantity)
```


## Data Models

### Database Schema

The database schema is already complete (implemented for the web client). The desktop application will use the same schema:

```sql
-- Works table (existing)
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50),
    name VARCHAR(500) NOT NULL,
    unit_id INTEGER,
    price FLOAT DEFAULT 0.0,
    labor_rate FLOAT DEFAULT 0.0,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (parent_id) REFERENCES works(id)
);

-- Cost Item Materials association table (existing)
CREATE TABLE cost_item_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER,
    quantity_per_unit FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    
    UNIQUE (work_id, cost_item_id, material_id)
);
```

### Repository Layer

The repository layer is already implemented:

- **CostItemMaterialRepository**: Manages work-cost item-material associations (existing)
- **WorkRepository**: Manages works (existing)
- **CostItemRepository**: Manages cost items (existing)
- **MaterialRepository**: Manages materials (existing)
- **UnitRepository**: Manages units (existing)

Key repository methods used:

```python
# CostItemMaterialRepository
get_cost_items_for_work(work_id) -> List[Tuple[CostItem, float]]
get_materials_for_work(work_id) -> List[Tuple[Material, float, CostItem]]
create_or_update_association(work_id, cost_item_id, material_id, quantity)
remove_association_by_work_cost_item_material(work_id, cost_item_id, material_id)
calculate_total_cost_for_work(work_id) -> float

# CostItemRepository
find_all() -> List[CostItem]
find_by_id(id) -> Optional[CostItem]

# MaterialRepository
find_all() -> List[Material]
find_by_id(id) -> Optional[Material]
```


## User Workflows

### Workflow 1: Create New Work with Composition

1. User opens work form (new work)
2. User enters basic info in "Основные данные" tab
3. User switches to "Статьи затрат" tab
4. User clicks "Добавить статью затрат"
5. System opens CostItemSelectorDialog
6. User searches and selects cost item
7. System adds cost item to table
8. User repeats steps 4-7 for additional cost items
9. User switches to "Материалы" tab
10. User clicks "Добавить материал"
11. System opens MaterialAddDialog (step 1: select cost item)
12. User selects cost item from work's cost items
13. System shows MaterialSelectorDialog (step 2: select material)
14. User searches and selects material
15. System shows quantity input dialog (step 3)
16. User enters quantity
17. System adds material to table with calculated total
18. User repeats steps 10-17 for additional materials
19. User clicks "Сохранить и закрыть"
20. System validates and saves all data
21. System closes form

### Workflow 2: Edit Existing Work Composition

1. User opens work form (existing work)
2. System loads basic info, cost items, and materials
3. User reviews cost items in "Статьи затрат" tab
4. User selects cost item and clicks "Удалить"
5. System checks if cost item has materials
6. IF has materials: System shows warning and prevents deletion
7. IF no materials: System shows confirmation dialog
8. User confirms deletion
9. System removes cost item from table
10. User switches to "Материалы" tab
11. User double-clicks quantity cell
12. System makes cell editable
13. User enters new quantity
14. System validates quantity > 0
15. System recalculates total cost
16. User clicks "Сохранить"
17. System saves changes
18. Form remains open for additional edits

### Workflow 3: Remove Material from Work

1. User opens work form with materials
2. User switches to "Материалы" tab
3. User selects material row
4. User clicks "Удалить"
5. System shows confirmation dialog "Удалить материал?"
6. User confirms
7. System removes material from table
8. System recalculates total work cost
9. System marks form as modified

### Workflow 4: Change Material Cost Item Association

1. User opens work form with materials
2. User switches to "Материалы" tab
3. User double-clicks cost item cell in material row
4. System opens CostItemSelectorDialog (filtered to work's cost items)
5. User selects different cost item
6. System updates material's cost item association
7. System refreshes materials table
8. System marks form as modified


## Error Handling

### Validation Errors

```python
class ValidationError:
    """Validation error messages in Russian"""
    WORK_NAME_REQUIRED = "Наименование обязательно для заполнения"
    GROUP_CANNOT_HAVE_PRICE = "Группа работ не может иметь цену или норму трудозатрат"
    INVALID_QUANTITY = "Количество должно быть больше нуля"
    DUPLICATE_COST_ITEM = "Эта статья затрат уже добавлена к работе"
    DUPLICATE_MATERIAL = "Этот материал уже добавлен к этой статье затрат"
    COST_ITEM_HAS_MATERIALS = "Невозможно удалить статью затрат с привязанными материалами. Сначала удалите материалы."
    MATERIAL_REQUIRES_COST_ITEM = "Материал должен быть привязан к статье затрат"
    CIRCULAR_REFERENCE = "Нельзя выбрать элемент в качестве родителя самого себя"
    DATABASE_ERROR = "Ошибка подключения к базе данных"
    UNEXPECTED_ERROR = "Произошла непредвиденная ошибка"
```

### Error Handling Strategy

**Client-Side Validation:**
- Validate required fields before submission (name)
- Validate numeric ranges (quantity > 0)
- Validate uniqueness constraints (duplicate cost items/materials)
- Display error messages using QMessageBox
- Prevent form submission until errors are resolved

**Database Error Handling:**
- Catch SQLAlchemy exceptions
- Translate to user-friendly Russian messages
- Use QMessageBox.critical() for database errors
- Log detailed error information for debugging

**User Experience:**
- Use QMessageBox.warning() for validation errors
- Use QMessageBox.question() for confirmations
- Use QMessageBox.information() for success messages
- Disable action buttons during operations to prevent double-clicks
- Show loading indicators for long operations

### Error Dialog Examples

```python
# Validation error
QMessageBox.warning(
    self,
    "Ошибка",
    "Наименование обязательно для заполнения"
)

# Confirmation dialog
reply = QMessageBox.question(
    self,
    "Подтверждение",
    "Удалить статью затрат?",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
)

# Database error
QMessageBox.critical(
    self,
    "Ошибка",
    f"Не удалось сохранить: {str(e)}"
)

# Success message
QMessageBox.information(
    self,
    "Успех",
    "Работа успешно сохранена"
)
```


## Implementation Details

### Tab Management

```python
def setup_ui(self):
    """Setup UI with tabs"""
    layout = QVBoxLayout()
    
    # Create tab widget
    self.tab_widget = QTabWidget()
    
    # Add tabs
    self.tab_widget.addTab(self.setup_basic_info_tab(), "Основные данные")
    self.tab_widget.addTab(self.setup_cost_items_tab(), "Статьи затрат")
    self.tab_widget.addTab(self.setup_materials_tab(), "Материалы")
    
    layout.addWidget(self.tab_widget)
    
    # Add button bar
    layout.addLayout(self.setup_button_bar())
    
    self.setLayout(layout)
```

### Cost Items Management

```python
def on_add_cost_item(self):
    """Add cost item to work"""
    dialog = CostItemSelectorDialog(self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        cost_item_id = dialog.get_selected_cost_item_id()
        
        # Check for duplicates
        if self.is_cost_item_in_work(cost_item_id):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Эта статья затрат уже добавлена к работе"
            )
            return
        
        # Add to local list
        cost_item = self.cost_item_repo.find_by_id(cost_item_id)
        self.cost_items.append((cost_item, 0.0))
        
        # Refresh table
        self.refresh_cost_items_table()
        
        # Mark as modified
        self.is_modified = True

def on_remove_cost_item(self):
    """Remove cost item from work"""
    selected_row = self.cost_items_table.currentRow()
    if selected_row < 0:
        return
    
    cost_item, _ = self.cost_items[selected_row]
    
    # Check if cost item has materials
    if self.cost_item_has_materials(cost_item.id):
        QMessageBox.warning(
            self,
            "Ошибка",
            "Невозможно удалить статью затрат с привязанными материалами. "
            "Сначала удалите материалы."
        )
        return
    
    # Confirm deletion
    reply = QMessageBox.question(
        self,
        "Подтверждение",
        "Удалить статью затрат?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        # Remove from local list
        del self.cost_items[selected_row]
        
        # Refresh table
        self.refresh_cost_items_table()
        
        # Mark as modified
        self.is_modified = True
```

### Materials Management

```python
def on_add_material(self):
    """Add material to work"""
    # Check if work has cost items
    if not self.cost_items:
        QMessageBox.warning(
            self,
            "Ошибка",
            "Сначала добавьте статьи затрат"
        )
        return
    
    dialog = MaterialAddDialog(self, work_id=self.work_id)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        cost_item_id, material_id, quantity = dialog.get_result()
        
        # Check for duplicates
        if self.is_material_in_cost_item(cost_item_id, material_id):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Этот материал уже добавлен к этой статье затрат"
            )
            return
        
        # Add to local list
        material = self.material_repo.find_by_id(material_id)
        cost_item = self.cost_item_repo.find_by_id(cost_item_id)
        self.materials.append((material, quantity, cost_item))
        
        # Refresh table
        self.refresh_materials_table()
        
        # Mark as modified
        self.is_modified = True

def on_remove_material(self):
    """Remove material from work"""
    selected_row = self.materials_table.currentRow()
    if selected_row < 0:
        return
    
    # Confirm deletion
    reply = QMessageBox.question(
        self,
        "Подтверждение",
        "Удалить материал?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        # Remove from local list
        del self.materials[selected_row]
        
        # Refresh table
        self.refresh_materials_table()
        
        # Mark as modified
        self.is_modified = True

def on_material_quantity_changed(self, row: int, column: int):
    """Handle material quantity change"""
    if column != 5:  # Quantity column
        return
    
    try:
        # Get new quantity
        quantity_text = self.materials_table.item(row, column).text()
        quantity = float(quantity_text)
        
        # Validate
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        
        # Update local list
        material, _, cost_item = self.materials[row]
        self.materials[row] = (material, quantity, cost_item)
        
        # Recalculate total
        total = material.price * quantity
        self.materials_table.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
        
        # Mark as modified
        self.is_modified = True
        
    except ValueError as e:
        QMessageBox.warning(
            self,
            "Ошибка",
            "Количество должно быть больше нуля"
        )
        # Revert to previous value
        material, quantity, cost_item = self.materials[row]
        self.materials_table.setItem(row, column, QTableWidgetItem(f"{quantity:.4f}"))
```


### Data Persistence

```python
def save_data(self) -> bool:
    """Save work data to database"""
    # Validate
    if not self.name_edit.text().strip():
        QMessageBox.warning(
            self,
            "Ошибка",
            "Наименование обязательно для заполнения"
        )
        self.name_edit.setFocus()
        return False
    
    try:
        # Save basic work info (existing code)
        if self.work_id > 0:
            # Update existing work
            work_data = self.work_repo.find_by_id(self.work_id)
            if work_data:
                work = Work()
                work.id = self.work_id
                work.name = self.name_edit.text()
                work.code = self.code_edit.text()
                work.unit = self.unit_edit.text()
                work.price = self.price_spinbox.value()
                work.labor_rate = self.labor_rate_spinbox.value()
                work.parent_id = self.parent_id
                work.is_group = self.is_group
                work.marked_for_deletion = work_data['marked_for_deletion']
                
                if not self.work_repo.update(work):
                    raise Exception("Failed to update work")
        else:
            # Create new work
            work = Work()
            work.name = self.name_edit.text()
            work.code = self.code_edit.text()
            work.unit = self.unit_edit.text()
            work.price = self.price_spinbox.value()
            work.labor_rate = self.labor_rate_spinbox.value()
            work.parent_id = self.parent_id
            work.is_group = self.is_group
            
            work_id = self.work_repo.save(work)
            if not work_id:
                raise Exception("Failed to save work")
            self.work_id = work_id
        
        # Save cost items
        self.save_cost_items()
        
        # Save materials
        self.save_materials()
        
        self.is_modified = False
        return True
        
    except Exception as e:
        QMessageBox.critical(
            self,
            "Ошибка",
            f"Не удалось сохранить: {str(e)}"
        )
        return False

def save_cost_items(self):
    """Save cost items to database"""
    # Get existing associations
    existing = self.cost_item_material_repo.get_cost_items_for_work(self.work_id)
    existing_ids = {ci.id for ci, _ in existing}
    
    # Get current associations
    current_ids = {ci.id for ci, _ in self.cost_items}
    
    # Remove deleted associations
    for cost_item_id in existing_ids - current_ids:
        self.cost_item_material_repo.remove_association_by_work_cost_item_material(
            self.work_id,
            cost_item_id,
            None
        )
    
    # Add new associations
    for cost_item_id in current_ids - existing_ids:
        self.cost_item_material_repo.create_or_update_association(
            self.work_id,
            cost_item_id,
            None,
            0.0
        )

def save_materials(self):
    """Save materials to database"""
    # Get existing associations
    existing = self.cost_item_material_repo.get_materials_for_work(self.work_id)
    existing_map = {(m.id, ci.id): quantity for m, quantity, ci in existing}
    
    # Get current associations
    current_map = {(m.id, ci.id): quantity for m, quantity, ci in self.materials}
    
    # Remove deleted associations
    for (material_id, cost_item_id) in set(existing_map.keys()) - set(current_map.keys()):
        self.cost_item_material_repo.remove_association_by_work_cost_item_material(
            self.work_id,
            cost_item_id,
            material_id
        )
    
    # Add or update associations
    for (material_id, cost_item_id), quantity in current_map.items():
        self.cost_item_material_repo.create_or_update_association(
            self.work_id,
            cost_item_id,
            material_id,
            quantity
        )
```


### Total Cost Calculation

```python
def calculate_total_cost(self) -> float:
    """Calculate total work cost from composition"""
    total = 0.0
    
    # Add cost items
    for cost_item, _ in self.cost_items:
        total += cost_item.price
    
    # Add materials
    for material, quantity, _ in self.materials:
        total += material.price * quantity
    
    return total

def update_total_cost_display(self):
    """Update total cost display"""
    total = self.calculate_total_cost()
    self.total_cost_label.setText(f"Общая стоимость: {total:,.2f} руб.")
```

### Keyboard Shortcuts

```python
def keyPressEvent(self, event):
    """Handle key press events"""
    if event.matches(QKeySequence.StandardKey.Save):
        # Ctrl+S
        self.on_save()
    elif event.key() == Qt.Key.Key_S and event.modifiers() == (
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    ):
        # Ctrl+Shift+S
        self.on_save_and_close()
    elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        # Ctrl+Enter
        self.on_save_and_close()
    elif event.key() == Qt.Key.Key_Escape:
        # Esc
        self.on_close()
    else:
        super().keyPressEvent(event)
```

## UI Layout Examples

### Basic Info Tab (Existing)

```
┌─────────────────────────────────────────────────────────────┐
│  Наименование*:  [_________________________________]         │
│  Код:            [____________]                              │
│  Родитель:       [_____________________] [...] [✕]          │
│  Единица изм:    [____________]                              │
│  Цена:           [____________]                              │
│  Норма труда:    [____________]                              │
└─────────────────────────────────────────────────────────────┘
```

### Cost Items Tab

```
┌─────────────────────────────────────────────────────────────┐
│  [Добавить статью затрат]  [Удалить]                        │
├─────────────────────────────────────────────────────────────┤
│  Код    │ Наименование              │ Ед.изм │ Цена │ Норма │
├─────────┼───────────────────────────┼────────┼──────┼───────┤
│  1.01   │ Труд рабочих              │ час    │ 500  │ 2.5   │
│  1.02   │ Аренда оборудования       │ час    │ 200  │ 0.5   │
│  ...    │ ...                       │ ...    │ ...  │ ...   │
└─────────────────────────────────────────────────────────────┘
```

### Materials Tab

```
┌─────────────────────────────────────────────────────────────┐
│  [Добавить материал]  [Удалить]                             │
├─────────────────────────────────────────────────────────────┤
│  Статья    │ Код  │ Наименование │ Ед.изм │ Цена │ Кол-во │ Сумма │
├────────────┼──────┼──────────────┼────────┼──────┼────────┼───────┤
│  Труд      │ M001 │ Цемент М400  │ т      │ 5000 │ 0.25   │ 1250  │
│  Труд      │ M002 │ Песок речной │ т      │ 800  │ 1.5    │ 1200  │
│  ...       │ ...  │ ...          │ ...    │ ...  │ ...    │ ...   │
├────────────┴──────┴──────────────┴────────┴──────┴────────┴───────┤
│  Общая стоимость: 2,450.00 руб.                                   │
└─────────────────────────────────────────────────────────────────────┘
```


## Testing Strategy

### Manual Testing Checklist

**Basic Functionality:**
- [ ] Create new work with cost items and materials
- [ ] Edit existing work composition
- [ ] Add cost items to work
- [ ] Remove cost items from work
- [ ] Add materials to work
- [ ] Remove materials from work
- [ ] Edit material quantities
- [ ] Change material cost item associations
- [ ] Save work with composition
- [ ] Load work with composition

**Validation:**
- [ ] Prevent saving work without name
- [ ] Prevent adding duplicate cost items
- [ ] Prevent adding duplicate materials to same cost item
- [ ] Prevent deleting cost item with materials
- [ ] Validate material quantity > 0
- [ ] Prevent circular parent references

**UI/UX:**
- [ ] Tab switching preserves unsaved changes
- [ ] Tables display correct data
- [ ] Search filters work in selector dialogs
- [ ] Double-click selects item in dialogs
- [ ] Keyboard shortcuts work (Ctrl+S, Ctrl+Shift+S, Esc)
- [ ] Total cost updates automatically
- [ ] Confirmation dialogs appear for deletions
- [ ] Error messages are clear and in Russian

**Data Persistence:**
- [ ] Cost items persist after save
- [ ] Materials persist after save
- [ ] Quantities persist correctly
- [ ] Deletions persist after save
- [ ] Changes persist across form reopens

**Error Handling:**
- [ ] Database errors show user-friendly messages
- [ ] Validation errors highlight problematic fields
- [ ] Unsaved changes prompt on close
- [ ] Failed saves don't corrupt data

### Integration Testing

**Test with existing data:**
- Test with works that already have cost items
- Test with works that already have materials
- Test with hierarchical work structures
- Test with large numbers of cost items/materials

**Test edge cases:**
- Empty work (no cost items or materials)
- Work with only cost items (no materials)
- Work with only materials (no cost items - should prevent)
- Very large quantities
- Very small quantities (0.0001)
- Special characters in names

### Performance Testing

**Test with large datasets:**
- 100+ cost items in selector
- 1000+ materials in selector
- Work with 50+ cost items
- Work with 100+ materials
- Search performance with large catalogs


## Implementation Notes

### Differences from Web Client

The desktop implementation differs from the web client in several ways:

1. **UI Framework**: PyQt6 instead of Vue.js
2. **State Management**: Instance variables instead of Vue reactivity
3. **Dialogs**: Modal QDialogs instead of Vue modals
4. **Tables**: QTableWidget instead of HTML tables
5. **Search**: Client-side filtering instead of server-side API calls
6. **Language**: All UI text in Russian (matching existing desktop app)

### Reuse of Existing Components

The implementation will reuse:

- **ReferencePickerDialog**: For selecting parent work (already exists)
- **Repository Layer**: All repositories already implemented
- **Database Schema**: No changes needed
- **Validation Logic**: Can reuse patterns from web client

### New Components to Create

The implementation will create:

- **CostItemSelectorDialog**: New dialog for selecting cost items
- **MaterialSelectorDialog**: New dialog for selecting materials
- **MaterialAddDialog**: New multi-step dialog for adding materials
- **CostItemsTable**: New table widget for cost items
- **MaterialsTable**: New table widget for materials
- **Tab management**: Extend WorkForm with QTabWidget

### Code Organization

```
src/views/
├── work_form.py (extend existing)
├── dialogs/
│   ├── cost_item_selector_dialog.py (new)
│   ├── material_selector_dialog.py (new)
│   └── material_add_dialog.py (new)
└── widgets/
    ├── cost_items_table.py (new)
    └── materials_table.py (new)
```

### Migration Path

1. **Phase 1**: Create selector dialogs
   - CostItemSelectorDialog
   - MaterialSelectorDialog
   - MaterialAddDialog

2. **Phase 2**: Create table widgets
   - CostItemsTable
   - MaterialsTable

3. **Phase 3**: Extend WorkForm
   - Add QTabWidget
   - Add cost items tab
   - Add materials tab
   - Implement save/load logic

4. **Phase 4**: Testing
   - Manual testing
   - Integration testing
   - Bug fixes

### Estimated Effort

- Selector dialogs: 4-6 hours
- Table widgets: 3-4 hours
- WorkForm extension: 6-8 hours
- Testing and bug fixes: 4-6 hours
- **Total**: 17-24 hours


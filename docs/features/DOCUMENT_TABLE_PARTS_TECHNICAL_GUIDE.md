# Technical Guide: Document Table Parts

## Architecture Overview

The Document Table Parts feature provides a unified interface for managing tabular data across all document types in the system. It consists of several integrated components working together to provide consistent functionality.

### Core Components

1. **BaseTablePart** - Base widget class for desktop (PyQt6)
2. **BaseTablePart.vue** - Base component for web client (Vue.js)
3. **TablePartKeyboardHandler** - Keyboard shortcuts management
4. **TablePartCalculationEngine** - Automatic calculations
5. **TablePartSettingsService** - User settings persistence
6. **TablePartCommandManager** - Command integration

## Component Integration

### Desktop Client (PyQt6)

```python
from src.views.widgets.base_table_part import BaseTablePart, TablePartConfiguration

# Create configuration
config = TablePartConfiguration(
    table_id='estimate_lines',
    document_type='estimate',
    visible_commands=['add_row', 'delete_row', 'move_up', 'move_down'],
    keyboard_shortcuts_enabled=True,
    auto_calculation_enabled=True,
    drag_drop_enabled=True
)

# Create table part instance
table_part = BaseTablePart(config, parent=form, db_session=session, user_id=user.id)

# Register form commands
table_part.register_form_command('add_row', form.add_estimate_line)
table_part.register_form_command('delete_row', form.delete_estimate_lines)
```

### Web Client (Vue.js)

```vue
<template>
  <BaseTablePart
    :data="tableData"
    :columns="tableColumns"
    :configuration="tableConfig"
    @row-selection-changed="onSelectionChanged"
    @data-changed="onDataChanged"
    @command-executed="onCommandExecuted"
  />
</template>

<script setup>
import BaseTablePart from '@/components/common/BaseTablePart.vue'

const tableConfig = {
  tableId: 'estimate_lines',
  documentType: 'estimate',
  visibleCommands: ['add_row', 'delete_row', 'move_up', 'move_down'],
  keyboardShortcutsEnabled: true,
  autoCalculationEnabled: true,
  dragDropEnabled: true
}
</script>
```

## Keyboard Shortcuts System

### Desktop Implementation

```python
from src.services.table_part_keyboard_handler import (
    TablePartKeyboardHandler, ShortcutAction, create_keyboard_handler
)

# Create keyboard handler
handler = create_keyboard_handler(table_widget)

# Register action handlers
handler.register_action_handler(ShortcutAction.ADD_ROW, add_row_callback)
handler.register_action_handler(ShortcutAction.DELETE_ROW, delete_row_callback)

# Update context
context = create_table_context(
    widget=table_widget,
    selected_rows=[0, 1],
    current_row=0,
    is_hierarchical=False,
    is_editing=False
)
handler.update_context(context)
```

### Web Implementation

```typescript
import { 
  createKeyboardHandler, 
  ShortcutAction, 
  createTableContext 
} from '@/services/tablePartKeyboardHandler'

// Create handler
const handler = createKeyboardHandler()

// Register handlers
handler.registerActionHandler(ShortcutAction.ADD_ROW, () => executeCommand('add_row'))
handler.registerActionHandler(ShortcutAction.DELETE_ROW, () => executeCommand('delete_row'))

// Attach to element
handler.attachTo(containerElement)
```

## Calculation Engine

### Desktop Implementation

```python
from src.services.table_part_calculation_engine import (
    TablePartCalculationEngine, create_calculation_engine
)

# Create engine
engine = create_calculation_engine()

# Set performance thresholds
engine.set_performance_thresholds(100, 200)  # 100ms field, 200ms totals

# Perform calculation
result = engine.calculate_field(row_data, 'sum', all_table_data)
if result.success:
    update_field_value(result.value)
```

### Web Implementation

```typescript
import { useCalculationEngine } from '@/services/tablePartCalculationEngine'

// Initialize engine
const { engine, calculateField, calculateTotals } = useCalculationEngine()

// Perform calculation
const result = await calculateField(rowData, 'sum', allTableData)
if (result.success) {
  updateFieldValue(result.value)
}
```

## Settings Management

### Database Schema

```sql
-- User table part settings
CREATE TABLE user_table_part_settings (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    table_part_id VARCHAR(100) NOT NULL,
    settings_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, document_type, table_part_id)
);

-- Command configuration
CREATE TABLE table_part_command_config (
    id UUID PRIMARY KEY,
    document_type VARCHAR(100) NOT NULL,
    table_part_id VARCHAR(100) NOT NULL,
    user_id UUID,
    command_id VARCHAR(100) NOT NULL,
    is_visible BOOLEAN DEFAULT true,
    position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Settings Service Usage

```python
from src.services.table_part_settings_service import TablePartSettingsService

# Create service
settings_service = TablePartSettingsService(db_session)

# Load user settings
settings = settings_service.get_user_settings(user_id, 'estimate', 'lines')

# Save settings
success = settings_service.save_user_settings(user_id, 'estimate', 'lines', settings_data)

# Reset to defaults
settings_service.reset_user_settings(user_id, 'estimate', 'lines')
```

## Form Layout Management

### Desktop Implementation

```python
from src.services.form_layout_manager import FormLayoutManager, FormField, FieldType

# Create layout manager
layout_manager = FormLayoutManager()

# Analyze fields
fields = [
    FormField('number', 'Number:', line_edit, FieldType.SHORT_TEXT),
    FormField('date', 'Date:', date_edit, FieldType.DATE),
    # ... more fields
]

analysis = layout_manager.analyze_fields(fields)

# Create layout
if analysis.recommended_layout == 'two_column':
    config = layout_manager.create_two_column_layout(fields)
```

### Web Implementation

```typescript
import { useFormLayoutManager } from '@/services/formLayoutManager'

// Initialize layout manager
const { analyzeFields, createTwoColumnLayout } = useFormLayoutManager()

// Analyze and create layout
const analysis = analyzeFields(formFields)
if (analysis.recommendedLayout === 'two_column') {
  const config = createTwoColumnLayout(formFields)
}
```

## Command Integration

### Form Command Discovery

```python
from src.services.table_part_command_manager import table_command, CommandAvailability

class EstimateForm:
    @table_command(
        command_id='add_estimate_line',
        name='Add Line',
        availability=CommandAvailability.ALWAYS
    )
    def add_estimate_line(self, context):
        # Add line logic
        return CommandResult(success=True, message="Line added")
    
    @table_command(
        command_id='delete_estimate_lines',
        name='Delete Lines',
        availability=CommandAvailability.REQUIRES_SELECTION
    )
    def delete_estimate_lines(self, context):
        # Delete lines logic
        return CommandResult(success=True, affected_rows=context.selected_rows)
```

### Web Command Integration

```typescript
import { TablePartCommandManager } from '@/services/tablePartCommandManager'

// Create command manager
const commandManager = new TablePartCommandManager()

// Register form instance
const form = {
  addEstimateLine: () => { /* add logic */ },
  deleteEstimateLines: () => { /* delete logic */ }
}

commandManager.discoverAndRegisterCommands(form)
```

## Performance Optimization

### Virtual Scrolling (Web)

```typescript
import { useTablePartVirtualization } from '@/composables/useTablePartVirtualization'

const { 
  visibleItems, 
  containerProps, 
  wrapperProps 
} = useTablePartVirtualization(allItems, {
  itemHeight: 40,
  containerHeight: 400,
  overscan: 5
})
```

### Memory Optimization

```typescript
import { createMemoryOptimizer } from '@/services/tablePartMemoryOptimizer'

const optimizer = createMemoryOptimizer({
  maxCacheSize: 1000,
  cleanupInterval: 30000,
  memoryThreshold: 0.8
})

optimizer.optimizeTableData(largeDataset)
```

## Error Handling

### Desktop Error Handling

```python
from src.services.table_part_error_handler import TablePartErrorHandler

# Create error handler
error_handler = TablePartErrorHandler()

# Handle calculation error
try:
    result = perform_calculation()
except Exception as e:
    recovery_action = error_handler.handle_calculation_error(e, context)
    if recovery_action:
        recovery_action.execute()
```

### Web Error Handling

```typescript
import { TablePartErrorHandler } from '@/services/tablePartErrorHandler'

const errorHandler = new TablePartErrorHandler()

// Handle error with recovery
try {
  await performOperation()
} catch (error) {
  const recovery = await errorHandler.handleError(error, context)
  if (recovery.canRecover) {
    await recovery.execute()
  }
}
```

## Testing

### Property-Based Testing

```python
from hypothesis import given, strategies as st
import pytest

@given(
    quantity=st.integers(min_value=1, max_value=1000),
    price=st.floats(min_value=0.01, max_value=10000.0)
)
def test_quantity_price_calculation(quantity, price):
    """
    **Feature: document-table-parts, Property 6: Automatic Sum Calculation on Quantity Change**
    **Validates: Requirements 8.1**
    """
    row_data = {'quantity': quantity, 'price': price}
    result = calculate_sum(row_data)
    
    expected = quantity * price
    assert abs(result - expected) < 0.01
```

### Integration Testing

```python
def test_complete_table_part_workflow():
    """Test complete user workflow"""
    # 1. Create table part
    table_part = create_test_table_part()
    
    # 2. Add row
    table_part.execute_command('add_row')
    assert len(table_part.get_data()) == 1
    
    # 3. Modify data
    table_part.update_cell(0, 'quantity', 10)
    table_part.update_cell(0, 'price', 100.0)
    
    # 4. Verify calculation
    assert table_part.get_cell_value(0, 'sum') == 1000.0
    
    # 5. Move row
    table_part.execute_command('move_up')
    
    # 6. Delete row
    table_part.execute_command('delete_row')
    assert len(table_part.get_data()) == 0
```

## Deployment

### Database Migration

```python
# Migration script
def upgrade():
    # Create user settings table
    op.create_table(
        'user_table_part_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('table_part_id', sa.String(100), nullable=False),
        sa.Column('settings_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'document_type', 'table_part_id')
    )
```

### Configuration

```python
# settings.py
TABLE_PART_SETTINGS = {
    'CALCULATION_TIMEOUT_MS': 100,
    'TOTAL_CALCULATION_TIMEOUT_MS': 200,
    'PERFORMANCE_MONITORING_ENABLED': True,
    'DEFAULT_VISIBLE_COMMANDS': [
        'add_row', 'delete_row', 'move_up', 'move_down'
    ]
}
```

### Web Client Build

```bash
# Build for production
cd web-client
npm run build

# Test build
npm run test:unit -- --run
```

## Monitoring and Maintenance

### Performance Monitoring

```python
from src.services.table_part_performance_monitor import PerformanceMonitor

# Create monitor
monitor = PerformanceMonitor()

# Track metrics
monitor.track_calculation_time(calculation_time)
monitor.track_memory_usage(memory_usage)

# Get alerts
if monitor.has_performance_alerts():
    alerts = monitor.get_alerts()
    send_admin_notification(alerts)
```

### Health Checks

```python
def check_table_part_health():
    """Health check for table part functionality"""
    checks = [
        check_database_connectivity(),
        check_calculation_engine_performance(),
        check_settings_service_availability(),
        check_keyboard_handler_registration()
    ]
    
    return all(checks)
```

## Troubleshooting

### Common Issues

1. **Slow Calculations**
   - Check data volume
   - Verify calculation rules
   - Monitor performance metrics

2. **Keyboard Shortcuts Not Working**
   - Verify handler registration
   - Check context updates
   - Ensure no conflicts with other handlers

3. **Settings Not Persisting**
   - Check database connectivity
   - Verify user permissions
   - Check settings service configuration

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('table_parts').setLevel(logging.DEBUG)

# Enable performance monitoring
table_part.show_performance_monitor()

# Enable calculation debugging
calculation_engine.set_debug_mode(True)
```

## API Reference

### Core Classes

- `BaseTablePart` - Main table part widget
- `TablePartConfiguration` - Configuration object
- `TablePartKeyboardHandler` - Keyboard shortcuts
- `TablePartCalculationEngine` - Calculations
- `TablePartSettingsService` - Settings management

### Key Methods

- `register_form_command()` - Register form command
- `execute_command()` - Execute table command
- `update_settings()` - Update user settings
- `calculate_field()` - Perform field calculation
- `get_performance_metrics()` - Get performance data

### Events

- `rowSelectionChanged` - Row selection changed
- `dataChanged` - Table data changed
- `commandExecuted` - Command executed
- `calculationCompleted` - Calculation completed
- `settingsChanged` - Settings changed
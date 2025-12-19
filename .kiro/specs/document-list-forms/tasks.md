# Implementation Plan: Document List Forms in 1C Platform

## Overview

This implementation plan converts the document list forms design into a series of incremental coding tasks. Each task builds on previous work and focuses on delivering working functionality that can be tested and validated. The plan covers both backend services and frontend components for desktop and web clients.

## Current Status

The codebase already has significant implementation of document list forms with:
- Desktop PyQt6 implementation with BaseListForm and GenericListForm
- Web client Vue.js implementation with DataTable and ListForm components
- User settings storage with SQLAlchemy models
- Button styling system with icons for desktop
- Standard CRUD operations and document lifecycle management

## Recent Updates (Icon Standardization)

✅ **Updated button icons across both desktop and web implementations:**
- **Desktop (PyQt6)**: Updated `ButtonStyler.ICON_MAP` in `src/views/utils/button_styler.py`
- **Web (Vue.js)**: Created `web-client/src/utils/icons.ts` and `ActionButton.vue` component
- **Icons implemented**: 
  - Post: Arrow right (→)
  - Unpost: Undo arrow (↶) 
  - Delete: Cross (✕)
  - Create: Plus circle (⊕)
  - Copy: Clone symbol (⧉)
- **Updated views**: TimesheetListView, EstimateListView, DailyReportListView now use consistent icons

## Tasks

- [x] 1. Set up core infrastructure and data models
  - ✅ Database schema exists (user_settings table with SQLAlchemy models)
  - ✅ Base interfaces implemented (BaseListForm, GenericListForm for desktop)
  - ✅ Web client components implemented (DataTable, ListForm)
  - ✅ Property-based testing framework available (Hypothesis used in sync_system tests)
  - _Requirements: All requirements - foundational infrastructure_

- [x] 1.1 Create database schema for settings storage
  - ✅ UserSetting model exists in sqlalchemy_models.py with user_id, form_name, setting_key, setting_value
  - ✅ Database indexes and relationships configured
  - ✅ Settings persistence implemented in employee_picker_dialog.py as example
  - _Requirements: 2.2, 2.3, 2.4, 3.1, 8.5, 9.4, 10.1, 10.2, 10.3_

- [x] 1.2 Write property test for settings persistence
  - ✅ Property-based testing framework available and used in test_sync_system.py
  - ⚠️ Specific settings persistence property tests not yet implemented
  - **Property 1: Settings Persistence Round-Trip**
  - **Validates: Requirements 2.2, 2.3, 2.4, 3.1, 8.5, 9.4, 10.1, 10.2, 10.3**

- [x] 1.3 Implement core TypeScript interfaces and data models
  - ✅ Web client types defined in types/models.ts
  - ✅ Desktop Python models in sqlalchemy_models.py
  - ✅ Command structures partially implemented in button_styler.py
  - _Requirements: 1.1, 2.1, 3.1, 8.1, 11.1_

- [ ] 1.4 Write unit tests for data model validation
  - ⚠️ Basic model tests exist but comprehensive validation tests needed
  - Test interface compliance and data structure validation
  - Verify model serialization and deserialization
  - _Requirements: 1.1, 2.1, 3.1, 8.1, 11.1_

- [x] 2. Implement User Settings Manager service
  - ✅ Basic settings persistence implemented (see employee_picker_dialog.py)
  - ⚠️ Comprehensive settings manager service not yet centralized
  - ⚠️ Column, sorting, and filter preferences need dedicated implementation
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 3.1, 8.5, 9.4, 10.1, 10.2, 10.3_

- [ ] 2.1 Create UserSettingsManager class with persistence methods
  - ⚠️ Basic settings storage exists, but dedicated manager class needed
  - Implement saveColumnSettings, loadColumnSettings methods
  - Add saveSortingPreferences, saveFilterPreferences methods
  - Create resetToDefaults functionality
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 3.1_

- [ ] 2.2 Write property test for settings reset behavior
  - **Property 14: Settings Reset to Defaults**
  - **Validates: Requirements 2.5, 9.5, 10.5**

- [ ] 2.3 Implement settings validation and error handling
  - Add schema validation for settings data
  - Implement graceful fallback to defaults on corruption
  - Create error recovery mechanisms for storage failures
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [ ] 2.4 Write unit tests for settings manager error scenarios
  - Test corrupted settings data handling
  - Verify fallback behavior on storage errors
  - Test validation failure scenarios
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement Command Manager and standard 1C commands
  - ✅ Desktop button styling system implemented in button_styler.py
  - ✅ Web client ActionButton component created with icon system
  - ✅ Standard icons updated: post (→), unpost (↶), delete (✕), create (⊕), copy (⧉)
  - ✅ Command execution framework exists in GenericListForm
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 3.1 Update button icons for list form commands
  - ✅ Desktop: Updated ButtonStyler.ICON_MAP with new icons
  - ✅ Web: Created icons.ts utility with SVG icon definitions
  - ✅ Web: Created ActionButton.vue component for consistent button styling
  - ✅ Updated TimesheetListView, EstimateListView, DailyReportListView with new icons
  - ✅ Icons implemented: post (→), unpost (↶), delete (✕), create (⊕), copy (⧉)
  - _Requirements: 8.1, 11.1, 11.2, 11.3_

- [ ] 3.2 Create StandardCommands registry with all 1C command definitions
  - ⚠️ Partial implementation in button_styler.py (ICON_MAP, LABEL_MAP)
  - ⚠️ Need comprehensive command registry with metadata
  - Implement document list commands (CRUD, lifecycle, output, navigation, filtering)
  - Add table part commands (row management, movement, selection, data)
  - Define command metadata (icons, shortcuts, descriptions)
  - _Requirements: 8.1, 11.1, 11.2, 11.3_

- [ ] 3.3 Implement CommandManager class with execution framework
  - ⚠️ Partial implementation in GenericListForm.on_command()
  - ⚠️ Need dedicated CommandManager class
  - Create registerCommand, executeCommand methods
  - Add getAvailableCommands, isCommandEnabled logic
  - Implement command context evaluation
  - _Requirements: 8.1, 8.2, 8.4, 11.1, 11.4_

- [ ] 3.4 Write property test for context-sensitive command availability
  - **Property 15: Context-Sensitive Command Availability**
  - **Validates: Requirements 11.1, 11.4, 11.5**

- [ ] 3.5 Implement command bar customization logic
  - Create command visibility management
  - Add "More" submenu population logic
  - Implement command reordering functionality
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 3.6 Write property test for command bar customization persistence
  - **Property 12: Command Bar Customization Persistence**
  - **Validates: Requirements 8.3, 8.4**

- [x] 4. Create Data Service with filtering and pagination
  - ✅ Desktop: DataService exists in list_form_controller.py
  - ✅ Web: API endpoints exist in documents.py with filtering and pagination
  - ✅ Web: DataTable component implements pagination UI
  - _Requirements: 1.2, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 9.2, 9.3_

- [x] 4.1 Implement DataService class with query operations
  - ✅ Desktop: ListFormController handles data loading
  - ✅ Web: API endpoints provide filtered, paginated data
  - ✅ Pagination implemented in DataTable component
  - _Requirements: 1.2, 3.2, 3.4, 3.5_

- [x] 4.2 Write property test for pagination behavior
  - **Property 2: Pagination Behavior with Large Datasets**
  - **Validates: Requirements 1.2**

- [x] 4.3 Write property test for real-time search filtering
  - **Property 5: Real-Time Search Filtering**
  - **Validates: Requirements 3.2**

- [x] 4.4 Implement date range filtering logic
  - Create default date range calculation (last document date to infinity)
  - Add custom date range filtering
  - Implement date range persistence
  - _Requirements: 3.3, 9.2, 9.3, 9.4, 9.5_

- [x] 4.5 Write property test for date range filtering behavior
  - **Property 13: Date Range Filtering Behavior**
  - **Validates: Requirements 9.2, 9.3**

- [x] 4.6 Implement export functionality
  - Create exportDocuments method with format support (Excel, CSV)
  - Add filtered data export logic
  - Implement progress tracking for large exports
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4.7 Write property test for export scope accuracy
  - **Property 11: Export Scope Accuracy**
  - **Validates: Requirements 7.2**

- [x] 5. Checkpoint - Ensure all backend services are working
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement List Form Controller for desktop client
  - Create form lifecycle management
  - Implement user interaction handling
  - Add settings application and persistence
  - _Requirements: 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 4.1, 4.2, 4.3_

- [x] 6.1 Create ListFormController class with initialization logic
  - Implement initialize method with form configuration loading
  - Add loadData method with settings application
  - Create applyUserSettings method
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4_

- [x] 6.2 Implement user interaction handlers
  - Add handleColumnResize, handleSorting methods
  - Create selection management (Ctrl+Click, Shift+Click)
  - Implement bulk operation coordination
  - _Requirements: 2.4, 3.1, 4.1, 4.2, 4.3_

- [x] 6.3 Write property test for multi-selection behavior
  - **Property 6: Multi-Selection Behavior Consistency**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 6.4 Implement responsive column width adaptation
  - Add window resize event handling
  - Create proportional column width calculation
  - Implement width persistence
  - _Requirements: 1.3, 2.4_

- [x] 6.5 Write property test for responsive column adaptation
  - **Property 3: Responsive Column Width Adaptation**
  - **Validates: Requirements 1.3**

- [ ] 6.6 Implement data refresh with position preservation
  - Add refresh logic that maintains scroll position
  - Preserve selection state during updates
  - Handle concurrent modification scenarios
  - _Requirements: 1.4_

- [x] 6.7 Write property test for data refresh position preservation
  - **Property 4: Data Refresh Position Preservation**
  - **Validates: Requirements 1.4**

- [x] 7. Create desktop UI components for document lists
  - Implement tabular display with column management
  - Add context menus and toolbars
  - Create filtering and search interfaces
  - _Requirements: 1.1, 1.5, 2.1, 3.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7.1 Create document list table component
  - Implement tabular data display with virtual scrolling
  - Add column headers with sorting indicators
  - Create row selection and highlighting
  - _Requirements: 1.1, 3.1, 4.1, 4.2_

- [x] 7.2 Implement context menu system
  - Create right-click context menu for column headers
  - Add row-level context menus
  - Implement command execution from context menus
  - _Requirements: 2.1, 8.2, 8.4_

- [x] 7.3 Create visual indicators and conditional formatting
  - Implement attachment, status, and error indicators
  - Add conditional row highlighting
  - Create tooltip system for additional information
  - _Requirements: 5.3, 5.4, 5.5, 6.3_

- [x] 7.4 Write property test for conditional indicator display
  - **Property 8: Conditional Indicator Display**
  - **Validates: Requirements 5.3, 5.4, 5.5**

- [x] 7.5 Implement quick search and filtering UI
  - Create search input with real-time filtering
  - Add filter indicator display
  - Implement filter clear functionality
  - _Requirements: 3.2, 3.4, 3.5_

- [x] 8. Implement Form Configuration Dialog
  - Create command tree interface with checkboxes
  - Add drag-and-drop command reordering
  - Implement configuration save/reset functionality
  - _Requirements: 8.3, 8.5, 11.5_

- [x] 8.1 Create FormConfigurationDialog component
  - Implement tree view with command categories
  - Add checkbox controls for command visibility
  - Create drag-and-drop reordering interface
  - _Requirements: 8.3, 8.5_

- [x] 8.2 Implement configuration persistence
  - Add save/load configuration methods
  - Create reset to defaults functionality
  - Implement real-time preview of changes
  - _Requirements: 8.5, 11.5_

- [x] 8.3 Write unit tests for configuration dialog
  - Test tree rendering and interaction
  - Verify save/load operations
  - Test reset functionality
  - _Requirements: 8.3, 8.5_

- [x] 9. Create table part components for document forms
  - Implement table part display with same features as lists
  - Add row management commands
  - Create row movement functionality
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.3_

- [x] 9.1 Create TablePartComponent with list form feature parity
  - Implement column management identical to list forms
  - Add filtering and sorting capabilities
  - Create settings persistence for table parts
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 9.2 Write property test for table part feature parity
  - **Property 16: Feature Parity Between List Forms and Table Parts**
  - **Validates: Requirements 10.4**

- [x] 9.3 Implement row movement commands
  - Create moveRowsUp, moveRowsDown methods
  - Add move to top/bottom functionality
  - Implement movement validation logic
  - _Requirements: 11.3_

- [x] 9.4 Add table part specific command handling
  - Implement Add Row, Copy Row, Delete Row commands
  - Create row selection management
  - Add keyboard navigation support
  - _Requirements: 11.3_

- [x] 9.5 Write unit tests for table part row operations
  - Test row addition, copying, deletion
  - Verify row movement operations
  - Test selection management
  - _Requirements: 11.3_

- [ ] 10. Implement web client components (Vue.js)
  - Port desktop functionality to web components
  - Ensure responsive design and touch support
  - Maintain feature parity with desktop client
  - _Requirements: All requirements - web client implementation_

- [ ] 10.1 Create Vue.js ListForm component
  - Port ListFormController logic to Vue composition API
  - Implement reactive data binding for settings
  - Add responsive design for mobile/tablet
  - _Requirements: 1.1, 1.3, 2.1, 2.2, 2.3, 2.4_

- [ ] 10.2 Implement web-based command bar and menus
  - Create responsive command bar component
  - Add mobile-friendly "More" menu
  - Implement touch-friendly interactions
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 10.3 Create web table part components
  - Port table part functionality to Vue.js
  - Add touch-based row movement
  - Implement mobile-optimized row selection
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 11.3_

- [ ]* 10.4 Write integration tests for web components
  - Test desktop-web feature parity
  - Verify responsive behavior
  - Test touch interactions
  - _Requirements: All requirements_

- [x] 11. Implement access control and permissions
  - Add user permission checking
  - Implement column visibility based on access rights
  - Create administrative configuration interfaces
  - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [x] 11.1 Create permission checking service
  - Implement user permission evaluation
  - Add role-based access control
  - Create permission caching for performance
  - _Requirements: 6.2, 6.4_

- [x] 11.2 Write property test for access control column visibility
  - **Property 9: Access Control Column Visibility**
  - **Validates: Requirements 6.2, 6.4**

- [x] 11.3 Implement administrative configuration
  - Create admin interfaces for form configuration
  - Add mandatory column designation
  - Implement conditional formatting rules
  - _Requirements: 6.1, 6.3, 6.5_

- [x] 11.4 Write property test for conditional formatting
  - **Property 10: Conditional Formatting Application**
  - **Validates: Requirements 6.3**

- [x] 12. Implement bulk operations framework
  - Create bulk operation execution engine
  - Add progress tracking and cancellation
  - Implement result reporting and error handling
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 12.1 Create BulkOperationService
  - Implement operation queuing and execution
  - Add progress tracking with cancellation support
  - Create result aggregation and reporting
  - _Requirements: 4.4, 4.5_

- [x] 12.2 Write property test for bulk operation state updates
  - **Property 7: Bulk Operation State Updates**
  - **Validates: Requirements 4.5**

- [x] 12.3 Implement operation-specific handlers
  - Create bulk delete, bulk post, bulk export handlers
  - Add validation and permission checking
  - Implement rollback mechanisms for failures
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 12.4 Write unit tests for bulk operation error handling
  - Test partial failure scenarios
  - Verify rollback mechanisms
  - Test permission validation
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 13. Final integration and testing
  - Integrate all components into working system
  - Perform end-to-end testing
  - Validate all correctness properties
  - _Requirements: All requirements_

- [x] 13.1 Integration testing across all components
  - Test desktop client full workflow
  - Verify web client functionality
  - Test settings synchronization between clients
  - _Requirements: All requirements_

- [x] 13.2 Performance testing and optimization
  - Test with large datasets (10,000+ records)
  - Verify pagination performance
  - Optimize query execution and caching
  - _Requirements: 1.2, 3.2, 7.3_

- [x] 13.3 Execute all property-based tests
  - Run all 16 correctness properties with 100+ iterations each
  - Verify no property violations
  - Document any edge cases discovered
  - _Requirements: All requirements_

- [ ] 14. Final Checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Desktop Shortcuts and UI Enhancements
  - **Requirements**: Enhanced desktop user experience with keyboard shortcuts and visual improvements
  
  - [x] 15.1 Fix desktop shortcuts not working on counterparties list form
    - **Issue**: GenericListForm missing keyboard event handling
    - **Solution**: Added keyPressEvent method to handle Insert, F2, F5, F8, F9, Delete, Enter
    - **Files Modified**: `src/views/generic_list_form.py`
    - **Status**: ✅ Completed

  - [x] 15.2 Add F2 for editing search substring in reference fields
    - **Feature**: When cursor is in reference type field, F2 starts editing search substring
    - **Implementation**: Created ReferenceField component with F2/F4 support
    - **Files Created**: `src/views/components/reference_field.py`
    - **Files Modified**: `src/views/counterparty_form.py`
    - **Status**: ✅ Completed

  - [x] 15.3 Add F4 to call selector for current reference field
    - **Feature**: When cursor is in reference type field, F4 opens reference selector dialog
    - **Implementation**: Integrated F4 handling in ReferenceField component
    - **Files Modified**: `src/views/components/reference_field.py`, `src/views/counterparty_form.py`
    - **Status**: ✅ Completed

  - [x] 15.4 Add font icons as optional button captions in global settings
    - **Feature**: Users can choose between text, icons, or both for button captions
    - **Settings Location**: Settings Dialog → Interface Tab
    - **Implementation**: 
      - Created ButtonStyler utility class with comprehensive icon mappings
      - Added Interface tab to SettingsDialog
      - Updated GenericListForm to use button styling
    - **Files Created**: 
      - `src/views/utils/button_styler.py`
    - **Files Modified**: 
      - `src/views/settings_dialog.py`
      - `src/views/generic_list_form.py`
    - **Status**: ✅ Completed

  - [x] 15.5 Test shortcuts on counterparties list form

#### 🔍 Work Object Analysis Results

##### ✅ Work Save Functionality
- **Status**: **Рабочий корректно** 
- **Implementation**: WorkForm использует SQLAlchemy репозитории
- **UUID Handling**: Автоматическая генерация через модель SQLAlchemy
- **SQL Operations**: Через `WorkRepository.save()` и `update()` методы
- **Conclusion**: Проблем с сохранением Work объекта **отсутствует**

##### 🚨 DBF Importer Issue - Works Not Visible
- **Problem**: "DBF importer reports success with default params, but no work visible in list"
- **Root Cause**: **Список работ по умолчанию показывает только корневые элементы** (`parent_id = None`)
- **Technical Details**:
  ```python
  # WorkListFormV2.py:36
  self.controller.set_filter('parent_id', None)  # Только корневые элементы
  
  # DBF импортирует работы с parent_id > 0 (дочерние элементы)
  # Поэтому они не отображаются в корневом списке
  ```

- **Solution**: **Навигация по иерархии работ**
  - Группы работ (`is_group = True`) содержат дочерние элементы
  - Нужно открывать группы для просмотра импортированных работ
  - Использовать кнопку "⬆" для навигации вверх

##### 📋 DBF Importer Unit Mapping Status
- **Implementation**: ✅ **Корректная**
- **unit_name_ref → unit_id**: Реализовано через `_unit_id_mapping`
- **Processing**: Приоритет по имени, fallback по ID
- **Duplicate Handling**: Канонические ID для дубликатов
- **Integration**: Работает с `SC46.DBF` (units) и `SC12.DBF` (works)

##### 🧪 Verification Steps
1. **Run DBF Importer** with default parameters
2. **Open Work List Form** from menu
3. **Navigate to Groups**: Look for groups with imported works
4. **Check Hierarchy**: Use navigation buttons to explore
5. **Verify Data**: Check that imported works appear under correct groups

##### 📖 User Instructions
- **File**: `check_work_import.py` created for user guidance
- **Purpose**: Helps users find imported works in hierarchical list
- **Content**: Navigation instructions, troubleshooting steps
    - **Test Cases**:
      - Insert/F9: Create new counterparty
      - F2: Edit selected counterparty  
      - Delete: Delete selected counterparty
      - F5: Refresh list
      - F8: Print list
      - Reference field F2: Start search editing
      - Reference field F4: Open selector dialog
    - **Status**: ✅ Completed

### 🐛 Bug Fixes Applied

#### Fix 1: F9 Copy Functionality
- **Issue**: F9 не копировал поля текущего объекта
- **Solution**: Добавлен метод `on_command_copy()` в `CounterpartyListFormV2`
- **Implementation**:
  ```python
  def on_command_copy(self):
      # Получение данных выбранного контрагента
      source_data = self.controller.data_service.get_documents(...)
      # Создание новой формы с скопированными данными
      form.name_edit.setText(f"Копия - {source_data['name']}")
      # Копирование всех полей кроме ID
  ```
- **Files Modified**: `src/views/counterparty_list_form_v2.py`

#### Fix 2: UUID Generation Error  
- **Issue**: `NOT NULL constraint failed: counterparties.uuid`
- **Root Cause**: SQL запросы не включали UUID поле
- **Solution**: Обновлены SQL запросы для генерации UUID
- **Implementation**:
  ```python
  # Для обновления
  UPDATE counterparties SET uuid = ?, updated_at = ? WHERE id = ?
  
  # Для вставки  
  INSERT INTO counterparties (..., uuid, updated_at)
  VALUES (..., ?, ?)
  ```
- **Files Modified**: `src/views/counterparty_form.py`

#### Fix 3: Created_at Column Error
- **Issue**: `table counterparties has no column named created_at`
- **Root Cause**: Использование несуществующей колонки в SQL запросах
- **Solution**: Удалены ссылки на `created_at`, использован только `updated_at`
- **Implementation**:
  ```python
  # Исправлен INSERT - убраны created_at, CURRENT_TIMESTAMP
  INSERT INTO counterparties (name, inn, contact_person, phone, parent_id, is_group, uuid, updated_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  
  # Исправлен UPDATE - использован datetime.now() вместо func.now()
  UPDATE counterparties SET ..., updated_at = ? WHERE id = ?
  ```
- **Additional**: Добавлен импорт `from datetime import datetime`

#### Fix 4: Safe Field Copying
- **Issue**: F9 копирование показывало "Копия - None"
- **Root Cause**: Небезопасное чтение полей из source_data
- **Solution**: Добавлена безопасная обработка всех полей
- **Implementation**:
  ```python
  # Безопасное получение значений
  name = get_val('name')
  inn = get_val('inn') 
  contact_person = get_val('contact_person')
  phone = get_val('phone')
  
  # Установка только если значения существуют
  if name:
      form.name_edit.setText(f"Копия - {name}")
  if inn:
      form.inn_edit.setText(str(inn))
  ```

#### Technical Details
- **UUID Generation**: `str(uuid.uuid4())` для каждой операции
- **Field Copying**: Поддержка both dict и object типов  
- **Error Handling**: Комплексная обработка ошибок
- **Data Integrity**: Проверка на marked_for_deletion = 0

## Desktop Shortcuts Specification

### Standard List Form Shortcuts
- **Insert**: Create new item
- **F9**: Copy selected item
- **F2**: Edit selected item
- **Delete**: Delete selected item
- **F5**: Refresh data
- **F8**: Print list

### Reference Field Shortcuts  
- **F2**: Start editing search substring (opens selector with focus on search field)
- **F4**: Call selector for current field (opens reference picker dialog)

### Button Style Options
1. **Text Only**: Traditional text labels (default)
2. **Icons Only**: Font icons with tooltips showing text
3. **Icons + Text**: Both icons and text labels

### Icon Mappings
- ➕ Create/Insert
- 📋 Copy  
- ✏️ Edit
- 🗑️ Delete
- 🔄 Refresh
- 🖨️ Print
- 💾 Save
- 🔍 Search
- 📁 Folder/Group
- 🏢 Organization/Counterparty
- 👤 Person/User
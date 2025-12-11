# Desktop Work Composition Specification

## Overview

This specification defines the implementation of work composition functionality in the desktop application (Python/PyQt6). The desktop application currently has a basic Work form that only includes fundamental fields. This spec extends the Work form to include full composition management with cost items and materials, bringing it to feature parity with the web client.

## Status

**Current Status**: Design Complete, Ready for Implementation

- ✅ Requirements document created (17 requirements)
- ✅ Design document created
- ✅ Tasks document created (14 tasks)
- ⏳ Implementation not started

## Documents

### 1. Requirements Document
**File**: `requirements.md`

Defines 17 requirements covering:
- Tabbed interface for work form
- Cost items table and management
- Materials table and management
- Data persistence and validation
- Selector dialogs
- Error handling
- User experience enhancements

All requirements written in Russian to match desktop app UI.

### 2. Design Document
**File**: `design.md`

Specifies:
- System architecture
- Component design (Qt widgets)
- Data models and repository layer
- User workflows
- Error handling strategy
- UI layouts
- Implementation details
- Testing strategy

### 3. Tasks Document
**File**: `tasks.md`

Defines 14 implementation tasks organized in 4 phases:
- **Phase 1**: Selector Dialogs (3 tasks, 4-6 hours)
- **Phase 2**: Table Widgets (2 tasks, 3-4 hours)
- **Phase 3**: WorkForm Extension (7 tasks, 10-14 hours)
- **Phase 4**: Testing and Polish (2 tasks, 4-6 hours)

**Total Estimated Time**: 21-30 hours

## Key Features

### Tabbed Interface
- Tab 1: Основные данные (Basic Info) - existing fields
- Tab 2: Статьи затрат (Cost Items) - new
- Tab 3: Материалы (Materials) - new

### Cost Items Management
- Add cost items to work
- Remove cost items (with validation)
- Display in hierarchical table
- Search and filter

### Materials Management
- Add materials linked to cost items
- Remove materials
- Edit quantities
- Change cost item associations
- Calculate total costs

### Data Persistence
- Save to existing database schema
- Use existing repository layer
- Atomic saves with validation

## Technical Details

### Technology Stack
- **UI Framework**: PyQt6
- **Database**: SQLite (existing)
- **ORM**: SQLAlchemy (existing)
- **Language**: Python 3.x

### Existing Infrastructure
- ✅ Database schema complete (no changes needed)
- ✅ Repository layer complete (CostItemMaterialRepository exists)
- ✅ Backend API complete (for web client)
- ⏳ Desktop UI needs implementation

### New Components
- CostItemSelectorDialog
- MaterialSelectorDialog
- MaterialAddDialog
- CostItemsTable widget
- MaterialsTable widget
- Extended WorkForm with tabs

## Implementation Approach

### Reuse Existing Patterns
- Follow existing ReferencePickerDialog pattern
- Use existing repository methods
- Match existing code style
- Maintain Russian UI text

### Incremental Development
1. Build selector dialogs first (independent)
2. Build table widgets (independent)
3. Integrate into WorkForm
4. Add persistence and validation
5. Test and polish

### Testing Strategy
- Manual testing with checklist
- Integration testing with real data
- Performance testing with large datasets
- Bug fixes and polish

## Getting Started

To begin implementation:

1. Read `requirements.md` to understand what needs to be built
2. Read `design.md` to understand how to build it
3. Follow `tasks.md` in order, starting with Task 1

Each task includes:
- Requirements it addresses
- Detailed implementation steps
- Acceptance criteria
- Files to create/modify
- Dependencies on other tasks

## Dependencies

### External Dependencies
- PyQt6 (already installed)
- SQLAlchemy (already installed)
- Existing repository layer

### Internal Dependencies
- Tasks have clear dependency chain
- Follow implementation order in tasks.md
- Some tasks can be done in parallel (dialogs, widgets)

## Success Criteria

Implementation is complete when:
- ✅ All 14 tasks completed
- ✅ All 17 requirements satisfied
- ✅ Manual testing checklist passes
- ✅ No critical bugs
- ✅ Feature parity with web client
- ✅ Data persists correctly
- ✅ UI responsive and intuitive

## Notes

- All UI text in Russian (matching desktop app)
- No database changes needed
- No repository changes needed
- Focus on desktop UI implementation only
- Reuse existing patterns and components where possible

## Questions?

Refer to:
- `requirements.md` for WHAT to build
- `design.md` for HOW to build it
- `tasks.md` for WHEN to build each part


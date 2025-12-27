# Documentation Structure Plan

## Current Issues
- Many files in root docs folder without categorization
- Overlapping content between folders
- Legacy files mixed with current documentation
- No clear separation for different user types (developers vs users)
- Inconsistent naming conventions

## Proposed New Structure

```
docs/
├── README.md                          # Main documentation index
├── CONTRIBUTING.md                    # Documentation contribution guide
│
├── user-guide/                       # End-user documentation
│   ├── README.md                     # User guide index
│   ├── quick-start/
│   │   ├── installation.md
│   │   ├── basic-usage.md
│   │   └── first-steps.md
│   ├── features/
│   │   ├── daily-reports.md
│   │   ├── estimates.md
│   │   ├── timesheets.md
│   │   ├── work-composition.md
│   │   └── bulk-operations.md
│   ├── russian/                      # Russian language docs
│   │   ├── README.md
│   │   └── [translated files]
│   └── troubleshooting/
│       ├── common-issues.md
│       └── faq.md
│
├── developer-guide/                  # Developer documentation
│   ├── README.md                     # Developer guide index
│   ├── setup/
│   │   ├── development-environment.md
│   │   ├── database-setup.md
│   │   └── project-structure.md
│   ├── api/
│   │   ├── README.md
│   │   ├── endpoints.md
│   │   ├── authentication.md
│   │   └── examples.md
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── data-model.md
│   │   ├── sync-system.md
│   │   └── patterns.md
│   ├── deployment/
│   │   ├── production.md
│   │   ├── distribution.md
│   │   └── configuration.md
│   └── testing/
│       ├── unit-tests.md
│       ├── integration-tests.md
│       └── debugging.md
│
├── administration/                    # System administration
│   ├── README.md                     # Admin guide index
│   ├── installation/
│   │   ├── server-setup.md
│   │   ├── database-migration.md
│   │   └── configuration.md
│   ├── maintenance/
│   │   ├── backups.md
│   │   ├── monitoring.md
│   │   └── performance.md
│   └── security/
│       ├── user-management.md
│       └── access-control.md
│
├── reference/                        # Reference documentation
│   ├── README.md                     # Reference index
│   ├── database/
│   │   ├── schema.md
│   │   ├── tables.md
│   │   └── relationships.md
│   ├── configuration/
│   │   ├── env-ini.md
│   │   ├── sync-settings.md
│   │   └── ui-settings.md
│   └── api/
│       ├── endpoints.md
│       └── models.md
│
├── changelogs/                       # Version history
│   ├── README.md                     # Changelog index
│   ├── latest/
│   │   └── [current release notes]
│   ├── 2025/
│   │   ├── 12-december.md
│   │   └── [other months]
│   └── [previous years]
│
├── tasks/                           # Development task documentation
│   ├── README.md                     # Tasks index
│   ├── completed/
│   │   ├── [completed task docs]
│   └── in-progress/
│       └── [active task docs]
│
└── archived/                        # Historical/legacy documentation
    ├── README.md                     # Archive notice
    ├── old-versions/
    └── deprecated/
```

## Migration Plan

### Phase 1: Create New Structure
1. Create new folders according to plan
2. Create README files for each section
3. Set up navigation indexes

### Phase 2: Migrate Content
1. Move and rename existing files to appropriate folders
2. Update internal links and references
3. Consolidate duplicate content

### Phase 3: Cleanup
1. Review and remove obsolete files
2. Update main README.md
3. Create redirects for commonly accessed files

## File Mapping

### Current → New Structure

#### API Documentation
- `api/` → `developer-guide/api/`
- `api/API_ESTIMATES_IMPLEMENTATION.md` → `developer-guide/api/estimates.md`

#### Database Documentation
- `database/` → `reference/database/`
- `database/DATABASE_SCHEMA.md` → `reference/database/schema.md`

#### Deployment Documentation
- `deployment/` → `administration/installation/` + `developer-guide/deployment/`

#### User Documentation
- `user-guide/` → `user-guide/`
- `features/` → `user-guide/features/`
- `russian/` → `user-guide/russian/`

#### Developer Documentation
- `guides/` → `developer-guide/setup/`
- `architecture/` → `developer-guide/architecture/`

#### Task Documentation
- `tasks/` → `tasks/completed/`

#### Historical Documentation
- `archived/` → `archived/old-versions/`
- `legacy/` → `archived/deprecated/`

## Benefits of New Structure

### For Users
- Clear separation of user vs developer content
- Logical flow from getting started to advanced features
- Better discoverability of relevant information

### For Developers
- Comprehensive technical documentation
- Clear API and architecture references
- Easy contribution process

### For Administrators
- Dedicated administration section
- Installation and maintenance guides
- Security and configuration references

### For Maintenance
- Logical organization reduces duplication
- Clear archive process
- Easier content updates
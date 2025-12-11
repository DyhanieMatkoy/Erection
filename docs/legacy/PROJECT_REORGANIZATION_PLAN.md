# Project Reorganization Plan

## Current Structure Analysis

### Issues Identified

1. **Scattered Documentation**: Multiple README files and documentation scattered across root, `docs/`, `distro/docs/`, and `deploy-to-prod/`
2. **Duplicate Files**: Multiple similar files with slight variations
3. **Mixed Languages**: Russian and English documentation mixed without clear organization
4. **Build Scripts**: Numerous `.bat` files in root directory without categorization
5. **Configuration Files**: Multiple `.ini` and `.env` files scattered
6. **Test Databases**: Multiple test database files cluttering the root
7. **Archive Files**: Large archive files in root directory

### Key Directories Analysis

- **`api/`**: Well-structured with proper separation (models, services, endpoints, tests)
- **`web-client/`**: Modern Vue.js structure with proper organization
- **`docs/`**: Contains many documentation files but needs better categorization
- **`distro/`**: Distribution package with its own documentation
- **`deploy-to-prod/`**: Deployment-specific files and documentation

## Recommended New Structure

```
Erection/
├── README.md                          # Main project README
├── .gitignore
├── requirements.txt
├── alembic.ini
├── env.ini
├── erection.db                        # OldMain database 
├── construction.db                    # Construction database
│
├── src/                              # Core application source
│   ├── main.py
│   ├── main_no_auth.py
│   ├── start_server.py
│   └── [other core Python files]
│
├── api/                              # API server (keep as-is, well-structured)
│   ├── main.py
│   ├── config.py
│   ├── dependencies/
│   ├── endpoints/
│   ├── middleware/
│   ├── models/
│   ├── services/
│   └── tests/
│
├── web-client/                       # Vue.js frontend (keep as-is, well-structured)
│   ├── src/
│   ├── public/
│   ├── e2e/
│   └── [web-client files]
│
├── scripts/                          # All utility and maintenance scripts
│   ├── database/
│   │   ├── migrate_database.py
│   │   ├── migrate_works_table.py
│   │   ├── clean_duplicate_works.py
│   │   ├── load_test_data.py
│   │   └── [other database scripts]
│   ├── auth/
│   │   ├── check_admin_hash.py
│   │   ├── fix_password_hashes.py
│   │   ├── manual_password_reset.py
│   │   ├── quick_reset_admin.py
│   │   └── [other auth scripts]
│   ├── import/
│   │   ├── import_works_from_csv.py
│   │   └── [other import scripts]
│   └── utils/
│       ├── check_status.py
│       ├── check_users.py
│       ├── manage_users.py
│       └── [other utility scripts]
│
├── build/                            # Build and deployment scripts
│   ├── build.bat
│   ├── build_all_distro.bat
│   ├── build_distro.bat
│   ├── build_exe.bat
│   ├── build_portable_distro.bat
│   ├── build_production_api.bat
│   ├── build_web.bat
│   ├── create_deployment_package.bat
│   ├── create_offline_distro.bat
│   ├── prepare_distro.bat
│   └── [other build scripts]
│
├── run/                              # Runtime and startup scripts
│   ├── run.bat
│   ├── run_clean.bat
│   ├── run_debug.bat
│   ├── run_no_auth.bat
│   ├── run_with_logging.bat
│   ├── start_api.bat
│   ├── start_api_production.bat
│   ├── start_dev.bat
│   ├── start_web.bat
│   ├── setup.bat
│   ├── clear_cache.bat
│   ├── debug_env.bat
│   └── [other runtime scripts]
│
├── docs/                             # Consolidated documentation
│   ├── README.md                     # Documentation index
│   ├── user-guide/                   # End-user documentation
│   │   ├── QUICK_START.md
│   │   ├── INSTALLATION_GUIDE.md
│   │   ├── TROUBLESHOOTING.md
│   │   └── [user guides]
│   ├── developer-guide/              # Developer documentation
│   │   ├── DEVELOPER_GUIDE.md
│   │   ├── API_IMPLEMENTATION_STATUS.md
│   │   ├── DATABASE_SCHEMA.md
│   │   ├── ARCHITECTURE.md
│   │   └── [developer docs]
│   ├── deployment/                   # Deployment documentation
│   │   ├── DEPLOYMENT_GUIDE.md
│   │   ├── DISTRIBUTION_GUIDE.md
│   │   ├── DEPLOYMENT_CHECKLIST.md
│   │   └── [deployment docs]
│   ├── features/                     # Feature-specific documentation
│   │   ├── FORMS_IMPLEMENTATION.md
│   │   ├── TIMESHEET_FEATURES.md
│   │   ├── DAILY_REPORT_FEATURES.md
│   │   └── [feature docs]
│   ├── changelogs/                   # Version history and changes
│   │   ├── CHANGELOG.md
│   │   ├── FEATURE_HISTORY.md
│   │   └── [changelogs]
│   ├── russian/                      # Russian documentation
│   │   ├── ИНСТРУКЦИЯ_НАСТРОЙКИ.md
│   │   ├── ИНСТРУКЦИЯ_ТАБЕЛЬ.md
│   │   └── [russian docs]
│   └── archived/                     # Old/obsolete documentation
│       ├── [old docs]
│
├── config/                           # Configuration files
│   ├── env.ini.backup
│   ├── .env
│   ├── .env.production
│   ├── nginx-ctm.conf
│   ├── nginx-ctm-https.conf
│   └── [other config files]
│
├── test/                             # Test files and databases
│   ├── databases/
│   │   ├── test_api_consistency.db
│   │   ├── test_legacy_compat.db
│   │   └── [other test databases]
│   ├── scripts/
│   │   ├── test_api_login.py
│   │   ├── test_password_truncation.py
│   │   ├── test_simple_login.py
│   │   └── [test scripts]
│   └── results/
│       └── [test results]
│
├── distro/                           # Distribution package
│   ├── README.md
│   ├── QUICK_START.md
│   ├── INSTALLATION_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   ├── create_installer.bat
│   └── app/
│
├── deploy-to-prod/                   # Production deployment (keep as-is)
│   ├── deploy.py
│   ├── deploy.sh
│   ├── deploy.bat
│   └── [deployment files]
│
├── archives/                         # Archive files and old versions
│   ├── distro.7z.001
│   ├── template.old
│   └── [other archives]
│
└── fonts/                            # Font files (keep as-is)
    └── [font files]
```

## Files to Remove/Deduplicate

### Duplicate Documentation Files
- Multiple README files → Consolidate into main README.md and docs/README.md
- Duplicate QUICK_START files → Keep one in docs/user-guide/
- Multiple FINAL_* files → Consolidate into docs/changelogs/
- Multiple FIX_SUMMARY files → Consolidate into docs/changelogs/

### Duplicate Configuration Files
- Multiple .env files → Keep in config/ directory
- Multiple .ini files → Consolidate in config/

### Test Databases in Root
- Move all test_*.db files to test/databases/

### Archive Files in Root
- Move large archives to archives/ directory

## Benefits of New Structure

1. **Clear Separation**: Each type of file has its designated place
2. **Easy Navigation**: Logical grouping makes finding files intuitive
3. **Better Maintenance**: Related files are grouped together
4. **Clean Root**: Root directory contains only essential files
5. **Scalable**: Structure can grow without becoming messy
6. **Language Organization**: Separate Russian and English documentation
7. **Build Organization**: Build, run, and utility scripts are properly categorized

## Migration Steps

1. Create new directory structure
2. Move files according to the plan
3. Update any hardcoded paths in configuration files
4. Update documentation to reflect new structure
5. Test that all scripts and applications still work
6. Remove old empty directories
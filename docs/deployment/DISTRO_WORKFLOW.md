# Distribution Workflow - Visual Guide

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTION WORKFLOW                         │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: PREPARATION (Developer/Admin)
═══════════════════════════════════════

┌──────────────────┐
│  Development     │
│  Environment     │
│  - Python 3.11+  │
│  - Node.js 20+   │
│  - Internet      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Run:             │
│ prepare_distro   │
│     .bat         │
└────────┬─────────┘
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│  Build Desktop   │                    │  Build Web       │
│  Application     │                    │  Client          │
│  (build.bat)     │                    │  (build_web.bat) │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                         ▼
         ┌───────────────────────────┐
         │  create_offline_distro    │
         │        .bat               │
         └───────────┬───────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ Download     │ │ Package  │ │ Copy         │
│ Python       │ │ Node.js  │ │ Application  │
│ Packages     │ │ Modules  │ │ Files        │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   distro/ folder       │
         │   created with:        │
         │   - python-packages/   │
         │   - node-packages/     │
         │   - app/               │
         │   - docs/              │
         │   - scripts            │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Download              │
         │  Prerequisites         │
         │  Manually:             │
         │  - Python installer    │
         │  - Node.js installer   │
         │  - VC++ Redistributable│
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Create ZIP Archive    │
         │  (Optional)            │
         │  ~250 MB compressed    │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  DISTRIBUTION PACKAGE  │
         │  READY                 │
         └────────────────────────┘


PHASE 2: DISTRIBUTION
══════════════════════

         ┌────────────────────────┐
         │  Distribution Package  │
         └────────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌──────────┐
    │  USB   │  │  DVD   │  │ Network  │
    │ Drive  │  │        │  │  Share   │
    └────────┘  └────────┘  └──────────┘


PHASE 3: INSTALLATION (End User)
═════════════════════════════════

         ┌────────────────────────┐
         │  Target Machine        │
         │  (No Internet)         │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Copy distro/ folder   │
         │  to local drive        │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Install Prerequisites │
         │  from prerequisites/   │
         └────────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ Python │  │Node.js │  │   VC++   │
    │ 3.11   │  │  20    │  │  Redist  │
    └───┬────┘  └───┬────┘  └────┬─────┘
        │           │            │
        └───────────┼────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │  Run:                  │
         │  create_installer.bat  │
         └────────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ Create │  │Install │  │  Create  │
    │Install │  │Python  │  │ Node.js  │
    │  Dir   │  │Packages│  │ Modules  │
    └───┬────┘  └───┬────┘  └────┬─────┘
        │           │            │
        └───────────┼────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │  Create Shortcuts      │
         │  - Desktop             │
         │  - Start Menu          │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  INSTALLATION COMPLETE │
         └────────────────────────┘


PHASE 4: USAGE
═══════════════

         ┌────────────────────────┐
         │  Launch Application    │
         └────────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         │                         │
         ▼                         ▼
    ┌──────────┐            ┌──────────┐
    │ Desktop  │            │   Web    │
    │   App    │            │   App    │
    │ (run.bat)│            │(start_   │
    │          │            │ dev.bat) │
    └────┬─────┘            └────┬─────┘
         │                       │
         ▼                       ▼
    ┌──────────┐            ┌──────────┐
    │  Login   │            │  Login   │
    │  admin/  │            │  via     │
    │  admin   │            │ Browser  │
    └────┬─────┘            └────┬─────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  Application Running   │
         │  - Manage data         │
         │  - Generate reports    │
         │  - User management     │
         └────────────────────────┘
```

## File Flow Diagram

```
SOURCE FILES                    DISTRIBUTION PACKAGE
════════════════               ═════════════════════

Project Root/                   distro/
├── src/          ────────────► app/src/
├── api/          ────────────► app/api/
├── web-client/   ────────────► app/web-client/
├── docs/         ────────────► docs/
├── *.py          ────────────► app/*.py
├── *.bat         ────────────► app/*.bat
├── requirements.txt ─────────► app/requirements.txt
├── .env          ────────────► app/.env
├── construction.db ──────────► app/construction.db
│
Python Packages   ────────────► python-packages/*.whl
(from PyPI)
│
Node Modules      ────────────► node-packages/
(from npm)                      ├── node_modules.tar.gz
                                └── npm-cache/
│
Downloaded        ────────────► prerequisites/
Installers                      ├── python-3.11.x.exe
                                ├── node-v20.x.x.msi
                                └── VC_redist.x64.exe
│
Generated Docs    ────────────► ├── README.md
                                ├── QUICK_START.md
                                ├── INSTALLATION_GUIDE.md
                                ├── TROUBLESHOOTING.md
                                └── create_installer.bat
```

## Decision Tree

```
                    START
                      │
                      ▼
         ┌────────────────────────┐
         │ Do you have the        │
         │ distribution package?  │
         └────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                 │
        NO                YES
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ Are you a       │  │ Are you          │
│ developer/admin?│  │ installing?      │
└────┬────────────┘  └────┬─────────────┘
     │                    │
    YES                  YES
     │                    │
     ▼                    ▼
┌─────────────────┐  ┌──────────────────┐
│ Run:            │  │ Go to PHASE 3    │
│ prepare_distro  │  │ (Installation)   │
│ .bat            │  │                  │
└────┬────────────┘  └──────────────────┘
     │
     ▼
┌─────────────────┐
│ Download        │
│ prerequisites   │
│ manually        │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Create ZIP      │
│ (optional)      │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Distribute      │
│ package         │
└─────────────────┘
```

## Time Estimates

```
TASK                                TIME        REQUIREMENTS
════════════════════════════════════════════════════════════

Package Creation (Developer)
────────────────────────────
Build applications                  5 min       Internet
Download dependencies              10 min       Internet
Package files                       5 min       -
Download prerequisites             10 min       Internet
Create archive                      5 min       -
────────────────────────────────────────────────────────────
TOTAL                              35 min

Installation (End User)
───────────────────────
Install Python                      2 min       Admin rights
Install Node.js                     2 min       Admin rights
Install VC++ Redistributable        1 min       Admin rights
Run installer                       3 min       Admin rights
────────────────────────────────────────────────────────────
TOTAL                               8 min

First Launch
────────────
Start application                  30 sec       -
Login                              10 sec       -
Change password                     1 min       -
────────────────────────────────────────────────────────────
TOTAL                               2 min

GRAND TOTAL (End User)             10 min
```

## Package Size Breakdown

```
COMPONENT                SIZE (MB)    COMPRESSED    PERCENTAGE
═══════════════════════════════════════════════════════════

Python packages            150          60            25%
Node.js packages           300         120            50%
Application files           50          30            12%
Prerequisites              100          40            13%
───────────────────────────────────────────────────────────
TOTAL                      600         250           100%

Distribution Methods:
• USB Drive (8GB+)         ✓ Uncompressed
• DVD (4.7GB)              ✓ Uncompressed
• Network Share            ✓ Uncompressed or Compressed
• Download                 ✓ Compressed (250 MB)
```

## Success Criteria

```
PHASE                   SUCCESS INDICATOR
═══════════════════════════════════════════════════════════

Package Creation        ✓ distro/ folder created
                        ✓ All dependencies downloaded
                        ✓ Prerequisites obtained
                        ✓ No errors in creation log

Distribution            ✓ Package copied to media
                        ✓ Archive integrity verified
                        ✓ Checksums match (if used)

Installation            ✓ Prerequisites installed
                        ✓ Python packages installed
                        ✓ Node modules extracted
                        ✓ Shortcuts created
                        ✓ No error messages

First Launch            ✓ Application starts
                        ✓ Login successful
                        ✓ Main window opens
                        ✓ Database accessible

Verification            ✓ All features work
                        ✓ Reports generate
                        ✓ Data saves correctly
                        ✓ Web client accessible (if used)
```

## Quick Command Reference

```
TASK                    COMMAND
═══════════════════════════════════════════════════════════

Create Package          prepare_distro.bat
Create Archive          powershell Compress-Archive -Path distro\* -DestinationPath package.zip
Install (Automated)     distro\create_installer.bat
Run Desktop App         run.bat
Run Web App (Dev)       start_dev.bat
Run Web App (Prod)      start_api_production.bat
Reset Password          python reset_admin_password.py
Check Status            python check_status.py
Build Desktop           build.bat
Build Web               build_web.bat
```

## Troubleshooting Flow

```
                    PROBLEM?
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    Installation   Runtime      Configuration
       Error        Error          Issue
         │             │             │
         ▼             ▼             ▼
    Check:         Check:         Check:
    • Python       • Database     • .env files
    • Node.js      • Ports        • env.ini
    • VC++         • Permissions  • API URL
    • Disk space   • Logs         • CORS
         │             │             │
         ▼             ▼             ▼
    See:           See:           See:
    INSTALLATION   TROUBLESHOOTING DATABASE_AND
    _GUIDE.md      .md            _CONFIG_GUIDE.md
```

## Support Resources

```
RESOURCE                        LOCATION
═══════════════════════════════════════════════════════════

Quick Start                     distro/QUICK_START.md
Detailed Installation           distro/INSTALLATION_GUIDE.md
Troubleshooting                 distro/TROUBLESHOOTING.md
Configuration                   docs/DATABASE_AND_CONFIG_GUIDE.md
Distribution Guide              DISTRIBUTION_GUIDE.md
Checklist                       DISTRIBUTION_CHECKLIST.md
This Workflow                   DISTRO_WORKFLOW.md
Summary                         DISTRO_SUMMARY.md
```

---

**Ready to start?** Run `prepare_distro.bat` and follow the prompts!

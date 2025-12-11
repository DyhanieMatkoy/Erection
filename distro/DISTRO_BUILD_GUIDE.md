# Distribution Package Build Guide

## Overview

This guide explains how to build distribution packages for the Construction Time Management System.

## Build Options

### Option 1: Portable Distribution (Recommended)

**Best for**: Most users, easy updates, smaller package size

**Command**: `build_portable_distro.bat` (from project root)

**What it creates**:
- Portable Python application
- All dependencies included offline
- Requires Python 3.11+ on target machine
- Package size: ~150-200 MB

**Advantages**:
- Smaller package size
- Easy to update (just replace files)
- No compilation required
- Faster build process

**Target machine requirements**:
- Python 3.11 or later installed
- Run Setup.bat once to install dependencies

### Option 2: Standalone Executables

**Best for**: Users without Python, corporate environments

**Command**: `build_distro.bat` (from project root)

**What it creates**:
- Compiled .exe files
- No Python required on target
- Package size: ~300-400 MB

**Advantages**:
- No Python installation needed
- Single-file executables
- Professional appearance

**Requirements**:
- PyInstaller installed
- Longer build time
- Larger package size

### Option 3: Complete Offline Package

**Best for**: True offline installation, includes everything

**Command**: `prepare_distro.bat` (from project root)

**What it creates**:
- Application files
- Python packages (offline)
- Python installer
- Node.js installer
- All prerequisites
- Package size: ~600 MB

**Advantages**:
- Complete offline installation
- Includes Python installer
- No internet required on target

**Requirements**:
- Internet connection for building
- Manual download of installers

## Quick Start

### Using the Master Builder

Run from project root:

```batch
build_all_distro.bat
```

This presents a menu with all options.

### Manual Build Process

#### For Portable Distribution:

```batch
REM From project root
build_portable_distro.bat
```

#### For Standalone Executables:

```batch
REM From project root
REM 1. Install PyInstaller
pip install pyinstaller

REM 2. Build
build_distro.bat
```

#### For Complete Offline:

```batch
REM From project root
prepare_distro.bat
```

## What Gets Built

### Directory Structure

```
distro/
├── app/                           # Application files
│   ├── Start.bat                  # Main launcher
│   ├── Setup.bat                  # Dependency installer
│   ├── StartDesktop.bat           # Desktop launcher
│   ├── StartServer.bat            # Server launcher
│   ├── main.py                    # Desktop entry point
│   ├── start_server.py            # Server entry point
│   ├── env.ini                    # Desktop config
│   ├── .env                       # Server config
│   ├── construction.db            # Database
│   ├── requirements.txt           # Dependencies
│   ├── python-packages/           # Offline packages
│   ├── src/                       # Source code
│   ├── api/                       # API code
│   ├── web-client/dist/           # Web client
│   ├── fonts/                     # Fonts
│   ├── PrnForms/                  # Print templates
│   └── README.md                  # User guide
│
├── docs/                          # Documentation
├── create_installer.bat           # Automated installer
├── INSTALLATION_GUIDE.md          # Install guide
├── README.md                      # Package overview
└── TROUBLESHOOTING.md             # Help guide
```

### Files Included

**Application Source**:
- `src/` - Desktop application code
- `api/` - API server code
- `web-client/dist/` - Built web client

**Configuration**:
- `env.ini` - Desktop app configuration
- `.env` - API server configuration
- `construction.db` - SQLite database

**Dependencies**:
- `python-packages/` - All Python packages as wheels
- `requirements.txt` - Package list

**Support Files**:
- `fonts/` - Application fonts
- `PrnForms/` - Print form templates

**Launchers**:
- `Start.bat` - Main menu launcher
- `Setup.bat` - Dependency installer
- `StartDesktop.bat` - Desktop app launcher
- `StartServer.bat` - Web server launcher

**Documentation**:
- `README.md` - Quick start guide
- `INSTALLATION_GUIDE.md` - Detailed installation
- `TROUBLESHOOTING.md` - Common issues

## Build Process Details

### Portable Distribution Build Steps

1. **Create directory structure**
   - Creates `distro/app/` and subdirectories

2. **Copy application source**
   - Copies `src/`, `api/`, `fonts/`, `PrnForms/`

3. **Copy Python scripts**
   - Copies all `.py` files

4. **Copy configuration**
   - Copies `env.ini`, `.env.production`, `construction.db`

5. **Build web client**
   - Runs `build_web.bat`
   - Copies `web-client/dist/`

6. **Download Python packages**
   - Downloads all packages from `requirements.txt`
   - Saves to `python-packages/` for offline use

7. **Create launcher scripts**
   - Generates `Setup.bat`, `Start.bat`, etc.

8. **Create documentation**
   - Generates `README.md` and guides

### Standalone Build Steps

1. **Install PyInstaller**
   - Checks if PyInstaller is installed
   - Installs if needed

2. **Build desktop executable**
   - Compiles `main.py` to `ConstructionTimeManagement.exe`
   - Includes all dependencies
   - Bundles fonts, forms, database

3. **Build API executable**
   - Compiles `start_server.py` to `ConstructionTimeAPI.exe`
   - Includes API code and dependencies

4. **Copy to distro**
   - Copies executables to `distro/app/`
   - Copies configuration and support files

5. **Create launchers**
   - Generates batch files to run executables

## Testing the Package

### Before Distribution

1. **Test on clean machine**
   - Use VM or clean Windows installation
   - Verify all dependencies work

2. **Test desktop application**
   ```batch
   cd distro\app
   StartDesktop.bat
   ```

3. **Test web server**
   ```batch
   cd distro\app
   StartServer.bat
   ```
   - Open browser to http://localhost:8000

4. **Test installation**
   ```batch
   cd distro
   create_installer.bat
   ```

5. **Verify functionality**
   - Login works
   - Database operations work
   - Reports generate
   - All features accessible

### Test Checklist

- [ ] Desktop app starts
- [ ] Web server starts
- [ ] Login successful
- [ ] Database accessible
- [ ] Forms load correctly
- [ ] Reports generate
- [ ] Print templates work
- [ ] Configuration editable
- [ ] No error messages
- [ ] All features work

## Distribution

### Creating ZIP Archive

**Using PowerShell**:
```batch
powershell -Command "Compress-Archive -Path distro\* -DestinationPath ConstructionTimeManagement.zip -Force"
```

**Using 7-Zip**:
```batch
"C:\Program Files\7-Zip\7z.exe" a -tzip ConstructionTimeManagement.zip distro\*
```

### Package Naming

Use semantic versioning:
```
ConstructionTimeManagement-v1.0.0-Portable-Win64.zip
ConstructionTimeManagement-v1.0.0-Standalone-Win64.zip
ConstructionTimeManagement-v1.0.0-Offline-Win64.zip
```

### Distribution Methods

1. **USB Drive**
   - Copy `distro/` folder to USB
   - Minimum 8 GB recommended

2. **Network Share**
   - Copy to shared folder
   - Users run `create_installer.bat`

3. **Download**
   - Create ZIP archive
   - Upload to file server
   - Provide download link

4. **DVD**
   - Burn `distro/` folder to DVD
   - Include autorun if desired

## Customization Before Build

### Change Default Database

Edit `construction.db` before building:
- Add default data
- Create user accounts
- Configure settings

### Customize Configuration

**Desktop (`env.ini`)**:
```ini
[Database]
type = sqlite
path = construction.db

[Application]
theme = default
language = ru
```

**API (`.env.production`)**:
```
DATABASE_TYPE=sqlite
DATABASE_PATH=construction.db
JWT_SECRET_KEY=your-secure-key-here
CORS_ORIGINS=http://localhost:8000
```

### Add Custom Documentation

Place files in `docs/` before building:
- User manuals
- Training materials
- Company policies

### Branding

Replace before building:
- `fonts/icon.ico` - Application icon
- Splash screen images
- Company logo

## Troubleshooting Build Issues

### PyInstaller not found

```batch
pip install pyinstaller
```

### Web build fails

```batch
cd web-client
npm install
npm run build
```

### Python packages download fails

Check internet connection, or:
```batch
pip download -r requirements.txt -d distro\app\python-packages
```

### Permission errors

Run command prompt as Administrator

### Disk space issues

Ensure at least 2 GB free space

## Maintenance

### Updating the Package

1. Update source code
2. Test changes
3. Increment version number
4. Rebuild package
5. Test new package
6. Distribute update

### Version Control

Tag releases in git:
```batch
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Changelog

Maintain `CHANGELOG.md`:
```markdown
# Changelog

## [1.0.0] - 2024-01-15
### Added
- Initial release
- Desktop application
- Web client
- API server

### Fixed
- Bug fixes

### Changed
- Improvements
```

## Best Practices

1. **Always test** on clean machine before distribution
2. **Document changes** in changelog
3. **Version everything** consistently
4. **Keep packages small** when possible
5. **Include documentation** for users
6. **Provide support** contact information
7. **Update regularly** with fixes and features
8. **Backup databases** before updates
9. **Test upgrades** from previous versions
10. **Gather feedback** from users

## Support

For build issues:
1. Check this guide
2. Review error messages
3. Check system requirements
4. Verify all prerequisites installed
5. Try clean build

For distribution issues:
1. Test package before distributing
2. Verify all files included
3. Check package integrity
4. Provide clear instructions
5. Offer installation support

## Conclusion

Choose the build option that best fits your needs:
- **Portable**: Most flexible, smaller size
- **Standalone**: No Python required
- **Offline**: Complete self-contained package

Test thoroughly before distribution, and provide clear documentation for users.

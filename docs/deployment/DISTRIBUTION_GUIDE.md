# Distribution Package Creation Guide
## Construction Time Management System

This guide explains how to create and use the offline distribution package.

## Overview

The offline distribution package allows installation on machines without internet access. It includes:
- All Python dependencies (as wheel files)
- All Node.js dependencies (as compressed archive)
- Complete application source code
- Documentation
- Installation scripts
- Download instructions for system prerequisites

## Creating the Distribution Package

### Prerequisites

Before creating the distribution package, ensure you have:
- ✅ Windows 10/11 (64-bit)
- ✅ Python 3.11+ installed
- ✅ Node.js 20+ installed
- ✅ Internet connection (for downloading packages)
- ✅ 5 GB free disk space

### Method 1: Automated (Recommended)

Run the master preparation script:

```batch
prepare_distro.bat
```

This will:
1. Build the desktop application
2. Build the web client
3. Download all Python packages
4. Package Node.js dependencies
5. Copy all application files
6. Create documentation
7. Generate installation scripts

### Method 2: Manual Steps

#### Step 1: Build Applications

```batch
REM Build web client
build_web.bat

REM Build desktop application
build.bat
```

#### Step 2: Create Distribution Package

```batch
create_offline_distro.bat
```

This creates the `distro` folder with all components.

#### Step 3: Download Prerequisites

Download these files manually and place in `distro\prerequisites\`:

1. **Python 3.11** - https://www.python.org/downloads/
   - File: `python-3.11.9-amd64.exe`
   - Direct: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

2. **Node.js 20 LTS** - https://nodejs.org/
   - File: `node-v20.11.0-x64.msi`
   - Direct: https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi

3. **Visual C++ Redistributable**
   - File: `VC_redist.x64.exe`
   - Direct: https://aka.ms/vs/17/release/vc_redist.x64.exe

4. **MinGW-w64** (Optional - for building)
   - Download from: https://github.com/niXman/mingw-builds-binaries/releases
   - Get: x86_64-posix-seh version

5. **CMake** (Optional - for building)
   - Download from: https://cmake.org/download/
   - Get: Windows x64 installer

#### Step 4: Create Archive (Optional)

Create a ZIP file for easy distribution:

```batch
REM Using 7-Zip
"C:\Program Files\7-Zip\7z.exe" a -tzip ConstructionTimeManagement-Offline.zip distro\*

REM Or use Windows built-in
powershell Compress-Archive -Path distro\* -DestinationPath ConstructionTimeManagement-Offline.zip
```

## Distribution Package Structure

```
distro/
├── README.md                          # Package overview
├── QUICK_START.md                     # Quick installation guide
├── INSTALLATION_GUIDE.md              # Detailed installation guide
├── TROUBLESHOOTING.md                 # Troubleshooting guide
├── PACKAGE_INFO.md                    # Package information
├── create_installer.bat               # Automated installer
│
├── prerequisites/                     # System prerequisites
│   ├── DOWNLOAD_INSTRUCTIONS.md       # Download links
│   ├── python-3.11.9-amd64.exe       # Python installer
│   ├── node-v20.11.0-x64.msi         # Node.js installer
│   ├── VC_redist.x64.exe             # VC++ Redistributable
│   ├── mingw-w64-installer.exe       # MinGW (optional)
│   └── cmake-x.xx.x-windows.msi      # CMake (optional)
│
├── python-packages/                   # Python dependencies
│   ├── PyQt6-6.7.1-*.whl
│   ├── fastapi-0.104.1-*.whl
│   ├── uvicorn-0.24.0-*.whl
│   └── ... (all dependencies)
│
├── node-packages/                     # Node.js dependencies
│   ├── node_modules.tar.gz           # Compressed node_modules
│   └── npm-cache/                    # NPM offline cache
│
├── app/                               # Application files
│   ├── src/                          # Desktop app source
│   ├── api/                          # API source
│   ├── web-client/                   # Web client source
│   ├── docs/                         # Documentation
│   ├── PrnForms/                     # Print templates
│   ├── fonts/                        # Fonts
│   ├── *.py                          # Python scripts
│   ├── *.bat                         # Batch scripts
│   ├── requirements.txt              # Python requirements
│   ├── .env                          # Environment config
│   └── construction.db               # Database file
│
└── docs/                              # Additional documentation
    ├── DATABASE_AND_CONFIG_GUIDE.md
    ├── START_HERE.md
    └── ... (other docs)
```

## Using the Distribution Package

### For End Users

#### Quick Installation (5 minutes)

1. Copy `distro` folder to target machine
2. Run `distro\create_installer.bat`
3. Follow on-screen instructions
4. Launch application from desktop shortcut

#### Manual Installation

See `distro\INSTALLATION_GUIDE.md` for detailed steps.

### For System Administrators

#### Network Deployment

1. Copy `distro` folder to network share
2. Create deployment script:

```batch
@echo off
net use Z: \\server\share\distro
Z:\create_installer.bat
net use Z: /delete
```

3. Deploy via Group Policy or SCCM

#### Silent Installation

Modify `create_installer.bat` for silent mode:
- Remove all `pause` commands
- Set `INSTALL_DIR` without prompting
- Skip confirmation prompts

#### Custom Configuration

Before distribution, customize:
- `.env` - API configuration
- `env.ini` - Desktop configuration
- `web-client\.env.production` - Web client API URL
- `construction.db` - Pre-populate database

## Distribution Checklist

### Before Creating Package

- [ ] All code tested and working
- [ ] Desktop application builds successfully
- [ ] Web client builds successfully
- [ ] Database schema is up to date
- [ ] Documentation is current
- [ ] Default credentials documented
- [ ] Configuration files reviewed

### Package Contents

- [ ] Python packages downloaded
- [ ] Node.js packages packaged
- [ ] Application files copied
- [ ] Documentation included
- [ ] Installation scripts created
- [ ] Prerequisites downloaded
- [ ] README files created

### Testing

- [ ] Test on clean Windows 10 machine
- [ ] Test on clean Windows 11 machine
- [ ] Test without internet connection
- [ ] Test automated installer
- [ ] Test manual installation
- [ ] Test desktop application
- [ ] Test web application
- [ ] Test all documentation links

### Distribution

- [ ] Create ZIP archive
- [ ] Verify archive integrity
- [ ] Test extraction
- [ ] Create checksums (optional)
- [ ] Upload to distribution server
- [ ] Notify users
- [ ] Provide support contact

## Package Sizes

Typical package sizes:
- Python packages: ~150 MB
- Node.js packages: ~300 MB
- Application files: ~50 MB
- Prerequisites: ~100 MB
- **Total**: ~600 MB

Compressed (ZIP): ~250 MB

## Version Management

### Versioning Scheme

Use semantic versioning: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Package Naming

```
ConstructionTimeManagement-v1.0.0-Offline-Win64.zip
```

### Changelog

Maintain `CHANGELOG.md` in package:
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

## Security Considerations

### Before Distribution

1. **Change default credentials**
   - Update default admin password
   - Or document clearly

2. **Review JWT secret**
   - Generate secure random key
   - Update in `.env.production`

3. **Check CORS settings**
   - Set appropriate origins
   - Don't use wildcard in production

4. **Database security**
   - Remove test data
   - Check no sensitive information

5. **Code review**
   - No hardcoded secrets
   - No debug code
   - No test credentials

### Distribution Security

1. **Create checksums**
   ```batch
   certutil -hashfile ConstructionTimeManagement-Offline.zip SHA256
   ```

2. **Sign package** (optional)
   - Use code signing certificate
   - Sign executables and installers

3. **Secure distribution**
   - Use HTTPS for downloads
   - Verify integrity after download

## Maintenance

### Updating Package

1. Update source code
2. Test changes
3. Increment version number
4. Rebuild applications
5. Recreate distribution package
6. Update documentation
7. Create new archive
8. Distribute update

### Patch Distribution

For small updates, create patch package:
- Only changed files
- Update script
- Changelog

## Support

### Documentation Included

- `README.md` - Overview
- `QUICK_START.md` - Quick guide
- `INSTALLATION_GUIDE.md` - Detailed installation
- `TROUBLESHOOTING.md` - Common issues
- `DATABASE_AND_CONFIG_GUIDE.md` - Configuration
- `docs/START_HERE.md` - User guide

### Support Channels

Document in package:
- Email support
- Issue tracker
- Documentation website
- FAQ

## Best Practices

1. **Test thoroughly** before distribution
2. **Document everything** clearly
3. **Version control** all changes
4. **Keep prerequisites current** (security updates)
5. **Maintain changelog** for transparency
6. **Provide examples** in documentation
7. **Include troubleshooting** guide
8. **Test on clean systems** regularly
9. **Gather feedback** from users
10. **Update regularly** with fixes and features

## Automation

### Continuous Integration

Create CI/CD pipeline:
1. Build applications
2. Run tests
3. Create distribution package
4. Generate checksums
5. Upload to distribution server
6. Notify stakeholders

### Example GitHub Actions

```yaml
name: Create Distribution Package

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
      - name: Create Package
        run: prepare_distro.bat
      - name: Upload Artifact
        uses: actions/upload-artifact@v2
        with:
          name: offline-package
          path: distro/
```

## Conclusion

The offline distribution package provides a complete, self-contained installation solution for environments without internet access. Follow this guide to create, test, and distribute the package effectively.

For questions or issues, refer to the troubleshooting guide or contact support.

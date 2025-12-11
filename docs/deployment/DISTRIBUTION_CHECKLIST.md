# Distribution Package Checklist

## Pre-Creation Checklist

### Development Environment
- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] All dependencies installed locally
- [ ] Internet connection available
- [ ] 5 GB free disk space

### Code Quality
- [ ] All code tested and working
- [ ] No debug code or test credentials
- [ ] No hardcoded secrets
- [ ] Code reviewed
- [ ] Version number updated

### Application Builds
- [ ] Desktop application builds successfully (`build.bat`)
- [ ] Web client builds successfully (`build_web.bat`)
- [ ] No build errors or warnings
- [ ] Executables tested

### Database
- [ ] Database schema is current
- [ ] Test data removed (or documented)
- [ ] No sensitive information
- [ ] Database file included

### Configuration
- [ ] `.env` file reviewed
- [ ] `.env.production` configured
- [ ] `env.ini` reviewed
- [ ] Default credentials documented
- [ ] JWT secret key set (production)
- [ ] CORS settings configured

### Documentation
- [ ] All documentation up to date
- [ ] README files complete
- [ ] Installation guide accurate
- [ ] Troubleshooting guide current
- [ ] Configuration guide complete
- [ ] User guide available

## Package Creation Checklist

### Run Creation Scripts
- [ ] Run `prepare_distro.bat` successfully
- [ ] Or run `create_offline_distro.bat` manually
- [ ] No errors during creation
- [ ] All files copied

### Verify Package Contents

#### Directory Structure
- [ ] `distro/` folder created
- [ ] `distro/prerequisites/` exists
- [ ] `distro/python-packages/` exists
- [ ] `distro/node-packages/` exists
- [ ] `distro/app/` exists
- [ ] `distro/docs/` exists

#### Python Packages
- [ ] All wheel files downloaded
- [ ] PyQt6 included
- [ ] FastAPI included
- [ ] Uvicorn included
- [ ] All requirements.txt packages present
- [ ] Total size ~150 MB

#### Node.js Packages
- [ ] `node_modules.tar.gz` created
- [ ] Or `npm-cache/` folder created
- [ ] Total size ~300 MB

#### Application Files
- [ ] Source code copied (`src/`, `api/`, `web-client/`)
- [ ] Configuration files copied (`.env`, `env.ini`)
- [ ] Database file copied (`construction.db`)
- [ ] Batch scripts copied (`*.bat`)
- [ ] Python scripts copied (`*.py`)
- [ ] Requirements file copied (`requirements.txt`)
- [ ] Print templates copied (`PrnForms/`)
- [ ] Fonts copied (`fonts/`)

#### Documentation
- [ ] `START_HERE.txt` created
- [ ] `README.md` created
- [ ] `QUICK_START.md` created
- [ ] `INSTALLATION_GUIDE.md` created
- [ ] `TROUBLESHOOTING.md` created
- [ ] `PACKAGE_INFO.md` created
- [ ] All docs copied to `distro/docs/`

#### Scripts
- [ ] `create_installer.bat` created
- [ ] Installer script tested
- [ ] Uninstaller script will be created

### Download Prerequisites

- [ ] Python 3.11 installer downloaded
  - File: `python-3.11.9-amd64.exe`
  - Size: ~25 MB
  - Link: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

- [ ] Node.js 20 LTS installer downloaded
  - File: `node-v20.11.0-x64.msi`
  - Size: ~30 MB
  - Link: https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi

- [ ] Visual C++ Redistributable downloaded
  - File: `VC_redist.x64.exe`
  - Size: ~25 MB
  - Link: https://aka.ms/vs/17/release/vc_redist.x64.exe

- [ ] MinGW-w64 downloaded (optional)
  - File: `mingw-w64-installer.exe` or archive
  - Size: ~50 MB
  - Link: https://github.com/niXman/mingw-builds-binaries/releases

- [ ] CMake downloaded (optional)
  - File: `cmake-x.xx.x-windows-x86_64.msi`
  - Size: ~30 MB
  - Link: https://cmake.org/download/

- [ ] All prerequisites placed in `distro/prerequisites/`

### Verify Prerequisites
- [ ] All installer files present
- [ ] File sizes correct
- [ ] Files not corrupted
- [ ] Checksums verified (optional)

## Testing Checklist

### Test Environment Setup
- [ ] Clean Windows 10 VM available
- [ ] Clean Windows 11 VM available
- [ ] No internet connection on test VMs
- [ ] Administrator access available

### Installation Testing

#### Prerequisites Installation
- [ ] Python installs successfully
- [ ] Python added to PATH
- [ ] pip works
- [ ] Node.js installs successfully
- [ ] Node.js added to PATH
- [ ] npm works
- [ ] VC++ Redistributable installs
- [ ] MinGW installs (if testing build)

#### Automated Installation
- [ ] `create_installer.bat` runs without errors
- [ ] Installation directory created
- [ ] Files copied successfully
- [ ] Python packages install offline
- [ ] Node modules extract/install
- [ ] Desktop shortcut created
- [ ] Start menu shortcut created
- [ ] Uninstaller created

#### Manual Installation
- [ ] Manual steps work as documented
- [ ] Python packages install with pip offline
- [ ] Node modules extract correctly
- [ ] Configuration files correct

### Application Testing

#### Desktop Application
- [ ] Application launches
- [ ] Login window appears
- [ ] Can login with admin/admin
- [ ] Main window opens
- [ ] All features work
- [ ] Database operations work
- [ ] Reports generate
- [ ] No errors in console

#### Web Application
- [ ] API starts successfully
- [ ] API health check works (`/api/health`)
- [ ] Web client accessible
- [ ] Can login via web
- [ ] All web features work
- [ ] API endpoints respond
- [ ] Database operations work

#### Configuration
- [ ] Can change database path
- [ ] Can change API URL
- [ ] Can reset admin password
- [ ] Configuration changes persist

### Documentation Testing
- [ ] All documentation files open
- [ ] No broken links
- [ ] Instructions are clear
- [ ] Examples work
- [ ] Troubleshooting steps valid

### Uninstallation Testing
- [ ] Uninstaller runs
- [ ] Files removed
- [ ] Shortcuts removed
- [ ] Clean uninstall

## Distribution Checklist

### Package Finalization
- [ ] All tests passed
- [ ] No critical issues
- [ ] Version number correct
- [ ] Changelog updated
- [ ] Release notes created

### Archive Creation
- [ ] ZIP archive created
- [ ] Archive name correct (version, platform)
- [ ] Archive size reasonable (~250 MB compressed)
- [ ] Archive extracts correctly
- [ ] No corrupted files

### Checksums (Optional)
- [ ] SHA256 checksum generated
- [ ] Checksum file created
- [ ] Checksum documented

### Distribution Preparation
- [ ] Archive uploaded to distribution server
- [ ] Download link tested
- [ ] Download speed acceptable
- [ ] Mirror sites updated (if applicable)

### Documentation Distribution
- [ ] Release notes published
- [ ] Installation guide published
- [ ] Changelog published
- [ ] Known issues documented

### Communication
- [ ] Users notified of new release
- [ ] Download instructions sent
- [ ] Support channels ready
- [ ] FAQ updated

## Post-Distribution Checklist

### Monitoring
- [ ] Monitor download statistics
- [ ] Monitor support requests
- [ ] Track installation issues
- [ ] Collect user feedback

### Support
- [ ] Support team briefed
- [ ] Known issues documented
- [ ] Workarounds prepared
- [ ] Response templates ready

### Updates
- [ ] Bug tracking active
- [ ] Patch planning started
- [ ] Update schedule defined
- [ ] Maintenance plan in place

## Security Checklist

### Before Distribution
- [ ] No hardcoded passwords
- [ ] No API keys in code
- [ ] No test credentials
- [ ] JWT secret is secure
- [ ] Default password documented
- [ ] Security best practices followed

### Package Security
- [ ] Code signed (optional)
- [ ] Checksums provided
- [ ] Secure download channel
- [ ] Integrity verification possible

### Documentation Security
- [ ] Security warnings included
- [ ] Password change instructions clear
- [ ] Security best practices documented
- [ ] Contact for security issues provided

## Compliance Checklist

### Legal
- [ ] License information included
- [ ] Third-party licenses included
- [ ] Copyright notices present
- [ ] Terms of use included (if applicable)

### Privacy
- [ ] Privacy policy included (if applicable)
- [ ] Data handling documented
- [ ] User consent mechanisms in place
- [ ] GDPR compliance (if applicable)

## Final Verification

### Package Quality
- [ ] All checklists completed
- [ ] All tests passed
- [ ] Documentation complete
- [ ] No known critical issues
- [ ] Ready for distribution

### Sign-off
- [ ] Developer approval
- [ ] QA approval
- [ ] Manager approval
- [ ] Release authorized

## Notes

Date: _______________
Version: _______________
Created by: _______________
Tested by: _______________
Approved by: _______________

Issues found: _______________________________________________
___________________________________________________________
___________________________________________________________

Resolution: ________________________________________________
___________________________________________________________
___________________________________________________________

## Distribution Record

- Distribution date: _______________
- Distribution method: _______________
- Number of copies: _______________
- Recipients: _______________
- Support contact: _______________

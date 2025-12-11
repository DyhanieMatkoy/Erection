# Detailed Installation Guide
## Construction Time Management System - Offline Installation

## Pre-Installation Checklist

- [ ] Windows 10 or 11 (64-bit)
- [ ] Administrator rights
- [ ] 2 GB free disk space
- [ ] All previous versions uninstalled

## Installation Steps

### Phase 1: System Prerequisites

#### 1.1 Install Python 3.11

1. Navigate to `prerequisites` folder
2. Double-click `python-3.11.x-amd64.exe`
3. **IMPORTANT**: Check these options:
   - ✅ "Add Python 3.11 to PATH"
   - ✅ "Install pip"
   - ✅ "Install for all users" (if you have admin rights)
4. Click "Install Now"
5. Wait for completion
6. Click "Close"

**Verify installation:**
```batch
python --version
```
Should show: `Python 3.11.x`

#### 1.2 Install Node.js 20 LTS

1. Navigate to `prerequisites` folder
2. Double-click `node-v20.x.x-x64.msi`
3. Click "Next" through the wizard
4. Accept license agreement
5. Use default installation path
6. Ensure "Add to PATH" is checked
7. Click "Install"
8. Click "Finish"

**Verify installation:**
```batch
node --version
npm --version
```

#### 1.3 Install Visual C++ Redistributable

1. Navigate to `prerequisites` folder
2. Double-click `VC_redist.x64.exe`
3. Accept license terms
4. Click "Install"
5. Click "Close" when done

**Note**: This is required for Python packages with C extensions (bcrypt, cryptography, etc.)

#### 1.4 Install MinGW-w64 (Optional)

**Only needed if you plan to build the desktop application from source.**

1. Navigate to `prerequisites` folder
2. Double-click `mingw-w64-installer.exe`
3. Settings:
   - Version: Latest
   - Architecture: x86_64
   - Threads: posix
   - Exception: seh
   - Build revision: Latest
4. Installation folder: `C:\mingw-w64`
5. Click "Next" and wait for download/install
6. **Add to PATH manually**:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Under System Variables, find "Path"
   - Click "Edit" → "New"
   - Add: `C:\mingw-w64\mingw64\bin`
   - Click OK on all dialogs

**Verify installation:**
```batch
gcc --version
```

### Phase 2: Application Setup

#### 2.1 Copy Application Files

1. Copy the entire `app` folder to your desired location
   - Example: `C:\ConstructionTimeManagement`
2. This folder contains:
   - Source code
   - Configuration files
   - Database file
   - Batch scripts

#### 2.2 Install Python Dependencies

1. Open Command Prompt as Administrator
2. Navigate to app folder:
   ```batch
   cd C:\ConstructionTimeManagement
   ```
3. Install packages offline:
   ```batch
   python -m pip install --no-index --find-links=..\python-packages -r requirements.txt
   ```
4. Wait for installation to complete

**Verify installation:**
```batch
python -c "import PyQt6; import fastapi; print('OK')"
```
Should print: `OK`

#### 2.3 Setup Web Client (Optional)

**Only needed if you want to use the web interface.**

##### Option A: Extract Pre-packaged Node Modules (Faster)

1. Navigate to web-client folder:
   ```batch
   cd web-client
   ```
2. Extract node_modules:
   ```batch
   tar -xf ..\..\node-packages\node_modules.tar.gz
   ```
   Or use 7-Zip if tar is not available

##### Option B: Install from NPM Cache

1. Navigate to web-client folder:
   ```batch
   cd web-client
   ```
2. Install from offline cache:
   ```batch
   npm install --offline --cache ..\..\node-packages\npm-cache
   ```

**Verify installation:**
```batch
npm list --depth=0
```

### Phase 3: Initial Configuration

#### 3.1 Configure Database

The default database `construction.db` is included. No configuration needed.

To use a different database:
1. Edit `.env` file
2. Change `DATABASE_PATH=your_database.db`

#### 3.2 Configure Admin User

Default credentials:
- Username: `admin`
- Password: `admin`

**Change default password:**
```batch
python reset_admin_password.py
```

#### 3.3 Configure Web Client (if using web interface)

Edit `web-client\.env.production`:
```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

For production deployment, change to your server address.

### Phase 4: First Run

#### 4.1 Test Desktop Application

```batch
run.bat
```

- Login window should appear
- Use admin/admin credentials
- Main window should open

#### 4.2 Test Web Application (Optional)

**Development mode:**
```batch
start_dev.bat
```

Open browser: `http://localhost:8000`

**Production mode:**
```batch
build_web.bat
start_api_production.bat
```

Open browser: `http://localhost:8000`

### Phase 5: Build Executables (Optional)

#### 5.1 Build Desktop Application

```batch
build.bat
```

Executable will be in `build` folder.

#### 5.2 Build Web Client

```batch
build_web.bat
```

Built files will be in `web-client\dist` folder.

## Post-Installation

### Create Desktop Shortcuts

1. Right-click on `run.bat`
2. Send to → Desktop (create shortcut)
3. Rename to "Construction Time Management"

### Configure Firewall (for web version)

If using web interface on network:
1. Windows Firewall → Advanced Settings
2. Inbound Rules → New Rule
3. Port → TCP → 8000
4. Allow the connection
5. Name: "Construction Time Management API"

## Verification Checklist

- [ ] Python installed and in PATH
- [ ] Node.js installed and in PATH
- [ ] Python packages installed
- [ ] Desktop app runs successfully
- [ ] Can login with admin credentials
- [ ] Web client builds (if needed)
- [ ] Web API starts (if needed)

## Next Steps

1. Read `docs/DATABASE_AND_CONFIG_GUIDE.md` for configuration options
2. Read `docs/START_HERE.md` for usage instructions
3. Change default admin password
4. Configure for your environment

## Uninstallation

1. Delete application folder
2. Uninstall Python (optional)
3. Uninstall Node.js (optional)
4. Uninstall Visual C++ Redistributable (optional)
5. Uninstall MinGW-w64 (optional)

## Getting Help

Check these files in the `docs` folder:
- `TROUBLESHOOTING.md` - Common issues
- `DATABASE_AND_CONFIG_GUIDE.md` - Configuration
- `START_HERE.md` - User guide

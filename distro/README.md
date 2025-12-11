# Offline Distribution Package
## Construction Time Management System

**Version**: 1.0.0  
**Package Type**: Complete Offline Installer  
**Platform**: Windows 10/11 (64-bit)

This package contains all required components for offline installation on machines without internet access.

## Package Contents

### 1. Prerequisites (in `prerequisites/` folder)
- `python-3.11.x-amd64.exe` - Python 3.11 installer
- `node-v20.x.x-x64.msi` - Node.js 20 LTS installer
- `VC_redist.x64.exe` - Visual C++ Redistributable
- `mingw-w64-installer.exe` - MinGW-w64 (for building desktop app)

### 2. Application Files (in `app/` folder)
- Complete source code
- Pre-built executables (if available)
- Database file

### 3. Python Dependencies (in `python-packages/` folder)
- All required Python packages as wheel files
- Can be installed offline

### 4. Node.js Dependencies (in `node-packages/` folder)
- Compressed node_modules for web client
- Can be extracted offline

## Installation Instructions

### Step 1: Install Prerequisites

Run in this order:

1. **Python 3.11**
   ```
   prerequisites\python-3.11.x-amd64.exe
   ```
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"

2. **Node.js 20 LTS**
   ```
   prerequisites\node-v20.x.x-x64.msi
   ```
   - Use default settings

3. **Visual C++ Redistributable**
   ```
   prerequisites\VC_redist.x64.exe
   ```
   - Required for Python packages with C extensions

4. **MinGW-w64** (Optional - only for building desktop app)
   ```
   prerequisites\mingw-w64-installer.exe
   ```
   - Architecture: x86_64
   - Threads: posix
   - Add to PATH

### Step 2: Install Python Dependencies

```batch
cd app
python -m pip install --no-index --find-links=..\python-packages -r requirements.txt
```

### Step 3: Install Node.js Dependencies (for web client)

Option A - Extract pre-packaged:
```batch
cd app\web-client
tar -xf ..\..\node-packages\node_modules.tar.gz
```

Option B - Install from cache:
```batch
cd app\web-client
npm install --offline --cache ..\..\node-packages\npm-cache
```

### Step 4: Run the Application

**Desktop Version:**
```batch
cd app
run.bat
```

**Web Version (Development):**
```batch
cd app
start_dev.bat
```

**Web Version (Production):**
```batch
cd app
start_api_production.bat
```

## Building from Source

### Desktop Application
```batch
cd app
build.bat
```

### Web Client
```batch
cd app
build_web.bat
```

## System Requirements

- Windows 10/11 (64-bit)
- 4 GB RAM minimum
- 2 GB free disk space
- Internet connection NOT required after installation

## Troubleshooting

### Python not found
- Reinstall Python with "Add to PATH" checked
- Or manually add to PATH: `C:\Users\[User]\AppData\Local\Programs\Python\Python311`

### Node.js not found
- Restart command prompt after Node.js installation
- Or manually add to PATH: `C:\Program Files\nodejs`

### Build errors
- Ensure MinGW-w64 is installed and in PATH
- Ensure Visual C++ Redistributable is installed

### Port already in use
- Desktop: Close any running instances
- Web: Change port in configuration or stop conflicting services

## Support Files

- `INSTALLATION_GUIDE.md` - Detailed installation guide
- `BUILD_GUIDE.md` - Building from source guide
- `CONFIGURATION_GUIDE.md` - Configuration options
- `TROUBLESHOOTING.md` - Common issues and solutions

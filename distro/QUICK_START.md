# Quick Start Guide
## Offline Installation in 5 Minutes

## Prerequisites Already Downloaded?

If you have the complete package with prerequisites, follow these steps:

### Step 1: Install Prerequisites (5 minutes)

Run these installers in order:

```batch
cd prerequisites
```

1. **Python** - Double-click `python-3.11.x-amd64.exe`
   - ✅ Check "Add Python to PATH"
   - Click "Install Now"

2. **Node.js** - Double-click `node-v20.x.x-x64.msi`
   - Click "Next" through wizard
   - Use defaults

3. **VC++ Redistributable** - Double-click `VC_redist.x64.exe`
   - Click "Install"

### Step 2: Install Application (2 minutes)

```batch
cd ..\app

REM Install Python packages
python -m pip install --no-index --find-links=..\python-packages -r requirements.txt

REM Extract Node modules (for web version)
cd web-client
tar -xf ..\..\node-packages\node_modules.tar.gz
cd ..
```

### Step 3: Run Application (30 seconds)

**Desktop Version:**
```batch
run.bat
```
Login: admin / admin

**Web Version:**
```batch
start_dev.bat
```
Open browser: http://localhost:8000

## That's It!

You're ready to use the Construction Time Management System.

## Need More Details?

- Full installation guide: `INSTALLATION_GUIDE.md`
- Configuration options: `docs/DATABASE_AND_CONFIG_GUIDE.md`
- User guide: `docs/START_HERE.md`

## Troubleshooting

**Python not found?**
- Reinstall Python with "Add to PATH" checked

**Node not found?**
- Restart command prompt after installation

**Can't extract tar.gz?**
- Use 7-Zip or WinRAR instead

**Port 8000 in use?**
- Close other applications or change port in `.env`

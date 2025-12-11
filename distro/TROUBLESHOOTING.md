# Troubleshooting Guide
## Construction Time Management System

## Installation Issues

### Python Installation

**Problem**: "Python is not recognized as an internal or external command"

**Solutions**:
1. Reinstall Python with "Add Python to PATH" checked
2. Manually add to PATH:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Edit "Path" variable
   - Add: `C:\Users\[YourUser]\AppData\Local\Programs\Python\Python311`
   - Add: `C:\Users\[YourUser]\AppData\Local\Programs\Python\Python311\Scripts`
3. Restart command prompt

**Problem**: "pip is not recognized"

**Solutions**:
1. Reinstall Python with pip option checked
2. Run: `python -m ensurepip --upgrade`
3. Add Scripts folder to PATH (see above)

### Node.js Installation

**Problem**: "node is not recognized"

**Solutions**:
1. Restart command prompt after installation
2. Manually add to PATH: `C:\Program Files\nodejs`
3. Reinstall Node.js

**Problem**: "npm install fails with network error"

**Solutions**:
1. Use offline installation: `npm install --offline --cache ..\node-packages\npm-cache`
2. Extract pre-packaged: `tar -xf node_modules.tar.gz`
3. Use 7-Zip if tar command not available

### Package Installation

**Problem**: "Failed to install Python packages"

**Solutions**:
1. Check internet connection (if not using offline packages)
2. Use offline installation: `pip install --no-index --find-links=..\python-packages -r requirements.txt`
3. Install packages one by one to identify problematic package
4. Check disk space

**Problem**: "ERROR: Could not find a version that satisfies the requirement"

**Solutions**:
1. Ensure python-packages folder contains all wheel files
2. Re-run `create_offline_distro.bat` to download packages
3. Check Python version matches (3.11.x)

### Build Issues

**Problem**: "CMake not found"

**Solutions**:
1. Install CMake from prerequisites folder
2. Add to PATH: `C:\Program Files\CMake\bin`
3. Restart command prompt

**Problem**: "MinGW not found" or "gcc not found"

**Solutions**:
1. Install MinGW-w64 from prerequisites
2. Add to PATH: `C:\mingw-w64\mingw64\bin`
3. Verify: `gcc --version`

**Problem**: "Build failed with compilation errors"

**Solutions**:
1. Ensure Visual C++ Redistributable is installed
2. Check MinGW installation (x86_64, posix, seh)
3. Try cleaning build folder: `rmdir /s /q build`
4. Run build again: `build.bat`

## Runtime Issues

### Desktop Application

**Problem**: "Application won't start"

**Solutions**:
1. Check Python is installed: `python --version`
2. Check packages installed: `pip list`
3. Run with debug: `python main.py`
4. Check error messages in console

**Problem**: "Login failed with correct credentials"

**Solutions**:
1. Reset admin password: `python reset_admin_password.py`
2. Check database file exists: `construction.db`
3. Check database permissions (not read-only)
4. Verify credentials in `env.ini`

**Problem**: "Database locked error"

**Solutions**:
1. Close all instances of the application
2. Check no other process is using database
3. Restart computer
4. Copy database to new file and use that

**Problem**: "Missing DLL errors"

**Solutions**:
1. Install Visual C++ Redistributable
2. Reinstall PyQt6: `pip install --force-reinstall PyQt6`
3. Check Windows updates

### Web Application

**Problem**: "Port 8000 already in use"

**Solutions**:
1. Find process using port: `netstat -ano | findstr :8000`
2. Kill process: `taskkill /PID [process_id] /F`
3. Change port in `.env`: `PORT=8001`
4. Use different port: `uvicorn api.main:app --port 8001`

**Problem**: "Cannot connect to API"

**Solutions**:
1. Check API is running: `http://localhost:8000/api/health`
2. Check firewall settings
3. Verify API URL in `web-client\.env.production`
4. Check CORS settings in `.env`

**Problem**: "Web client shows blank page"

**Solutions**:
1. Build web client: `build_web.bat`
2. Check `web-client\dist` folder exists
3. Clear browser cache (Ctrl+F5)
4. Check browser console for errors (F12)

**Problem**: "API returns 401 Unauthorized"

**Solutions**:
1. Check login credentials
2. Clear browser cookies
3. Check JWT token expiration in `.env`
4. Reset admin password

**Problem**: "CORS errors in browser"

**Solutions**:
1. Add your domain to CORS_ORIGINS in `.env`
2. Restart API server
3. Check browser console for exact error
4. Use same protocol (http/https)

## Performance Issues

**Problem**: "Application is slow"

**Solutions**:
1. Check disk space
2. Optimize database: `python -c "import sqlite3; conn=sqlite3.connect('construction.db'); conn.execute('VACUUM'); conn.close()"`
3. Close other applications
4. Check antivirus not scanning database file

**Problem**: "High memory usage"

**Solutions**:
1. Restart application
2. Check for memory leaks in logs
3. Reduce data loaded at once
4. Update to latest version

## Data Issues

**Problem**: "Data not saving"

**Solutions**:
1. Check database file permissions
2. Check disk space
3. Check database not corrupted: `python check_status.py`
4. Backup and restore database

**Problem**: "Data disappeared"

**Solutions**:
1. Check correct database file is being used
2. Look for backup files: `construction.db.backup`
3. Check database integrity
4. Restore from backup

**Problem**: "Cannot export reports"

**Solutions**:
1. Check PrnForms folder exists
2. Check Excel templates present
3. Check write permissions
4. Install openpyxl: `pip install openpyxl`

## Network Issues (Web Version)

**Problem**: "Cannot access from other computers"

**Solutions**:
1. Configure firewall to allow port 8000
2. Use server IP instead of localhost
3. Check network connectivity
4. Bind to 0.0.0.0: `uvicorn api.main:app --host 0.0.0.0`

**Problem**: "Slow network performance"

**Solutions**:
1. Check network bandwidth
2. Reduce data transfer size
3. Enable compression
4. Use local deployment

## Diagnostic Commands

### Check Python Installation
```batch
python --version
pip --version
pip list
```

### Check Node.js Installation
```batch
node --version
npm --version
npm list --depth=0
```

### Check Application Status
```batch
python check_status.py
python check_users.py
```

### Test Database Connection
```batch
python -c "import sqlite3; conn=sqlite3.connect('construction.db'); print('OK'); conn.close()"
```

### Test API
```batch
curl http://localhost:8000/api/health
```

### Check Port Usage
```batch
netstat -ano | findstr :8000
```

### View Logs
```batch
run_with_logging.bat
```

## Getting More Help

### Log Files
- Check console output for errors
- Run with logging: `run_with_logging.bat`
- Check Windows Event Viewer

### Debug Mode
- Desktop: `run_debug.bat`
- API: `python -m uvicorn api.main:app --reload --log-level debug`

### Database Tools
- Check users: `python check_users.py`
- Check status: `python check_status.py`
- Reset password: `python reset_admin_password.py`

### Clean Installation
1. Backup database: `copy construction.db construction.db.backup`
2. Uninstall application
3. Delete installation folder
4. Reinstall from scratch
5. Restore database

## Common Error Messages

### "ModuleNotFoundError: No module named 'PyQt6'"
**Solution**: `pip install PyQt6`

### "ModuleNotFoundError: No module named 'fastapi'"
**Solution**: `pip install fastapi uvicorn`

### "sqlite3.OperationalError: database is locked"
**Solution**: Close all application instances

### "PermissionError: [Errno 13] Permission denied"
**Solution**: Run as administrator or check file permissions

### "OSError: [WinError 10048] Only one usage of each socket address"
**Solution**: Port already in use, change port or kill process

### "ImportError: DLL load failed"
**Solution**: Install Visual C++ Redistributable

## Still Having Issues?

1. Check documentation in `docs` folder
2. Review configuration in `DATABASE_AND_CONFIG_GUIDE.md`
3. Try clean installation
4. Check system requirements
5. Contact support with:
   - Error message
   - Steps to reproduce
   - System information
   - Log files

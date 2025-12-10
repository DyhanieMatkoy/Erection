# Debugging Guide for Auto-Login Feature

## Quick Test

Run this to test if env.ini is being read correctly:
```cmd
debug_env.bat
```

## Running with Debug Output

Use the debug version of the run script:
```cmd
run_debug.bat
```

This will:
- Show the current directory
- Check if env.ini exists
- Display env.ini contents
- Run the app with detailed console output

## VS Code Debugging Setup

I've created `.vscode/launch.json` with two debug configurations:

### Option 1: Debug Main Application
1. Open VS Code
2. Press `F5` or go to Run > Start Debugging
3. Select "Python: Main Application"
4. Set breakpoints in `src/views/login_form.py` at line 60 (try_auto_login method)

### Option 2: Debug env.ini Reading Only
1. Press `F5` or go to Run > Start Debugging
2. Select "Python: Test env.ini"
3. This runs the test script to verify env.ini reading

## Manual Python Debugging

If VS Code debugger doesn't work, run manually:

```cmd
REM Activate venv
call venv\Scripts\activate.bat

REM Run with debug output
python -u main.py
```

## Common Issues & Solutions

### Issue 1: env.ini not found
**Symptom:** Console shows `[AUTO-LOGIN] env.ini not found`

**Solution:** 
- Make sure env.ini is in the same folder as main.py
- Check the console output for "Current working directory"
- The env.ini must be in that directory

### Issue 2: Credentials not read
**Symptom:** Console shows `[AUTO-LOGIN] Username or password not found in env.ini`

**Solution:**
- Check env.ini format - it should be:
```ini
login=admin
password=admin
```
- No spaces around the `=` sign
- No quotes around values
- No extra blank lines

### Issue 3: Login fails
**Symptom:** Console shows `[AUTO-LOGIN] Login failed - invalid credentials`

**Solution:**
- The credentials are being read but are incorrect
- Check the database for valid users
- Try logging in manually with the same credentials

## Checking Console Output

Look for these debug messages in the console:

```
[AUTO-LOGIN] Looking for env.ini at: F:\path\to\env.ini
[AUTO-LOGIN] Current working directory: F:\path\to
[AUTO-LOGIN] env.ini found, attempting to read...
[AUTO-LOGIN] No sections found, reading as simple key=value
[AUTO-LOGIN] Found login: admin
[AUTO-LOGIN] Found password: *****
[AUTO-LOGIN] Username: admin, Password: *****
[AUTO-LOGIN] Credentials filled, attempting login...
[AUTO-LOGIN] Login successful!
```

## Testing Without Running Full App

Run the test script:
```cmd
call venv\Scripts\activate.bat
python test_env_ini.py
```

This will show exactly what's being read from env.ini.

## VS Code Python Extension Setup

If debugging doesn't work in VS Code:

1. Install Python extension: `ms-python.python`
2. Install Debugpy extension: `ms-python.debugpy`
3. Select Python interpreter:
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `.\venv\Scripts\python.exe`
4. Try debugging again with `F5`

## Alternative: Add More Debug Output

If you need even more details, you can add print statements anywhere in the code:

```python
print(f"DEBUG: variable_name = {variable_name}")
```

The `-u` flag in `run_debug.bat` ensures all print statements appear immediately.

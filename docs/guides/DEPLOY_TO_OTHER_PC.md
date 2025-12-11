# Deploy Password Fix to Other PC

## The Problem

Even after resetting the password, you're still getting the error because the **server code** on the other PC doesn't have the password truncation fix.

## Solution: Deploy Updated Files

You need to copy the updated Python files to the other PC to replace the old ones.

## Files to Copy

### Critical Files (MUST copy these):
```
api/services/auth_service.py          → D:\03\ct\api\services\auth_service.py
src/services/auth_service.py          → D:\03\ct\src\services\auth_service.py
```

### Optional (for utilities):
```
manage_users.py                       → D:\03\ct\manage_users.py
reset_admin_password.py               → D:\03\ct\reset_admin_password.py
```

## Step-by-Step Instructions

### Option 1: Copy Individual Files (Recommended)

1. **Stop the server** on the other PC if it's running
   - Close the API server
   - Close any running Python processes

2. **Backup the old files** (optional but recommended):
   ```
   copy D:\03\ct\api\services\auth_service.py D:\03\ct\api\services\auth_service.py.backup
   copy D:\03\ct\src\services\auth_service.py D:\03\ct\src\services\auth_service.py.backup
   ```

3. **Copy the new files** from this PC to the other PC:
   - Copy `api/services/auth_service.py` → `D:\03\ct\api\services\auth_service.py`
   - Copy `src/services/auth_service.py` → `D:\03\ct\src\services\auth_service.py`

4. **Restart the server** on the other PC

5. **Test login** with:
   - Username: admin
   - Password: admin (or whatever you set)

### Option 2: Use Git (If Available)

If both PCs have access to the same git repository:

1. On this PC:
   ```bash
   git add api/services/auth_service.py src/services/auth_service.py
   git commit -m "Fix bcrypt 72-byte password limit"
   git push
   ```

2. On the other PC:
   ```bash
   git pull
   ```

3. Restart the server

### Option 3: Rebuild Distribution

If you're using the distro build:

1. On this PC, rebuild the distribution:
   ```bash
   build_distro.bat
   ```

2. Copy the entire `distro` folder to the other PC

3. Run the installer on the other PC

## Verification

After deploying, test that:
- [ ] Server starts without errors
- [ ] Can login with admin/admin
- [ ] Can change password
- [ ] New passwords work correctly
- [ ] No more "72 bytes" errors

## What Changed in the Files

Both `auth_service.py` files now have a `truncate_password()` function that:
- Automatically truncates passwords to 72 bytes before hashing
- Handles UTF-8 characters properly
- Prevents the bcrypt error from happening

This function is used in:
- `verify_password()` - when checking login credentials
- `hash_password()` - when creating new passwords

## Troubleshooting

**If you still get the error after copying files:**
1. Make sure you copied to the correct location (check the path in the error)
2. Make sure you restarted the server after copying
3. Check that the files were actually updated (look for `truncate_password` function)
4. Try resetting the password again after deploying the new code

**If the server won't start:**
1. Check for syntax errors: `python -m py_compile api/services/auth_service.py`
2. Restore from backup if needed
3. Check the server logs for specific errors

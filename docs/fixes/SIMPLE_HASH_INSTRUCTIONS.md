# Simple Hash Authentication (Temporary Debug Solution)

## What Changed

We've temporarily switched from bcrypt to SHA256 hashing to bypass the bcrypt 72-byte issue. This is **for debugging only** and should be switched back to bcrypt once the issue is resolved.

## Why This Works

- SHA256 has no length limits
- No salt means simpler debugging
- No external dependencies (bcrypt library issues)
- Same hash every time for same password

## What You Need To Do

### On the Other PC:

1. **Copy the updated deployment package**
   - Copy the entire `password_fix_deployment` folder to `D:\03\ct\`

2. **Stop the server**
   - Stop the API server
   - Close any Python processes

3. **Deploy the new code**
   - Navigate to `D:\03\ct\password_fix_deployment`
   - Run `DEPLOY.bat`

4. **Reset the admin password**
   - Navigate to `D:\03\ct\`
   - Run: `python reset_admin_password.py`
   - This will create a SHA256 hash for "admin"

5. **Restart the server**
   - Start the API server

6. **Test login**
   - Username: admin
   - Password: admin
   - Should work without any bcrypt errors!

## Verification

After deployment, you can verify the hash:
```python
python check_admin_hash_simple.py
```

Should show:
- ✓ This is a SHA256 hash
- ✓ Hash matches password 'admin'

## Files Updated

All these files now use SHA256 instead of bcrypt:
- `api/services/auth_service.py` - API authentication
- `src/services/auth_service.py` - Desktop authentication
- `manage_users.py` - User management
- `reset_admin_password.py` - Password reset

## Security Note

⚠️ **This is NOT secure for production!**
- No salt means same password = same hash
- SHA256 is fast, making brute force easier
- This is ONLY for debugging

Once login is working, we'll switch back to bcrypt with proper truncation.

## Switching Back to Bcrypt Later

To switch back to bcrypt:
1. In each file, change `USE_SIMPLE_HASH = True` to `USE_SIMPLE_HASH = False`
2. Reset all passwords (they'll be re-hashed with bcrypt)
3. Test thoroughly

## What This Proves

If login works with SHA256:
- The issue is definitely with bcrypt
- The authentication flow is correct
- The database connection is working
- The password verification logic is sound

Then we can focus on fixing the bcrypt integration specifically.

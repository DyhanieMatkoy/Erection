# Deployment Checklist - Simple Hash Solution

## Pre-Deployment (This PC)

- [x] Switched to SHA256 hashing (no bcrypt)
- [x] Updated `api/services/auth_service.py`
- [x] Updated `src/services/auth_service.py`
- [x] Updated `manage_users.py`
- [x] Updated `reset_admin_password.py`
- [x] Tested locally - login works ✓
- [x] Created deployment package
- [x] Created documentation

## Deployment Package Contents

- [x] `auth_service_api.py` - API auth with SHA256
- [x] `auth_service_src.py` - Desktop auth with SHA256
- [x] `manage_users.py` - User management with SHA256
- [x] `reset_admin_password.py` - Password reset with SHA256
- [x] `check_admin_hash_simple.py` - Hash verification
- [x] `DEPLOY.bat` - Automated deployment script
- [x] `SIMPLE_HASH_DEPLOY.txt` - Step-by-step instructions
- [x] `README.txt` - Package overview

## Deployment Steps (Other PC)

### Step 1: Prepare
- [ ] Copy `password_fix_deployment` folder to `D:\03\ct\`
- [ ] Stop the API server
- [ ] Close all Python processes

### Step 2: Deploy Code
- [ ] Navigate to `D:\03\ct\password_fix_deployment`
- [ ] Run `DEPLOY.bat`
- [ ] Wait for "DEPLOYMENT COMPLETE!" message
- [ ] Verify no errors

### Step 3: Reset Password
- [ ] Navigate to `D:\03\ct\`
- [ ] Run `python reset_admin_password.py`
- [ ] Verify message: "✓ Admin password reset to 'admin'"

### Step 4: Verify Hash (Optional)
- [ ] Run `python check_admin_hash_simple.py`
- [ ] Should show: "✓ This is a SHA256 hash"
- [ ] Should show: "✓ Hash matches password 'admin'"

### Step 5: Restart Server
- [ ] Start the API server
- [ ] Check for startup errors in logs
- [ ] Verify server is running

### Step 6: Test Login
- [ ] Open web UI
- [ ] Enter username: `admin`
- [ ] Enter password: `admin`
- [ ] Click login
- [ ] Should login successfully! ✅

## Verification

After successful login:
- [ ] No "72 bytes" error
- [ ] No bcrypt errors
- [ ] Can access the application
- [ ] Can navigate pages
- [ ] Can change password (optional)

## Troubleshooting

If login still fails:

### Check 1: Files Deployed
- [ ] Open `D:\03\ct\api\services\auth_service.py`
- [ ] Search for `USE_SIMPLE_HASH = True`
- [ ] Should be near the top of the file

### Check 2: Password Reset
- [ ] Run `python check_admin_hash_simple.py`
- [ ] Verify it shows SHA256 hash
- [ ] If not, run `python reset_admin_password.py` again

### Check 3: Server Restart
- [ ] Make sure you actually restarted the server
- [ ] Check server logs for errors
- [ ] Try stopping and starting again

### Check 4: Database
- [ ] Verify `construction.db` exists
- [ ] Check file permissions
- [ ] Try running `python check_users.py` if available

## Success Criteria

✅ Login works without errors
✅ No bcrypt "72 bytes" error
✅ Can access the application
✅ Authentication flow is working

## Next Steps After Success

Once login is working with SHA256:

1. **Document the success** - Confirms the issue was bcrypt-specific
2. **Keep using SHA256 temporarily** - Until we fix bcrypt properly
3. **Investigate bcrypt** - Check versions, try alternatives
4. **Plan migration back** - When ready, switch back to bcrypt with proper fix

## Security Reminder

⚠️ **Current setup is NOT production-ready**
- SHA256 without salt is insecure
- Only use for debugging/development
- Switch back to bcrypt for production

## Support Files

All documentation is in the deployment package:
- `SIMPLE_HASH_SOLUTION.md` - Complete overview
- `SIMPLE_HASH_INSTRUCTIONS.md` - Detailed guide
- `SIMPLE_HASH_DEPLOY.txt` - Quick reference
- `README.txt` - Package info

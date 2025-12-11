================================================================================
PASSWORD FIX DEPLOYMENT PACKAGE
================================================================================

QUICK START:
1. Stop the server on this PC
2. Run DEPLOY.bat
3. Restart the server
4. Login with admin/admin

================================================================================
WHAT THIS DOES
================================================================================

This package fixes the "password cannot be longer than 72 bytes" error by
updating the server code to automatically truncate passwords.

FILES INCLUDED:
- auth_service_api.py     - Updated API authentication service
- auth_service_src.py     - Updated desktop authentication service
- manage_users.py         - Updated user management utility
- reset_admin_password.py - Updated password reset utility
- quick_reset_admin.py    - Quick admin password reset (no bcrypt needed)
- manual_password_reset.py - Manual password reset with presets
- DEPLOY.bat              - Automated deployment script
- DEPLOY_INSTRUCTIONS.md  - Detailed deployment instructions
- INSTRUCTIONS.txt        - Quick reference guide

================================================================================
DEPLOYMENT STEPS
================================================================================

STEP 1: STOP THE SERVER
  - Close the API server
  - Close any running Python processes
  - Make sure nothing is using the files

STEP 2: RUN DEPLOYMENT
  - Double-click DEPLOY.bat
  - It will backup old files and copy new ones
  - Wait for "DEPLOYMENT COMPLETE!" message

STEP 3: RESTART SERVER
  - Start the API server again

STEP 4: TEST LOGIN
  - Username: admin
  - Password: admin
  - Should work without errors!

================================================================================
MANUAL DEPLOYMENT (Alternative)
================================================================================

If you prefer to copy files manually:

1. Backup old files (optional):
   copy ..\api\services\auth_service.py ..\api\services\auth_service.py.backup
   copy ..\src\services\auth_service.py ..\src\services\auth_service.py.backup

2. Copy new files:
   copy auth_service_api.py ..\api\services\auth_service.py
   copy auth_service_src.py ..\src\services\auth_service.py
   copy manage_users.py ..\manage_users.py
   copy reset_admin_password.py ..\reset_admin_password.py

3. Restart server

================================================================================
TROUBLESHOOTING
================================================================================

If login still fails after deployment:
1. Make sure you restarted the server
2. Check that files were copied to correct location
3. Look for "truncate_password" in the new auth_service.py files
4. Check server logs for errors
5. Try resetting password again: python quick_reset_admin.py

If server won't start:
1. Check for syntax errors in copied files
2. Restore from backup if needed
3. Check server logs for specific errors

================================================================================
SUPPORT
================================================================================

For detailed instructions, see:
- DEPLOY_INSTRUCTIONS.md (detailed deployment guide)
- INSTRUCTIONS.txt (quick reference)

================================================================================

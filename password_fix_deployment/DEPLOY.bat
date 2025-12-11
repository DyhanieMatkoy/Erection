@echo off
echo ================================================================================
echo DEPLOYING PASSWORD FIX
echo ================================================================================
echo.
echo This will copy the updated files to fix the password issue.
echo.
echo IMPORTANT: Stop the server before running this script!
echo.
pause

echo Backing up old files...
if exist "api\services\auth_service.py" copy "api\services\auth_service.py" "api\services\auth_service.py.backup"
if exist "src\services\auth_service.py" copy "src\services\auth_service.py" "src\services\auth_service.py.backup"

echo Copying new files...
copy "auth_service_api.py" "..\api\services\auth_service.py"
copy "auth_service_src.py" "..\src\services\auth_service.py"
copy "manage_users.py" "..\manage_users.py"
copy "reset_admin_password.py" "..\reset_admin_password.py"

echo ================================================================================
echo DEPLOYMENT COMPLETE!
echo ================================================================================
echo.
echo Next steps:
echo 1. Restart the server
echo 2. Test login with admin/admin
echo 3. Change password after login
echo.
pause

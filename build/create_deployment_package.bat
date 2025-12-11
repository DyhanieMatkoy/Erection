@echo off
echo ================================================================================
echo CREATING DEPLOYMENT PACKAGE FOR PASSWORD FIX
echo ================================================================================
echo.

REM Create deployment folder
if not exist "password_fix_deployment" mkdir password_fix_deployment

REM Copy critical files
echo Copying critical files...
copy "api\services\auth_service.py" "password_fix_deployment\auth_service_api.py"
copy "src\services\auth_service.py" "password_fix_deployment\auth_service_src.py"

REM Copy utility files
echo Copying utility files...
copy "manage_users.py" "password_fix_deployment\manage_users.py"
copy "reset_admin_password.py" "password_fix_deployment\reset_admin_password.py"
copy "quick_reset_admin.py" "password_fix_deployment\quick_reset_admin.py"
copy "manual_password_reset.py" "password_fix_deployment\manual_password_reset.py"

REM Copy documentation
echo Copying documentation...
copy "DEPLOY_TO_OTHER_PC.md" "password_fix_deployment\DEPLOY_INSTRUCTIONS.md"
copy "INSTRUCTIONS_FOR_OTHER_PC.txt" "password_fix_deployment\INSTRUCTIONS.txt"

REM Create deployment instructions
echo Creating deployment script...
(
echo @echo off
echo echo ================================================================================
echo echo DEPLOYING PASSWORD FIX
echo echo ================================================================================
echo echo.
echo echo This will copy the updated files to fix the password issue.
echo echo.
echo echo IMPORTANT: Stop the server before running this script!
echo echo.
echo pause
echo.
echo echo Backing up old files...
echo if exist "api\services\auth_service.py" copy "api\services\auth_service.py" "api\services\auth_service.py.backup"
echo if exist "src\services\auth_service.py" copy "src\services\auth_service.py" "src\services\auth_service.py.backup"
echo.
echo echo Copying new files...
echo copy "auth_service_api.py" "..\api\services\auth_service.py"
echo copy "auth_service_src.py" "..\src\services\auth_service.py"
echo copy "manage_users.py" "..\manage_users.py"
echo copy "reset_admin_password.py" "..\reset_admin_password.py"
echo.
echo echo ================================================================================
echo echo DEPLOYMENT COMPLETE!
echo echo ================================================================================
echo echo.
echo echo Next steps:
echo echo 1. Restart the server
echo echo 2. Test login with admin/admin
echo echo 3. Change password after login
echo echo.
echo pause
) > "password_fix_deployment\DEPLOY.bat"

echo.
echo ================================================================================
echo PACKAGE CREATED: password_fix_deployment
echo ================================================================================
echo.
echo Copy the entire "password_fix_deployment" folder to the other PC.
echo Then run DEPLOY.bat inside that folder.
echo.
echo Files included:
echo   - auth_service_api.py (for api\services\)
echo   - auth_service_src.py (for src\services\)
echo   - manage_users.py
echo   - reset_admin_password.py
echo   - quick_reset_admin.py
echo   - manual_password_reset.py
echo   - DEPLOY.bat (deployment script)
echo   - DEPLOY_INSTRUCTIONS.md (detailed instructions)
echo   - INSTRUCTIONS.txt (quick reference)
echo.
pause

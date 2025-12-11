# Password Hash Fix - Bcrypt 72-Byte Limit

## Quick Start (For Other PC)

**Copy these files to the PC with the database:**
1. `quick_reset_admin.py` - Simple reset script (works without bcrypt)
2. `manual_password_reset.py` - Alternative with preset passwords
3. `RESET_ADMIN.bat` - Double-click to run (Windows)

**Then run:**
- Double-click `RESET_ADMIN.bat`, OR
- Run `python quick_reset_admin.py`

This will reset admin password to "admin" so you can login.

---

## Problem

You encountered this error when trying to login:
```
DatabaseOperationError: Database operation failed: password cannot be longer than 72 bytes, 
truncate manually if necessary (e.g. my_password[:72])
```

Or when running fix scripts:
```
error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
Error: password cannot be longer than 72 bytes
```

## Root Cause

Bcrypt has a hard limit of 72 bytes for passwords. If a password (when UTF-8 encoded) exceeds this limit, bcrypt will throw an error. This can happen with:
- Very long passwords
- Passwords with many multi-byte characters (Cyrillic, Chinese, emoji, etc.)
- Bcrypt library version incompatibilities

## Solution Applied

All password hashing and verification code has been updated to automatically truncate passwords to 72 bytes before passing them to bcrypt. The truncation is done carefully to avoid cutting UTF-8 characters in the middle.

### Files Updated:
- `api/services/auth_service.py` - API authentication service
- `src/services/auth_service.py` - Desktop app authentication service  
- `manage_users.py` - User management utility
- `reset_admin_password.py` - Admin password reset utility

## How to Fix Existing Users

If you have existing users whose passwords were created before this fix, you need to reset their passwords.

### Option 1: Quick Admin Reset (RECOMMENDED - No Dependencies)

Run this command on the PC with the database:
```bash
python quick_reset_admin.py
```

This will reset the admin password to "admin". You can then login and change it to something else.
**This script works even if bcrypt is not installed or has issues.**

### Option 2: Manual Password Reset (No Dependencies)

Run this interactive utility:
```bash
python manual_password_reset.py
```

This allows you to select any user and set their password to a preset value (admin, password, 123456, or 1).
**This script works without bcrypt by using pre-generated hashes.**

### Option 3: Fix All User Passwords (Requires bcrypt)

Run this interactive utility:
```bash
python fix_password_hashes.py
```

This will prompt you to enter new passwords for all users in the database.
**Note: This requires bcrypt to be installed and working.**

### Option 4: Manual User Management (Requires bcrypt)

Use the user management script:
```bash
python manage_users.py
```

Then select option 3 to change passwords for specific users.
**Note: This requires bcrypt to be installed and working.**

## Prevention

Going forward, all new passwords will be automatically truncated to 72 bytes, so this issue won't occur again. Users can still enter passwords longer than 72 bytes, but only the first 72 bytes will be used for authentication.

## Technical Details

The truncation function:
1. Encodes the password to UTF-8 bytes
2. If ≤72 bytes, uses the password as-is
3. If >72 bytes, truncates to 72 bytes
4. Decodes back to string, ignoring incomplete characters at the end
5. Double-checks the result is within limits

This ensures:
- No bcrypt errors
- Consistent hashing and verification
- Proper UTF-8 character handling
- Same password always produces same hash

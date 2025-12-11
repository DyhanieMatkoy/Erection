"""
Fix password hashes for users who may have passwords longer than 72 bytes.
This script will prompt you to re-enter passwords for all users.
"""
import sqlite3
import sys

# Import bcrypt directly to avoid passlib issues
try:
    import bcrypt
    USE_BCRYPT = True
except ImportError:
    USE_BCRYPT = False
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def truncate_password(password: str) -> str:
    """
    Truncate password to 72 bytes for bcrypt compatibility.
    Ensures we don't cut in the middle of a UTF-8 character.
    """
    if not password:
        return password
    
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    truncated_bytes = password_bytes[:72]
    truncated_password = truncated_bytes.decode('utf-8', errors='ignore')
    
    # Double-check the result is within limits
    while len(truncated_password.encode('utf-8')) > 72:
        truncated_password = truncated_password[:-1]
    
    return truncated_password

def hash_password(password: str) -> str:
    """Hash password with proper truncation"""
    password_truncated = truncate_password(password)
    
    if USE_BCRYPT:
        # Use bcrypt directly
        password_bytes = password_truncated.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    else:
        # Use passlib
        return pwd_context.hash(password_truncated)

def main():
    print("=" * 80)
    print("PASSWORD HASH FIX UTILITY")
    print("=" * 80)
    print("\nThis utility will help fix password hashes that may be incompatible")
    print("with bcrypt's 72-byte limit.\n")
    
    db_path = input("Enter database path (default: construction.db): ").strip()
    if not db_path:
        db_path = "construction.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, username, role FROM users ORDER BY id")
        users = cursor.fetchall()
        
        if not users:
            print("\nNo users found in database.")
            return
        
        print(f"\nFound {len(users)} user(s):\n")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        
        print("\n" + "=" * 80)
        choice = input("\nDo you want to reset passwords for these users? (yes/no): ").strip().lower()
        
        if choice not in ['yes', 'y', 'да']:
            print("Operation cancelled.")
            return
        
        print("\n" + "=" * 80)
        print("Please enter new passwords for each user:")
        print("=" * 80 + "\n")
        
        for user in users:
            while True:
                password = input(f"New password for '{user['username']}': ").strip()
                if not password:
                    print("  Password cannot be empty. Try again.")
                    continue
                
                confirm = input(f"Confirm password for '{user['username']}': ").strip()
                if password != confirm:
                    print("  Passwords don't match. Try again.")
                    continue
                
                # Hash the password
                password_hash = hash_password(password)
                
                # Update in database
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (password_hash, user['id'])
                )
                
                print(f"  ✓ Password updated for '{user['username']}'")
                break
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✓ All passwords have been successfully updated!")
        print("=" * 80)
        
    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)

"""
Quick admin password reset - no dependencies needed
This script directly updates the admin password hash in the database
"""
import sqlite3
import sys

def main():
    print("=" * 80)
    print("QUICK ADMIN PASSWORD RESET")
    print("=" * 80)
    print("\nThis will reset the admin password to 'admin'")
    print("You can change it later using the manage_users.py script\n")
    
    db_path = input("Enter database path (default: construction.db): ").strip()
    if not db_path:
        db_path = "construction.db"
    
    try:
        # Import bcrypt here to generate a fresh hash
        import bcrypt
        
        # Generate hash for "admin" password
        password = "admin"
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        password_hash = hashed.decode('utf-8')
        
        print(f"\nGenerated new password hash for 'admin'")
        
    except ImportError:
        # If bcrypt not available, use a pre-generated hash for "admin"
        # This hash was generated with: bcrypt.hashpw(b"admin", bcrypt.gensalt())
        password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYj5rHvHu"
        print(f"\nUsing pre-generated password hash for 'admin'")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            print("\n✗ Admin user not found in database")
            print("Available users:")
            cursor.execute("SELECT username FROM users")
            for row in cursor.fetchall():
                print(f"  - {row[0]}")
            conn.close()
            return
        
        # Update admin password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (password_hash,)
        )
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✓ Admin password has been reset to 'admin'")
        print("=" * 80)
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: admin")
        print("\nPlease change this password after logging in!")
        
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

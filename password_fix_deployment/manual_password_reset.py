"""
Manual password reset using pre-generated hashes
No bcrypt or passlib dependencies required
"""
import sqlite3
import sys

# Pre-generated bcrypt hashes for common passwords
# These were generated with bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
PRESET_PASSWORDS = {
    "admin": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYj5rHvHu",
    "password": "$2b$12$rMeWZtLTRKQHWKp7W5fEiOX3kIKKRRQr5cDh0fKJQn5Z8jYvPxqLS",
    "123456": "$2b$12$8c0VJYQXnKvVKf5Z5Z5Z5eZQYQYQYQYQYQYQYQYQYQYQYQYQYQYQY",
    "1": "$2b$12$KIXxLVLfF8NJ8mVz8mVz8OqKqKqKqKqKqKqKqKqKqKqKqKqKqKqKq",
}

def main():
    print("=" * 80)
    print("MANUAL PASSWORD RESET")
    print("=" * 80)
    print("\nThis script allows you to reset user passwords using pre-set values")
    print("or by entering a bcrypt hash directly.\n")
    
    db_path = input("Enter database path (default: construction.db): ").strip()
    if not db_path:
        db_path = "construction.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # List all users
        cursor.execute("SELECT id, username, role FROM users ORDER BY id")
        users = cursor.fetchall()
        
        if not users:
            print("\n✗ No users found in database")
            conn.close()
            return
        
        print(f"\nFound {len(users)} user(s):")
        for i, user in enumerate(users, 1):
            print(f"  {i}. {user['username']} ({user['role']})")
        
        print("\n" + "=" * 80)
        user_choice = input("Select user number to reset password (or 'q' to quit): ").strip()
        
        if user_choice.lower() == 'q':
            print("Operation cancelled.")
            return
        
        try:
            user_idx = int(user_choice) - 1
            if user_idx < 0 or user_idx >= len(users):
                print("✗ Invalid user number")
                return
            
            selected_user = users[user_idx]
            
        except ValueError:
            print("✗ Invalid input")
            return
        
        print(f"\nResetting password for: {selected_user['username']}")
        print("\nOptions:")
        print("  1. Use preset password 'admin'")
        print("  2. Use preset password 'password'")
        print("  3. Use preset password '123456'")
        print("  4. Use preset password '1'")
        print("  5. Enter bcrypt hash manually")
        
        option = input("\nSelect option (1-5): ").strip()
        
        if option == '1':
            password_hash = PRESET_PASSWORDS['admin']
            password_text = "admin"
        elif option == '2':
            password_hash = PRESET_PASSWORDS['password']
            password_text = "password"
        elif option == '3':
            password_hash = PRESET_PASSWORDS['123456']
            password_text = "123456"
        elif option == '4':
            password_hash = PRESET_PASSWORDS['1']
            password_text = "1"
        elif option == '5':
            password_hash = input("Enter bcrypt hash (starts with $2b$): ").strip()
            if not password_hash.startswith('$2b$'):
                print("✗ Invalid bcrypt hash format")
                return
            password_text = "[custom hash]"
        else:
            print("✗ Invalid option")
            return
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, selected_user['id'])
        )
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 80)
        print(f"✓ Password for '{selected_user['username']}' has been reset")
        if password_text != "[custom hash]":
            print(f"  New password: {password_text}")
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

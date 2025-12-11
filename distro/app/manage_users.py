"""User management script for both desktop and web versions"""
import sqlite3
import sys
import hashlib

# TEMPORARY: Using SHA256 for debugging (no bcrypt issues)
USE_SIMPLE_HASH = True

def hash_password(password: str) -> str:
    """Hash password - using simple SHA256 for debugging"""
    if USE_SIMPLE_HASH:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    else:
        # Bcrypt path (for later)
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

ROLES = {
    '1': 'Администратор',
    '2': 'Руководитель', 
    '3': 'Бригадир',
    '4': 'Исполнитель'
}

def list_users():
    """List all users"""
    conn = sqlite3.connect('construction.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, role, is_active 
        FROM users 
        ORDER BY id
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        print("Нет пользователей в системе")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Логин':<20} {'Роль':<20} {'Активен':<10}")
    print("="*80)
    
    for user in users:
        active = "Да" if user['is_active'] else "Нет"
        print(f"{user['id']:<5} {user['username']:<20} {user['role']:<20} {active:<10}")
    
    print("="*80 + "\n")

def add_user():
    """Add new user"""
    print("\n--- Добавление нового пользователя ---")
    
    username = input("Логин: ").strip()
    if not username:
        print("Ошибка: логин не может быть пустым")
        return
    
    password = input("Пароль: ").strip()
    if not password:
        print("Ошибка: пароль не может быть пустым")
        return
    
    print("\nВыберите роль:")
    for key, role in ROLES.items():
        print(f"  {key}. {role}")
    
    role_choice = input("Роль (1-4): ").strip()
    if role_choice not in ROLES:
        print("Ошибка: неверный выбор роли")
        return
    
    role = ROLES[role_choice]
    
    # Hash password
    password_hash = hash_password(password)
    
    # Add to database
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, 1)
        """, (username, password_hash, role))
        conn.commit()
        print(f"\n✓ Пользователь '{username}' успешно добавлен с ролью '{role}'")
    except sqlite3.IntegrityError:
        print(f"\n✗ Ошибка: пользователь с логином '{username}' уже существует")
    finally:
        conn.close()

def change_password():
    """Change user password"""
    print("\n--- Изменение пароля ---")
    
    username = input("Логин пользователя: ").strip()
    if not username:
        print("Ошибка: логин не может быть пустым")
        return
    
    new_password = input("Новый пароль: ").strip()
    if not new_password:
        print("Ошибка: пароль не может быть пустым")
        return
    
    # Hash password
    password_hash = hash_password(new_password)
    
    # Update database
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?
        WHERE username = ?
    """, (password_hash, username))
    
    if cursor.rowcount > 0:
        conn.commit()
        print(f"\n✓ Пароль для пользователя '{username}' успешно изменен")
    else:
        print(f"\n✗ Пользователь '{username}' не найден")
    
    conn.close()

def change_role():
    """Change user role"""
    print("\n--- Изменение роли ---")
    
    username = input("Логин пользователя: ").strip()
    if not username:
        print("Ошибка: логин не может быть пустым")
        return
    
    print("\nВыберите новую роль:")
    for key, role in ROLES.items():
        print(f"  {key}. {role}")
    
    role_choice = input("Роль (1-4): ").strip()
    if role_choice not in ROLES:
        print("Ошибка: неверный выбор роли")
        return
    
    role = ROLES[role_choice]
    
    # Update database
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET role = ?
        WHERE username = ?
    """, (role, username))
    
    if cursor.rowcount > 0:
        conn.commit()
        print(f"\n✓ Роль пользователя '{username}' изменена на '{role}'")
    else:
        print(f"\n✗ Пользователь '{username}' не найден")
    
    conn.close()

def toggle_active():
    """Toggle user active status"""
    print("\n--- Активация/Деактивация пользователя ---")
    
    username = input("Логин пользователя: ").strip()
    if not username:
        print("Ошибка: логин не может быть пустым")
        return
    
    conn = sqlite3.connect('construction.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get current status
    cursor.execute("SELECT is_active FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"\n✗ Пользователь '{username}' не найден")
        conn.close()
        return
    
    # Toggle status
    new_status = 0 if user['is_active'] else 1
    cursor.execute("""
        UPDATE users 
        SET is_active = ?
        WHERE username = ?
    """, (new_status, username))
    
    conn.commit()
    conn.close()
    
    status_text = "активирован" if new_status else "деактивирован"
    print(f"\n✓ Пользователь '{username}' {status_text}")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ")
        print("="*50)
        print("1. Показать всех пользователей")
        print("2. Добавить пользователя")
        print("3. Изменить пароль")
        print("4. Изменить роль")
        print("5. Активировать/Деактивировать пользователя")
        print("0. Выход")
        print("="*50)
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            add_user()
        elif choice == '3':
            change_password()
        elif choice == '4':
            change_role()
        elif choice == '5':
            toggle_active()
        elif choice == '0':
            print("\nДо свидания!")
            break
        else:
            print("\nОшибка: неверный выбор")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(0)

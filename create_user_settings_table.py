"""Create user_settings table directly"""
import sqlite3
import os

def create_user_settings_table():
    """Create user_settings table in SQLite database"""
    db_path = "construction.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create user_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key VARCHAR(100) NOT NULL,
                setting_value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE (user_id, setting_key)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_key ON user_settings (setting_key)')
        
        conn.commit()
        conn.close()
        
        print("✅ Таблица user_settings создана успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        return False

if __name__ == "__main__":
    create_user_settings_table()
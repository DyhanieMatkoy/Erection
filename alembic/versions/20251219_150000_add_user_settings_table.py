"""Add user settings table

Revision ID: 20251219_150000
Revises: 20251219_140000
Create Date: 2024-12-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20251219_150000_add_user_settings_table'
down_revision = '20251219_140000_add_table_part_settings'
branch_labels = None
depends_on = None


def upgrade():
    """Add user settings table for application preferences"""
    
    # Create user_settings table if it doesn't exist
    op.execute("""
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
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_key ON user_settings (setting_key)")


def downgrade():
    """Remove user settings table"""
    op.drop_table('user_settings')
"""merge_multiple_heads

Revision ID: e281607a0287
Revises: 20251219_150000_add_user_settings_table, 2e0125e231cb
Create Date: 2026-01-28 00:54:13.880759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e281607a0287'
down_revision: Union[str, Sequence[str], None] = ('20251219_150000_add_user_settings_table', '2e0125e231cb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""Merge branches

Revision ID: 6e8f9b678b09
Revises: 50fb17bd38f9, 53b5b4dbfe35
Create Date: 2026-01-27 16:45:16.008255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e8f9b678b09'
down_revision: Union[str, Sequence[str], None] = ('50fb17bd38f9', '53b5b4dbfe35')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

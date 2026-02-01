"""merge_sync_and_material_branches

Revision ID: 2e0125e231cb
Revises: 7a2e5fef8cdb
Create Date: 2026-01-27 23:16:46.795340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e0125e231cb'
down_revision: Union[str, Sequence[str], None] = '7a2e5fef8cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

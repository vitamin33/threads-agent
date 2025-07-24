"""merge heads

Revision ID: f7a3888941f4
Revises: change_posting_hours_to_json, threads_posts_001
Create Date: 2025-07-25 01:18:07.109025

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "f7a3888941f4"
down_revision: Union[str, Sequence[str], None] = (
    "change_posting_hours_to_json",
    "threads_posts_001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

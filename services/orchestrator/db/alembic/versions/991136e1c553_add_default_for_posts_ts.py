"""add default for posts.ts

Revision ID: 991136e1c553
Revises: 5a6061e08784
Create Date: 2025-07-16 15:32:22.496079

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "991136e1c553"
down_revision: Union[str, Sequence[str], None] = "5a6061e08784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE posts ALTER COLUMN ts SET DEFAULT now();")
    pass


def downgrade() -> None:
    op.execute("ALTER TABLE posts ALTER COLUMN ts DROP DEFAULT;")
    pass

"""change posting_hours to json

Revision ID: change_posting_hours_to_json
Revises: add_experiment_tables
Create Date: 2025-01-23 19:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "change_posting_hours_to_json"
down_revision: Union[str, None] = "add_experiment_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change posting_hours column from Text to JSON
    op.alter_column(
        "experiments",
        "posting_hours",
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_type=sa.Text(),
        postgresql_using="posting_hours::json",
    )


def downgrade() -> None:
    # Change posting_hours column from JSON back to Text
    op.alter_column(
        "experiments",
        "posting_hours",
        type_=sa.Text(),
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        postgresql_using="posting_hours::text",
    )

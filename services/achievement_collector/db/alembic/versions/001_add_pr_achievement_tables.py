"""Add PR achievement tables and metadata column

Revision ID: 001
Revises:
Create Date: 2025-01-28

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_add_pr_achievement_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add metadata column to achievements table
    op.add_column("achievements", sa.Column("metadata", sa.JSON(), nullable=True))

    # Create pr_achievements table
    op.create_table(
        "pr_achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("merge_timestamp", sa.DateTime(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("reviewers", sa.JSON(), nullable=True),
        sa.Column("code_analysis", sa.JSON(), nullable=True),
        sa.Column("impact_analysis", sa.JSON(), nullable=True),
        sa.Column("stories", sa.JSON(), nullable=True),
        sa.Column("ci_metrics", sa.JSON(), nullable=True),
        sa.Column("performance_metrics", sa.JSON(), nullable=True),
        sa.Column("quality_metrics", sa.JSON(), nullable=True),
        sa.Column("posting_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pr_number", name="uq_pr_achievement_number"),
    )
    op.create_index(
        "idx_pr_achievement_merge", "pr_achievements", ["merge_timestamp"], unique=False
    )

    # Create pr_code_changes table
    op.create_table(
        "pr_code_changes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pr_achievement_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("change_type", sa.String(length=50), nullable=True),
        sa.Column("lines_added", sa.Integer(), nullable=True),
        sa.Column("lines_deleted", sa.Integer(), nullable=True),
        sa.Column("complexity_before", sa.Float(), nullable=True),
        sa.Column("complexity_after", sa.Float(), nullable=True),
        sa.Column("key_changes", sa.JSON(), nullable=True),
        sa.Column("patterns_used", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pr_achievement_id"],
            ["pr_achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create pr_kpi_impacts table
    op.create_table(
        "pr_kpi_impacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pr_achievement_id", sa.Integer(), nullable=False),
        sa.Column("kpi_name", sa.String(length=255), nullable=False),
        sa.Column("kpi_category", sa.String(length=100), nullable=False),
        sa.Column("value_before", sa.Float(), nullable=True),
        sa.Column("value_after", sa.Float(), nullable=True),
        sa.Column("improvement_percentage", sa.Float(), nullable=True),
        sa.Column("improvement_absolute", sa.Float(), nullable=True),
        sa.Column("measurement_method", sa.String(length=255), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pr_achievement_id"],
            ["pr_achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_kpi_impact_category", "pr_kpi_impacts", ["kpi_category"], unique=False
    )
    op.create_index(
        "idx_kpi_impact_improvement",
        "pr_kpi_impacts",
        ["improvement_percentage"],
        unique=False,
    )

    # Create pr_evidence table
    op.create_table(
        "pr_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pr_achievement_id", sa.Integer(), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("pr_achievement_id_fk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pr_achievement_id"],
            ["pr_achievements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["pr_achievement_id_fk"],
            ["pr_achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_evidence_type", "pr_evidence", ["evidence_type"], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index("idx_evidence_type", table_name="pr_evidence")
    op.drop_table("pr_evidence")

    op.drop_index("idx_kpi_impact_improvement", table_name="pr_kpi_impacts")
    op.drop_index("idx_kpi_impact_category", table_name="pr_kpi_impacts")
    op.drop_table("pr_kpi_impacts")

    op.drop_table("pr_code_changes")

    op.drop_index("idx_pr_achievement_merge", table_name="pr_achievements")
    op.drop_table("pr_achievements")

    # Drop metadata column from achievements
    op.drop_column("achievements", "metadata")

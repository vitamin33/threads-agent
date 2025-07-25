"""Add achievement collector tables

Revision ID: add_achievement_collector_tables
Revises: threads_posts_001
Create Date: 2025-01-24 23:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_achievement_collector_tables"
down_revision: Union[str, None] = "simple_test"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create achievements table
    op.create_table(
        "achievements",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "feature",
                "optimization",
                "bugfix",
                "infrastructure",
                "documentation",
                "testing",
                "security",
                "performance",
                "architecture",
                name="achievement_category",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("git", "github", "ci", "manual", "api", name="achievement_source"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("impact_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("complexity_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "business_value",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("time_saved_hours", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "performance_improvement_pct",
            sa.Float(),
            server_default="0.0",
            nullable=False,
        ),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
        sa.Column(
            "skills_demonstrated", sa.JSON(), server_default="[]", nullable=False
        ),
        sa.Column("evidence", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("metrics_before", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("metrics_after", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_impact_analysis", sa.Text(), nullable=True),
        sa.Column("ai_technical_analysis", sa.Text(), nullable=True),
        sa.Column(
            "portfolio_ready", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("portfolio_section", sa.String(length=100), nullable=True),
        sa.Column(
            "display_priority", sa.Integer(), server_default="50", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_achievements_category"), "achievements", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_achievements_impact_score"),
        "achievements",
        ["impact_score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_achievements_portfolio_ready"),
        "achievements",
        ["portfolio_ready"],
        unique=False,
    )
    op.create_index(
        op.f("ix_achievements_source_type"),
        "achievements",
        ["source_type"],
        unique=False,
    )

    # Create git_commits table
    op.create_table(
        "git_commits",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.BigInteger(), nullable=True),
        sa.Column("commit_hash", sa.String(length=40), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("author_email", sa.String(length=255), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("branch", sa.String(length=255), nullable=True),
        sa.Column("files_changed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("insertions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deletions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_git_commits_commit_hash"), "git_commits", ["commit_hash"], unique=True
    )

    # Create github_prs table
    op.create_table(
        "github_prs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.BigInteger(), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("merged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("additions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deletions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("changed_files", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("review_comments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("labels", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_github_prs_pr_number"), "github_prs", ["pr_number"], unique=True
    )

    # Create ci_runs table
    op.create_table(
        "ci_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.BigInteger(), nullable=True),
        sa.Column("workflow_name", sa.String(length=255), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("conclusion", sa.String(length=20), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("branch", sa.String(length=255), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ci_runs_run_id"), "ci_runs", ["run_id"], unique=True)

    # Create achievement_templates table
    op.create_table(
        "achievement_templates",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column(
            "default_impact_score", sa.Float(), server_default="50.0", nullable=False
        ),
        sa.Column(
            "default_complexity_score",
            sa.Float(),
            server_default="50.0",
            nullable=False,
        ),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("skills", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_achievement_templates_name"),
        "achievement_templates",
        ["name"],
        unique=True,
    )

    # Create portfolio_snapshots table
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "total_achievements", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "total_impact_score", sa.Float(), server_default="0.0", nullable=False
        ),
        sa.Column(
            "total_value_generated",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("total_time_saved", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("generation_time_seconds", sa.Float(), nullable=False),
        sa.Column("storage_url", sa.Text(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_snapshots_version"),
        "portfolio_snapshots",
        ["version"],
        unique=False,
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index(
        op.f("ix_portfolio_snapshots_version"), table_name="portfolio_snapshots"
    )
    op.drop_table("portfolio_snapshots")

    op.drop_index(
        op.f("ix_achievement_templates_name"), table_name="achievement_templates"
    )
    op.drop_table("achievement_templates")

    op.drop_index(op.f("ix_ci_runs_run_id"), table_name="ci_runs")
    op.drop_table("ci_runs")

    op.drop_index(op.f("ix_github_prs_pr_number"), table_name="github_prs")
    op.drop_table("github_prs")

    op.drop_index(op.f("ix_git_commits_commit_hash"), table_name="git_commits")
    op.drop_table("git_commits")

    op.drop_index(op.f("ix_achievements_source_type"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_portfolio_ready"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_impact_score"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_category"), table_name="achievements")
    op.drop_table("achievements")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS achievement_source")
    op.execute("DROP TYPE IF EXISTS achievement_category")

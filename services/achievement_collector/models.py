"""Achievement Collector Production Database Models.

This module contains the optimized database models for the achievement collector
system with proper indexing and constraints for production use.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


class Achievement(Base):
    """Core achievement record with optimized indexes for sub-200ms queries."""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        Enum(
            "feature",
            "optimization",
            "bugfix",
            "infrastructure",
            "documentation",
            "testing",
            "security",
            "performance",
            "architecture",
            "content",
            "business",
            "milestone",
            name="achievement_category",
        ),
        nullable=False,
        index=True,  # Index for fast category filtering
    )

    # Timing with UTC awareness
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    duration_hours = Column(Float, nullable=False)

    # Impact Metrics with constraints
    impact_score = Column(Float, default=0.0, nullable=False)
    complexity_score = Column(Float, default=0.0, nullable=False)
    business_value = Column(Text)  # Large JSON for AI-generated business value
    time_saved_hours = Column(Float, default=0.0, nullable=False)
    performance_improvement_pct = Column(Float, default=0.0, nullable=False)

    # Source Tracking
    source_type = Column(
        Enum(
            "git",
            "github",
            "github_pr",
            "ci",
            "manual",
            "api",
            "threads",
            "prometheus",
            "webhook",
            name="source_type",
        ),
        nullable=False,
        index=True,  # Index for source filtering
    )
    source_id = Column(String(255), index=True)  # Index for fast lookups
    source_url = Column(String(500))

    # Evidence
    evidence = Column(JSON, default=dict)
    metrics_before = Column(JSON, default=dict)
    metrics_after = Column(JSON, default=dict)

    # Tags & Skills
    tags = Column(JSON, default=list)
    skills_demonstrated = Column(JSON, default=list)

    # AI Analysis
    ai_summary = Column(Text)
    ai_impact_analysis = Column(Text)
    ai_technical_analysis = Column(Text)

    # Portfolio
    portfolio_ready = Column(Boolean, default=False, index=True)
    portfolio_section = Column(String(100))
    display_priority = Column(Integer, default=50)

    # Social Media Publishing
    linkedin_post_id = Column(String(255))
    linkedin_published_at = Column(DateTime(timezone=True))
    github_gist_id = Column(String(255))
    blog_post_url = Column(String(500))

    # Metadata and timestamps
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    git_commits = relationship(
        "GitCommit", back_populates="achievement", cascade="all, delete-orphan"
    )
    github_prs = relationship(
        "GitHubPR", back_populates="achievement", cascade="all, delete-orphan"
    )
    pr_achievements = relationship(
        "PRAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )
    ci_runs = relationship(
        "CIRun", back_populates="achievement", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("idx_achievement_date_category", "completed_at", "category"),
        Index("idx_achievement_impact_date", "impact_score", "completed_at"),
        Index(
            "idx_achievement_portfolio_priority", "portfolio_ready", "display_priority"
        ),
        Index("idx_achievement_source", "source_type", "source_id"),
        # Constraints for data integrity
        CheckConstraint(
            "impact_score >= 0 AND impact_score <= 100", name="check_impact_score_range"
        ),
        CheckConstraint(
            "complexity_score >= 0 AND complexity_score <= 100",
            name="check_complexity_score_range",
        ),
        CheckConstraint(
            "display_priority >= 0 AND display_priority <= 100",
            name="check_display_priority_range",
        ),
        CheckConstraint("duration_hours >= 0", name="check_duration_positive"),
        CheckConstraint("time_saved_hours >= 0", name="check_time_saved_positive"),
        CheckConstraint("completed_at >= started_at", name="check_date_order"),
    )

    @validates("impact_score", "complexity_score")
    def validate_scores(self, key, value):
        """Validate score ranges."""
        if value is not None and (value < 0 or value > 100):
            raise ValueError(f"{key} must be between 0 and 100")
        return value


class PRAchievement(Base):
    """Enhanced PR-specific achievement data with optimized queries."""

    __tablename__ = "pr_achievements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(
        Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )

    # PR Details
    pr_number = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    merge_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    reviewers = Column(JSON, default=list)

    # Comprehensive Analysis
    code_analysis = Column(JSON, default=dict)
    impact_analysis = Column(JSON, default=dict)
    stories = Column(JSON, default=dict)

    # CI/CD Metrics
    ci_metrics = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    quality_metrics = Column(JSON, default=dict)

    # Publishing Metadata
    posting_metadata = Column(JSON, default=dict)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    achievement = relationship("Achievement", back_populates="pr_achievements")
    code_changes = relationship(
        "PRCodeChange", back_populates="pr_achievement", cascade="all, delete-orphan"
    )
    kpi_impacts = relationship(
        "PRKPIImpact", back_populates="pr_achievement", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Indexes for common queries
        Index("idx_pr_achievement_author_date", "author", "merge_timestamp"),
        Index("idx_pr_achievement_number", "pr_number"),
    )


class PRCodeChange(Base):
    """Detailed code changes from PR with language statistics."""

    __tablename__ = "pr_code_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id", ondelete="CASCADE"), nullable=False
    )

    # File info
    file_path = Column(String(500), nullable=False)
    language = Column(String(50), index=True)
    change_type = Column(String(50), index=True)

    # Metrics
    lines_added = Column(Integer, default=0, nullable=False)
    lines_deleted = Column(Integer, default=0, nullable=False)
    complexity_before = Column(Float)
    complexity_after = Column(Float)

    # Analysis
    key_changes = Column(JSON, default=list)
    patterns_used = Column(JSON, default=list)

    # Relationships
    pr_achievement = relationship("PRAchievement", back_populates="code_changes")

    __table_args__ = (
        Index("idx_code_change_language", "language"),
        Index("idx_code_change_type", "change_type"),
        CheckConstraint("lines_added >= 0", name="check_lines_added_positive"),
        CheckConstraint("lines_deleted >= 0", name="check_lines_deleted_positive"),
    )


class PRKPIImpact(Base):
    """KPI impacts from PR changes with confidence tracking."""

    __tablename__ = "pr_kpi_impacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id", ondelete="CASCADE"), nullable=False
    )

    # KPI info
    kpi_name = Column(String(255), nullable=False, index=True)
    kpi_category = Column(String(100), nullable=False, index=True)

    # Impact
    value_before = Column(Float)
    value_after = Column(Float)
    improvement_percentage = Column(Float, index=True)
    improvement_absolute = Column(Float)

    # Context
    measurement_method = Column(String(255))
    confidence_score = Column(Float)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    pr_achievement = relationship("PRAchievement", back_populates="kpi_impacts")

    __table_args__ = (
        Index("idx_kpi_impact_name_category", "kpi_name", "kpi_category"),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 100",
            name="check_confidence_range",
        ),
    )


class GitCommit(Base):
    """Git commit tracking with significance analysis."""

    __tablename__ = "git_commits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))

    sha = Column(String(40), nullable=False, unique=True, index=True)
    message = Column(Text, nullable=False)
    author = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Code changes
    files_changed = Column(Integer, default=0, nullable=False)
    additions = Column(Integer, default=0, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)

    # Analysis
    is_significant = Column(Boolean, default=False, index=True)
    complexity_score = Column(Float, default=0.0)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    achievement = relationship("Achievement", back_populates="git_commits")

    __table_args__ = (
        Index("idx_commit_author_date", "author", "timestamp"),
        CheckConstraint("files_changed >= 0", name="check_files_changed_positive"),
        CheckConstraint("additions >= 0", name="check_additions_positive"),
        CheckConstraint("deletions >= 0", name="check_deletions_positive"),
    )


class GitHubPR(Base):
    """GitHub Pull Request tracking with review metrics."""

    __tablename__ = "github_prs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))

    pr_number = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    state = Column(String(50), nullable=False, index=True)

    # Metrics
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    merged_at = Column(DateTime(timezone=True), index=True)
    review_time_hours = Column(Float)
    comments_count = Column(Integer, default=0, nullable=False)
    commits_count = Column(Integer, default=0, nullable=False)

    # Impact
    files_changed = Column(Integer, default=0, nullable=False)
    additions = Column(Integer, default=0, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)

    # Quality
    tests_passed = Column(Boolean, default=True)
    code_coverage_pct = Column(Float)

    # Relationships
    achievement = relationship("Achievement", back_populates="github_prs")

    __table_args__ = (
        Index("idx_pr_state_date", "state", "created_at"),
        CheckConstraint(
            "code_coverage_pct >= 0 AND code_coverage_pct <= 100",
            name="check_coverage_range",
        ),
    )


class CIRun(Base):
    """CI/CD run tracking with cost analysis."""

    __tablename__ = "ci_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))

    run_id = Column(String(255), nullable=False, unique=True, index=True)
    workflow_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Performance
    tests_total = Column(Integer, default=0, nullable=False)
    tests_passed = Column(Integer, default=0, nullable=False)
    build_time_seconds = Column(Integer)

    # Cost
    compute_cost_dollars = Column(Numeric(10, 4), default=0)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    achievement = relationship("Achievement", back_populates="ci_runs")

    __table_args__ = (
        Index("idx_ci_run_status_date", "status", "started_at"),
        CheckConstraint("tests_passed <= tests_total", name="check_tests_valid"),
        CheckConstraint("compute_cost_dollars >= 0", name="check_cost_positive"),
    )


# Support Tables


class AchievementTemplate(Base):
    """Templates for common achievement types."""

    __tablename__ = "achievement_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=False, index=True)

    # Template content
    title_template = Column(String(500), nullable=False)
    description_template = Column(Text, nullable=False)

    # Default metrics
    default_impact_score = Column(Float, default=50.0)
    default_complexity_score = Column(Float, default=50.0)

    # Required evidence
    required_evidence = Column(JSON, default=list)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PortfolioSnapshot(Base):
    """Generated portfolio snapshots with versioning."""

    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Snapshot info
    version = Column(String(50), nullable=False)
    format = Column(
        Enum("markdown", "pdf", "html", "json", name="portfolio_format"),
        nullable=False,
    )

    # Content
    content = Column(Text, nullable=False)
    snapshot_metadata = Column(JSON, default=dict)

    # Stats at time of generation
    total_achievements = Column(Integer, default=0, nullable=False)
    total_impact_score = Column(Float, default=0.0)
    total_value_generated = Column(Numeric(12, 2), default=0)
    total_time_saved = Column(Float, default=0.0)

    # Generation details
    generated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    generation_time_seconds = Column(Float)

    # Storage
    storage_url = Column(String(500))

    __table_args__ = (
        UniqueConstraint("version", "format", name="uq_portfolio_version_format"),
        Index("idx_portfolio_generated", "generated_at"),
    )


class PREvidence(Base):
    """Evidence and artifacts from PR."""

    __tablename__ = "pr_evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id", ondelete="CASCADE"), nullable=False
    )

    # Evidence info
    evidence_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Storage
    file_path = Column(String(500))
    url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Metadata
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_evidence_pr_type", "pr_achievement_id", "evidence_type"),
    )

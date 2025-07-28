# Achievement Collector Database Models

from datetime import datetime

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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship

Base = declarative_base()


class Achievement(Base):
    """Core achievement record"""

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
    )

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    duration_hours = Column(Float, nullable=False)

    # Impact Metrics
    impact_score = Column(Float, default=0.0)  # 0-100 calculated score
    complexity_score = Column(Float, default=0.0)  # 0-100 technical complexity
    business_value = Column(String(255))  # Business value description
    time_saved_hours = Column(Float, default=0.0)  # Hours saved per month
    performance_improvement_pct = Column(Float, default=0.0)  # Performance gain %

    # Source Tracking
    source_type = Column(
        Enum(
            "git",
            "github",
            "ci",
            "manual",
            "api",
            "threads",
            "prometheus",
            "webhook",
            name="source_type",
        ),
        nullable=False,
    )
    source_id = Column(String(255))  # PR number, commit SHA, etc.
    source_url = Column(String(500))  # Link to PR, commit, etc.

    # Evidence
    evidence = Column(JSON, default=dict)  # Screenshots, metrics, logs
    metrics_before = Column(JSON, default=dict)  # Baseline metrics
    metrics_after = Column(JSON, default=dict)  # Post-implementation metrics

    # Tags & Skills
    tags = Column(JSON, default=list)  # ["kubernetes", "python", "optimization"]
    skills_demonstrated = Column(JSON, default=list)  # Technical skills used

    # AI Analysis
    ai_summary = Column(Text)  # AI-generated professional summary
    ai_impact_analysis = Column(Text)  # AI analysis of business impact
    ai_technical_analysis = Column(Text)  # AI analysis of technical approach

    # Portfolio
    portfolio_ready = Column(Boolean, default=False)
    portfolio_section = Column(String(100))  # Which portfolio section
    display_priority = Column(Integer, default=50)  # 0-100, higher = more prominent

    # Social Media Publishing
    linkedin_post_id = Column(String(255))  # LinkedIn post ID after publishing
    linkedin_published_at = Column(DateTime)  # When published to LinkedIn
    github_gist_id = Column(String(255))  # GitHub gist ID for detailed writeup
    blog_post_url = Column(String(500))  # URL if published as blog post

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)  # Additional flexible storage

    # Relationships
    git_commits: Mapped[list["GitCommit"]] = relationship(
        "GitCommit", back_populates="achievement"
    )
    github_prs: Mapped[list["GitHubPR"]] = relationship(
        "GitHubPR", back_populates="achievement"
    )
    pr_achievements: Mapped[list["PRAchievement"]] = relationship(
        "PRAchievement", back_populates="achievement"
    )
    ci_runs: Mapped[list["CIRun"]] = relationship("CIRun", back_populates="achievement")

    # Indexes
    __table_args__ = (
        Index("idx_achievement_category", "category"),
        Index("idx_achievement_impact", "impact_score"),
        Index("idx_achievement_date", "completed_at"),
        Index("idx_achievement_portfolio", "portfolio_ready", "display_priority"),
    )


class GitCommit(Base):
    """Git commit tracking"""

    __tablename__ = "git_commits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"))

    sha = Column(String(40), nullable=False, unique=True)
    message = Column(Text, nullable=False)
    author = Column(String(255), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    # Code changes
    files_changed = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    # Analysis
    is_significant = Column(Boolean, default=False)
    complexity_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="git_commits"
    )


class GitHubPR(Base):
    """GitHub Pull Request tracking"""

    __tablename__ = "github_prs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"))

    pr_number = Column(Integer, nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    state = Column(String(50), nullable=False)  # open, closed, merged

    # Metrics
    created_at = Column(DateTime, nullable=False)
    merged_at = Column(DateTime)
    review_time_hours = Column(Float)
    comments_count = Column(Integer, default=0)
    commits_count = Column(Integer, default=0)

    # Impact
    files_changed = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    # Quality
    tests_passed = Column(Boolean, default=True)
    code_coverage_pct = Column(Float)

    # Relationships
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="github_prs"
    )


class CIRun(Base):
    """CI/CD run tracking"""

    __tablename__ = "ci_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"))

    run_id = Column(String(255), nullable=False, unique=True)
    workflow_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # success, failure, cancelled

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Performance
    tests_total = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    build_time_seconds = Column(Integer)

    # Cost
    compute_cost_dollars = Column(Numeric(10, 4), default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="ci_runs"
    )


class AchievementTemplate(Base):
    """Templates for common achievement types"""

    __tablename__ = "achievement_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=False)

    # Template content
    title_template = Column(String(500), nullable=False)
    description_template = Column(Text, nullable=False)

    # Default metrics
    default_impact_score = Column(Float, default=50.0)
    default_complexity_score = Column(Float, default=50.0)

    # Required evidence
    required_evidence = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PortfolioSnapshot(Base):
    """Generated portfolio snapshots"""

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
    total_achievements = Column(Integer, default=0)
    total_impact_score = Column(Float, default=0.0)
    total_value_generated = Column(Numeric(12, 2), default=0)
    total_time_saved = Column(Float, default=0.0)

    # Generation details
    generated_at = Column(DateTime, default=datetime.utcnow)
    generation_time_seconds = Column(Float)

    # Storage
    storage_url = Column(String(500))  # S3, GCS, etc.

    __table_args__ = (
        UniqueConstraint("version", "format", name="uq_portfolio_version_format"),
    )


class PRAchievement(Base):
    """Enhanced PR-specific achievement data"""

    __tablename__ = "pr_achievements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)

    # PR Details
    pr_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    merge_timestamp = Column(DateTime, nullable=False)
    author = Column(String(255), nullable=False)
    reviewers = Column(JSON, default=list)  # List of reviewer usernames

    # Comprehensive Analysis
    code_analysis = Column(JSON, default=dict)  # From comprehensive analyzer
    impact_analysis = Column(JSON, default=dict)  # Performance, business, quality
    stories = Column(JSON, default=dict)  # Generated stories by persona

    # CI/CD Metrics
    ci_metrics = Column(JSON, default=dict)  # Build times, test results
    performance_metrics = Column(JSON, default=dict)  # Benchmarks, profiling
    quality_metrics = Column(JSON, default=dict)  # Coverage, complexity

    # Publishing Metadata
    posting_metadata = Column(JSON, default=dict)  # Platform-specific info

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="pr_achievements"
    )
    code_changes: Mapped[list["PRCodeChange"]] = relationship(
        "PRCodeChange", back_populates="pr_achievement"
    )
    kpi_impacts: Mapped[list["PRKPIImpact"]] = relationship(
        "PRKPIImpact", back_populates="pr_achievement"
    )

    __table_args__ = (
        UniqueConstraint("pr_number", name="uq_pr_achievement_number"),
        Index("idx_pr_achievement_merge", "merge_timestamp"),
    )


class PRCodeChange(Base):
    """Detailed code changes from PR"""

    __tablename__ = "pr_code_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id"), nullable=False
    )

    # File info
    file_path = Column(String(500), nullable=False)
    language = Column(String(50))
    change_type = Column(String(50))  # feature, bugfix, refactor, test, docs

    # Metrics
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    complexity_before = Column(Float)
    complexity_after = Column(Float)

    # Analysis
    key_changes = Column(JSON, default=list)  # Important modifications
    patterns_used = Column(JSON, default=list)  # Design patterns

    # Relationships
    pr_achievement: Mapped["PRAchievement"] = relationship(
        "PRAchievement", back_populates="code_changes"
    )


class PRKPIImpact(Base):
    """KPI impacts from PR changes"""

    __tablename__ = "pr_kpi_impacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id"), nullable=False
    )

    # KPI info
    kpi_name = Column(String(255), nullable=False)
    kpi_category = Column(String(100), nullable=False)  # performance, business, quality

    # Impact
    value_before = Column(Float)
    value_after = Column(Float)
    improvement_percentage = Column(Float)
    improvement_absolute = Column(Float)

    # Context
    measurement_method = Column(String(255))  # How it was measured
    confidence_score = Column(Float)  # 0-100 confidence in measurement

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pr_achievement: Mapped["PRAchievement"] = relationship(
        "PRAchievement", back_populates="kpi_impacts"
    )

    __table_args__ = (
        Index("idx_kpi_impact_category", "kpi_category"),
        Index("idx_kpi_impact_improvement", "improvement_percentage"),
    )


class PREvidence(Base):
    """Evidence and artifacts from PR"""

    __tablename__ = "pr_evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_achievement_id = Column(
        Integer, ForeignKey("pr_achievements.id"), nullable=False
    )

    # Evidence info
    evidence_type = Column(String(50), nullable=False)  # screenshot, graph, diagram
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Storage
    file_path = Column(String(500))
    url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Metadata
    metadata = Column(JSON, default=dict)  # Additional info
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pr_achievement_id_fk = Column(Integer, ForeignKey("pr_achievements.id"))

    __table_args__ = (Index("idx_evidence_type", "evidence_type"),)

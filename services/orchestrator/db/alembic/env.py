# services/orchestrator/db/alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool

# ── logging --------------------------------------------------------------
fileConfig(context.config.config_file_name)  # type: ignore[arg-type]

# ── import Base ----------------------------------------------------------
# At runtime we’re “inside” db/alembic/, so go three dirs up → repo root.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.orchestrator.db import Base  # noqa: E402

target_metadata: MetaData = Base.metadata
target_metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "pk": "pk_%(table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

db_url = (
    os.getenv("POSTGRES_DSN")
    or context.config.get_main_option("db_url")
    or context.config.get_main_option("sqlalchemy.url")
)

if not db_url:
    raise RuntimeError("❌  Set POSTGRES_DSN or db_url or sqlalchemy.url")


def run_migrations_offline() -> None:
    """Generate SQL files without DB connection (CI autogen)."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # 👉 safe for future table refactors
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations inside the Helm Job."""
    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,  # SQLA 2.x style
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detect column type changes
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

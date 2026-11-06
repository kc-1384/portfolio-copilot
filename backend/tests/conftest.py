"""Shared test fixtures.

Database tests run against a separate `<db>_test` database that is created fresh, migrated with
Alembic, and dropped at the end — your real data is never touched. If PostgreSQL isn't running,
those tests are skipped locally; in CI (REQUIRE_DB=1) they fail instead, so they can't be silently
skipped.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    settings = get_settings()
    test_db = f"{settings.postgres_db}_test"
    # Connect to the built-in "postgres" database to create/drop the test database.
    admin = create_engine(
        settings.database_url_for("postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{test_db}"'))
    except OperationalError as exc:
        if os.environ.get("REQUIRE_DB") == "1":
            raise
        pytest.skip(f"PostgreSQL not reachable, skipping database tests ({exc.orig})")

    test_url = settings.database_url_for(test_db)
    alembic_cfg = Config(BACKEND_DIR / "alembic.ini")
    alembic_cfg.attributes["database_url"] = test_url
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(test_url)
    yield engine

    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back after each test, so tests don't affect each other."""
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()

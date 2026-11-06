"""Alembic environment: connects migrations to our models and database settings."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import URL, create_engine, pool

from app.core.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares the database against these tables.
target_metadata = Base.metadata

# TimescaleDB creates these time indexes itself when a table becomes a hypertable. They aren't in
# our models, so without this autogenerate would keep trying to drop them.
TIMESCALE_INDEXES = {"prices_daily_date_idx", "prices_intraday_ts_idx"}


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    return not (type_ == "index" and reflected and name in TIMESCALE_INDEXES)


def database_url() -> URL:
    # Tests pass a URL for the separate test database through config.attributes.
    url = config.attributes.get("database_url")
    return url if url is not None else get_settings().database_url


def run_migrations_offline() -> None:
    """Write the SQL to the screen instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=database_url().render_as_string(hide_password=False),
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply the migrations."""
    engine = create_engine(database_url(), poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

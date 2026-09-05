"""LandSight AI - Alembic Environment Configuration with PostGIS Support."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Add project root and backend to sys.path
backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

# Load .env file
load_dotenv(root_dir / ".env")
load_dotenv(backend_dir / ".env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL dynamically from environment
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Arul%402007@localhost:5432/landsight_ai"
)
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# Import models to ensure all tables are registered in Base.metadata
from backend.app.database import Base  # noqa: E402
import backend.app.models  # noqa: E402, F401

target_metadata = Base.metadata

# Ignore PostGIS internal system tables during autogenerate and migrations
POSTGIS_INTERNAL_TABLES = {
    "spatial_ref_sys",
    "geometry_columns",
    "geography_columns",
    "raster_columns",
    "raster_overviews",
}


def include_object(object, name, type_, reflected, compare_to):
    """Filter out PostGIS internal tables from Alembic diffs."""
    if type_ == "table" and name in POSTGIS_INTERNAL_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    from sqlalchemy import create_engine
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
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

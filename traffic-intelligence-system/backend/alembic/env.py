"""Alembic reads our models and the DATABASE_URL so `alembic revision --autogenerate` works."""
from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401
from app.core.config import settings
from app.database.session import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata

# PostGIS owns these tables; never let Alembic touch them.
POSTGIS_TABLES = {"spatial_ref_sys", "geometry_columns", "geography_columns"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and name in POSTGIS_TABLES)


def run_migrations_offline():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata,
                      literal_binds=True, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.",
                                poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

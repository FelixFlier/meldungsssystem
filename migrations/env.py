"""
Alembic migration environment script.
Updated to support both sync and async SQLAlchemy.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add base directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models and config
from database import Base, engine
from config import get_settings
from models import User, Incident, AuditLog

# Load Alembic config
config = context.config

# Override sqlalchemy.url from database settings
url = config.get_main_option("sqlalchemy.url")
if not url or url == '':
    # Use settings if no URL in alembic.ini
    settings = get_settings()
    # Use standard SQLite URL instead of aiosqlite for Alembic
    db_url = settings.DATABASE_URL
    if db_url.startswith('sqlite+aiosqlite:'):
        db_url = db_url.replace('sqlite+aiosqlite:', 'sqlite:')
    config.set_main_option("sqlalchemy.url", db_url)

# Logger configuration
fileConfig(config.config_file_name)

# Metadata object used for ORM classes
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Use standard engine configuration for migrations
    # This works for both sync and async setups
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
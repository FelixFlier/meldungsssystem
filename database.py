"""
Database configuration and session management.
Uses SQLAlchemy 2.0 async API for database operations.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, MetaData, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pathlib import Path
import os
import asyncio

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Import configuration
from config import get_settings
settings = get_settings()

# Create metadata with naming conventions for constraints
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# Create declarative base with metadata
Base = declarative_base(metadata=metadata)

# Convert SQLite URL to async format if needed
db_url = settings.DATABASE_URL
if db_url.startswith('sqlite:'):
    # For SQLite, use aiosqlite
    db_url_async = db_url.replace('sqlite:', 'sqlite+aiosqlite:')
else:
    db_url_async = db_url

# Create async engine
engine = create_async_engine(
    db_url_async,
    echo=settings.DEBUG,
    future=True,  # Use SQLAlchemy 2.0 API
    pool_pre_ping=True,  # Verify connections before using them
)

# Also create a sync engine for synchronous operations
sync_engine = create_engine(
    db_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Create async session factory
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Create sync session factory
sync_session_factory = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autoflush=False
)

# Dependency for getting async database session
async def get_db():
    """Async dependency for getting a database session."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()

# For synchronous operations (compatibility)
def get_db_sync():
    """Synchronous version of get_db for compatibility."""
    session = sync_session_factory()
    try:
        yield session
    finally:
        session.close()

# Create database tables asynchronously
async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Synchronous function to create tables (for direct import in sync code)
def create_tables_sync():
    """Create all database tables synchronously."""
    Base.metadata.create_all(sync_engine)

# Run this when using from the command line
if __name__ == "__main__":
    asyncio.run(create_tables())
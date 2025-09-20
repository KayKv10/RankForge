# src/rankforge/db/session.py

"""Database session management."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# For Development and Testing, SQLite is used as the database.
# In production, this can be replaced with PostgreSQL or another database.
DATABASE_URL = "sqlite+aiosqlite:///./rankforge.db"

# The engine is the core interface to the database.
engine = create_async_engine(DATABASE_URL)

# Create a configured "Session" class.
# autocommit=False: Transactions are committed manually.
# autoflush=False: Changes are not flushed to the database until explicitly committed.
# expire_on_commit=False: Objects remain accessible after commit.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from pros.src.config.settings import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Database:
    """Database connection manager."""
    
    def __init__(self, url: str | None = None):
        self.url = url or settings.database.url
        self.engine = create_async_engine(
            self.url,
            echo=settings.database.echo,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def create_tables(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic commit/rollback."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()


# Global database instance
_db: Database | None = None


async def get_db() -> AsyncGenerator[Database, None]:
    """Get the database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.create_tables()
    yield _db


async def init_db() -> Database:
    """Initialize the database."""
    global _db
    if _db is None:
        _db = Database()
        await _db.create_tables()
    return _db


async def close_db() -> None:
    """Close the database."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None

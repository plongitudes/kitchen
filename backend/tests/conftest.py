"""
Pytest configuration and shared fixtures for testing.

This module provides:
- Database fixtures for creating/tearing down test databases
- FastAPI client fixtures for API testing
- Authentication fixtures for testing protected endpoints
- Common test data factories

Environment variables:
- TEST_DATABASE_URL: Sync database URL (default: sqlite:///:memory:)
- TEST_DATABASE_URL_ASYNC: Async database URL (default: sqlite+aiosqlite:///:memory:)

To run tests against PostgreSQL (required for backup tests):
    TEST_DATABASE_URL=postgresql://admin:changeme@localhost:5432/roanes_kitchen_test
    TEST_DATABASE_URL_ASYNC=postgresql+asyncpg://admin:changeme@localhost:5432/roanes_kitchen_test
"""

import os
import uuid as uuid_module

# Read test database URLs from environment (default to SQLite for fast unit tests)
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
TEST_DATABASE_URL_ASYNC = os.environ.get("TEST_DATABASE_URL_ASYNC", "sqlite+aiosqlite:///:memory:")

# Detect if we're using SQLite
USING_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

# IMPORTANT: Monkey-patch UUID ONLY when using SQLite
# This ensures SQLite compatibility for PostgreSQL UUID columns
if USING_SQLITE:
    import sqlalchemy.dialects.postgresql as pg_dialect
    from sqlalchemy import String, TypeDecorator

    class SQLiteUUID(TypeDecorator):
        """UUID type that works with SQLite by storing UUIDs as 36-char strings."""

        impl = String
        cache_ok = True

        def __init__(self, *args, **_kwargs):
            # Ignore UUID-specific args
            super().__init__()
            self.impl = String(36)

        def process_bind_param(self, value, _dialect):
            """Convert UUID to string for SQLite."""
            if value is None:
                return value
            if isinstance(value, uuid_module.UUID):
                return str(value)
            return str(value)

        def process_result_value(self, value, _dialect):
            """Convert string back to UUID."""
            if value is None:
                return value
            if isinstance(value, uuid_module.UUID):
                return value
            return uuid_module.UUID(value)

    # Replace PostgreSQL UUID globally before models are loaded
    pg_dialect.UUID = SQLiteUUID

# Now safe to import everything else
# flake8: noqa: E402
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import Base, get_db
from app.core.config import get_settings
from app.core.security import create_access_token

settings = get_settings()


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine (SQLite or PostgreSQL based on TEST_DATABASE_URL)."""
    # Import models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.recipe import Recipe, RecipeIngredient, RecipeInstruction
    from app.models.ingredient import CommonIngredient, IngredientAlias
    from app.models.meal_plan import MealPlanInstance, GroceryList, GroceryListItem
    from app.models.schedule import (
        ScheduleSequence,
        WeekTemplate,
        WeekDayAssignment,
        SequenceWeekMapping,
    )
    from app.models.settings import Settings

    if USING_SQLITE:
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL - no special connection args needed
        engine = create_engine(TEST_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def async_db_engine():
    """Create an async test database engine (SQLite or PostgreSQL based on TEST_DATABASE_URL_ASYNC).

    For SQLite: Uses async operations for schema since :memory: DB is connection-specific.
    For PostgreSQL: Uses sync operations to avoid event loop conflicts with asyncpg.
    """
    import asyncio

    # Import models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.recipe import Recipe, RecipeIngredient, RecipeInstruction
    from app.models.ingredient import CommonIngredient, IngredientAlias
    from app.models.meal_plan import MealPlanInstance, GroceryList, GroceryListItem
    from app.models.schedule import (
        ScheduleSequence,
        WeekTemplate,
        WeekDayAssignment,
        SequenceWeekMapping,
    )
    from app.models.settings import Settings

    if USING_SQLITE:
        # SQLite :memory: needs same connection for all ops, use async throughout
        async_engine = create_async_engine(
            TEST_DATABASE_URL_ASYNC,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create tables asynchronously for SQLite
        async def create_tables():
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.get_event_loop().run_until_complete(create_tables())

        yield async_engine

        # Drop tables asynchronously for SQLite
        async def drop_tables():
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await async_engine.dispose()

        asyncio.get_event_loop().run_until_complete(drop_tables())
    else:
        # PostgreSQL - use sync engine for schema management to avoid event loop issues
        async_engine = create_async_engine(TEST_DATABASE_URL_ASYNC)
        sync_engine = create_engine(TEST_DATABASE_URL)

        # Create all tables synchronously
        Base.metadata.create_all(bind=sync_engine)

        yield async_engine

        # Drop all tables synchronously
        Base.metadata.drop_all(bind=sync_engine)
        sync_engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async test database session."""
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def async_client(async_db_engine) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with async database dependency.

    Note: Uses a fresh session for each request to avoid event loop conflicts
    when running against PostgreSQL with asyncpg.
    """
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user in the database."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass123"),
        discord_user_id=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user) -> str:
    """Generate a valid JWT token for the test user."""
    return create_access_token(
        data={"user_id": str(test_user.id), "username": test_user.username}
    )


@pytest.fixture
def authenticated_client(client: TestClient, test_user_token: str) -> TestClient:
    """Create an authenticated test client with JWT token in headers."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}",
    }
    return client


@pytest.fixture
def second_test_user(db_session: Session):
    """Create a second test user for multi-user scenarios."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="alice",
        password_hash=get_password_hash("alicepass123"),
        discord_user_id="123456789",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
async def async_test_user(async_db_session: AsyncSession):
    """Create an async test user in the database."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass123"),
        discord_user_id=None,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
def async_test_user_token(async_test_user) -> str:
    """Generate a valid JWT token for the async test user."""
    return create_access_token(
        data={"user_id": str(async_test_user.id), "username": async_test_user.username}
    )


@pytest.fixture
def async_authenticated_client(
    async_client: TestClient, async_test_user_token: str
) -> TestClient:
    """Create an async authenticated test client with JWT token in headers."""
    async_client.headers = {
        **async_client.headers,
        "Authorization": f"Bearer {async_test_user_token}",
    }
    return async_client


@pytest.fixture
async def async_second_test_user(async_db_session: AsyncSession):
    """Create a second async test user for multi-user scenarios."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="alice",
        password_hash=get_password_hash("alicepass123"),
        discord_user_id="123456789",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user

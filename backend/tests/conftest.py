"""
Pytest configuration and shared fixtures for testing.

This module provides:
- Database fixtures for creating/tearing down test databases
- FastAPI client fixtures for API testing
- Authentication fixtures for testing protected endpoints
- Common test data factories
"""

# IMPORTANT: Monkey-patch UUID BEFORE any other imports
# This ensures SQLite compatibility for PostgreSQL UUID columns
import sqlalchemy.dialects.postgresql as pg_dialect
from sqlalchemy import String, TypeDecorator
import uuid as uuid_module

class SQLiteUUID(TypeDecorator):
    """UUID type that works with SQLite by storing UUIDs as 36-char strings."""
    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        # Ignore UUID-specific args
        super().__init__()
        self.impl = String(36)

    def process_bind_param(self, value, dialect):
        """Convert UUID to string for SQLite."""
        if value is None:
            return value
        if isinstance(value, uuid_module.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        """Convert string back to UUID."""
        if value is None:
            return value
        if isinstance(value, uuid_module.UUID):
            return value
        return uuid_module.UUID(value)

# Replace PostgreSQL UUID globally before models are loaded
pg_dialect.UUID = SQLiteUUID

# Now safe to import everything else
import os
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

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///:memory:"

settings = get_settings()


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine with SQLite in-memory."""
    # Import models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.recipe import Recipe, RecipeIngredient, RecipeInstruction
    from app.models.ingredient import CommonIngredient, IngredientAlias
    from app.models.meal_plan import MealPlanInstance, GroceryList, GroceryListItem
    from app.models.schedule import ScheduleSequence, WeekTemplate, WeekDayAssignment, SequenceWeekMapping
    from app.models.settings import Settings

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
async def async_db_engine():
    """Create an async test database engine with SQLite in-memory."""
    # Import models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.recipe import Recipe, RecipeIngredient, RecipeInstruction
    from app.models.ingredient import CommonIngredient, IngredientAlias
    from app.models.meal_plan import MealPlanInstance, GroceryList, GroceryListItem
    from app.models.schedule import ScheduleSequence, WeekTemplate, WeekDayAssignment, SequenceWeekMapping
    from app.models.settings import Settings

    engine = create_async_engine(
        TEST_DATABASE_URL_ASYNC,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


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
def async_client(async_db_session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with async database dependency."""

    async def override_get_db():
        try:
            yield async_db_session
        finally:
            pass

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
def async_authenticated_client(async_client: TestClient, async_test_user_token: str) -> TestClient:
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

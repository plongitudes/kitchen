#!/usr/bin/env python3
"""Seed development data for Roanes Kitchen.

Creates a default test user for development environments only.
ONLY runs when ENVIRONMENT=development.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.user import User


async def seed_dev_user():
    """Create default test user for development."""
    settings = get_settings()

    # Safety check: only run in development
    if settings.environment != "development":
        print(f"⚠️  Skipping dev user creation - environment is '{settings.environment}' (not 'development')")
        return

    print("🌱 Seeding development data...")

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Check if demo user already exists
            result = await session.execute(
                select(User).where(User.username == "demo")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("✅ Demo user already exists - skipping creation")
                return

            # Create demo user
            hashed_password = get_password_hash("demo1234")
            demo_user = User(
                username="demo",
                password_hash=hashed_password,
            )

            session.add(demo_user)
            await session.commit()
            await session.refresh(demo_user)

            print("✅ Created development test user")
            print(f"   Username: demo")
            print(f"   Password: demo1234")
            print(f"   User ID: {demo_user.id}")

    except Exception as e:
        print(f"❌ Error seeding development data: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_dev_user())

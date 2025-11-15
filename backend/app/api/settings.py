"""Settings API endpoints for global application configuration."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.settings import Settings
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Response model for settings."""

    id: str
    discord_bot_token: Optional[str] = None
    notification_channel_id: Optional[str] = None
    notification_time: str
    notification_timezone: str


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""

    discord_bot_token: Optional[str] = None
    notification_channel_id: Optional[str] = None
    notification_time: Optional[str] = None
    notification_timezone: Optional[str] = None


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get global application settings.

    Returns the current settings or creates default settings if none exist.
    """
    result = await db.execute(select(Settings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = Settings(
            notification_time="07:00",
            notification_timezone="UTC",
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SettingsResponse(
        id=str(settings.id),
        discord_bot_token=settings.discord_bot_token if settings.discord_bot_token else None,
        notification_channel_id=settings.notification_channel_id,
        notification_time=settings.notification_time,
        notification_timezone=settings.notification_timezone,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(
    updates: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update global application settings.

    Only updates fields that are provided in the request.
    """
    result = await db.execute(select(Settings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create new settings if none exist
        settings = Settings(
            discord_bot_token=updates.discord_bot_token,
            notification_channel_id=updates.notification_channel_id,
            notification_time=updates.notification_time or "07:00",
            notification_timezone=updates.notification_timezone or "UTC",
        )
        db.add(settings)
    else:
        # Update existing settings
        if updates.discord_bot_token is not None:
            settings.discord_bot_token = updates.discord_bot_token
        if updates.notification_channel_id is not None:
            settings.notification_channel_id = updates.notification_channel_id
        if updates.notification_time is not None:
            settings.notification_time = updates.notification_time
        if updates.notification_timezone is not None:
            settings.notification_timezone = updates.notification_timezone

    await db.commit()
    await db.refresh(settings)

    return SettingsResponse(
        id=str(settings.id),
        discord_bot_token=settings.discord_bot_token if settings.discord_bot_token else None,
        notification_channel_id=settings.notification_channel_id,
        notification_time=settings.notification_time,
        notification_timezone=settings.notification_timezone,
    )

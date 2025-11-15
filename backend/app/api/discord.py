"""Discord API endpoints for bot status and user synchronization."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.core.deps import get_current_user
from app.models.user import User
from app.services.discord_service import get_bot

router = APIRouter(prefix="/discord", tags=["discord"])


class DiscordStatusResponse(BaseModel):
    """Response for Discord bot status."""

    connected: bool
    channel_id: Optional[int] = None
    bot_username: Optional[str] = None


class SyncUserRequest(BaseModel):
    """Request to sync Discord user ID with app user."""

    discord_user_id: str


class SyncUserResponse(BaseModel):
    """Response for user sync."""

    success: bool
    message: str


class TestMessageRequest(BaseModel):
    """Request to send a test message."""

    message: str


class ChannelInfo(BaseModel):
    """Discord channel information."""

    id: str
    name: str
    guild_name: str
    position: int


class ChannelsResponse(BaseModel):
    """Response with list of Discord channels."""

    channels: list[ChannelInfo]


@router.get("/status", response_model=DiscordStatusResponse)
async def get_discord_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get Discord bot connection status.

    Returns bot connection state and configuration.
    """
    bot = get_bot()

    return DiscordStatusResponse(
        connected=bot.is_connected(),
        channel_id=bot.channel_id,
        bot_username=bot.bot.user.name if bot.bot and bot.bot.user else None,
    )


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_discord_user(
    request: SyncUserRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Link Discord user ID to the current app user.

    This allows the system to mention the correct Discord user in notifications.

    Note: In MVP, this stores the Discord ID but doesn't persist it yet.
    This will be implemented when user table schema is extended.
    """
    # TODO: Store discord_user_id in user table once schema is updated
    # For now, just validate the request

    if not request.discord_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord user ID cannot be empty",
        )

    return SyncUserResponse(
        success=True,
        message=f"Discord user ID {request.discord_user_id} linked to {current_user.username} (Note: Persistence not yet implemented in MVP)",
    )


@router.post("/test-message")
async def send_test_message(
    request: TestMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a test message to the configured Discord channel.

    Useful for testing bot connectivity.
    """
    bot = get_bot()

    if not bot.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discord bot is not connected. Check configuration and restart.",
        )

    success = await bot.send_message(request.message)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message to Discord",
        )

    return {"success": True, "message": "Test message sent successfully"}


@router.get("/channels", response_model=ChannelsResponse)
async def get_discord_channels(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of Discord channels the bot has access to.

    Requires bot to be connected. Returns channels from all guilds
    the bot is a member of, sorted by guild name and position.
    """
    bot = get_bot()

    if not bot.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discord bot is not connected. Configure bot token and restart.",
        )

    channels = await bot.fetch_channels()

    return ChannelsResponse(channels=channels)

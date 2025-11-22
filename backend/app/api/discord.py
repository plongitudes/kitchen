"""Discord API endpoints for bot status and user synchronization."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.meal_plan import MealAssignment, GroceryList
from app.models.recipe import Recipe
from app.services.discord_service import get_bot
from app.services.notification_messages import build_notification_message
from app.core.config import get_settings

settings = get_settings()

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
    db: AsyncSession = Depends(get_db),
):
    """
    Link Discord user ID to the current app user.

    This allows the system to @mention the user in Discord notifications.
    """
    if not request.discord_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord user ID cannot be empty",
        )

    # Update user's Discord ID
    current_user.discord_user_id = request.discord_user_id
    await db.commit()
    await db.refresh(current_user)

    return SyncUserResponse(
        success=True,
        message=f"Discord user ID linked! You'll now be @mentioned in notifications.",
    )


@router.post("/test-message")
async def send_test_message(
    request: TestMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a test message to the configured Discord channel.

    In development/staging environments, uses test_channel_id if configured,
    otherwise falls back to the main notification_channel_id.

    Useful for testing bot connectivity.
    """
    bot = get_bot()

    if not bot.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discord bot is not connected. Check configuration and restart.",
        )

    # In dev/staging, use test channel if configured
    channel_id = None
    if settings.environment in ["development", "staging"] and settings.discord_test_channel_id:
        channel_id = int(settings.discord_test_channel_id)

    success = await bot.send_message(request.message, channel_id=channel_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message to Discord",
        )

    channel_type = "test" if channel_id else "production"
    return {
        "success": True,
        "message": f"Test message sent successfully to {channel_type} channel"
    }


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


@router.post("/reconnect")
async def reconnect_discord_bot(
    current_user: User = Depends(get_current_user),
):
    """
    Reconnect Discord bot with updated environment variables.

    After updating DISCORD_BOT_TOKEN or channel IDs in .env file,
    use this endpoint to reconnect the bot without restarting the app.

    Returns:
        Success message with connection status
    """
    # Invalidate settings cache to re-read .env
    get_settings.cache_clear()
    fresh_settings = get_settings()

    # Get credentials from env vars
    discord_token = fresh_settings.discord_bot_token
    discord_channel_id = fresh_settings.discord_notification_channel_id

    if not discord_token or not discord_channel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord credentials not configured. Set DISCORD_BOT_TOKEN and DISCORD_NOTIFICATION_CHANNEL_ID in .env file."
        )

    bot = get_bot()

    try:
        # Stop existing bot if running
        if bot.is_running:
            await bot.stop()

        # Start with new credentials
        await bot.start(
            token=discord_token,
            channel_id=int(discord_channel_id)
        )

        return {
            "success": True,
            "message": f"Discord bot reconnected successfully (channel: {discord_channel_id})",
            "connected": bot.is_connected()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reconnect Discord bot: {str(e)}"
        )


@router.post("/test-notifications")
async def send_test_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send real notification dry-run to the test channel.

    Queries for actual meal assignments from the database and sends
    real notifications using the same message logic as the scheduler.
    Useful for testing notification formatting and Discord integration.
    """
    bot = get_bot()

    if not bot.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discord bot is not connected. Check configuration and restart.",
        )

    # In dev/staging, use test channel if configured
    channel_id = None
    if settings.environment in ["development", "staging"] and settings.discord_test_channel_id:
        channel_id = int(settings.discord_test_channel_id)

    # Get bot name for signatures
    bot_name = bot.bot.user.name if bot.bot and bot.bot.user else 'Kitchen Bot'

    # Get meal plan instances to test with
    from app.services.meal_plan_service import MealPlanService
    from app.models.meal_plan import MealPlanInstance
    from app.models.schedule import WeekTemplate
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(MealPlanInstance)
        .options(
            selectinload(MealPlanInstance.week_template).selectinload(WeekTemplate.day_assignments)
        )
        .limit(5)
    )
    instances = result.scalars().all()

    if not instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meal plan instances found. Create a meal plan first to test notifications."
        )

    notifications_sent = 0
    max_notifications = 10  # Limit total notifications for testing

    try:
        # Process instances and send sample notifications
        for instance in instances:
            if notifications_sent >= max_notifications:
                break

            # Try each day of the week to find notifiable assignments
            for day_of_week in range(7):
                if notifications_sent >= max_notifications:
                    break

                # Get merged assignments for this day
                assignments_with_data = await MealPlanService.get_merged_assignments_for_day(
                    db=db,
                    instance=instance,
                    day_of_week=day_of_week,
                )

                for assignment, user, recipe in assignments_with_data:
                    if notifications_sent >= max_notifications:
                        break

                    # Skip non-notifiable actions
                    if assignment.action in ["rest", "leftovers"]:
                        continue

                    # Skip if user not found
                    if not user:
                        continue

                    # For shop actions, find the grocery list for that day
                    grocery_list_id = None
                    if assignment.action == "shop":
                        from datetime import timedelta
                        shopping_date = instance.instance_start_date + timedelta(days=day_of_week)
                        grocery_list_result = await db.execute(
                            select(GroceryList)
                            .where(GroceryList.meal_plan_instance_id == instance.id)
                            .where(GroceryList.shopping_date == shopping_date)
                        )
                        grocery_list = grocery_list_result.scalar_one_or_none()
                        if grocery_list:
                            grocery_list_id = str(grocery_list.id)

                    # Build notification message using shared logic
                    message = build_notification_message(
                        user=user,
                        assignment=assignment,
                        recipe=recipe,
                        frontend_url=settings.frontend_url,
                        bot_name=bot_name,
                        grocery_list_id=grocery_list_id,
                    )

                    # Send to test channel
                    success = await bot.send_message(message, channel_id=channel_id)
                    if not success:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to send one or more test notifications",
                        )

                    notifications_sent += 1

        channel_type = "test" if channel_id else "production"
        return {
            "success": True,
            "message": f"Sent {notifications_sent} real notification(s) to {channel_type} channel"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notifications: {str(e)}"
        )

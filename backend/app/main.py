from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.api import auth, recipes, schedules, meal_plans, discord, backup, templates, ingredients
from app.api import settings as settings_api
from app.core.deps import get_current_user
from app.models.user import User
from app.services.discord_service import get_bot
from app.services.scheduler_service import start_scheduler, stop_scheduler
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    logger.info("Starting application lifespan...")
    # Startup: Initialize Discord bot from environment variables
    try:
        # Read Discord credentials from environment variables only
        discord_token = settings.discord_bot_token
        discord_channel_id = settings.discord_notification_channel_id

        # Initialize bot if we have credentials
        if discord_token and discord_channel_id:
            bot = get_bot()
            try:
                await bot.start(
                    token=discord_token,
                    channel_id=int(discord_channel_id)
                )
                logger.info(f"Discord bot initialized successfully (channel: {discord_channel_id})")
            except Exception as e:
                logger.error(f"Failed to initialize Discord bot: {e}")
        else:
            logger.info("Discord bot not configured - set DISCORD_BOT_TOKEN and DISCORD_NOTIFICATION_CHANNEL_ID in .env")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

    # Start scheduler
    try:
        await start_scheduler()
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

    yield

    # Shutdown: Stop scheduler and Discord bot
    try:
        await stop_scheduler()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

    try:
        bot = get_bot()
        await bot.stop()
        logger.info("Discord bot stopped")
    except Exception as e:
        logger.error(f"Error stopping Discord bot: {e}")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(templates.router)
app.include_router(schedules.router)
app.include_router(meal_plans.router)
app.include_router(ingredients.router)
app.include_router(discord.router)
app.include_router(settings_api.router)
app.include_router(backup.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Protected endpoint - get current user info."""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "discord_user_id": current_user.discord_user_id,
        "created_at": current_user.created_at,
    }

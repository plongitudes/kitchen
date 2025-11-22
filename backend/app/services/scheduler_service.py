"""Scheduler service for automated notifications and week advancement."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from app.db.session import AsyncSessionLocal
from app.models.settings import Settings
from app.models.schedule import ScheduleSequence, WeekTemplate, SequenceWeekMapping
from app.models.meal_plan import MealPlanInstance, GroceryList
from app.services.discord_service import get_bot
from app.services.schedule_service import ScheduleService
from app.services.meal_plan_service import MealPlanService
from app.services.notification_messages import build_notification_message

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
last_notification_date = None


async def check_and_send_notifications():
    """Check if it's time to send daily notifications."""
    global last_notification_date

    async with AsyncSessionLocal() as session:
        # Get settings
        result = await session.execute(select(Settings).limit(1))
        settings = result.scalar_one_or_none()

        if not settings:
            return

        # Convert to configured timezone
        tz = ZoneInfo(settings.notification_timezone)
        now = datetime.now(tz)
        today = now.date()

        # Check if already notified today
        if last_notification_date == today:
            return

        # Parse notification time
        notify_hour, notify_minute = map(int, settings.notification_time.split(":"))

        # Check if current time matches notification time (within 5 minutes)
        if now.hour == notify_hour and abs(now.minute - notify_minute) < 5:
            await send_daily_notifications(session, today)
            last_notification_date = today


async def send_daily_notifications(session: AsyncSession, date):
    """Send all notifications for today's events and shopping."""
    from app.models.user import User
    from app.models.recipe import Recipe
    from app.core.config import get_settings

    bot = get_bot()
    settings = get_settings()

    # Calculate day of week (0=Sunday, 6=Saturday)
    day_of_week = date.weekday()
    if day_of_week == 6:  # Python's weekday: Monday=0, Sunday=6
        day_of_week = 0  # Convert to our format: Sunday=0
    else:
        day_of_week += 1  # Monday=1, Tuesday=2, etc.

    # Get active meal plan instances for today (with eager loading for relationships)
    result = await session.execute(
        select(MealPlanInstance)
        .options(
            selectinload(MealPlanInstance.week_template).selectinload(WeekTemplate.day_assignments)
        )
        .where(MealPlanInstance.instance_start_date <= date)
    )
    instances = result.scalars().all()

    # Filter to instances where today falls within the week (start_date to start_date + 6 days)
    from datetime import timedelta

    active_instances = [
        inst
        for inst in instances
        if inst.instance_start_date
        <= date
        <= inst.instance_start_date + timedelta(days=6)
    ]

    if not active_instances:
        logger.info(f"No active meal plan instances for {date}")
        return

    # Get bot name for signatures
    bot_name = bot.bot.user.name if bot.bot and bot.bot.user else 'Kitchen Bot'

    # Process each instance
    for instance in active_instances:
        # Get merged assignments (template + overrides) for this day
        assignments_with_data = await MealPlanService.get_merged_assignments_for_day(
            db=session,
            instance=instance,
            day_of_week=day_of_week,
        )

        for assignment, user, recipe in assignments_with_data:
            # Skip non-notifiable actions
            if assignment.action in ["rest", "leftovers"]:
                continue

            # Skip if user not found
            if not user:
                continue

            # For shop actions, find the grocery list for today
            grocery_list_id = None
            if assignment.action == "shop":
                grocery_list_result = await session.execute(
                    select(GroceryList)
                    .where(GroceryList.meal_plan_instance_id == instance.id)
                    .where(GroceryList.shopping_date == date)
                )
                grocery_list = grocery_list_result.scalar_one_or_none()
                if grocery_list:
                    grocery_list_id = str(grocery_list.id)

            # Build notification message
            message = build_notification_message(
                user=user,
                assignment=assignment,
                recipe=recipe,
                frontend_url=settings.frontend_url,
                bot_name=bot_name,
                grocery_list_id=grocery_list_id,
            )

            await bot.send_message(message)
            logger.info(
                f"Sent {assignment.action} notification to {user.username} for {date}"
            )

    logger.info(f"Completed daily notifications for {date}")


async def advance_week():
    """Advance to next week for all active sequences."""
    async with AsyncSessionLocal() as session:
        # Get all sequences
        result = await session.execute(select(ScheduleSequence))
        sequences = result.scalars().all()

        bot = get_bot()

        for sequence in sequences:
            try:
                # Get active template mappings for this sequence
                mappings = await ScheduleService.get_active_templates_for_sequence(
                    db=session, sequence_id=sequence.id
                )

                if not mappings:
                    logger.warning(f"No active templates for sequence {sequence.id}")
                    continue

                # Calculate current position
                current_position = sequence.current_week_index % len(mappings)

                # Find current mapping
                current_mapping = None
                for mapping in mappings:
                    if (
                        mapping.position == current_position + 1
                    ):  # positions are 1-based
                        current_mapping = mapping
                        break

                if not current_mapping:
                    logger.error(
                        f"Could not find current mapping for sequence {sequence.id}"
                    )
                    continue

                # Check if current template is retired - if so, skip creating instance
                if current_mapping.week_template.retired_at:
                    logger.info(
                        f"Skipping retired template {current_mapping.week_template_id} for sequence {sequence.id}"
                    )
                    # Just advance the index, don't create instance
                    sequence.current_week_index = (current_position + 1) % len(mappings)
                    await session.commit()
                    continue

                # Get the most recent instance to calculate next start date
                current_instance = await MealPlanService.get_current_instance(
                    db=session, sequence_id=sequence.id
                )

                # Calculate next start date
                if current_instance:
                    next_start_date = current_instance.instance_start_date + timedelta(
                        days=7
                    )
                else:
                    # No previous instance, start today
                    next_start_date = datetime.now().date()

                # Advance to next week index
                next_position = (current_position + 1) % len(mappings)
                sequence.current_week_index = next_position

                # Find next mapping
                next_mapping = None
                for mapping in mappings:
                    if mapping.position == next_position + 1:  # positions are 1-based
                        next_mapping = mapping
                        break

                if not next_mapping:
                    logger.error(
                        f"Could not find next mapping for sequence {sequence.id}"
                    )
                    continue

                # Create new instance for next week
                new_instance = await MealPlanService.create_instance(
                    db=session,
                    template_id=next_mapping.week_template_id,
                    instance_start_date=next_start_date,
                    sequence_id=sequence.id,
                )

                await session.commit()

                # Send notification
                template_name = next_mapping.week_template.name
                await bot.send_message(
                    f"🔄 **Week Advanced**\n\n"
                    f"Sequence: {sequence.name}\n"
                    f"New Template: {template_name}\n"
                    f"Position: {next_position + 1}/{len(mappings)}\n"
                    f"Start Date: {next_start_date}"
                )
                logger.info(
                    f"Advanced sequence {sequence.id} to position {next_position}"
                )

            except Exception as e:
                logger.error(f"Error advancing sequence {sequence.id}: {e}")
                continue


def configure_scheduler():
    """Configure scheduler jobs based on settings."""
    # Notification check every 5 minutes
    scheduler.add_job(
        check_and_send_notifications,
        CronTrigger(minute="*/5"),
        id="notification_check",
        replace_existing=True,
    )

    # Week advancement - default Sunday at midnight
    scheduler.add_job(
        advance_week,
        CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="week_advancement",
        replace_existing=True,
    )

    logger.info("Scheduler configured")


async def start_scheduler():
    """Start the scheduler."""
    configure_scheduler()
    scheduler.start()
    logger.info("Scheduler started")


async def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")

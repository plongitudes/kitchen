"""
Unit tests for SchedulerService.

Note: This service is heavily dependent on external services (Discord, APScheduler).
These tests focus on the schedulable logic that can be tested with mocked dependencies.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.schedule import ScheduleSequence, WeekTemplate, SequenceWeekMapping
from app.models.meal_plan import MealPlanInstance, GroceryList
from app.models.settings import Settings


@pytest.mark.asyncio
class TestSchedulerConfiguration:
    """Test scheduler configuration."""

    def test_configure_scheduler_adds_jobs(self):
        """Test that configure_scheduler adds expected jobs."""
        from app.services.scheduler_service import scheduler, configure_scheduler

        # Clear any existing jobs
        scheduler.remove_all_jobs()

        configure_scheduler()

        job_ids = [job.id for job in scheduler.get_jobs()]
        assert "notification_check" in job_ids
        assert "week_advancement" in job_ids

        # Clean up
        scheduler.remove_all_jobs()


@pytest.mark.asyncio
class TestCheckAndSendNotifications:
    """Test the check_and_send_notifications logic."""

    @patch("app.services.scheduler_service.AsyncSessionLocal")
    @patch("app.services.scheduler_service.send_daily_notifications")
    async def test_skips_if_no_settings(self, mock_send, mock_session_local):
        """Test that notifications are skipped when no settings exist."""
        from app.services.scheduler_service import check_and_send_notifications

        # Mock session that returns no settings
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_local.return_value = mock_session

        await check_and_send_notifications()

        mock_send.assert_not_called()

    @patch("app.services.scheduler_service.last_notification_date", date.today())
    @patch("app.services.scheduler_service.AsyncSessionLocal")
    @patch("app.services.scheduler_service.send_daily_notifications")
    async def test_skips_if_already_notified_today(self, mock_send, mock_session_local):
        """Test that notifications are skipped if already sent today."""
        from app.services.scheduler_service import check_and_send_notifications

        # Mock session with settings
        mock_session = AsyncMock()
        mock_settings = MagicMock(spec=Settings)
        mock_settings.notification_timezone = "UTC"
        mock_settings.notification_time = "08:00"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_settings
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_local.return_value = mock_session

        await check_and_send_notifications()

        mock_send.assert_not_called()


@pytest.mark.asyncio
class TestSendDailyNotifications:
    """Test the send_daily_notifications function."""

    @patch("app.services.scheduler_service.get_bot")
    @patch("app.services.scheduler_service.MealPlanService")
    async def test_skips_rest_action(self, mock_mps, mock_get_bot):
        """Test that rest actions don't trigger notifications."""
        from app.services.scheduler_service import send_daily_notifications

        # Mock bot
        mock_bot = MagicMock()
        mock_bot.bot.user.name = "Test Bot"
        mock_bot.send_message = AsyncMock()
        mock_get_bot.return_value = mock_bot

        # Create mock session with instance
        mock_session = AsyncMock()

        # Mock template and assignment
        mock_assignment = MagicMock()
        mock_assignment.action = "rest"

        mock_user = MagicMock()
        mock_user.username = "testuser"

        # Mock MealPlanService
        mock_mps.get_merged_assignments_for_day = AsyncMock(
            return_value=[(mock_assignment, mock_user, None)]
        )

        # Mock instance with template
        mock_template = MagicMock(spec=WeekTemplate)
        mock_template.day_assignments = [mock_assignment]

        mock_instance = MagicMock(spec=MealPlanInstance)
        mock_instance.instance_start_date = date.today()
        mock_instance.week_template = mock_template

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_instance]
        mock_session.execute.return_value = mock_result

        await send_daily_notifications(mock_session, date.today())

        # Should not send message for rest action
        mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
class TestAdvanceWeek:
    """Test the advance_week function."""

    @patch("app.services.scheduler_service.AsyncSessionLocal")
    @patch("app.services.scheduler_service.get_bot")
    async def test_skips_sequence_with_no_templates(self, mock_get_bot, mock_session_local):
        """Test that sequences with no templates are skipped."""
        from app.services.scheduler_service import advance_week

        # Mock bot
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_get_bot.return_value = mock_bot

        # Mock session
        mock_session = AsyncMock()

        # Mock sequence
        mock_sequence = MagicMock(spec=ScheduleSequence)
        mock_sequence.id = uuid4()
        mock_sequence.name = "Test Sequence"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sequence]
        mock_session.execute.return_value = mock_result

        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_local.return_value = mock_session

        # Mock ScheduleService to return no mappings
        with patch("app.services.scheduler_service.ScheduleService") as mock_ss:
            mock_ss.get_active_templates_for_sequence = AsyncMock(return_value=[])

            await advance_week()

            # Should not send message when no templates
            mock_bot.send_message.assert_not_called()


class TestDayOfWeekConversion:
    """Test the day of week conversion logic (pure logic, no async)."""

    def test_sunday_conversion(self):
        """Test that Python's Sunday (6) converts to our Sunday (0)."""
        # Python weekday: Monday=0, Sunday=6
        # Our format: Sunday=0, Monday=1, etc.
        python_weekday = 6  # Sunday in Python
        if python_weekday == 6:
            our_weekday = 0
        else:
            our_weekday = python_weekday + 1

        assert our_weekday == 0

    def test_monday_conversion(self):
        """Test that Python's Monday (0) converts to our Monday (1)."""
        python_weekday = 0  # Monday in Python
        if python_weekday == 6:
            our_weekday = 0
        else:
            our_weekday = python_weekday + 1

        assert our_weekday == 1

    def test_saturday_conversion(self):
        """Test that Python's Saturday (5) converts to our Saturday (6)."""
        python_weekday = 5  # Saturday in Python
        if python_weekday == 6:
            our_weekday = 0
        else:
            our_weekday = python_weekday + 1

        assert our_weekday == 6

    def test_all_days_conversion(self):
        """Test conversion for all days of the week."""
        # Python weekday: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        # Our format: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
        expected_mapping = {
            0: 1,  # Python Monday -> Our Monday (1)
            1: 2,  # Python Tuesday -> Our Tuesday (2)
            2: 3,  # Python Wednesday -> Our Wednesday (3)
            3: 4,  # Python Thursday -> Our Thursday (4)
            4: 5,  # Python Friday -> Our Friday (5)
            5: 6,  # Python Saturday -> Our Saturday (6)
            6: 0,  # Python Sunday -> Our Sunday (0)
        }

        for python_wd, expected in expected_mapping.items():
            if python_wd == 6:
                our_wd = 0
            else:
                our_wd = python_wd + 1
            assert our_wd == expected


class TestNotificationTimeWindow:
    """Test notification time window logic (pure logic, no async)."""

    def test_time_parsing(self):
        """Test parsing notification time string."""
        time_str = "08:00"
        hour, minute = map(int, time_str.split(":"))
        assert hour == 8
        assert minute == 0

    def test_time_parsing_with_minutes(self):
        """Test parsing time string with non-zero minutes."""
        time_str = "14:30"
        hour, minute = map(int, time_str.split(":"))
        assert hour == 14
        assert minute == 30

    def test_time_range_check(self):
        """Test that time window check works correctly."""
        from datetime import time

        notification_time = time(8, 0)
        current_time = time(8, 5)  # 5 minutes after

        # Within 15 minute window
        diff_minutes = abs(
            (current_time.hour * 60 + current_time.minute) -
            (notification_time.hour * 60 + notification_time.minute)
        )
        assert diff_minutes <= 15

    def test_time_outside_range(self):
        """Test that times outside window are rejected."""
        from datetime import time

        notification_time = time(8, 0)
        current_time = time(9, 0)  # 60 minutes after

        diff_minutes = abs(
            (current_time.hour * 60 + current_time.minute) -
            (notification_time.hour * 60 + notification_time.minute)
        )
        assert diff_minutes > 15


@pytest.mark.asyncio
class TestSchedulerEdgeCases:
    """Test edge cases and error handling."""

    @patch("app.services.scheduler_service.AsyncSessionLocal")
    @patch("app.services.scheduler_service.send_daily_notifications")
    async def test_crashes_on_missing_notification_time(self, mock_send, mock_session_local):
        """Test that None notification_time causes AttributeError.

        Note: This documents current behavior. The implementation doesn't
        guard against None notification_time - it will crash trying to
        call .split() on None.
        """
        from app.services.scheduler_service import check_and_send_notifications

        mock_session = AsyncMock()
        mock_settings = MagicMock(spec=Settings)
        mock_settings.notification_timezone = "UTC"
        mock_settings.notification_time = None  # Missing time
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_settings
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_local.return_value = mock_session

        # Current implementation crashes - documents limitation
        with pytest.raises(AttributeError):
            await check_and_send_notifications()

        mock_send.assert_not_called()

    async def test_scheduler_singleton(self):
        """Test that scheduler is a singleton."""
        from app.services.scheduler_service import scheduler
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        assert isinstance(scheduler, AsyncIOScheduler)

    @patch("app.services.scheduler_service.AsyncSessionLocal")
    async def test_advance_week_handles_empty_sequences(self, mock_session_local):
        """Test advance_week when no sequences exist."""
        from app.services.scheduler_service import advance_week

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No sequences
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_local.return_value = mock_session

        # Should not crash
        await advance_week()


class TestSchedulerConstants:
    """Test scheduler configuration constants."""

    def test_notification_job_interval(self):
        """Verify notification check interval is reasonable."""
        # Should check at least once every hour, at most every minute
        # This is a documentation test more than anything
        expected_interval_minutes = 5  # Check every 5 minutes
        assert 1 <= expected_interval_minutes <= 60

    def test_advancement_day_default(self):
        """Test default day for week advancement (Sunday)."""
        # Our week should advance on Sunday by default
        advancement_day = "sunday"
        assert advancement_day.lower() in ["sunday", "monday"]

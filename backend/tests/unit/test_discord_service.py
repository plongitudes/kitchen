"""
Unit tests for discord_service module.

Tests focus on NotificationFormatter (pure functions) and basic DiscordBot
state management. Actual Discord API calls are not tested here.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from enum import Enum

from app.services.discord_service import (
    DiscordBot,
    NotificationFormatter,
    get_bot,
)


class TestNotificationFormatterActionNotification:
    """Tests for NotificationFormatter.format_action_notification()."""

    def test_cook_with_recipe(self):
        """Test cooking action with recipe name."""
        result = NotificationFormatter.format_action_notification(
            day_name="Monday",
            person_name="Bob",
            action="cook",
            recipe_name="Tikka Masala",
        )

        assert "Monday" in result
        assert "Bob" in result
        assert "cooking" in result
        assert "Tikka Masala" in result
        assert "**" in result  # Bold formatting

    def test_cook_without_recipe(self):
        """Test cooking action without recipe name."""
        result = NotificationFormatter.format_action_notification(
            day_name="Monday",
            person_name="Bob",
            action="cook",
            recipe_name=None,
        )

        assert "Monday" in result
        assert "Bob" in result
        assert "cooking" in result

    def test_shop_action(self):
        """Test shopping action."""
        result = NotificationFormatter.format_action_notification(
            day_name="Sunday",
            person_name="Alice",
            action="shop",
        )

        assert "Sunday" in result
        assert "Alice" in result
        assert "shopping" in result

    def test_takeout_action(self):
        """Test takeout action."""
        result = NotificationFormatter.format_action_notification(
            day_name="Friday",
            person_name="Bob",
            action="takeout",
        )

        assert "Friday" in result
        assert "Bob" in result
        assert "takeout" in result

    def test_rest_action(self):
        """Test rest day action."""
        result = NotificationFormatter.format_action_notification(
            day_name="Saturday",
            person_name="Alice",
            action="rest",
        )

        assert "Saturday" in result
        assert "Alice" in result
        assert "rest" in result

    def test_leftovers_action(self):
        """Test leftovers action."""
        result = NotificationFormatter.format_action_notification(
            day_name="Tuesday",
            person_name="Bob",
            action="leftovers",
        )

        assert "Tuesday" in result
        assert "Bob" in result
        assert "leftovers" in result

    def test_unknown_action(self):
        """Test unknown action falls back to action name."""
        result = NotificationFormatter.format_action_notification(
            day_name="Wednesday",
            person_name="Alice",
            action="mystery",
        )

        assert "Wednesday" in result
        assert "Alice" in result
        assert "mystery" in result

    def test_case_insensitive_action(self):
        """Test action matching is case-insensitive."""
        result = NotificationFormatter.format_action_notification(
            day_name="Monday",
            person_name="Bob",
            action="COOK",
            recipe_name="Pasta",
        )

        assert "cooking" in result


class TestNotificationFormatterShoppingNotification:
    """Tests for NotificationFormatter.format_shopping_notification()."""

    def test_basic_shopping_list(self):
        """Test basic shopping list formatting."""
        items = [
            {"ingredient_name": "Onions", "total_quantity": 2, "unit": "whole"},
            {"ingredient_name": "Garlic", "total_quantity": 4, "unit": "cloves"},
        ]

        result = NotificationFormatter.format_shopping_notification(
            shopping_date="Monday, Nov 25",
            items=items,
        )

        assert "Shopping List" in result
        assert "Monday, Nov 25" in result
        assert "Onions" in result
        assert "Garlic" in result
        assert "Total items: 2" in result

    def test_empty_shopping_list(self):
        """Test empty shopping list."""
        result = NotificationFormatter.format_shopping_notification(
            shopping_date="Sunday",
            items=[],
        )

        assert "Shopping List" in result
        assert "Total items: 0" in result

    def test_item_with_enum_unit(self):
        """Test handling enum unit values."""
        # Create a mock enum
        class MockUnit(Enum):
            CUP = "cup"

        items = [
            {"ingredient_name": "Flour", "total_quantity": 2, "unit": MockUnit.CUP},
        ]

        result = NotificationFormatter.format_shopping_notification(
            shopping_date="Monday",
            items=items,
        )

        assert "cup" in result
        assert "Flour" in result

    def test_item_missing_fields(self):
        """Test handling items with missing fields."""
        items = [
            {"ingredient_name": "Salt"},  # Missing quantity and unit
            {"total_quantity": 1},  # Missing name and unit
        ]

        result = NotificationFormatter.format_shopping_notification(
            shopping_date="Monday",
            items=items,
        )

        assert "Total items: 2" in result


class TestNotificationFormatterWeekTransition:
    """Tests for NotificationFormatter.format_week_transition()."""

    def test_basic_week_transition(self):
        """Test basic week transition formatting."""
        assignments = [
            {"person_name": "Bob", "days": ["Monday", "Wednesday"]},
            {"person_name": "Alice", "days": ["Thursday", "Friday"]},
        ]

        result = NotificationFormatter.format_week_transition(
            theme_name="Burger Week",
            week_number=3,
            assignments_summary=assignments,
        )

        assert "Burger Week" in result
        assert "Week 3" in result
        assert "Bob" in result
        assert "Alice" in result
        assert "Monday" in result
        assert "Wednesday" in result

    def test_single_assignment(self):
        """Test week transition with single assignment."""
        assignments = [
            {"person_name": "Bob", "days": ["Monday"]},
        ]

        result = NotificationFormatter.format_week_transition(
            theme_name="Taco Week",
            week_number=1,
            assignments_summary=assignments,
        )

        assert "Taco Week" in result
        assert "Bob" in result
        assert "Monday" in result

    def test_empty_assignments(self):
        """Test week transition with no assignments."""
        result = NotificationFormatter.format_week_transition(
            theme_name="Rest Week",
            week_number=5,
            assignments_summary=[],
        )

        assert "Rest Week" in result
        assert "Week 5" in result

    def test_assignment_with_empty_days(self):
        """Test assignment with empty days list."""
        assignments = [
            {"person_name": "Bob", "days": []},
        ]

        result = NotificationFormatter.format_week_transition(
            theme_name="Test Week",
            week_number=1,
            assignments_summary=assignments,
        )

        # Bob should not appear since they have no days
        assert "Test Week" in result


class TestNotificationFormatterTemplateRetirement:
    """Tests for NotificationFormatter.format_template_retirement()."""

    def test_retirement_no_affected_sequences(self):
        """Test retirement with no affected sequences."""
        result = NotificationFormatter.format_template_retirement(
            template_name="Old Week",
            affected_sequences=[],
        )

        assert "Old Week" in result
        assert "retired" in result
        assert "🗑️" in result

    def test_retirement_single_sequence(self):
        """Test retirement with single affected sequence."""
        affected = [
            {"sequence_name": "Main Rotation", "old_position": 3, "new_position": 4},
        ]

        result = NotificationFormatter.format_template_retirement(
            template_name="Burger Week",
            affected_sequences=affected,
        )

        assert "Burger Week" in result
        assert "1 schedule" in result  # Singular
        assert "Main Rotation" in result
        assert "3" in result
        assert "4" in result

    def test_retirement_multiple_sequences(self):
        """Test retirement with multiple affected sequences."""
        affected = [
            {"sequence_name": "Main Rotation", "old_position": 3, "new_position": 4},
            {"sequence_name": "Summer Menu", "old_position": 2, "new_position": 3},
        ]

        result = NotificationFormatter.format_template_retirement(
            template_name="Burger Week",
            affected_sequences=affected,
        )

        assert "Burger Week" in result
        assert "2 schedules" in result  # Plural
        assert "Main Rotation" in result
        assert "Summer Menu" in result


class TestDiscordBotState:
    """Tests for DiscordBot state management."""

    def test_initial_state(self):
        """Test bot initial state."""
        bot = DiscordBot()

        assert bot.bot is None
        assert bot.channel_id is None
        assert bot.is_running is False
        assert bot._bot_task is None

    def test_is_connected_when_not_running(self):
        """Test is_connected returns False when not running."""
        bot = DiscordBot()

        assert bot.is_connected() is False

    def test_is_connected_with_no_bot(self):
        """Test is_connected returns falsy with no bot."""
        bot = DiscordBot()
        bot.is_running = True
        bot.bot = None

        assert not bot.is_connected()


class TestDiscordBotSendMessage:
    """Tests for DiscordBot.send_message() edge cases."""

    @pytest.mark.asyncio
    async def test_send_message_not_running(self):
        """Test send_message returns False when bot not running."""
        bot = DiscordBot()

        result = await bot.send_message("Hello")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_no_channel_id(self):
        """Test send_message returns False when no channel configured."""
        bot = DiscordBot()
        bot.is_running = True
        bot.bot = MagicMock()
        bot.channel_id = None

        result = await bot.send_message("Hello")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_with_override_channel(self):
        """Test send_message uses override channel_id when provided."""
        bot = DiscordBot()
        bot.is_running = True
        bot.channel_id = 111  # Default channel

        mock_bot = MagicMock()
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        mock_bot.fetch_channel = AsyncMock(return_value=mock_channel)
        bot.bot = mock_bot

        result = await bot.send_message("Hello", channel_id=222)  # Override

        # Should use the override channel, not the default
        mock_bot.fetch_channel.assert_called_with(222)


class TestDiscordBotFetchChannels:
    """Tests for DiscordBot.fetch_channels()."""

    @pytest.mark.asyncio
    async def test_fetch_channels_not_running(self):
        """Test fetch_channels returns empty list when not running."""
        bot = DiscordBot()

        result = await bot.fetch_channels()

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_channels_with_guilds(self):
        """Test fetch_channels returns channel info."""
        bot = DiscordBot()
        bot.is_running = True

        # Mock guild and channel
        mock_channel = MagicMock()
        mock_channel.id = 123456789
        mock_channel.name = "general"
        mock_channel.position = 0

        mock_guild = MagicMock()
        mock_guild.name = "Test Server"
        mock_guild.text_channels = [mock_channel]

        mock_bot = MagicMock()
        mock_bot.guilds = [mock_guild]
        bot.bot = mock_bot

        result = await bot.fetch_channels()

        assert len(result) == 1
        assert result[0]["name"] == "general"
        assert result[0]["guild_name"] == "Test Server"
        assert result[0]["id"] == "123456789"


class TestGetBot:
    """Tests for get_bot() singleton."""

    def test_returns_discord_bot(self):
        """Test get_bot returns a DiscordBot instance."""
        bot = get_bot()

        assert isinstance(bot, DiscordBot)

    def test_returns_same_instance(self):
        """Test get_bot returns the same instance on multiple calls."""
        bot1 = get_bot()
        bot2 = get_bot()

        assert bot1 is bot2

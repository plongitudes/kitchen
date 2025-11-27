"""Unit tests for notification_messages module."""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.notification_messages import (
    build_user_mention,
    build_cook_notification,
    build_shop_notification,
    build_takeout_notification,
    build_generic_notification,
    build_notification_message,
)


# Test fixtures
@pytest.fixture
def user_with_discord():
    """User with Discord ID."""
    user = MagicMock()
    user.username = "alice"
    user.discord_user_id = "123456789"
    return user


@pytest.fixture
def user_without_discord():
    """User without Discord ID."""
    user = MagicMock()
    user.username = "bob"
    user.discord_user_id = None
    return user


@pytest.fixture
def recipe():
    """Mock recipe."""
    recipe = MagicMock()
    recipe.id = uuid4()
    recipe.name = "Spaghetti Carbonara"
    return recipe


@pytest.fixture
def cook_assignment(recipe):
    """Mock cook assignment."""
    assignment = MagicMock()
    assignment.action = "cook"
    assignment.recipe_id = recipe.id
    return assignment


@pytest.fixture
def shop_assignment():
    """Mock shop assignment."""
    assignment = MagicMock()
    assignment.action = "shop"
    assignment.recipe_id = None
    return assignment


@pytest.fixture
def takeout_assignment():
    """Mock takeout assignment."""
    assignment = MagicMock()
    assignment.action = "takeout"
    assignment.recipe_id = None
    return assignment


@pytest.fixture
def leftovers_assignment():
    """Mock leftovers assignment."""
    assignment = MagicMock()
    assignment.action = "leftovers"
    assignment.recipe_id = None
    return assignment


class TestBuildUserMention:
    """Tests for build_user_mention()."""

    def test_with_discord_id(self, user_with_discord):
        """Returns Discord mention format when user has Discord ID."""
        result = build_user_mention(user_with_discord)
        assert result == "<@123456789>"

    def test_without_discord_id(self, user_without_discord):
        """Returns username when user has no Discord ID."""
        result = build_user_mention(user_without_discord)
        assert result == "bob"

    def test_empty_discord_id(self):
        """Returns username when Discord ID is empty string."""
        user = MagicMock()
        user.username = "charlie"
        user.discord_user_id = ""
        result = build_user_mention(user)
        # Empty string is falsy, so should return username
        assert result == "charlie"


class TestBuildCookNotification:
    """Tests for build_cook_notification()."""

    def test_with_recipe(self, user_with_discord, cook_assignment, recipe):
        """Includes recipe name and link when recipe provided."""
        result = build_cook_notification(
            user_with_discord,
            cook_assignment,
            recipe,
            "https://kitchen.example.com",
            "KitchenBot",
        )

        assert "<@123456789>" in result
        assert "cooking" in result
        assert "Spaghetti Carbonara" in result
        assert f"/recipes/{cook_assignment.recipe_id}" in result
        assert "KitchenBot" in result

    def test_without_recipe(self, user_with_discord, cook_assignment):
        """Uses fallback text when no recipe provided."""
        result = build_cook_notification(
            user_with_discord,
            cook_assignment,
            None,  # No recipe
            "https://kitchen.example.com",
            "Chef",
        )

        assert "your recipe" in result
        assert "/meal-plans" in result
        assert "Chef" in result

    def test_with_recipe_but_no_assignment_recipe_id(self, user_without_discord):
        """Uses fallback when assignment has no recipe_id."""
        assignment = MagicMock()
        assignment.action = "cook"
        assignment.recipe_id = None

        recipe = MagicMock()
        recipe.name = "Test Recipe"

        result = build_cook_notification(
            user_without_discord,
            assignment,
            recipe,
            "https://example.com",
            "Bot",
        )

        # Should use fallback since assignment.recipe_id is None
        assert "your recipe" in result
        assert "/meal-plans" in result

    def test_uses_username_without_discord(self, user_without_discord, cook_assignment, recipe):
        """Uses username when user has no Discord ID."""
        result = build_cook_notification(
            user_without_discord,
            cook_assignment,
            recipe,
            "https://example.com",
            "Bot",
        )

        assert "bob" in result
        assert "<@" not in result


class TestBuildShopNotification:
    """Tests for build_shop_notification()."""

    def test_with_grocery_list_id(self, user_with_discord, shop_assignment):
        """Links to specific grocery list when ID provided."""
        grocery_id = str(uuid4())
        result = build_shop_notification(
            user_with_discord,
            shop_assignment,
            "https://kitchen.example.com",
            "ShopBot",
            grocery_list_id=grocery_id,
        )

        assert "<@123456789>" in result
        assert "shopping" in result
        assert f"/grocery-lists/{grocery_id}" in result
        assert "ShopBot" in result

    def test_without_grocery_list_id(self, user_with_discord, shop_assignment):
        """Links to grocery lists index when no ID provided."""
        result = build_shop_notification(
            user_with_discord,
            shop_assignment,
            "https://kitchen.example.com",
            "ShopBot",
            grocery_list_id=None,
        )

        assert "/grocery-lists" in result
        # Should not have a specific ID
        assert "/grocery-lists/" not in result or result.count("/grocery-lists/") == 0

    def test_uses_username_without_discord(self, user_without_discord, shop_assignment):
        """Uses username when user has no Discord ID."""
        result = build_shop_notification(
            user_without_discord,
            shop_assignment,
            "https://example.com",
            "Bot",
        )

        assert "bob" in result
        assert "<@" not in result


class TestBuildTakeoutNotification:
    """Tests for build_takeout_notification()."""

    def test_basic_message(self, user_with_discord):
        """Returns takeout notification message."""
        result = build_takeout_notification(
            user_with_discord,
            "https://kitchen.example.com",
            "TakeoutBot",
        )

        assert "<@123456789>" in result
        assert "takeout" in result
        assert "TakeoutBot" in result

    def test_uses_username_without_discord(self, user_without_discord):
        """Uses username when user has no Discord ID."""
        result = build_takeout_notification(
            user_without_discord,
            "https://example.com",
            "Bot",
        )

        assert "bob" in result
        assert "<@" not in result


class TestBuildGenericNotification:
    """Tests for build_generic_notification()."""

    def test_leftovers_action(self, user_with_discord, leftovers_assignment):
        """Handles leftovers action type."""
        result = build_generic_notification(
            user_with_discord,
            leftovers_assignment,
            "https://kitchen.example.com",
            "GenericBot",
        )

        assert "<@123456789>" in result
        assert "leftoversing" in result  # action + "ing"
        assert "/meal-plans" in result
        assert "GenericBot" in result

    def test_rest_action(self, user_with_discord):
        """Handles rest action type."""
        assignment = MagicMock()
        assignment.action = "rest"

        result = build_generic_notification(
            user_with_discord,
            assignment,
            "https://example.com",
            "Bot",
        )

        assert "resting" in result

    def test_custom_action(self, user_without_discord):
        """Handles custom/unknown action types."""
        assignment = MagicMock()
        assignment.action = "prep"

        result = build_generic_notification(
            user_without_discord,
            assignment,
            "https://example.com",
            "Bot",
        )

        assert "preping" in result
        assert "bob" in result


class TestBuildNotificationMessage:
    """Tests for build_notification_message() dispatcher."""

    def test_routes_cook_action(self, user_with_discord, cook_assignment, recipe):
        """Routes cook action to cook notification builder."""
        result = build_notification_message(
            user_with_discord,
            cook_assignment,
            recipe,
            "https://example.com",
            "Bot",
        )

        assert "cooking" in result
        assert recipe.name in result

    def test_routes_shop_action(self, user_with_discord, shop_assignment):
        """Routes shop action to shop notification builder."""
        grocery_id = str(uuid4())
        result = build_notification_message(
            user_with_discord,
            shop_assignment,
            None,
            "https://example.com",
            "Bot",
            grocery_list_id=grocery_id,
        )

        assert "shopping" in result
        assert grocery_id in result

    def test_routes_takeout_action(self, user_with_discord, takeout_assignment):
        """Routes takeout action to takeout notification builder."""
        result = build_notification_message(
            user_with_discord,
            takeout_assignment,
            None,
            "https://example.com",
            "Bot",
        )

        assert "takeout" in result

    def test_routes_leftovers_to_generic(self, user_with_discord, leftovers_assignment):
        """Routes leftovers action to generic notification builder."""
        result = build_notification_message(
            user_with_discord,
            leftovers_assignment,
            None,
            "https://example.com",
            "Bot",
        )

        assert "leftoversing" in result
        assert "/meal-plans" in result

    def test_routes_unknown_action_to_generic(self, user_with_discord):
        """Routes unknown action types to generic notification builder."""
        assignment = MagicMock()
        assignment.action = "mystery"

        result = build_notification_message(
            user_with_discord,
            assignment,
            None,
            "https://example.com",
            "Bot",
        )

        assert "mysterying" in result
        assert "/meal-plans" in result

    def test_all_messages_include_bot_name(self, user_with_discord):
        """All notification types include the bot name."""
        bot_name = "TestBotName"

        # Cook
        cook = MagicMock()
        cook.action = "cook"
        cook.recipe_id = None
        result = build_notification_message(user_with_discord, cook, None, "https://x.com", bot_name)
        assert bot_name in result

        # Shop
        shop = MagicMock()
        shop.action = "shop"
        result = build_notification_message(user_with_discord, shop, None, "https://x.com", bot_name)
        assert bot_name in result

        # Takeout
        takeout = MagicMock()
        takeout.action = "takeout"
        result = build_notification_message(user_with_discord, takeout, None, "https://x.com", bot_name)
        assert bot_name in result

        # Generic
        other = MagicMock()
        other.action = "other"
        result = build_notification_message(user_with_discord, other, None, "https://x.com", bot_name)
        assert bot_name in result

    def test_all_messages_include_user_mention(self, user_with_discord):
        """All notification types include user mention."""
        actions = ["cook", "shop", "takeout", "leftovers", "rest"]

        for action in actions:
            assignment = MagicMock()
            assignment.action = action
            assignment.recipe_id = None

            result = build_notification_message(
                user_with_discord,
                assignment,
                None,
                "https://example.com",
                "Bot",
            )

            assert "<@123456789>" in result, f"User mention missing for action: {action}"

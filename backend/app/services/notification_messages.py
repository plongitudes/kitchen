"""Notification message formatting for Discord notifications.

Shared message builders used by both the scheduler and test endpoints.
"""

from typing import Optional
from app.models.user import User
from app.models.recipe import Recipe
from app.models.meal_plan import MealAssignment


def build_user_mention(user: User) -> str:
    """Build Discord mention or fallback to username."""
    if user.discord_user_id:
        return f"<@{user.discord_user_id}>"
    return user.username


def build_cook_notification(
    user: User,
    assignment: MealAssignment,
    recipe: Optional[Recipe],
    frontend_url: str,
    bot_name: str,
) -> str:
    """Build notification message for cooking action."""
    user_mention = build_user_mention(user)

    recipe_name = "your recipe"
    recipe_link = f"{frontend_url}/meal-plans"

    if recipe and assignment.recipe_id:
        recipe_name = recipe.name
        recipe_link = f"{frontend_url}/recipes/{assignment.recipe_id}"

    return (
        f"Hey {user_mention}, you're {assignment.action}ing today! "
        f"Don't forget to check the _[{recipe_name}]({recipe_link})_ recipe to see if you need to do any "
        f"prep before dinner!\n"
        f"Warmly, **{bot_name}**"
    )


def build_shop_notification(
    user: User,
    assignment: MealAssignment,
    frontend_url: str,
    bot_name: str,
    grocery_list_id: str = None,
) -> str:
    """Build notification message for shopping action."""
    user_mention = build_user_mention(user)

    # Link to specific grocery list if available, otherwise to all grocery lists
    if grocery_list_id:
        grocery_url = f"{frontend_url}/grocery-lists/{grocery_list_id}"
    else:
        grocery_url = f"{frontend_url}/grocery-lists"

    return (
        f"Hey {user_mention}, you're shopping today! "
        f"Check out [the grocery list]({grocery_url}) for what you need to pick up. "
        f"Warmly, {bot_name}"
    )


def build_takeout_notification(
    user: User,
    frontend_url: str,
    bot_name: str,
) -> str:
    """Build notification message for takeout action."""
    user_mention = build_user_mention(user)

    return (
        f"Hey {user_mention}, it's takeout night! "
        f"Time to pick where we're ordering from. "
        f"Warmly, {bot_name}"
    )


def build_generic_notification(
    user: User,
    assignment: MealAssignment,
    frontend_url: str,
    bot_name: str,
) -> str:
    """Build generic notification message for other action types."""
    user_mention = build_user_mention(user)

    return (
        f"Hey {user_mention}, you're {assignment.action}ing today! "
        f"Check [the meal plan]({frontend_url}/meal-plans) for details. "
        f"Warmly, {bot_name}"
    )


def build_notification_message(
    user: User,
    assignment: MealAssignment,
    recipe: Optional[Recipe],
    frontend_url: str,
    bot_name: str,
    grocery_list_id: Optional[str] = None,
) -> str:
    """Build notification message based on assignment action type.

    Args:
        user: User receiving the notification
        assignment: Meal assignment with action type
        recipe: Recipe for cooking assignments (optional)
        frontend_url: Base URL for frontend links
        bot_name: Name of the Discord bot for signature
        grocery_list_id: GroceryList ID for shop notification links

    Returns:
        Formatted notification message string
    """
    if assignment.action == "cook":
        return build_cook_notification(user, assignment, recipe, frontend_url, bot_name)
    elif assignment.action == "shop":
        return build_shop_notification(user, assignment, frontend_url, bot_name, grocery_list_id)
    elif assignment.action == "takeout":
        return build_takeout_notification(user, frontend_url, bot_name)
    else:
        return build_generic_notification(user, assignment, frontend_url, bot_name)

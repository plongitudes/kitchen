"""
Unit test configuration and fixtures.

These fixtures are specific to unit tests and provide:
- Quick model creation without database persistence
- Mock services and dependencies
- Common test data patterns
"""

import pytest
from uuid import uuid4

from tests.factories import (
    UserFactory,
    RecipeFactory,
    RecipeIngredientFactory,
    WeekTemplateFactory,
    WeekDayAssignmentFactory,
    ScheduleSequenceFactory,
    MealPlanInstanceFactory,
    CommonIngredientFactory,
)


# ============================================================================
# User fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create a mock user without database."""
    return UserFactory.build(username="mockuser")


@pytest.fixture
def mock_user_id():
    """Create a mock user ID for tests that only need the ID."""
    return uuid4()


@pytest.fixture
def mock_second_user():
    """Create a second mock user for multi-user tests."""
    return UserFactory.build(username="seconduser")


# ============================================================================
# Recipe fixtures
# ============================================================================


@pytest.fixture
def mock_recipe(mock_user):
    """Create a mock recipe without database."""
    return RecipeFactory.build(owner_id=mock_user.id, name="Mock Recipe")


@pytest.fixture
def mock_recipe_with_ingredients(mock_user):
    """Create a mock recipe with common ingredients."""
    return RecipeFactory.build_with_ingredients(
        owner_id=mock_user.id,
        name="Recipe with Ingredients",
        ingredients=[
            ("flour", 2.0, "cup"),
            ("sugar", 1.0, "cup"),
            ("eggs", 3.0, "whole"),
            ("butter", 0.5, "cup"),
            ("salt", 1.0, "teaspoon"),
        ],
    )


@pytest.fixture
def mock_recipe_with_instructions(mock_user):
    """Create a mock recipe with instructions."""
    return RecipeFactory.build_with_instructions(
        owner_id=mock_user.id,
        name="Recipe with Instructions",
        instructions=[
            "Preheat oven to 350F",
            "Mix dry ingredients",
            "Add wet ingredients",
            "Pour into pan",
            "Bake for 30 minutes",
        ],
    )


@pytest.fixture
def mock_ingredient():
    """Create a single mock ingredient."""
    return RecipeIngredientFactory.build(
        ingredient_name="Test Ingredient",
        quantity=1.0,
        unit="cup",
    )


# ============================================================================
# Template fixtures
# ============================================================================


@pytest.fixture
def mock_template():
    """Create a mock week template without database."""
    return WeekTemplateFactory.build(name="Mock Week")


@pytest.fixture
def mock_template_with_assignments(mock_user, mock_recipe):
    """Create a mock template with day assignments."""
    return WeekTemplateFactory.build_with_assignments(
        name="Week with Assignments",
        assignments=[
            # (day_of_week, action, user_id, recipe_id)
            (0, "rest", mock_user.id, None),  # Sunday
            (1, "cook", mock_user.id, mock_recipe.id),  # Monday
            (2, "cook", mock_user.id, mock_recipe.id),  # Tuesday
            (3, "takeout", mock_user.id, None),  # Wednesday
            (4, "cook", mock_user.id, mock_recipe.id),  # Thursday
            (5, "cook", mock_user.id, mock_recipe.id),  # Friday
            (6, "rest", mock_user.id, None),  # Saturday
        ],
    )


@pytest.fixture
def mock_assignment(mock_user):
    """Create a single mock day assignment."""
    return WeekDayAssignmentFactory.build(
        day_of_week=1,
        action="cook",
        assigned_user_id=mock_user.id,
    )


# ============================================================================
# Schedule fixtures
# ============================================================================


@pytest.fixture
def mock_schedule():
    """Create a mock schedule sequence without database."""
    return ScheduleSequenceFactory.build(name="Mock Schedule")


@pytest.fixture
def mock_schedule_with_templates(mock_template):
    """Create a mock schedule with week templates."""
    template2 = WeekTemplateFactory.build(name="Week 2")
    template3 = WeekTemplateFactory.build(name="Week 3")

    return ScheduleSequenceFactory.build_with_templates(
        name="Schedule with Templates",
        templates=[mock_template, template2, template3],
    )


# ============================================================================
# Meal plan fixtures
# ============================================================================


@pytest.fixture
def mock_meal_plan_instance(mock_template):
    """Create a mock meal plan instance."""
    return MealPlanInstanceFactory.build(
        week_template_id=mock_template.id,
    )


# ============================================================================
# Ingredient fixtures
# ============================================================================


@pytest.fixture
def mock_common_ingredient():
    """Create a mock common ingredient."""
    return CommonIngredientFactory.build(
        name="all-purpose flour",
        category="pantry",
    )


@pytest.fixture
def mock_common_ingredient_with_aliases():
    """Create a mock common ingredient with aliases."""
    return CommonIngredientFactory.build_with_aliases(
        name="all-purpose flour",
        category="pantry",
        aliases=["ap flour", "flour", "white flour", "plain flour"],
    )


# ============================================================================
# Bulk fixtures for testing aggregation/collections
# ============================================================================


@pytest.fixture
def mock_recipe_list(mock_user):
    """Create a list of mock recipes for testing lists/collections."""
    return [
        RecipeFactory.build(owner_id=mock_user.id, name="Breakfast Pancakes", recipe_type="breakfast"),
        RecipeFactory.build(owner_id=mock_user.id, name="Lunch Salad", recipe_type="lunch"),
        RecipeFactory.build(owner_id=mock_user.id, name="Dinner Pasta", recipe_type="dinner"),
        RecipeFactory.build(owner_id=mock_user.id, name="Dessert Cake", recipe_type="dessert"),
    ]


@pytest.fixture
def mock_ingredients_for_aggregation():
    """Create ingredients that can be aggregated (same name, different quantities)."""
    recipe_id_1 = uuid4()
    recipe_id_2 = uuid4()
    recipe_id_3 = uuid4()

    return [
        # Flour from multiple recipes
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_1, ingredient_name="flour", quantity=2.0, unit="cup"
        ),
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_2, ingredient_name="flour", quantity=1.5, unit="cup"
        ),
        # Sugar from multiple recipes
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_1, ingredient_name="sugar", quantity=1.0, unit="cup"
        ),
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_3, ingredient_name="sugar", quantity=0.5, unit="cup"
        ),
        # Eggs (countable, not convertible)
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_1, ingredient_name="eggs", quantity=2.0, unit="whole"
        ),
        RecipeIngredientFactory.build(
            recipe_id=recipe_id_2, ingredient_name="eggs", quantity=3.0, unit="whole"
        ),
    ]


# ============================================================================
# Helper functions available as fixtures
# ============================================================================


@pytest.fixture
def create_recipe_with_n_ingredients(mock_user):
    """Factory fixture to create recipes with N ingredients."""

    def _create(n: int, name: str = "Generated Recipe"):
        ingredients = [
            (f"ingredient_{i}", float(i), "cup")
            for i in range(1, n + 1)
        ]
        return RecipeFactory.build_with_ingredients(
            owner_id=mock_user.id,
            name=name,
            ingredients=ingredients,
        )

    return _create


@pytest.fixture
def create_template_with_n_days(mock_user):
    """Factory fixture to create templates with N days of assignments."""

    def _create(n: int, action: str = "cook", name: str = "Generated Week"):
        assignments = [
            (day % 7, action, mock_user.id, None)
            for day in range(n)
        ]
        return WeekTemplateFactory.build_with_assignments(
            name=name,
            assignments=assignments,
        )

    return _create

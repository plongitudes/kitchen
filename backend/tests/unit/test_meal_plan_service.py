"""Unit tests for MealPlanService."""

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.meal_plan_service import MealPlanService
from app.models.meal_plan import MealPlanInstance, MealAssignment
from app.models.schedule import WeekTemplate, WeekDayAssignment
from app.models.user import User
from app.models.recipe import Recipe


async def load_instance_with_relationships(db, instance_id):
    """Helper to load instance with eager-loaded relationships."""
    result = await db.execute(
        select(MealPlanInstance)
        .options(
            selectinload(MealPlanInstance.week_template).selectinload(WeekTemplate.day_assignments)
        )
        .where(MealPlanInstance.id == instance_id)
    )
    return result.scalar_one()


@pytest.mark.asyncio
class TestGetMergedAssignmentsForDay:
    """Test the get_merged_assignments_for_day method."""

    async def test_uses_template_assignments_when_no_overrides(
        self, async_db_session, async_test_user
    ):
        """Test that template assignments are used when instance has no overrides."""
        # Create a template with assignments
        template = WeekTemplate(
            id=uuid4(),
            name="Test Week",
        )
        async_db_session.add(template)

        # Add a day assignment to the template
        day_assignment = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=1,  # Monday
            assigned_user_id=async_test_user.id,
            action="cook",
            recipe_id=None,
            order=0,
        )
        async_db_session.add(day_assignment)

        # Create an instance from the template (no MealAssignments)
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 6),  # A Monday
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get merged assignments for Monday (day 1)
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=1,
        )

        # Should return the template assignment
        assert len(results) == 1
        assignment, user, recipe = results[0]

        assert assignment.action == "cook"
        assert assignment.day_of_week == 1
        assert user.id == async_test_user.id
        assert recipe is None

    async def test_uses_instance_overrides_when_present(
        self, async_db_session, async_test_user
    ):
        """Test that instance overrides take precedence over template assignments."""
        # Create a template with assignments
        template = WeekTemplate(
            id=uuid4(),
            name="Test Week",
        )
        async_db_session.add(template)

        # Template says "cook" on Monday
        template_assignment = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=1,  # Monday
            assigned_user_id=async_test_user.id,
            action="cook",
            recipe_id=None,
            order=0,
        )
        async_db_session.add(template_assignment)

        # Create instance
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 6),
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Add instance override: "takeout" instead of "cook"
        instance_override = MealAssignment(
            id=uuid4(),
            meal_plan_instance_id=instance.id,
            day_of_week=1,  # Monday
            assigned_user_id=async_test_user.id,
            action="takeout",  # Override!
            recipe_id=None,
            order=0,
        )
        async_db_session.add(instance_override)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get merged assignments for Monday
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=1,
        )

        # Should return the OVERRIDE, not the template
        assert len(results) == 1
        assignment, user, recipe = results[0]

        assert assignment.action == "takeout"  # Override value
        assert isinstance(assignment, MealAssignment)  # Not WeekDayAssignment
        assert user.id == async_test_user.id

    async def test_returns_user_and_recipe_objects(
        self, async_db_session, async_test_user
    ):
        """Test that user and recipe are properly loaded, not just IDs."""
        # Create a recipe
        recipe = Recipe(
            id=uuid4(),
            name="Test Recipe",
            owner_id=async_test_user.id,  # Use owner_id, not created_by_id
        )
        async_db_session.add(recipe)

        # Create template with cook assignment
        template = WeekTemplate(
            id=uuid4(),
            name="Test Week",
        )
        async_db_session.add(template)

        day_assignment = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=2,  # Tuesday
            assigned_user_id=async_test_user.id,
            action="cook",
            recipe_id=recipe.id,
            order=0,
        )
        async_db_session.add(day_assignment)

        # Create instance
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 6),
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get merged assignments
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=2,
        )

        assert len(results) == 1
        assignment, user, recipe_obj = results[0]

        # Verify we got full objects, not just IDs
        assert isinstance(user, User)
        assert user.username == async_test_user.username

        assert isinstance(recipe_obj, Recipe)
        assert recipe_obj.name == "Test Recipe"

    async def test_handles_day_with_no_assignments(
        self, async_db_session, async_test_user
    ):
        """Test that empty list is returned when day has no assignments."""
        # Create template with no assignments
        template = WeekTemplate(
            id=uuid4(),
            name="Empty Week",
        )
        async_db_session.add(template)

        # Create instance
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 6),
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get assignments for a day with none
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=3,
        )

        assert results == []

    async def test_handles_missing_recipe_gracefully(
        self, async_db_session, async_test_user
    ):
        """Test that None recipe is handled for non-cook actions."""
        # Create template with shop assignment (no recipe)
        template = WeekTemplate(
            id=uuid4(),
            name="Test Week",
        )
        async_db_session.add(template)

        day_assignment = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=0,  # Sunday
            assigned_user_id=async_test_user.id,
            action="shop",
            recipe_id=None,  # No recipe for shopping
            order=0,
        )
        async_db_session.add(day_assignment)

        # Create instance
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 5),  # Sunday
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get assignments
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=0,
        )

        assert len(results) == 1
        assignment, user, recipe = results[0]

        assert assignment.action == "shop"
        assert recipe is None  # Should be None, not error

    async def test_multiple_assignments_same_day(
        self, async_db_session, async_test_user
    ):
        """Test handling multiple assignments on the same day."""
        # Create template
        template = WeekTemplate(
            id=uuid4(),
            name="Test Week",
        )
        async_db_session.add(template)

        # Add two assignments for the same day (different order)
        assignment1 = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=5,  # Friday
            assigned_user_id=async_test_user.id,
            action="cook",
            recipe_id=None,
            order=0,
        )
        assignment2 = WeekDayAssignment(
            id=uuid4(),
            week_template_id=template.id,
            day_of_week=5,  # Friday
            assigned_user_id=async_test_user.id,
            action="shop",
            recipe_id=None,
            order=1,
        )
        async_db_session.add(assignment1)
        async_db_session.add(assignment2)

        # Create instance
        instance = MealPlanInstance(
            id=uuid4(),
            week_template_id=template.id,
            instance_start_date=date(2025, 1, 6),
        )
        async_db_session.add(instance)
        await async_db_session.commit()

        # Load instance with relationships using eager loading
        instance = await load_instance_with_relationships(async_db_session, instance.id)

        # Get assignments
        results = await MealPlanService.get_merged_assignments_for_day(
            db=async_db_session,
            instance=instance,
            day_of_week=5,
        )

        # Should return both assignments
        assert len(results) == 2
        actions = [r[0].action for r in results]
        assert "cook" in actions
        assert "shop" in actions

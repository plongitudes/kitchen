"""
Unit tests for TemplateService.

Tests cover:
- list_templates: listing with/without retired
- get_template_by_id: fetching with/without assignments
- create_template: creating templates with assignments
- update_template: updating name and assignments
- fork_template: deep copying templates
- retire_template: soft delete with sequence handling
- delete_template: hard delete constraints
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.services.template_service import TemplateService
from app.schemas.schedule import WeekTemplateCreate, WeekTemplateUpdate, WeekDayAssignmentCreate
from tests.factories import (
    UserFactory,
    RecipeFactory,
    WeekTemplateFactory,
    WeekDayAssignmentFactory,
    ScheduleSequenceFactory,
    SequenceWeekMappingFactory,
    MealPlanInstanceFactory,
)


@pytest.mark.asyncio
class TestListTemplates:
    """Test the list_templates method."""

    async def test_lists_active_templates(self, async_db_session):
        """Test that active templates are listed."""
        # Create some templates
        template1 = WeekTemplateFactory.build(name="Week A")
        template2 = WeekTemplateFactory.build(name="Week B")
        async_db_session.add(template1)
        async_db_session.add(template2)
        await async_db_session.commit()

        result = await TemplateService.list_templates(async_db_session)

        assert len(result) >= 2
        names = [t.name for t in result]
        assert "Week A" in names
        assert "Week B" in names

    async def test_excludes_retired_by_default(self, async_db_session):
        """Test that retired templates are excluded by default."""
        active = WeekTemplateFactory.build(name="Active Week")
        retired = WeekTemplateFactory.build(name="Retired Week", retired_at=datetime.utcnow())
        async_db_session.add(active)
        async_db_session.add(retired)
        await async_db_session.commit()

        result = await TemplateService.list_templates(async_db_session)

        names = [t.name for t in result]
        assert "Active Week" in names
        assert "Retired Week" not in names

    async def test_includes_retired_when_requested(self, async_db_session):
        """Test that retired templates can be included."""
        active = WeekTemplateFactory.build(name="Active Week 2")
        retired = WeekTemplateFactory.build(name="Retired Week 2", retired_at=datetime.utcnow())
        async_db_session.add(active)
        async_db_session.add(retired)
        await async_db_session.commit()

        result = await TemplateService.list_templates(async_db_session, include_retired=True)

        names = [t.name for t in result]
        assert "Active Week 2" in names
        assert "Retired Week 2" in names

    async def test_returns_sorted_by_name(self, async_db_session):
        """Test that templates are sorted alphabetically."""
        template_c = WeekTemplateFactory.build(name="Charlie Week")
        template_a = WeekTemplateFactory.build(name="Alpha Week")
        template_b = WeekTemplateFactory.build(name="Bravo Week")
        async_db_session.add(template_c)
        async_db_session.add(template_a)
        async_db_session.add(template_b)
        await async_db_session.commit()

        result = await TemplateService.list_templates(async_db_session)

        # Filter to just our test templates and check order
        test_templates = [t for t in result if t.name in ["Alpha Week", "Bravo Week", "Charlie Week"]]
        names = [t.name for t in test_templates]
        assert names == sorted(names)


@pytest.mark.asyncio
class TestGetTemplateById:
    """Test the get_template_by_id method."""

    async def test_gets_existing_template(self, async_db_session):
        """Test fetching an existing template."""
        template = WeekTemplateFactory.build(name="Fetchable Week")
        async_db_session.add(template)
        await async_db_session.commit()

        result = await TemplateService.get_template_by_id(async_db_session, template.id)

        assert result is not None
        assert result.id == template.id
        assert result.name == "Fetchable Week"

    async def test_returns_none_for_missing_template(self, async_db_session):
        """Test that None is returned for non-existent template."""
        fake_id = uuid4()

        result = await TemplateService.get_template_by_id(async_db_session, fake_id)

        assert result is None

    async def test_includes_assignments_by_default(self, async_db_session, async_test_user):
        """Test that assignments are loaded by default."""
        template = WeekTemplateFactory.build(name="Week with Assignments")
        async_db_session.add(template)
        await async_db_session.flush()

        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=1,
            assigned_user_id=async_test_user.id,
            action="cook",
        )
        async_db_session.add(assignment)
        await async_db_session.commit()

        result = await TemplateService.get_template_by_id(async_db_session, template.id)

        assert result is not None
        assert len(result.day_assignments) == 1
        assert result.day_assignments[0].action == "cook"

    async def test_can_exclude_assignments(self, async_db_session, async_test_user):
        """Test that assignments can be excluded from load."""
        template = WeekTemplateFactory.build(name="Week Without Eager Load")
        async_db_session.add(template)
        await async_db_session.commit()

        result = await TemplateService.get_template_by_id(
            async_db_session, template.id, include_assignments=False
        )

        assert result is not None
        assert result.name == "Week Without Eager Load"


@pytest.mark.asyncio
class TestCreateTemplate:
    """Test the create_template method."""

    async def test_creates_template_with_name(self, async_db_session, async_test_user):
        """Test creating a basic template."""
        template_data = WeekTemplateCreate(
            name="New Week",
            assignments=[],
        )

        result = await TemplateService.create_template(async_db_session, template_data)

        assert result is not None
        assert result.name == "New Week"
        assert result.id is not None
        assert result.retired_at is None

    async def test_creates_template_with_assignments(self, async_db_session, async_test_user):
        """Test creating a template with day assignments."""
        template_data = WeekTemplateCreate(
            name="Week with Meals",
            assignments=[
                WeekDayAssignmentCreate(
                    day_of_week=1,
                    assigned_user_id=async_test_user.id,
                    action="cook",
                    recipe_id=None,
                    order=0,
                ),
                WeekDayAssignmentCreate(
                    day_of_week=2,
                    assigned_user_id=async_test_user.id,
                    action="takeout",
                    recipe_id=None,
                    order=0,
                ),
            ],
        )

        result = await TemplateService.create_template(async_db_session, template_data)

        assert result is not None
        assert len(result.day_assignments) == 2
        actions = [a.action for a in result.day_assignments]
        assert "cook" in actions
        assert "takeout" in actions

    async def test_creates_template_with_recipe_assignment(self, async_db_session, async_test_user):
        """Test creating a template with a recipe assigned."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Test Dinner")
        async_db_session.add(recipe)
        await async_db_session.commit()

        template_data = WeekTemplateCreate(
            name="Week with Recipe",
            assignments=[
                WeekDayAssignmentCreate(
                    day_of_week=3,
                    assigned_user_id=async_test_user.id,
                    action="cook",
                    recipe_id=recipe.id,
                    order=0,
                ),
            ],
        )

        result = await TemplateService.create_template(async_db_session, template_data)

        assert result is not None
        assert len(result.day_assignments) == 1
        assert result.day_assignments[0].recipe_id == recipe.id


@pytest.mark.asyncio
class TestUpdateTemplate:
    """Test the update_template method."""

    async def test_updates_template_name(self, async_db_session):
        """Test updating only the template name."""
        template = WeekTemplateFactory.build(name="Original Name")
        async_db_session.add(template)
        await async_db_session.commit()

        update_data = WeekTemplateUpdate(name="Updated Name")
        result = await TemplateService.update_template(async_db_session, template.id, update_data)

        assert result is not None
        assert result.name == "Updated Name"

    async def test_returns_none_for_missing_template(self, async_db_session):
        """Test that None is returned when template doesn't exist."""
        fake_id = uuid4()
        update_data = WeekTemplateUpdate(name="Whatever")

        result = await TemplateService.update_template(async_db_session, fake_id, update_data)

        assert result is None

    async def test_replaces_assignments(self, async_db_session, async_test_user):
        """Test that updating assignments replaces all existing ones."""
        # Create template with initial assignment
        template = WeekTemplateFactory.build(name="Week to Update")
        async_db_session.add(template)
        await async_db_session.flush()

        old_assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=1,
            assigned_user_id=async_test_user.id,
            action="cook",
        )
        async_db_session.add(old_assignment)
        await async_db_session.commit()

        # Update with new assignments
        update_data = WeekTemplateUpdate(
            assignments=[
                WeekDayAssignmentCreate(
                    day_of_week=5,
                    assigned_user_id=async_test_user.id,
                    action="takeout",
                    recipe_id=None,
                    order=0,
                ),
            ]
        )

        result = await TemplateService.update_template(async_db_session, template.id, update_data)

        assert result is not None
        assert len(result.day_assignments) == 1
        assert result.day_assignments[0].day_of_week == 5
        assert result.day_assignments[0].action == "takeout"


@pytest.mark.asyncio
class TestForkTemplate:
    """Test the fork_template method."""

    async def test_forks_template_with_default_name(self, async_db_session, async_test_user):
        """Test forking creates a copy with 'Fork of' prefix."""
        original = WeekTemplateFactory.build(name="Original Week")
        async_db_session.add(original)
        await async_db_session.commit()

        result = await TemplateService.fork_template(async_db_session, original.id)

        assert result is not None
        assert result.name == "Fork of Original Week"
        assert result.id != original.id

    async def test_forks_template_with_custom_name(self, async_db_session, async_test_user):
        """Test forking with a custom name."""
        original = WeekTemplateFactory.build(name="Source Week")
        async_db_session.add(original)
        await async_db_session.commit()

        result = await TemplateService.fork_template(
            async_db_session, original.id, new_name="My Custom Copy"
        )

        assert result is not None
        assert result.name == "My Custom Copy"

    async def test_forks_assignments(self, async_db_session, async_test_user):
        """Test that assignments are deep copied."""
        original = WeekTemplateFactory.build(name="Week with Assignments")
        async_db_session.add(original)
        await async_db_session.flush()

        assignment1 = WeekDayAssignmentFactory.build(
            week_template_id=original.id,
            day_of_week=1,
            assigned_user_id=async_test_user.id,
            action="cook",
        )
        assignment2 = WeekDayAssignmentFactory.build(
            week_template_id=original.id,
            day_of_week=3,
            assigned_user_id=async_test_user.id,
            action="shop",
        )
        async_db_session.add(assignment1)
        async_db_session.add(assignment2)
        await async_db_session.commit()

        result = await TemplateService.fork_template(async_db_session, original.id)

        assert result is not None
        assert len(result.day_assignments) == 2

        # Verify assignments are copies, not references
        forked_ids = [a.id for a in result.day_assignments]
        assert assignment1.id not in forked_ids
        assert assignment2.id not in forked_ids

        # Verify content is same
        actions = sorted([a.action for a in result.day_assignments])
        assert actions == ["cook", "shop"]

    async def test_returns_none_for_missing_template(self, async_db_session):
        """Test that None is returned when original doesn't exist."""
        fake_id = uuid4()

        result = await TemplateService.fork_template(async_db_session, fake_id)

        assert result is None


@pytest.mark.asyncio
class TestRetireTemplate:
    """Test the retire_template method."""

    async def test_soft_deletes_template(self, async_db_session):
        """Test that retiring sets retired_at timestamp."""
        template = WeekTemplateFactory.build(name="To Retire")
        async_db_session.add(template)
        await async_db_session.commit()

        result = await TemplateService.retire_template(async_db_session, template.id)

        assert result is not None
        assert result["template"].retired_at is not None

    async def test_returns_none_for_missing_template(self, async_db_session):
        """Test that None is returned when template doesn't exist."""
        fake_id = uuid4()

        result = await TemplateService.retire_template(async_db_session, fake_id)

        assert result is None

    async def test_indicates_can_hard_delete_when_no_instances(self, async_db_session):
        """Test that can_hard_delete is True when no instances reference template."""
        template = WeekTemplateFactory.build(name="Unused Template")
        async_db_session.add(template)
        await async_db_session.commit()

        result = await TemplateService.retire_template(async_db_session, template.id)

        assert result["can_hard_delete"] is True

    async def test_indicates_cannot_hard_delete_when_has_instances(self, async_db_session):
        """Test that can_hard_delete is False when instances reference template."""
        template = WeekTemplateFactory.build(name="Used Template")
        async_db_session.add(template)
        await async_db_session.flush()

        # Create an instance referencing the template
        instance = MealPlanInstanceFactory.build(week_template_id=template.id)
        async_db_session.add(instance)
        await async_db_session.commit()

        result = await TemplateService.retire_template(async_db_session, template.id)

        assert result["can_hard_delete"] is False


@pytest.mark.asyncio
class TestDeleteTemplate:
    """Test the delete_template method."""

    async def test_deletes_unreferenced_template(self, async_db_session):
        """Test that unreferenced templates can be deleted."""
        template = WeekTemplateFactory.build(name="To Delete")
        async_db_session.add(template)
        await async_db_session.commit()
        template_id = template.id

        result = await TemplateService.delete_template(async_db_session, template_id)

        assert result is True

        # Verify it's gone
        check = await TemplateService.get_template_by_id(async_db_session, template_id)
        assert check is None

    async def test_cannot_delete_referenced_template(self, async_db_session):
        """Test that templates with instances cannot be deleted."""
        template = WeekTemplateFactory.build(name="Referenced Template")
        async_db_session.add(template)
        await async_db_session.flush()

        instance = MealPlanInstanceFactory.build(week_template_id=template.id)
        async_db_session.add(instance)
        await async_db_session.commit()

        result = await TemplateService.delete_template(async_db_session, template.id)

        assert result is False

        # Verify it still exists
        check = await TemplateService.get_template_by_id(async_db_session, template.id)
        assert check is not None

    async def test_returns_false_for_missing_template(self, async_db_session):
        """Test that False is returned when template doesn't exist."""
        fake_id = uuid4()

        result = await TemplateService.delete_template(async_db_session, fake_id)

        assert result is False

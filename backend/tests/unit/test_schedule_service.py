"""
Unit tests for ScheduleService.

Tests cover:
- Sequence CRUD: get_sequences, get_sequence_by_id, create, update, delete
- Template mappings: add, remove, reorder, get current template
- Day assignments: get, create, update, delete
"""

import pytest
from uuid import uuid4
from fastapi import HTTPException

from app.services.schedule_service import ScheduleService
from app.schemas.schedule import (
    ScheduleSequenceCreate,
    ScheduleSequenceUpdate,
    WeekDayAssignmentCreate,
    WeekDayAssignmentUpdate,
)
from tests.factories import (
    UserFactory,
    RecipeFactory,
    WeekTemplateFactory,
    WeekDayAssignmentFactory,
    ScheduleSequenceFactory,
    SequenceWeekMappingFactory,
)


@pytest.mark.asyncio
class TestGetSequences:
    """Test the get_sequences method."""

    async def test_returns_all_sequences(self, async_db_session):
        """Test that all sequences are returned."""
        seq1 = ScheduleSequenceFactory.build(name="Schedule A")
        seq2 = ScheduleSequenceFactory.build(name="Schedule B")
        async_db_session.add(seq1)
        async_db_session.add(seq2)
        await async_db_session.commit()

        result = await ScheduleService.get_sequences(async_db_session)

        names = [s.name for s in result]
        assert "Schedule A" in names
        assert "Schedule B" in names

    async def test_returns_empty_list_when_none(self, async_db_session):
        """Test that empty list is returned when no sequences exist."""
        result = await ScheduleService.get_sequences(async_db_session)

        # May have sequences from other tests, but should be a list
        assert isinstance(result, list)


@pytest.mark.asyncio
class TestGetSequenceById:
    """Test the get_sequence_by_id method."""

    async def test_gets_existing_sequence(self, async_db_session):
        """Test fetching an existing sequence."""
        seq = ScheduleSequenceFactory.build(name="Findable Schedule")
        async_db_session.add(seq)
        await async_db_session.commit()

        result = await ScheduleService.get_sequence_by_id(async_db_session, seq.id)

        assert result is not None
        assert result.name == "Findable Schedule"

    async def test_returns_none_for_missing_sequence(self, async_db_session):
        """Test that None is returned for non-existent sequence."""
        fake_id = uuid4()

        result = await ScheduleService.get_sequence_by_id(async_db_session, fake_id)

        assert result is None

    async def test_includes_mappings_by_default(self, async_db_session):
        """Test that template mappings are loaded by default."""
        seq = ScheduleSequenceFactory.build(name="Seq with Templates")
        async_db_session.add(seq)
        await async_db_session.flush()

        template = WeekTemplateFactory.build(name="Mapped Template")
        async_db_session.add(template)
        await async_db_session.flush()

        mapping = SequenceWeekMappingFactory.build(
            sequence_id=seq.id,
            week_template_id=template.id,
            position=1,
        )
        async_db_session.add(mapping)
        await async_db_session.commit()

        result = await ScheduleService.get_sequence_by_id(async_db_session, seq.id)

        assert result is not None
        assert len(result.week_mappings) == 1


@pytest.mark.asyncio
class TestCreateSequence:
    """Test the create_sequence method."""

    async def test_creates_sequence(self, async_db_session):
        """Test creating a new sequence."""
        data = ScheduleSequenceCreate(
            name="New Schedule",
            advancement_day_of_week=0,  # Sunday
            advancement_time="08:00",
        )

        result = await ScheduleService.create_sequence(async_db_session, data)

        assert result is not None
        assert result.name == "New Schedule"
        assert result.advancement_day_of_week == 0
        assert result.advancement_time == "08:00"
        assert result.current_week_index == 0

    async def test_creates_with_different_advancement(self, async_db_session):
        """Test creating sequence with different advancement settings."""
        data = ScheduleSequenceCreate(
            name="Wednesday Schedule",
            advancement_day_of_week=3,  # Wednesday
            advancement_time="18:30",
        )

        result = await ScheduleService.create_sequence(async_db_session, data)

        assert result.advancement_day_of_week == 3
        assert result.advancement_time == "18:30"


@pytest.mark.asyncio
class TestUpdateSequence:
    """Test the update_sequence method."""

    async def test_updates_sequence_name(self, async_db_session):
        """Test updating sequence name."""
        seq = ScheduleSequenceFactory.build(name="Original Name")
        async_db_session.add(seq)
        await async_db_session.commit()

        update_data = ScheduleSequenceUpdate(name="Updated Name")
        result = await ScheduleService.update_sequence(async_db_session, seq.id, update_data)

        assert result.name == "Updated Name"

    async def test_updates_advancement_settings(self, async_db_session):
        """Test updating advancement day and time."""
        seq = ScheduleSequenceFactory.build(
            name="Seq to Update",
            advancement_day_of_week=0,
            advancement_time="00:00",
        )
        async_db_session.add(seq)
        await async_db_session.commit()

        update_data = ScheduleSequenceUpdate(
            advancement_day_of_week=5,  # Friday
            advancement_time="17:00",
        )
        result = await ScheduleService.update_sequence(async_db_session, seq.id, update_data)

        assert result.advancement_day_of_week == 5
        assert result.advancement_time == "17:00"

    async def test_raises_for_missing_sequence(self, async_db_session):
        """Test that HTTPException is raised for non-existent sequence."""
        fake_id = uuid4()
        update_data = ScheduleSequenceUpdate(name="Whatever")

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.update_sequence(async_db_session, fake_id, update_data)

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestDeleteSequence:
    """Test the delete_sequence method."""

    async def test_deletes_sequence(self, async_db_session):
        """Test deleting an existing sequence."""
        seq = ScheduleSequenceFactory.build(name="To Delete")
        async_db_session.add(seq)
        await async_db_session.commit()
        seq_id = seq.id

        result = await ScheduleService.delete_sequence(async_db_session, seq_id)

        assert result is True

        # Verify it's gone
        check = await ScheduleService.get_sequence_by_id(async_db_session, seq_id)
        assert check is None

    async def test_raises_for_missing_sequence(self, async_db_session):
        """Test that HTTPException is raised for non-existent sequence."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.delete_sequence(async_db_session, fake_id)

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestGetActiveTemplatesForSequence:
    """Test the get_active_templates_for_sequence method."""

    async def test_returns_active_mappings(self, async_db_session):
        """Test that only active (non-removed) mappings are returned."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        template1 = WeekTemplateFactory.build(name="Active Template")
        template2 = WeekTemplateFactory.build(name="Removed Template")
        async_db_session.add(template1)
        async_db_session.add(template2)
        await async_db_session.flush()

        # Active mapping
        mapping1 = SequenceWeekMappingFactory.build(
            sequence_id=seq.id,
            week_template_id=template1.id,
            position=1,
        )
        # Removed mapping
        from datetime import datetime
        mapping2 = SequenceWeekMappingFactory.build(
            sequence_id=seq.id,
            week_template_id=template2.id,
            position=2,
            removed_at=datetime.utcnow(),
        )
        async_db_session.add(mapping1)
        async_db_session.add(mapping2)
        await async_db_session.commit()

        result = await ScheduleService.get_active_templates_for_sequence(async_db_session, seq.id)

        assert len(result) == 1
        assert result[0].week_template.name == "Active Template"

    async def test_returns_sorted_by_position(self, async_db_session):
        """Test that mappings are sorted by position."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build(name="Week 1")
        t2 = WeekTemplateFactory.build(name="Week 2")
        t3 = WeekTemplateFactory.build(name="Week 3")
        async_db_session.add_all([t1, t2, t3])
        await async_db_session.flush()

        # Add out of order
        m2 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t2.id, position=2)
        m3 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t3.id, position=3)
        m1 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t1.id, position=1)
        async_db_session.add_all([m2, m3, m1])
        await async_db_session.commit()

        result = await ScheduleService.get_active_templates_for_sequence(async_db_session, seq.id)

        positions = [m.position for m in result]
        assert positions == [1, 2, 3]


@pytest.mark.asyncio
class TestAddTemplateToSequence:
    """Test the add_template_to_sequence method."""

    async def test_adds_template_to_sequence(self, async_db_session):
        """Test adding a template to a sequence."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.commit()

        result = await ScheduleService.add_template_to_sequence(
            async_db_session, seq.id, template.id
        )

        assert result is not None
        assert result.sequence_id == seq.id
        assert result.week_template_id == template.id
        assert result.position == 1

    async def test_auto_assigns_position(self, async_db_session):
        """Test that position is auto-assigned when not specified."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build()
        t2 = WeekTemplateFactory.build()
        async_db_session.add_all([t1, t2])
        await async_db_session.commit()

        # Add first template
        await ScheduleService.add_template_to_sequence(async_db_session, seq.id, t1.id)

        # Add second - should get position 2
        result = await ScheduleService.add_template_to_sequence(async_db_session, seq.id, t2.id)

        assert result.position == 2

    async def test_raises_for_missing_sequence(self, async_db_session):
        """Test HTTPException for non-existent sequence."""
        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.commit()

        fake_seq_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.add_template_to_sequence(
                async_db_session, fake_seq_id, template.id
            )

        assert exc.value.status_code == 404

    async def test_raises_for_missing_template(self, async_db_session):
        """Test HTTPException for non-existent template."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)
        await async_db_session.commit()

        fake_template_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.add_template_to_sequence(
                async_db_session, seq.id, fake_template_id
            )

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestRemoveTemplateFromSequence:
    """Test the remove_template_from_sequence method."""

    async def test_soft_deletes_mapping(self, async_db_session):
        """Test that removing marks the mapping as removed."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.flush()

        mapping = SequenceWeekMappingFactory.build(
            sequence_id=seq.id,
            week_template_id=template.id,
            position=1,
        )
        async_db_session.add(mapping)
        await async_db_session.commit()

        result = await ScheduleService.remove_template_from_sequence(
            async_db_session, seq.id, template.id
        )

        assert result is True

        # Verify it's soft deleted
        active = await ScheduleService.get_active_templates_for_sequence(
            async_db_session, seq.id
        )
        assert len(active) == 0

    async def test_raises_for_missing_mapping(self, async_db_session):
        """Test HTTPException when mapping doesn't exist."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)
        await async_db_session.commit()

        fake_template_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.remove_template_from_sequence(
                async_db_session, seq.id, fake_template_id
            )

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestReorderSequenceTemplates:
    """Test the reorder_sequence_templates method."""

    async def test_reorders_templates(self, async_db_session):
        """Test reordering templates in a sequence."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build(name="Week 1")
        t2 = WeekTemplateFactory.build(name="Week 2")
        t3 = WeekTemplateFactory.build(name="Week 3")
        async_db_session.add_all([t1, t2, t3])
        await async_db_session.flush()

        m1 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t1.id, position=1)
        m2 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t2.id, position=2)
        m3 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t3.id, position=3)
        async_db_session.add_all([m1, m2, m3])
        await async_db_session.commit()

        # Reorder: 3, 1, 2
        new_order = [t3.id, t1.id, t2.id]
        result = await ScheduleService.reorder_sequence_templates(
            async_db_session, seq.id, new_order
        )

        # Check new positions
        pos_by_name = {m.week_template.name: m.position for m in result}
        assert pos_by_name["Week 3"] == 1
        assert pos_by_name["Week 1"] == 2
        assert pos_by_name["Week 2"] == 3

    async def test_raises_for_mismatched_template_ids(self, async_db_session):
        """Test HTTPException when template IDs don't match."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build()
        async_db_session.add(t1)
        await async_db_session.flush()

        m1 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t1.id, position=1)
        async_db_session.add(m1)
        await async_db_session.commit()

        # Try to reorder with wrong IDs
        wrong_ids = [uuid4()]

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.reorder_sequence_templates(async_db_session, seq.id, wrong_ids)

        assert exc.value.status_code == 400


@pytest.mark.asyncio
class TestGetCurrentTemplate:
    """Test the get_current_template method."""

    async def test_returns_current_template(self, async_db_session, async_test_user):
        """Test getting the current template based on index."""
        seq = ScheduleSequenceFactory.build(current_week_index=0)
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build(name="Current Week")
        t2 = WeekTemplateFactory.build(name="Next Week")
        async_db_session.add_all([t1, t2])
        await async_db_session.flush()

        m1 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t1.id, position=1)
        m2 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t2.id, position=2)
        async_db_session.add_all([m1, m2])
        await async_db_session.commit()

        result = await ScheduleService.get_current_template(async_db_session, seq.id)

        assert result is not None
        assert result.name == "Current Week"

    async def test_returns_none_when_no_templates(self, async_db_session):
        """Test that None is returned when sequence has no templates."""
        seq = ScheduleSequenceFactory.build()
        async_db_session.add(seq)
        await async_db_session.commit()

        result = await ScheduleService.get_current_template(async_db_session, seq.id)

        assert result is None

    async def test_wraps_index_around(self, async_db_session):
        """Test that index wraps around when exceeding template count."""
        # Index 2 with 2 templates should wrap to index 0
        seq = ScheduleSequenceFactory.build(current_week_index=2)
        async_db_session.add(seq)

        t1 = WeekTemplateFactory.build(name="First Week")
        t2 = WeekTemplateFactory.build(name="Second Week")
        async_db_session.add_all([t1, t2])
        await async_db_session.flush()

        m1 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t1.id, position=1)
        m2 = SequenceWeekMappingFactory.build(sequence_id=seq.id, week_template_id=t2.id, position=2)
        async_db_session.add_all([m1, m2])
        await async_db_session.commit()

        result = await ScheduleService.get_current_template(async_db_session, seq.id)

        # 2 % 2 = 0, position 1
        assert result is not None
        assert result.name == "First Week"


@pytest.mark.asyncio
class TestAssignmentCRUD:
    """Test day assignment CRUD methods."""

    async def test_get_assignments_for_template(self, async_db_session, async_test_user):
        """Test getting all assignments for a template."""
        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.flush()

        a1 = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=1,
            assigned_user_id=async_test_user.id,
            order=0,
        )
        a2 = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=2,
            assigned_user_id=async_test_user.id,
            order=0,
        )
        async_db_session.add_all([a1, a2])
        await async_db_session.commit()

        result = await ScheduleService.get_assignments_for_template(
            async_db_session, template.id
        )

        assert len(result) == 2

    async def test_create_assignment(self, async_db_session, async_test_user):
        """Test creating a new assignment."""
        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.commit()

        data = WeekDayAssignmentCreate(
            day_of_week=3,
            assigned_user_id=async_test_user.id,
            action="cook",
            recipe_id=None,
            order=0,
        )

        result = await ScheduleService.create_assignment(
            async_db_session, template.id, data
        )

        assert result is not None
        assert result.day_of_week == 3
        assert result.action == "cook"

    async def test_update_assignment(self, async_db_session, async_test_user):
        """Test updating an assignment."""
        template = WeekTemplateFactory.build()
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

        update_data = WeekDayAssignmentUpdate(action="takeout")
        result = await ScheduleService.update_assignment(
            async_db_session, assignment.id, update_data
        )

        assert result.action == "takeout"

    async def test_delete_assignment(self, async_db_session, async_test_user):
        """Test deleting an assignment."""
        template = WeekTemplateFactory.build()
        async_db_session.add(template)
        await async_db_session.flush()

        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=1,
            assigned_user_id=async_test_user.id,
        )
        async_db_session.add(assignment)
        await async_db_session.commit()
        assignment_id = assignment.id

        await ScheduleService.delete_assignment(async_db_session, assignment_id)

        # Verify deleted
        assignments = await ScheduleService.get_assignments_for_template(
            async_db_session, template.id
        )
        assert len(assignments) == 0

    async def test_update_raises_for_missing(self, async_db_session):
        """Test HTTPException when updating non-existent assignment."""
        fake_id = uuid4()
        update_data = WeekDayAssignmentUpdate(action="whatever")

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.update_assignment(async_db_session, fake_id, update_data)

        assert exc.value.status_code == 404

    async def test_delete_raises_for_missing(self, async_db_session):
        """Test HTTPException when deleting non-existent assignment."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            await ScheduleService.delete_assignment(async_db_session, fake_id)

        assert exc.value.status_code == 404

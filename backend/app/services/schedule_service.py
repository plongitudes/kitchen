from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.schedule import (
    ScheduleSequence,
    WeekTemplate,
    SequenceWeekMapping,
    WeekDayAssignment,
)
from app.schemas.schedule import (
    ScheduleSequenceCreate,
    ScheduleSequenceUpdate,
    WeekDayAssignmentCreate,
    WeekDayAssignmentUpdate,
    TemplateReorderRequest,
)


class ScheduleService:
    """Service layer for schedule business logic."""

    # ========================================================================
    # Schedule Sequence Methods
    # ========================================================================

    @staticmethod
    async def get_sequences(db: AsyncSession) -> List[ScheduleSequence]:
        """Get list of all schedule sequences."""
        query = select(ScheduleSequence).order_by(ScheduleSequence.created_at)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_sequence_by_id(
        db: AsyncSession,
        sequence_id: UUID,
        include_mappings: bool = True,
    ) -> Optional[ScheduleSequence]:
        """Get a single sequence by ID with optional template mappings."""
        query = select(ScheduleSequence).where(ScheduleSequence.id == sequence_id)

        if include_mappings:
            query = query.options(
                selectinload(ScheduleSequence.week_mappings).selectinload(
                    SequenceWeekMapping.week_template
                )
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_sequence(
        db: AsyncSession,
        sequence_data: ScheduleSequenceCreate,
    ) -> ScheduleSequence:
        """Create a new schedule sequence."""
        sequence = ScheduleSequence(
            name=sequence_data.name,
            advancement_day_of_week=sequence_data.advancement_day_of_week,
            advancement_time=sequence_data.advancement_time,
        )

        db.add(sequence)
        await db.commit()
        await db.refresh(sequence)

        return sequence

    @staticmethod
    async def update_sequence(
        db: AsyncSession,
        sequence_id: UUID,
        sequence_data: ScheduleSequenceUpdate,
    ) -> ScheduleSequence:
        """Update a schedule sequence."""
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=False,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        # Update fields
        if sequence_data.name is not None:
            sequence.name = sequence_data.name
        if sequence_data.advancement_day_of_week is not None:
            sequence.advancement_day_of_week = sequence_data.advancement_day_of_week
        if sequence_data.advancement_time is not None:
            sequence.advancement_time = sequence_data.advancement_time

        await db.commit()
        await db.refresh(sequence)

        return sequence

    @staticmethod
    async def delete_sequence(
        db: AsyncSession,
        sequence_id: UUID,
    ) -> bool:
        """Delete a schedule sequence."""
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=False,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        await db.delete(sequence)
        await db.commit()
        return True

    # ========================================================================
    # Template Mapping Methods
    # ========================================================================

    @staticmethod
    async def get_active_templates_for_sequence(
        db: AsyncSession,
        sequence_id: UUID,
    ) -> List[SequenceWeekMapping]:
        """Get all active (non-removed) template mappings for a sequence."""
        query = (
            select(SequenceWeekMapping)
            .where(
                SequenceWeekMapping.sequence_id == sequence_id,
                SequenceWeekMapping.removed_at.is_(None),
            )
            .options(selectinload(SequenceWeekMapping.week_template))
            .order_by(SequenceWeekMapping.position)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def add_template_to_sequence(
        db: AsyncSession,
        sequence_id: UUID,
        template_id: UUID,
        position: Optional[int] = None,
    ) -> SequenceWeekMapping:
        """Add a template to a sequence at a specific position."""
        # Verify sequence exists
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=False,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        # Verify template exists
        from app.services.template_service import TemplateService

        template = await TemplateService.get_template_by_id(
            db=db,
            template_id=template_id,
            include_assignments=False,
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Week template not found",
            )

        # Get existing mappings
        existing_mappings = await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

        # Determine position
        if position is None:
            position = len(existing_mappings) + 1

        # Create mapping
        mapping = SequenceWeekMapping(
            sequence_id=sequence_id,
            week_template_id=template_id,
            position=position,
        )

        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)

        return mapping

    @staticmethod
    async def remove_template_from_sequence(
        db: AsyncSession,
        sequence_id: UUID,
        template_id: UUID,
    ) -> bool:
        """Remove (soft delete) a template from a sequence."""
        # Find the mapping
        query = select(SequenceWeekMapping).where(
            SequenceWeekMapping.sequence_id == sequence_id,
            SequenceWeekMapping.week_template_id == template_id,
            SequenceWeekMapping.removed_at.is_(None),
        )

        result = await db.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template mapping not found in sequence",
            )

        # Soft delete
        mapping.removed_at = datetime.utcnow()
        await db.commit()

        return True

    @staticmethod
    async def reorder_sequence_templates(
        db: AsyncSession,
        sequence_id: UUID,
        template_ids: List[UUID],
    ) -> List[SequenceWeekMapping]:
        """Reorder templates in a sequence."""
        # Verify sequence exists
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=False,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        # Get all active mappings
        mappings = await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

        # Build dict of mappings by template_id
        mapping_dict = {m.week_template_id: m for m in mappings}

        # Verify all template_ids match
        if set(template_ids) != set(mapping_dict.keys()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template IDs do not match sequence templates",
            )

        # Update positions
        for index, template_id in enumerate(template_ids, start=1):
            mapping_dict[template_id].position = index

        await db.commit()

        # Return reordered mappings
        return await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

    @staticmethod
    async def get_current_template(
        db: AsyncSession,
        sequence_id: UUID,
    ) -> Optional[WeekTemplate]:
        """Get the currently active week template for a sequence."""
        # Get sequence with current_week_index
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=False,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        # Get active mappings
        mappings = await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

        if not mappings:
            return None

        # Calculate current template based on index (0-based)
        # Loop back to start if index exceeds template count
        current_index = sequence.current_week_index % len(mappings)

        # Find mapping at current position (positions are 1-based)
        for mapping in mappings:
            if mapping.position == current_index + 1:
                # Load template with assignments
                from app.services.template_service import TemplateService

                template = await TemplateService.get_template_by_id(
                    db=db,
                    template_id=mapping.week_template_id,
                    include_assignments=True,
                )
                return template

        return None

    # ========================================================================
    # Week Day Assignment Methods
    # ========================================================================

    @staticmethod
    async def get_assignments_for_template(
        db: AsyncSession,
        template_id: UUID,
    ) -> List[WeekDayAssignment]:
        """Get all day assignments for a template."""
        query = (
            select(WeekDayAssignment)
            .where(WeekDayAssignment.week_template_id == template_id)
            .order_by(WeekDayAssignment.day_of_week, WeekDayAssignment.order)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_assignment(
        db: AsyncSession,
        template_id: UUID,
        assignment_data: WeekDayAssignmentCreate,
    ) -> WeekDayAssignment:
        """Create a new day assignment for a template."""
        # Verify template exists
        from app.services.template_service import TemplateService

        template = await TemplateService.get_template_by_id(
            db=db,
            template_id=template_id,
            include_assignments=False,
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Week template not found",
            )

        assignment = WeekDayAssignment(
            week_template_id=template_id,
            day_of_week=assignment_data.day_of_week,
            assigned_user_id=assignment_data.assigned_user_id,
            action=assignment_data.action,
            recipe_id=assignment_data.recipe_id,
            order=assignment_data.order,
        )

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        return assignment

    @staticmethod
    async def update_assignment(
        db: AsyncSession,
        assignment_id: UUID,
        assignment_data: WeekDayAssignmentUpdate,
    ) -> WeekDayAssignment:
        """Update a day assignment."""
        query = select(WeekDayAssignment).where(WeekDayAssignment.id == assignment_id)
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        # Update fields
        if assignment_data.day_of_week is not None:
            assignment.day_of_week = assignment_data.day_of_week
        if assignment_data.assigned_user_id is not None:
            assignment.assigned_user_id = assignment_data.assigned_user_id
        if assignment_data.action is not None:
            assignment.action = assignment_data.action
        if assignment_data.recipe_id is not None:
            assignment.recipe_id = assignment_data.recipe_id
        if assignment_data.order is not None:
            assignment.order = assignment_data.order

        await db.commit()
        await db.refresh(assignment)

        return assignment

    @staticmethod
    async def delete_assignment(
        db: AsyncSession,
        assignment_id: UUID,
    ) -> None:
        """Delete a day assignment."""
        query = select(WeekDayAssignment).where(WeekDayAssignment.id == assignment_id)
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        await db.delete(assignment)
        await db.commit()

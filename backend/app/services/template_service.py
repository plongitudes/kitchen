"""Service layer for week template management."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.schedule import WeekTemplate, WeekDayAssignment, SequenceWeekMapping, ScheduleSequence
from app.models.meal_plan import MealPlanInstance
from app.schemas.schedule import WeekTemplateCreate, WeekTemplateUpdate, WeekDayAssignmentCreate


class TemplateService:
    """Service for managing week templates."""

    @staticmethod
    async def list_templates(db, include_retired: bool = False) -> List[WeekTemplate]:
        """
        List all week templates.

        Args:
            db: Database session
            include_retired: If True, include retired templates

        Returns:
            List of WeekTemplate objects
        """
        query = select(WeekTemplate)

        if not include_retired:
            query = query.where(WeekTemplate.retired_at.is_(None))

        query = query.order_by(WeekTemplate.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_template_by_id(
        db,
        template_id: UUID,
        include_assignments: bool = True
    ) -> Optional[WeekTemplate]:
        """
        Get a specific week template by ID.

        Args:
            db: Database session
            template_id: UUID of the template
            include_assignments: If True, eagerly load day assignments

        Returns:
            WeekTemplate object or None if not found
        """
        query = select(WeekTemplate).where(WeekTemplate.id == template_id)

        if include_assignments:
            query = query.options(
                selectinload(WeekTemplate.day_assignments).selectinload(
                    WeekDayAssignment.recipe
                )
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_template(
        db,
        template_data: WeekTemplateCreate
    ) -> WeekTemplate:
        """
        Create a new week template with assignments.

        Args:
            db: Database session
            template_data: Template creation schema

        Returns:
            Created WeekTemplate object
        """
        # Create the template
        template = WeekTemplate(name=template_data.name)
        db.add(template)
        await db.flush()  # Get the ID

        # Create day assignments
        for assignment_data in template_data.assignments:
            assignment = WeekDayAssignment(
                week_template_id=template.id,
                day_of_week=assignment_data.day_of_week,
                assigned_user_id=assignment_data.assigned_user_id,
                action=assignment_data.action,
                recipe_id=assignment_data.recipe_id,
                order=assignment_data.order,
            )
            db.add(assignment)

        await db.commit()
        await db.refresh(template)

        # Load with assignments
        return await TemplateService.get_template_by_id(db, template.id)

    @staticmethod
    async def update_template(
        db,
        template_id: UUID,
        template_data: WeekTemplateUpdate
    ) -> Optional[WeekTemplate]:
        """
        Update a week template.

        Args:
            db: Database session
            template_id: UUID of the template
            template_data: Template update schema

        Returns:
            Updated WeekTemplate object or None if not found
        """
        template = await TemplateService.get_template_by_id(db, template_id, include_assignments=True)
        if not template:
            return None

        # Update fields
        if template_data.name is not None:
            template.name = template_data.name

        # Update assignments if provided
        if template_data.assignments is not None:
            # Delete all existing assignments
            for assignment in template.day_assignments:
                await db.delete(assignment)
            await db.flush()

            # Create new assignments
            for assignment_data in template_data.assignments:
                assignment = WeekDayAssignment(
                    week_template_id=template.id,
                    day_of_week=assignment_data.day_of_week,
                    assigned_user_id=assignment_data.assigned_user_id,
                    action=assignment_data.action,
                    recipe_id=assignment_data.recipe_id,
                    order=assignment_data.order,
                )
                db.add(assignment)

        await db.commit()
        await db.refresh(template)

        # Return with assignments loaded
        return await TemplateService.get_template_by_id(db, template.id)

    @staticmethod
    async def fork_template(
        db,
        template_id: UUID,
        new_name: Optional[str] = None
    ) -> Optional[WeekTemplate]:
        """
        Fork (deep copy) a week template.

        Args:
            db: Database session
            template_id: UUID of the template to fork
            new_name: Optional new name, defaults to "Fork of [original name]"

        Returns:
            New forked WeekTemplate object or None if original not found
        """
        # Load original template with assignments
        original = await TemplateService.get_template_by_id(db, template_id, include_assignments=True)
        if not original:
            return None

        # Determine new name
        fork_name = new_name or f"Fork of {original.name}"

        # Create new template
        forked = WeekTemplate(name=fork_name)
        db.add(forked)
        await db.flush()  # Get the ID

        # Deep copy all day assignments
        for original_assignment in original.day_assignments:
            forked_assignment = WeekDayAssignment(
                week_template_id=forked.id,
                day_of_week=original_assignment.day_of_week,
                assigned_user_id=original_assignment.assigned_user_id,
                action=original_assignment.action,
                recipe_id=original_assignment.recipe_id,
                order=original_assignment.order,
            )
            db.add(forked_assignment)

        await db.commit()
        await db.refresh(forked)

        # Load with assignments
        return await TemplateService.get_template_by_id(db, forked.id)

    @staticmethod
    async def retire_template(
        db,
        template_id: UUID
    ) -> dict:
        """
        Retire a week template (soft delete).

        This removes the template from all sequences and auto-advances
        sequences that are currently on this template.

        Args:
            db: Database session
            template_id: UUID of the template to retire

        Returns:
            Dict with:
                - template: The retired template
                - affected_sequences: List of sequences that were auto-advanced
                - can_hard_delete: Whether template can be safely deleted
        """
        template = await TemplateService.get_template_by_id(db, template_id, include_assignments=False)
        if not template:
            return None

        # Check if any MealPlanInstances reference this template
        instances_query = select(MealPlanInstance).where(
            MealPlanInstance.week_template_id == template_id
        )
        instances_result = await db.execute(instances_query)
        instances = instances_result.scalars().all()
        can_hard_delete = len(instances) == 0

        # Soft delete the template
        template.retired_at = datetime.utcnow()

        # Find all sequence mappings for this template
        mappings_query = select(SequenceWeekMapping).where(
            SequenceWeekMapping.week_template_id == template_id,
            SequenceWeekMapping.removed_at.is_(None)
        ).options(selectinload(SequenceWeekMapping.sequence))

        mappings_result = await db.execute(mappings_query)
        mappings = mappings_result.scalars().all()

        affected_sequences = []

        for mapping in mappings:
            # Mark mapping as removed
            mapping.removed_at = datetime.utcnow()

            sequence = mapping.sequence

            # Check if this sequence is currently on this template
            # Get active mappings for this sequence
            active_mappings_query = select(SequenceWeekMapping).where(
                SequenceWeekMapping.sequence_id == sequence.id,
                SequenceWeekMapping.removed_at.is_(None)
            ).order_by(SequenceWeekMapping.position)

            active_mappings_result = await db.execute(active_mappings_query)
            active_mappings = active_mappings_result.scalars().all()

            # Find current position (excluding the one we just removed)
            current_position = sequence.current_week_index
            if current_position < len(active_mappings) and active_mappings[current_position].week_template_id == template_id:
                # This sequence is currently on the retired template
                # Auto-advance to next week
                sequence.current_week_index = (current_position + 1) % len(active_mappings)
                affected_sequences.append({
                    'sequence_id': sequence.id,
                    'sequence_name': sequence.name,
                    'old_position': current_position,
                    'new_position': sequence.current_week_index,
                })

        await db.commit()
        await db.refresh(template)

        return {
            'template': template,
            'affected_sequences': affected_sequences,
            'can_hard_delete': can_hard_delete,
        }

    @staticmethod
    async def delete_template(db, template_id: UUID) -> bool:
        """
        Hard delete a template (only if not referenced by any instances).

        Args:
            db: Database session
            template_id: UUID of the template

        Returns:
            True if deleted, False if cannot delete (has instances)
        """
        template = await TemplateService.get_template_by_id(db, template_id, include_assignments=False)
        if not template:
            return False

        # Check if any MealPlanInstances reference this template
        instances_query = select(MealPlanInstance).where(
            MealPlanInstance.week_template_id == template_id
        )
        instances_result = await db.execute(instances_query)
        instances = instances_result.scalars().all()

        if len(instances) > 0:
            return False  # Cannot delete, has instances

        # Safe to delete
        await db.delete(template)
        await db.commit()
        return True

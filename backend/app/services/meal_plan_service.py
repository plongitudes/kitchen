from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.meal_plan import MealPlanInstance, MealAssignment
from app.models.schedule import (
    ScheduleSequence,
    WeekTemplate,
    SequenceWeekMapping,
    WeekDayAssignment,
)
from app.models.recipe import Recipe
from app.schemas.meal_plan import DayAssignmentWithDate
from app.services.schedule_service import ScheduleService
import logging

logger = logging.getLogger(__name__)


class MealPlanService:
    """Service layer for meal plan business logic."""

    # ========================================================================
    # Meal Plan Instance Methods
    # ========================================================================

    @staticmethod
    async def get_instances(
        db: AsyncSession,
        limit: Optional[int] = None,
    ) -> List[MealPlanInstance]:
        """Get list of all meal plan instances, ordered by date descending."""
        query = (
            select(MealPlanInstance)
            .options(selectinload(MealPlanInstance.week_template))
            .order_by(desc(MealPlanInstance.instance_start_date))
        )

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_instance_by_id(
        db: AsyncSession,
        instance_id: UUID,
    ) -> Optional[MealPlanInstance]:
        """Get a single instance by ID with template and assignments."""
        query = (
            select(MealPlanInstance)
            .where(MealPlanInstance.id == instance_id)
            .options(
                selectinload(MealPlanInstance.week_template).selectinload(
                    WeekTemplate.day_assignments
                )
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_current_instance(
        db: AsyncSession,
        sequence_id: UUID,
    ) -> Optional[MealPlanInstance]:
        """Get the most recent meal plan instance for a sequence."""
        # Get the sequence with current template
        sequence = await ScheduleService.get_sequence_by_id(
            db=db,
            sequence_id=sequence_id,
            include_mappings=True,
        )

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule sequence not found",
            )

        # Get active template IDs from mappings
        template_ids = [
            mapping.week_template_id
            for mapping in sequence.week_mappings
            if mapping.removed_at is None
        ]

        if not template_ids:
            return None

        # Get the most recent instance for any of these templates
        query = (
            select(MealPlanInstance)
            .where(MealPlanInstance.week_template_id.in_(template_ids))
            .options(
                selectinload(MealPlanInstance.week_template).selectinload(
                    WeekTemplate.day_assignments
                )
            )
            .order_by(desc(MealPlanInstance.instance_start_date))
            .limit(1)
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_instance(
        db: AsyncSession,
        template_id: UUID,
        instance_start_date: date,
        sequence_id: Optional[UUID] = None,
    ) -> MealPlanInstance:
        """Create a new meal plan instance from a week template.

        Args:
            db: Database session
            template_id: UUID of the week template
            instance_start_date: Start date for the instance
            sequence_id: Optional UUID of the sequence that created this instance
        """
        # Verify template exists
        from app.services.template_service import TemplateService

        template = await TemplateService.get_template_by_id(
            db=db,
            template_id=template_id,
            include_assignments=True,
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Week template not found",
            )

        # Create instance
        instance = MealPlanInstance(
            sequence_id=sequence_id,
            week_template_id=template_id,
            instance_start_date=instance_start_date,
        )

        db.add(instance)
        await db.commit()
        await db.refresh(instance)

        # Load relationships for response
        instance = await MealPlanService.get_instance_by_id(
            db=db,
            instance_id=instance.id,
        )

        return instance

    @staticmethod
    async def auto_generate_grocery_lists(
        db: AsyncSession,
        instance: MealPlanInstance,
    ) -> List:
        """Auto-generate grocery lists for all shopping days in the instance's template.

        Args:
            db: Database session
            instance: MealPlanInstance to generate grocery lists for

        Returns:
            List of generated GroceryList objects
        """
        from app.services.grocery_service import GroceryService

        # Load template with assignments if not already loaded
        if not instance.week_template:
            instance = await MealPlanService.get_instance_by_id(
                db=db,
                instance_id=instance.id,
            )

        template = instance.week_template
        start_date = instance.instance_start_date

        # Find all shop days in the template
        shopping_days = []
        for assignment in template.day_assignments:
            if assignment.action.lower() == "shop":
                shopping_date = start_date + timedelta(days=assignment.day_of_week)
                shopping_days.append(shopping_date)

        if not shopping_days:
            logger.info(f"No shopping days found for instance {instance.id}, skipping grocery list generation")
            return []

        # Generate a grocery list for each shopping day
        generated_lists = []
        for shopping_date in shopping_days:
            try:
                grocery_list = await GroceryService.generate_grocery_list(
                    db=db,
                    instance_id=instance.id,
                    shopping_date=shopping_date,
                )
                generated_lists.append(grocery_list)
                logger.info(f"Auto-generated grocery list for {shopping_date} (instance {instance.id})")
            except HTTPException as e:
                # Log but don't fail if grocery list generation has issues
                logger.warning(f"Could not generate grocery list for {shopping_date}: {e.detail}")
            except Exception as e:
                logger.error(f"Error generating grocery list for {shopping_date}: {e}")

        return generated_lists

    @staticmethod
    async def get_merged_assignments_for_day(
        db: AsyncSession,
        instance: MealPlanInstance,
        day_of_week: int,
    ) -> List[tuple]:
        """Get merged assignments for a specific day of week.

        Merges template assignments with per-instance overrides.
        Per-instance assignments take precedence over template assignments.

        Args:
            db: Database session
            instance: MealPlanInstance to get assignments for
            day_of_week: Day of week (0=Sunday, 6=Saturday)

        Returns:
            List of tuples: (assignment_object, user, recipe)
            where assignment_object is either MealAssignment or WeekDayAssignment
        """
        from app.models.user import User

        template = instance.week_template

        # Load per-instance overrides for this day
        meal_assignments_query = (
            select(MealAssignment)
            .where(MealAssignment.meal_plan_instance_id == instance.id)
            .where(MealAssignment.day_of_week == day_of_week)
            .order_by(MealAssignment.order)
        )
        meal_assignments_result = await db.execute(meal_assignments_query)
        meal_assignments = meal_assignments_result.scalars().all()

        results = []

        # If there are per-instance overrides, use those
        if meal_assignments:
            for assignment in meal_assignments:
                # Get user
                user_result = await db.execute(
                    select(User).where(User.id == assignment.assigned_user_id)
                )
                user = user_result.scalar_one_or_none()

                # Get recipe if needed
                recipe = None
                if assignment.recipe_id:
                    recipe_result = await db.execute(
                        select(Recipe).where(Recipe.id == assignment.recipe_id)
                    )
                    recipe = recipe_result.scalar_one_or_none()

                results.append((assignment, user, recipe))
        else:
            # Use template assignments for this day
            for day_assignment in template.day_assignments:
                if day_assignment.day_of_week == day_of_week:
                    # Get user
                    user_result = await db.execute(
                        select(User).where(User.id == day_assignment.assigned_user_id)
                    )
                    user = user_result.scalar_one_or_none()

                    # Get recipe if needed
                    recipe = None
                    if day_assignment.recipe_id:
                        recipe_result = await db.execute(
                            select(Recipe).where(Recipe.id == day_assignment.recipe_id)
                        )
                        recipe = recipe_result.scalar_one_or_none()

                    results.append((day_assignment, user, recipe))

        return results

    @staticmethod
    async def build_instance_detail(
        instance: MealPlanInstance,
        db: AsyncSession,
    ) -> dict:
        """Build detailed response with assignments and calculated dates.

        Merges template assignments from week with per-instance overrides from meal_assignments.
        Per-instance assignments take precedence over template assignments for the same day_of_week.
        """
        template = instance.week_template

        # Load meal_assignments for this instance (per-instance overrides)
        from app.models.meal_plan import MealAssignment

        meal_assignments_query = (
            select(MealAssignment)
            .where(MealAssignment.meal_plan_instance_id == instance.id)
            .order_by(MealAssignment.day_of_week, MealAssignment.order)
        )
        meal_assignments_result = await db.execute(meal_assignments_query)
        meal_assignments = meal_assignments_result.scalars().all()

        # Build a map of day_of_week -> list of meal_assignments
        meal_assignments_by_day = {}
        for ma in meal_assignments:
            if ma.day_of_week not in meal_assignments_by_day:
                meal_assignments_by_day[ma.day_of_week] = []
            meal_assignments_by_day[ma.day_of_week].append(ma)

        # Calculate dates and build assignments
        # Use meal_assignments if they exist for a day, otherwise use template assignments
        assignments = []

        # Process each day of the week (0-6)
        for day_of_week in range(7):
            actual_date = instance.instance_start_date + timedelta(days=day_of_week)

            # Check if there are per-instance overrides for this day
            if day_of_week in meal_assignments_by_day:
                # Use per-instance assignments
                for meal_assignment in meal_assignments_by_day[day_of_week]:
                    recipe_name = None
                    if meal_assignment.recipe_id:
                        recipe_query = select(Recipe).where(
                            Recipe.id == meal_assignment.recipe_id
                        )
                        recipe_result = await db.execute(recipe_query)
                        recipe = recipe_result.scalar_one_or_none()
                        if recipe:
                            recipe_name = recipe.name

                    assignment_with_date = DayAssignmentWithDate(
                        id=meal_assignment.id,
                        date=actual_date,
                        day_of_week=meal_assignment.day_of_week,
                        assigned_user_id=meal_assignment.assigned_user_id,
                        action=meal_assignment.action,
                        recipe_id=meal_assignment.recipe_id,
                        recipe_name=recipe_name,
                        order=meal_assignment.order,
                        is_modified=True,
                    )
                    assignments.append(assignment_with_date)
            else:
                # Use template assignments for this day
                for day_assignment in template.day_assignments:
                    if day_assignment.day_of_week == day_of_week:
                        recipe_name = None
                        if day_assignment.recipe_id:
                            recipe_query = select(Recipe).where(
                                Recipe.id == day_assignment.recipe_id
                            )
                            recipe_result = await db.execute(recipe_query)
                            recipe = recipe_result.scalar_one_or_none()
                            if recipe:
                                recipe_name = recipe.name

                        assignment_with_date = DayAssignmentWithDate(
                            date=actual_date,
                            day_of_week=day_assignment.day_of_week,
                            assigned_user_id=day_assignment.assigned_user_id,
                            action=day_assignment.action,
                            recipe_id=day_assignment.recipe_id,
                            recipe_name=recipe_name,
                            order=day_assignment.order,
                        )
                        assignments.append(assignment_with_date)

        # Calculate week_number from sequence position
        # Use the sequence_id to find the correct mapping
        from app.models.schedule import SequenceWeekMapping

        week_number = 0

        if instance.sequence_id:
            # Instance was created by a sequence - get position from that specific sequence
            mapping_query = select(SequenceWeekMapping).where(
                SequenceWeekMapping.sequence_id == instance.sequence_id,
                SequenceWeekMapping.week_template_id == instance.week_template_id,
                SequenceWeekMapping.removed_at.is_(None),
            )
            mapping_result = await db.execute(mapping_query)
            mapping = mapping_result.scalar_one_or_none()
            week_number = mapping.position if mapping else 0
        else:
            # Instance was created manually (no sequence) - try to find any active mapping
            mapping_query = (
                select(SequenceWeekMapping)
                .where(
                    SequenceWeekMapping.week_template_id == instance.week_template_id,
                    SequenceWeekMapping.removed_at.is_(None),
                )
                .limit(1)
            )
            mapping_result = await db.execute(mapping_query)
            mapping = mapping_result.scalar_one_or_none()
            week_number = mapping.position if mapping else 0

        return {
            "id": instance.id,
            "week_template_id": instance.week_template_id,
            "instance_start_date": instance.instance_start_date,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
            "theme_name": template.name,
            "week_number": week_number,
            "assignments": assignments,
        }

    @staticmethod
    async def advance_week(
        db: AsyncSession,
        sequence_id: UUID,
    ) -> dict:
        """Manually advance to the next week in the sequence."""
        # Get sequence
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

        # Get active template mappings
        mappings = await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active templates in sequence",
            )

        # Store old position for response
        old_position = sequence.current_week_index
        old_week_number = (old_position % len(mappings)) + 1

        # Increment and loop back if needed
        new_position = (sequence.current_week_index + 1) % len(mappings)
        sequence.current_week_index = new_position

        # Find the mapping at new position (positions are 1-based)
        new_mapping = None
        for mapping in mappings:
            if mapping.position == new_position + 1:
                new_mapping = mapping
                break

        if not new_mapping:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template mapping not found for new index",
            )

        # Calculate start date (today or next occurrence of advancement day)
        today = date.today()

        # Create new instance starting today
        instance = await MealPlanService.create_instance(
            db=db,
            template_id=new_mapping.week_template_id,
            instance_start_date=today,
            sequence_id=sequence_id,
        )

        # Auto-generate grocery lists for shop days
        await MealPlanService.auto_generate_grocery_lists(
            db=db,
            instance=instance,
        )

        await db.commit()
        await db.refresh(sequence)

        # Build detailed response
        instance_detail = await MealPlanService.build_instance_detail(
            instance=instance,
            db=db,
        )

        return {
            "new_instance": instance_detail,
            "old_week_number": old_week_number,
            "new_week_number": new_mapping.position,
            "sequence_current_week_index": sequence.current_week_index,
        }

    @staticmethod
    async def start_on_arbitrary_week(
        db: AsyncSession,
        sequence_id: UUID,
        week_template_id: UUID,
        position: int,
    ) -> dict:
        """Start a schedule on an arbitrary week with smooth transition.

        This allows users to:
        1. Start a new schedule mid-week
        2. Switch from one schedule to another
        3. Preserve history from existing instances

        Args:
            db: Database session
            sequence_id: The schedule sequence to start
            week_template_id: The template to start with
            position: The 1-indexed position of the template in the sequence

        Returns:
            Dict with new instance details and transition info
        """
        # Get sequence
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

        # Validate that the template exists in the sequence
        mappings = await ScheduleService.get_active_templates_for_sequence(
            db=db,
            sequence_id=sequence_id,
        )

        if not mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active templates in sequence",
            )

        # Verify the template and position match
        target_mapping = None
        for mapping in mappings:
            if (
                mapping.week_template_id == week_template_id
                and mapping.position == position
            ):
                target_mapping = mapping
                break

        if not target_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template not found at position {position} in sequence",
            )

        # Calculate instance start date (most recent Sunday or today if today is Sunday)
        # Note: Python's weekday() returns 0=Monday, 6=Sunday
        # We need to convert to our 0=Sunday convention
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        instance_start_date = today - timedelta(days=days_since_sunday)

        # Check if there's an existing instance for this sequence for the current week
        # Query for instances with the same start date OR the sequence's current instance
        existing_instance_query = (
            select(MealPlanInstance)
            .where(
                MealPlanInstance.sequence_id == sequence_id,
                MealPlanInstance.instance_start_date == instance_start_date,
            )
            .options(selectinload(MealPlanInstance.meal_assignments))
        )

        existing_instance_result = await db.execute(existing_instance_query)
        existing_instance = existing_instance_result.scalar_one_or_none()

        preserved_assignments = []

        if existing_instance:
            # Preserve meal assignments from past days (before today)
            # Use the existing instance's start date for calculating which days are in the past
            existing_start_date = existing_instance.instance_start_date
            for assignment in existing_instance.meal_assignments:
                assignment_date = existing_start_date + timedelta(
                    days=assignment.day_of_week
                )
                if assignment_date < today:
                    # Store data to recreate this assignment
                    preserved_assignments.append(
                        {
                            "day_of_week": assignment.day_of_week,
                            "assigned_user_id": assignment.assigned_user_id,
                            "action": assignment.action,
                            "recipe_id": assignment.recipe_id,
                            "order": assignment.order,
                        }
                    )

            # Delete the old instance (cascades to meal_assignments and grocery_lists)
            await db.delete(existing_instance)
            await db.flush()

        # Create new instance
        new_instance = await MealPlanService.create_instance(
            db=db,
            template_id=week_template_id,
            instance_start_date=instance_start_date,
            sequence_id=sequence_id,
        )

        # Auto-generate grocery lists for shop days
        await MealPlanService.auto_generate_grocery_lists(
            db=db,
            instance=new_instance,
        )

        # Add preserved assignments back
        for assignment_data in preserved_assignments:
            meal_assignment = MealAssignment(
                meal_plan_instance_id=new_instance.id, **assignment_data
            )
            db.add(meal_assignment)

        # Update sequence current_week_index to this position (0-indexed)
        sequence.current_week_index = position - 1

        await db.commit()
        await db.refresh(new_instance)
        await db.refresh(sequence)

        # Build detailed response
        instance_detail = await MealPlanService.build_instance_detail(
            instance=new_instance,
            db=db,
        )

        return {
            "new_instance": instance_detail,
            "week_number": position,
            "sequence_current_week_index": sequence.current_week_index,
            "transition_type": "switched" if existing_instance else "fresh_start",
            "preserved_days": len(preserved_assignments),
        }

    # ========================================================================
    # Meal Assignment Methods (Per-Instance Modifications)
    # ========================================================================

    @staticmethod
    async def get_meal_assignments(
        db: AsyncSession,
        instance_id: UUID,
    ) -> list:
        """Get all meal assignments for a meal plan instance."""
        from app.models.meal_plan import MealAssignment

        result = await db.execute(
            select(MealAssignment)
            .where(MealAssignment.meal_plan_instance_id == instance_id)
            .order_by(MealAssignment.day_of_week, MealAssignment.order)
        )
        return result.scalars().all()

    @staticmethod
    async def create_meal_assignment(
        db: AsyncSession,
        instance_id: UUID,
        assignment_data,
    ):
        """Create a new meal assignment for an instance."""
        from app.models.meal_plan import MealAssignment

        # Verify instance exists
        instance = await MealPlanService.get_instance_by_id(
            db=db, instance_id=instance_id
        )
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan instance not found",
            )

        # Validate recipe_id required for cook action
        if assignment_data.action == "cook" and not assignment_data.recipe_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="recipe_id is required when action is 'cook'",
            )

        assignment = MealAssignment(
            meal_plan_instance_id=instance_id,
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
    async def update_meal_assignment(
        db: AsyncSession,
        instance_id: UUID,
        assignment_id: UUID,
        assignment_data,
    ):
        """
        Update a meal assignment.

        Uses lazy creation: if assignment_id is a template assignment (WeekDayAssignment),
        create a new MealAssignment record first, then update it.
        """
        from app.models.meal_plan import MealAssignment
        from app.models.schedule import WeekDayAssignment

        # Try to find existing MealAssignment
        result = await db.execute(
            select(MealAssignment).where(
                MealAssignment.id == assignment_id,
                MealAssignment.meal_plan_instance_id == instance_id,
            )
        )
        assignment = result.scalar_one_or_none()

        # If no MealAssignment exists, this might be a template assignment ID
        # We need to create a MealAssignment as an override
        if not assignment:
            # Check if assignment_id is a template assignment
            template_assignment_result = await db.execute(
                select(WeekDayAssignment).where(WeekDayAssignment.id == assignment_id)
            )
            template_assignment = template_assignment_result.scalar_one_or_none()

            if not template_assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found in template or instance",
                )

            # Verify this template assignment belongs to the instance's template
            instance = await MealPlanService.get_instance_by_id(db, instance_id)
            if (
                not instance
                or template_assignment.week_template_id != instance.week_template_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignment does not belong to this instance's template",
                )

            # Create new MealAssignment as override (lazy creation)
            assignment = MealAssignment(
                meal_plan_instance_id=instance_id,
                day_of_week=template_assignment.day_of_week,
                assigned_user_id=template_assignment.assigned_user_id,
                action=template_assignment.action,
                recipe_id=template_assignment.recipe_id,
                order=template_assignment.order,
            )
            db.add(assignment)
            await db.flush()  # Get the ID

        # Now update the assignment with new values
        if assignment_data.assigned_user_id is not None:
            assignment.assigned_user_id = assignment_data.assigned_user_id
        if assignment_data.action is not None:
            assignment.action = assignment_data.action
        if assignment_data.recipe_id is not None:
            assignment.recipe_id = assignment_data.recipe_id
        if assignment_data.order is not None:
            assignment.order = assignment_data.order

        # Validate recipe_id required for cook action
        if assignment.action == "cook" and not assignment.recipe_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="recipe_id is required when action is 'cook'",
            )

        await db.commit()
        await db.refresh(assignment)

        return assignment

    @staticmethod
    async def delete_meal_assignment(
        db: AsyncSession,
        instance_id: UUID,
        assignment_id: UUID,
    ):
        """Delete a meal assignment."""
        from app.models.meal_plan import MealAssignment

        result = await db.execute(
            select(MealAssignment).where(
                MealAssignment.id == assignment_id,
                MealAssignment.meal_plan_instance_id == instance_id,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal assignment not found",
            )

        await db.delete(assignment)
        await db.commit()

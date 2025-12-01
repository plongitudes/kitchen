"""
Model factories for testing.

These factories create model instances with sensible defaults.
Use them to quickly set up test data without specifying every field.

Usage:
    # Simple creation (no DB)
    user = UserFactory.build()
    recipe = RecipeFactory.build(owner_id=user.id)

    # With ingredients
    recipe = RecipeFactory.build_with_ingredients(
        owner_id=user.id,
        ingredients=[("flour", 2, "cup"), ("sugar", 1, "cup")]
    )

    # Persist to DB
    user = UserFactory.create(db_session)
    recipe = RecipeFactory.create(db_session, owner_id=user.id)
"""

from datetime import date
from typing import Optional, List, Tuple
from uuid import uuid4, UUID

from app.models.user import User
from app.models.recipe import Recipe, RecipeIngredient, RecipeInstruction, RecipePrepStep, PrepStepIngredient, IngredientUnit
from app.models.schedule import (
    ScheduleSequence,
    WeekTemplate,
    WeekDayAssignment,
    SequenceWeekMapping,
)
from app.models.meal_plan import (
    MealPlanInstance,
    MealAssignment,
    GroceryList,
    GroceryListItem,
)
from app.models.ingredient import CommonIngredient, IngredientAlias


class UserFactory:
    """Factory for creating User instances."""

    _counter = 0

    @classmethod
    def _next_username(cls) -> str:
        cls._counter += 1
        return f"testuser{cls._counter}"

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        username: Optional[str] = None,
        password_hash: str = "hashed_password",
        discord_user_id: Optional[str] = None,
    ) -> User:
        """Build a User instance without persisting."""
        return User(
            id=id or uuid4(),
            username=username or cls._next_username(),
            password_hash=password_hash,
            discord_user_id=discord_user_id,
        )

    @classmethod
    def create(cls, db, **kwargs) -> User:
        """Create and persist a User instance."""
        user = cls.build(**kwargs)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    async def create_async(cls, db, **kwargs) -> User:
        """Create and persist a User instance (async)."""
        user = cls.build(**kwargs)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


class RecipeFactory:
    """Factory for creating Recipe instances."""

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Recipe {cls._counter}"

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        owner_id: Optional[UUID] = None,
        name: Optional[str] = None,
        recipe_type: Optional[str] = "dinner",
        description: Optional[str] = None,
        prep_time_minutes: Optional[int] = 15,
        cook_time_minutes: Optional[int] = 30,
        prep_notes: Optional[str] = None,
        postmortem_notes: Optional[str] = None,
        source_url: Optional[str] = None,
        retired_at=None,
    ) -> Recipe:
        """Build a Recipe instance without persisting."""
        if owner_id is None:
            raise ValueError("owner_id is required for Recipe")

        return Recipe(
            id=id or uuid4(),
            owner_id=owner_id,
            name=name or cls._next_name(),
            recipe_type=recipe_type,
            description=description,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
            prep_notes=prep_notes,
            postmortem_notes=postmortem_notes,
            source_url=source_url,
            retired_at=retired_at,
        )

    @classmethod
    def build_with_ingredients(
        cls,
        owner_id: UUID,
        ingredients: List[Tuple[str, float, str]],
        **kwargs,
    ) -> Recipe:
        """
        Build a Recipe with ingredients.

        Args:
            owner_id: Owner user ID
            ingredients: List of (name, quantity, unit) tuples
            **kwargs: Additional Recipe fields

        Returns:
            Recipe with populated ingredients list
        """
        recipe = cls.build(owner_id=owner_id, **kwargs)

        for order, (name, qty, unit) in enumerate(ingredients):
            ingredient = RecipeIngredientFactory.build(
                recipe_id=recipe.id,
                ingredient_name=name,
                quantity=qty,
                unit=unit,
                order=order,
            )
            recipe.ingredients.append(ingredient)

        return recipe

    @classmethod
    def build_with_instructions(
        cls,
        owner_id: UUID,
        instructions: List[str],
        **kwargs,
    ) -> Recipe:
        """
        Build a Recipe with instructions.

        Args:
            owner_id: Owner user ID
            instructions: List of instruction strings
            **kwargs: Additional Recipe fields
        """
        recipe = cls.build(owner_id=owner_id, **kwargs)

        for step_num, description in enumerate(instructions, start=1):
            instruction = RecipeInstructionFactory.build(
                recipe_id=recipe.id,
                step_number=step_num,
                description=description,
            )
            recipe.instructions.append(instruction)

        return recipe

    @classmethod
    def create(cls, db, **kwargs) -> Recipe:
        """Create and persist a Recipe instance."""
        recipe = cls.build(**kwargs)
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return recipe

    @classmethod
    async def create_async(cls, db, **kwargs) -> Recipe:
        """Create and persist a Recipe instance (async)."""
        recipe = cls.build(**kwargs)
        db.add(recipe)
        await db.commit()
        await db.refresh(recipe)
        return recipe


class RecipeIngredientFactory:
    """Factory for creating RecipeIngredient instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        recipe_id: Optional[UUID] = None,
        ingredient_name: str = "Test Ingredient",
        quantity: Optional[float] = 1.0,
        unit: Optional[str] = "cup",
        order: int = 0,
        common_ingredient_id: Optional[UUID] = None,
        prep_note: Optional[str] = None,
    ) -> RecipeIngredient:
        """Build a RecipeIngredient instance."""
        return RecipeIngredient(
            id=id or uuid4(),
            recipe_id=recipe_id or uuid4(),
            ingredient_name=ingredient_name,
            quantity=quantity,
            unit=unit,
            order=order,
            common_ingredient_id=common_ingredient_id,
            prep_note=prep_note,
        )


class RecipeInstructionFactory:
    """Factory for creating RecipeInstruction instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        recipe_id: Optional[UUID] = None,
        step_number: int = 1,
        description: str = "Do something",
        duration_minutes: Optional[int] = None,
        depends_on_step_id: Optional[UUID] = None,
    ) -> RecipeInstruction:
        """Build a RecipeInstruction instance."""
        return RecipeInstruction(
            id=id or uuid4(),
            recipe_id=recipe_id or uuid4(),
            step_number=step_number,
            description=description,
            duration_minutes=duration_minutes,
            depends_on_step_id=depends_on_step_id,
        )


class RecipePrepStepFactory:
    """Factory for creating RecipePrepStep instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        recipe_id: Optional[UUID] = None,
        description: str = "Prep step",
        order: int = 0,
    ) -> RecipePrepStep:
        """Build a RecipePrepStep instance."""
        return RecipePrepStep(
            id=id or uuid4(),
            recipe_id=recipe_id or uuid4(),
            description=description,
            order=order,
        )


class PrepStepIngredientFactory:
    """Factory for creating PrepStepIngredient instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        prep_step_id: Optional[UUID] = None,
        recipe_ingredient_id: Optional[UUID] = None,
    ) -> PrepStepIngredient:
        """Build a PrepStepIngredient instance."""
        return PrepStepIngredient(
            id=id or uuid4(),
            prep_step_id=prep_step_id or uuid4(),
            recipe_ingredient_id=recipe_ingredient_id or uuid4(),
        )


class WeekTemplateFactory:
    """Factory for creating WeekTemplate instances."""

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Week {cls._counter}"

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        retired_at=None,
    ) -> WeekTemplate:
        """Build a WeekTemplate instance."""
        return WeekTemplate(
            id=id or uuid4(),
            name=name or cls._next_name(),
            retired_at=retired_at,
        )

    @classmethod
    def build_with_assignments(
        cls,
        assignments: List[Tuple[int, str, UUID, Optional[UUID]]],
        **kwargs,
    ) -> WeekTemplate:
        """
        Build a WeekTemplate with day assignments.

        Args:
            assignments: List of (day_of_week, action, user_id, recipe_id) tuples
            **kwargs: Additional WeekTemplate fields
        """
        template = cls.build(**kwargs)

        for order, (day, action, user_id, recipe_id) in enumerate(assignments):
            assignment = WeekDayAssignmentFactory.build(
                week_template_id=template.id,
                day_of_week=day,
                action=action,
                assigned_user_id=user_id,
                recipe_id=recipe_id,
                order=order,
            )
            template.day_assignments.append(assignment)

        return template

    @classmethod
    def create(cls, db, **kwargs) -> WeekTemplate:
        """Create and persist a WeekTemplate instance."""
        template = cls.build(**kwargs)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @classmethod
    async def create_async(cls, db, **kwargs) -> WeekTemplate:
        """Create and persist a WeekTemplate instance (async)."""
        template = cls.build(**kwargs)
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template


class WeekDayAssignmentFactory:
    """Factory for creating WeekDayAssignment instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        week_template_id: Optional[UUID] = None,
        day_of_week: int = 0,
        assigned_user_id: Optional[UUID] = None,
        action: str = "cook",
        recipe_id: Optional[UUID] = None,
        order: int = 0,
    ) -> WeekDayAssignment:
        """Build a WeekDayAssignment instance."""
        if assigned_user_id is None:
            raise ValueError("assigned_user_id is required for WeekDayAssignment")

        return WeekDayAssignment(
            id=id or uuid4(),
            week_template_id=week_template_id or uuid4(),
            day_of_week=day_of_week,
            assigned_user_id=assigned_user_id,
            action=action,
            recipe_id=recipe_id,
            order=order,
        )


class ScheduleSequenceFactory:
    """Factory for creating ScheduleSequence instances."""

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Schedule {cls._counter}"

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        current_week_index: int = 0,
        advancement_day_of_week: int = 0,  # Sunday
        advancement_time: str = "00:00",
    ) -> ScheduleSequence:
        """Build a ScheduleSequence instance."""
        return ScheduleSequence(
            id=id or uuid4(),
            name=name or cls._next_name(),
            current_week_index=current_week_index,
            advancement_day_of_week=advancement_day_of_week,
            advancement_time=advancement_time,
        )

    @classmethod
    def build_with_templates(
        cls,
        templates: List[WeekTemplate],
        **kwargs,
    ) -> ScheduleSequence:
        """
        Build a ScheduleSequence with week templates.

        Args:
            templates: List of WeekTemplate instances to add
            **kwargs: Additional ScheduleSequence fields
        """
        sequence = cls.build(**kwargs)

        for position, template in enumerate(templates, start=1):
            mapping = SequenceWeekMappingFactory.build(
                sequence_id=sequence.id,
                week_template_id=template.id,
                position=position,
            )
            sequence.week_mappings.append(mapping)

        return sequence

    @classmethod
    def create(cls, db, **kwargs) -> ScheduleSequence:
        """Create and persist a ScheduleSequence instance."""
        sequence = cls.build(**kwargs)
        db.add(sequence)
        db.commit()
        db.refresh(sequence)
        return sequence

    @classmethod
    async def create_async(cls, db, **kwargs) -> ScheduleSequence:
        """Create and persist a ScheduleSequence instance (async)."""
        sequence = cls.build(**kwargs)
        db.add(sequence)
        await db.commit()
        await db.refresh(sequence)
        return sequence


class SequenceWeekMappingFactory:
    """Factory for creating SequenceWeekMapping instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        sequence_id: Optional[UUID] = None,
        week_template_id: Optional[UUID] = None,
        position: int = 1,
        removed_at=None,
    ) -> SequenceWeekMapping:
        """Build a SequenceWeekMapping instance."""
        return SequenceWeekMapping(
            id=id or uuid4(),
            sequence_id=sequence_id or uuid4(),
            week_template_id=week_template_id or uuid4(),
            position=position,
            removed_at=removed_at,
        )


class MealPlanInstanceFactory:
    """Factory for creating MealPlanInstance instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        sequence_id: Optional[UUID] = None,
        week_template_id: Optional[UUID] = None,
        instance_start_date: Optional[date] = None,
    ) -> MealPlanInstance:
        """Build a MealPlanInstance instance."""
        if week_template_id is None:
            raise ValueError("week_template_id is required for MealPlanInstance")

        return MealPlanInstance(
            id=id or uuid4(),
            sequence_id=sequence_id,
            week_template_id=week_template_id,
            instance_start_date=instance_start_date or date.today(),
        )

    @classmethod
    def create(cls, db, **kwargs) -> MealPlanInstance:
        """Create and persist a MealPlanInstance instance."""
        instance = cls.build(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    async def create_async(cls, db, **kwargs) -> MealPlanInstance:
        """Create and persist a MealPlanInstance instance (async)."""
        instance = cls.build(**kwargs)
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance


class MealAssignmentFactory:
    """Factory for creating MealAssignment (instance override) instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        meal_plan_instance_id: Optional[UUID] = None,
        day_of_week: int = 0,
        assigned_user_id: Optional[UUID] = None,
        action: str = "cook",
        recipe_id: Optional[UUID] = None,
        order: int = 0,
    ) -> MealAssignment:
        """Build a MealAssignment instance."""
        if assigned_user_id is None:
            raise ValueError("assigned_user_id is required for MealAssignment")

        return MealAssignment(
            id=id or uuid4(),
            meal_plan_instance_id=meal_plan_instance_id or uuid4(),
            day_of_week=day_of_week,
            assigned_user_id=assigned_user_id,
            action=action,
            recipe_id=recipe_id,
            order=order,
        )


class GroceryListFactory:
    """Factory for creating GroceryList instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        meal_plan_instance_id: Optional[UUID] = None,
        shopping_date: Optional[date] = None,
    ) -> GroceryList:
        """Build a GroceryList instance."""
        return GroceryList(
            id=id or uuid4(),
            meal_plan_instance_id=meal_plan_instance_id or uuid4(),
            shopping_date=shopping_date or date.today(),
        )

    @classmethod
    def build_with_items(
        cls,
        items: List[Tuple[str, float, str]],
        **kwargs,
    ) -> GroceryList:
        """
        Build a GroceryList with items.

        Args:
            items: List of (ingredient_name, quantity, unit) tuples
            **kwargs: Additional GroceryList fields
        """
        grocery_list = cls.build(**kwargs)

        for name, qty, unit in items:
            item = GroceryListItemFactory.build(
                grocery_list_id=grocery_list.id,
                ingredient_name=name,
                total_quantity=qty,
                unit=unit,
            )
            grocery_list.items.append(item)

        return grocery_list


class GroceryListItemFactory:
    """Factory for creating GroceryListItem instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        grocery_list_id: Optional[UUID] = None,
        ingredient_name: str = "Test Ingredient",
        total_quantity: float = 1.0,
        unit: str = "cup",
        source_recipe_ids: str = "[]",
        source_recipe_details: Optional[str] = None,
    ) -> GroceryListItem:
        """Build a GroceryListItem instance."""
        return GroceryListItem(
            id=id or uuid4(),
            grocery_list_id=grocery_list_id or uuid4(),
            ingredient_name=ingredient_name,
            total_quantity=total_quantity,
            unit=unit,
            source_recipe_ids=source_recipe_ids,
            source_recipe_details=source_recipe_details,
        )


class CommonIngredientFactory:
    """Factory for creating CommonIngredient instances."""

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"ingredient{cls._counter}"

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        category: Optional[str] = "pantry",
    ) -> CommonIngredient:
        """Build a CommonIngredient instance."""
        return CommonIngredient(
            id=id or uuid4(),
            name=name or cls._next_name(),
            category=category,
        )

    @classmethod
    def build_with_aliases(
        cls,
        aliases: List[str],
        **kwargs,
    ) -> CommonIngredient:
        """
        Build a CommonIngredient with aliases.

        Args:
            aliases: List of alias strings
            **kwargs: Additional CommonIngredient fields
        """
        ingredient = cls.build(**kwargs)

        for alias_name in aliases:
            alias = IngredientAliasFactory.build(
                common_ingredient_id=ingredient.id,
                alias=alias_name,
            )
            ingredient.aliases.append(alias)

        return ingredient

    @classmethod
    def create(cls, db, **kwargs) -> CommonIngredient:
        """Create and persist a CommonIngredient instance."""
        ingredient = cls.build(**kwargs)
        db.add(ingredient)
        db.commit()
        db.refresh(ingredient)
        return ingredient


class IngredientAliasFactory:
    """Factory for creating IngredientAlias instances."""

    @classmethod
    def build(
        cls,
        id: Optional[UUID] = None,
        common_ingredient_id: Optional[UUID] = None,
        alias: str = "test alias",
    ) -> IngredientAlias:
        """Build an IngredientAlias instance."""
        return IngredientAlias(
            id=id or uuid4(),
            common_ingredient_id=common_ingredient_id or uuid4(),
            alias=alias,
        )


# Convenience functions for common test scenarios

def create_user_with_recipe(db, recipe_name: str = "Test Recipe") -> Tuple[User, Recipe]:
    """Create a user and a recipe owned by them."""
    user = UserFactory.create(db)
    recipe = RecipeFactory.create(db, owner_id=user.id, name=recipe_name)
    return user, recipe


def create_full_meal_plan_setup(db, user: User) -> dict:
    """
    Create a complete meal plan setup for testing.

    Returns dict with:
        - user: The user
        - recipe: A test recipe
        - template: A week template with assignments
        - sequence: A schedule sequence containing the template
        - instance: A meal plan instance
    """
    recipe = RecipeFactory.create(db, owner_id=user.id, name="Test Dinner")

    template = WeekTemplateFactory.build(name="Test Week")
    db.add(template)
    db.commit()

    # Add some assignments
    for day in range(7):
        action = "cook" if day not in [0, 6] else "rest"  # Rest on weekends
        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            day_of_week=day,
            assigned_user_id=user.id,
            action=action,
            recipe_id=recipe.id if action == "cook" else None,
        )
        db.add(assignment)
    db.commit()

    sequence = ScheduleSequenceFactory.build(name="Test Schedule")
    db.add(sequence)
    db.commit()

    mapping = SequenceWeekMappingFactory.build(
        sequence_id=sequence.id,
        week_template_id=template.id,
        position=1,
    )
    db.add(mapping)
    db.commit()

    instance = MealPlanInstanceFactory.build(
        sequence_id=sequence.id,
        week_template_id=template.id,
        instance_start_date=date.today(),
    )
    db.add(instance)
    db.commit()

    return {
        "user": user,
        "recipe": recipe,
        "template": template,
        "sequence": sequence,
        "instance": instance,
    }

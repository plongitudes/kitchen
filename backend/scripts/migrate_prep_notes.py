"""One-time script to convert legacy prep_note fields to RecipePrepStep objects.

Run inside the backend container:
    python -m scripts.migrate_prep_notes

For each ingredient with a prep_note:
1. Creates a RecipePrepStep (or reuses one with matching description in the same recipe)
2. Links the ingredient to it via PrepStepIngredient
3. Clears the prep_note field
"""

import asyncio
import uuid
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.recipe import (
    RecipeIngredient,
    RecipePrepStep,
    PrepStepIngredient,
)


async def migrate():
    async with AsyncSessionLocal() as db:
        # Find all ingredients with a prep_note
        result = await db.execute(
            select(RecipeIngredient)
            .where(RecipeIngredient.prep_note.isnot(None))
            .where(RecipeIngredient.prep_note != "")
        )
        ingredients = result.scalars().all()

        if not ingredients:
            print("No ingredients with prep_note found. Nothing to migrate.")
            return

        print(f"Found {len(ingredients)} ingredients with prep_note to migrate.")

        # Group by recipe_id and prep_note text
        # recipe_id -> { description -> [ingredient_ids] }
        recipe_groups = defaultdict(lambda: defaultdict(list))
        for ing in ingredients:
            recipe_groups[ing.recipe_id][ing.prep_note.strip()].append(ing.id)

        total_steps_created = 0
        total_links_created = 0

        for recipe_id, descriptions in recipe_groups.items():
            # Check for existing prep steps in this recipe
            existing = await db.execute(
                select(RecipePrepStep)
                .where(RecipePrepStep.recipe_id == recipe_id)
            )
            existing_steps = {ps.description.lower(): ps for ps in existing.scalars().all()}
            next_order = len(existing_steps)

            for description, ingredient_ids in descriptions.items():
                # Reuse existing step or create new one
                key = description.lower()
                if key in existing_steps:
                    prep_step = existing_steps[key]
                else:
                    prep_step = RecipePrepStep(
                        id=uuid.uuid4(),
                        recipe_id=recipe_id,
                        description=description,
                        order=next_order,
                    )
                    db.add(prep_step)
                    await db.flush()
                    existing_steps[key] = prep_step
                    next_order += 1
                    total_steps_created += 1

                # Link each ingredient to the prep step
                for ing_id in ingredient_ids:
                    link = PrepStepIngredient(
                        id=uuid.uuid4(),
                        prep_step_id=prep_step.id,
                        recipe_ingredient_id=ing_id,
                    )
                    db.add(link)
                    total_links_created += 1

        # Clear all prep_note fields that were migrated
        await db.execute(
            update(RecipeIngredient)
            .where(RecipeIngredient.prep_note.isnot(None))
            .where(RecipeIngredient.prep_note != "")
            .values(prep_note=None)
        )

        await db.commit()

        print(f"Migration complete:")
        print(f"  {len(recipe_groups)} recipes affected")
        print(f"  {total_steps_created} prep steps created")
        print(f"  {total_links_created} ingredient links created")
        print(f"  {len(ingredients)} prep_note fields cleared")


if __name__ == "__main__":
    asyncio.run(migrate())

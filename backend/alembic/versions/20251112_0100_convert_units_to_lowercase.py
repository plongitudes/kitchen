"""convert units to lowercase

Revision ID: e8a3f1c2d5b6
Revises: d8f9e2a1b3c4
Create Date: 2025-11-12 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e8a3f1c2d5b6'
down_revision: Union[str, None] = 'd8f9e2a1b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert ingredientunit enum and all data to lowercase."""

    # Step 1: Add temporary column to store unit values as text
    op.execute("ALTER TABLE recipe_ingredients ADD COLUMN unit_temp text")

    # Step 2: Copy unit values to temp column (converting to lowercase)
    op.execute("UPDATE recipe_ingredients SET unit_temp = LOWER(unit::text) WHERE unit IS NOT NULL")

    # Step 3: Drop the unit column
    op.execute("ALTER TABLE recipe_ingredients DROP COLUMN unit")

    # Step 4: Drop and recreate the enum type with lowercase values
    op.execute("DROP TYPE IF EXISTS ingredientunit CASCADE")
    op.execute("""
        CREATE TYPE ingredientunit AS ENUM (
            'cup', 'tablespoon', 'teaspoon', 'fluid_ounce', 'pint', 'quart', 'gallon',
            'ml', 'liter', 'gram', 'kilogram', 'ounce', 'pound',
            'count', 'whole', 'item', 'bunch', 'clove', 'can', 'jar', 'package',
            'pinch', 'dash', 'to taste'
        )
    """)

    # Step 5: Recreate the unit column with the new enum type
    op.execute("ALTER TABLE recipe_ingredients ADD COLUMN unit ingredientunit")

    # Step 6: Copy data back from temp column
    op.execute("UPDATE recipe_ingredients SET unit = unit_temp::ingredientunit WHERE unit_temp IS NOT NULL")

    # Step 7: Drop the temporary column
    op.execute("ALTER TABLE recipe_ingredients DROP COLUMN unit_temp")


def downgrade() -> None:
    """Convert back to uppercase (not implemented)."""
    pass

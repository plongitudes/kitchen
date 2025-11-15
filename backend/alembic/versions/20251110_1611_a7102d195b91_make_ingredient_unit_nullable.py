"""make ingredient unit nullable

Revision ID: a7102d195b91
Revises: 5f8f8c3b7c2e
Create Date: 2025-11-10 16:11:15.718062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7102d195b91'
down_revision: Union[str, None] = '5f8f8c3b7c2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make the unit column nullable
    op.alter_column('recipe_ingredients', 'unit',
                    existing_type=sa.Enum('cup', 'tablespoon', 'teaspoon', 'fluid_ounce', 'pint', 'quart', 'gallon', 'ml', 'liter', 'gram', 'kilogram', 'ounce', 'pound', 'count', 'whole', 'item', 'bunch', 'clove', 'can', 'jar', 'package', 'pinch', 'dash', 'to taste', name='ingredientunit'),
                    nullable=True)


def downgrade() -> None:
    # Make the unit column NOT nullable (may fail if NULL values exist)
    op.alter_column('recipe_ingredients', 'unit',
                    existing_type=sa.Enum('cup', 'tablespoon', 'teaspoon', 'fluid_ounce', 'pint', 'quart', 'gallon', 'ml', 'liter', 'gram', 'kilogram', 'ounce', 'pound', 'count', 'whole', 'item', 'bunch', 'clove', 'can', 'jar', 'package', 'pinch', 'dash', 'to taste', name='ingredientunit'),
                    nullable=False)

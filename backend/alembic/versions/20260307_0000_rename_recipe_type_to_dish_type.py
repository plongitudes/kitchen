"""rename_recipe_type_to_dish_type

Revision ID: c4a7e2f1b3d5
Revises: ad8b6d7aadf0
Create Date: 2026-03-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4a7e2f1b3d5"
down_revision: Union[str, None] = "ad8b6d7aadf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("recipes", "recipe_type", new_column_name="dish_type")


def downgrade() -> None:
    op.alter_column("recipes", "dish_type", new_column_name="recipe_type")

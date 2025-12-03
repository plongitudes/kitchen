"""add composite index on recipe_prep_steps

Revision ID: 05fd81a3226b
Revises: 207171b7160b
Create Date: 2025-12-02 22:02:02.005786

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "05fd81a3226b"
down_revision: Union[str, None] = "207171b7160b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite index on (recipe_id, description) for efficient prep step lookups
    op.create_index(
        "ix_recipe_prep_steps_recipe_id_description",
        "recipe_prep_steps",
        ["recipe_id", "description"],
        unique=False,
    )


def downgrade() -> None:
    # Drop the composite index
    op.drop_index("ix_recipe_prep_steps_recipe_id_description", table_name="recipe_prep_steps")

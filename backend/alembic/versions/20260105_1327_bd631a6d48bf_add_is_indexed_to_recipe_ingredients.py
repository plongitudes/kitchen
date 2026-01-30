"""add_is_indexed_to_recipe_ingredients

Revision ID: bd631a6d48bf
Revises: 05fd81a3226b
Create Date: 2026-01-05 13:27:30.740569

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bd631a6d48bf"
down_revision: Union[str, None] = "05fd81a3226b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_indexed column to recipe_ingredients table
    op.add_column(
        "recipe_ingredients",
        sa.Column("is_indexed", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove is_indexed column from recipe_ingredients table
    op.drop_column("recipe_ingredients", "is_indexed")

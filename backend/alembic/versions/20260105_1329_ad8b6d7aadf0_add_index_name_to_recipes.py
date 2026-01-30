"""add_index_name_to_recipes

Revision ID: ad8b6d7aadf0
Revises: bd631a6d48bf
Create Date: 2026-01-05 13:29:52.133276

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ad8b6d7aadf0"
down_revision: Union[str, None] = "bd631a6d48bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index_name column to recipes table for alternative alphabetization
    op.add_column("recipes", sa.Column("index_name", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove index_name column from recipes table
    op.drop_column("recipes", "index_name")

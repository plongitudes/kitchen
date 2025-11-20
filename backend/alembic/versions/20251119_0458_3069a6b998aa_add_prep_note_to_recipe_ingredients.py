"""add_prep_note_to_recipe_ingredients

Revision ID: 3069a6b998aa
Revises: 492e0e5e3bc2
Create Date: 2025-11-19 04:58:26.149110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3069a6b998aa'
down_revision: Union[str, None] = '492e0e5e3bc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recipe_ingredients', sa.Column('prep_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('recipe_ingredients', 'prep_note')

"""add_source_recipe_details_to_grocery_list_items

Revision ID: 492e0e5e3bc2
Revises: e8a3f1c2d5b6
Create Date: 2025-11-18 05:20:50.914320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '492e0e5e3bc2'
down_revision: Union[str, None] = 'e8a3f1c2d5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source_recipe_details column to grocery_list_items
    op.add_column(
        'grocery_list_items',
        sa.Column('source_recipe_details', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove source_recipe_details column
    op.drop_column('grocery_list_items', 'source_recipe_details')

"""make ingredient quantity nullable

Revision ID: d8f9e2a1b3c4
Revises: f63e1be88176
Create Date: 2025-11-11 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f9e2a1b3c4'
down_revision: Union[str, None] = 'f63e1be88176'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make recipe_ingredients.quantity nullable."""
    op.alter_column('recipe_ingredients', 'quantity',
                    existing_type=sa.Float(),
                    nullable=True)


def downgrade() -> None:
    """Revert recipe_ingredients.quantity to non-nullable."""
    # First set any NULL values to 1.0 before making it non-nullable
    op.execute("UPDATE recipe_ingredients SET quantity = 1.0 WHERE quantity IS NULL")

    op.alter_column('recipe_ingredients', 'quantity',
                    existing_type=sa.Float(),
                    nullable=False)

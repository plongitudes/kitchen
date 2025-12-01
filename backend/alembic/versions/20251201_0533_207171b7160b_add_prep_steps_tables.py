"""add prep steps tables

Revision ID: 207171b7160b
Revises: a8f5dfbab94e
Create Date: 2025-12-01 05:33:47.731837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '207171b7160b'
down_revision: Union[str, None] = 'a8f5dfbab94e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create recipe_prep_steps table
    op.create_table(
        'recipe_prep_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create prep_step_ingredients junction table
    op.create_table(
        'prep_step_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prep_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipe_prep_steps.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recipe_ingredient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipe_ingredients.id', ondelete='CASCADE'), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table('prep_step_ingredients')
    op.drop_table('recipe_prep_steps')

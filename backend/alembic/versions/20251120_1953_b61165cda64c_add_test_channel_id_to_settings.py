"""add_test_channel_id_to_settings

Revision ID: b61165cda64c
Revises: 3069a6b998aa
Create Date: 2025-11-20 19:53:46.237966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b61165cda64c'
down_revision: Union[str, None] = '3069a6b998aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add test_channel_id column to settings table
    op.add_column('settings', sa.Column('test_channel_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove test_channel_id column from settings table
    op.drop_column('settings', 'test_channel_id')

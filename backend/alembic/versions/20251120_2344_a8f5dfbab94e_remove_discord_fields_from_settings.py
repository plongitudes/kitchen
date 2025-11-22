"""remove_discord_fields_from_settings

Revision ID: a8f5dfbab94e
Revises: b61165cda64c
Create Date: 2025-11-20 23:44:48.186281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8f5dfbab94e'
down_revision: Union[str, None] = 'b61165cda64c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove Discord fields from settings table
    # These are now configured via environment variables only
    op.drop_column('settings', 'discord_bot_token')
    op.drop_column('settings', 'notification_channel_id')
    op.drop_column('settings', 'test_channel_id')


def downgrade() -> None:
    # Restore Discord fields to settings table
    op.add_column('settings', sa.Column('test_channel_id', sa.String(), nullable=True))
    op.add_column('settings', sa.Column('notification_channel_id', sa.String(), nullable=True))
    op.add_column('settings', sa.Column('discord_bot_token', sa.String(), nullable=True))

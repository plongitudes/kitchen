"""add jar and package units, fix to_taste spacing

Revision ID: 5f8f8c3b7c2e
Revises: a3f4e8b2c9d1
Create Date: 2025-11-10 14:14:54.708866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f8f8c3b7c2e'
down_revision: Union[str, None] = 'a3f4e8b2c9d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

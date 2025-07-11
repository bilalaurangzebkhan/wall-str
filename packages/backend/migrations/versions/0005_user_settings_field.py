"""user settings field

Revision ID: 0005
Revises: 0004
Create Date: 2025-03-12 12:46:26.060452

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.types import Text

import wallstr.models.base
from wallstr.auth.schemas import UserSettings

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_users",
        sa.Column(
            "settings",
            wallstr.models.base.PydanticJSON(UserSettings, astext_type=Text()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("auth_users", "settings")

"""server default created_at

Revision ID: 87c0a4e71aed
Revises: b4ebb9bd04cb
Create Date: 2026-08-18 21:50:47.039647

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "87c0a4e71aed"
down_revision: Union[str, Sequence[str], None] = "b4ebb9bd04cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

op.alter_column("orders", "created_at", server_default=sa.text("now()"))


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

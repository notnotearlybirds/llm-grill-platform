"""add provisioning_started_at to runs

The stuck-provisioning watchdog must measure from when a run actually entered
`provisioning`, not from `created_at`: under the per-type capacity gate a run
can wait in `queued` for a long time before a GPU slot frees, and that wait must
not count against the provisioning timeout.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("provisioning_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("runs", "provisioning_started_at")

"""drop gpu_count from nodes and runs

gpu_count was always 1 and never used in any business logic.
All GPU VMs are single-GPU instances by design.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-09 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("nodes", "gpu_count")
    op.drop_column("runs", "gpu_count")


def downgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("gpu_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "nodes",
        sa.Column("gpu_count", sa.Integer(), nullable=False, server_default="1"),
    )

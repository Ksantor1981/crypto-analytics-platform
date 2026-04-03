"""review_labels for Review Console (data plane phase 4)

Revision ID: g1a2b3c4d5e6
Revises: f8e9a0b1c2d3
Create Date: 2026-04-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g1a2b3c4d5e6"
down_revision: Union[str, None] = "f8e9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_labels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=128), nullable=True),
        sa.Column("label_type", sa.String(length=32), nullable=False),
        sa.Column("corrected_fields", sa.JSON(), nullable=True),
        sa.Column("linked_signal_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["linked_signal_id"], ["signals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_labels_raw_event_id", "review_labels", ["raw_event_id"], unique=False)
    op.create_index("ix_review_labels_reviewer_user_id", "review_labels", ["reviewer_user_id"], unique=False)
    op.create_index("ix_review_labels_label_type", "review_labels", ["label_type"], unique=False)
    op.create_index("ix_review_labels_linked_signal_id", "review_labels", ["linked_signal_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_labels_linked_signal_id", table_name="review_labels")
    op.drop_index("ix_review_labels_label_type", table_name="review_labels")
    op.drop_index("ix_review_labels_reviewer_user_id", table_name="review_labels")
    op.drop_index("ix_review_labels_raw_event_id", table_name="review_labels")
    op.drop_table("review_labels")

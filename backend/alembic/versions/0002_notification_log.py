"""Create notification_log table for early warning notification dispatch logging.

Revision ID: 0002_notification_log
Revises: 0001_initial_schema
Create Date: 2026-09-07 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_notification_log"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    data_source_enum = postgresql.ENUM("synthetic", "real", name="data_source_enum", create_type=False)

    op.create_table(
        "notification_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alerts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=50), server_default="sms", nullable=False),
        sa.Column("recipient_role", sa.String(length=100), server_default="District Collector", nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notification_log_id", "notification_log", ["id"])
    op.create_index("ix_notification_log_alert_id", "notification_log", ["alert_id"])
    op.create_index("ix_notification_log_sent_at", "notification_log", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_log_sent_at", table_name="notification_log")
    op.drop_index("ix_notification_log_alert_id", table_name="notification_log")
    op.drop_index("ix_notification_log_id", table_name="notification_log")
    op.drop_table("notification_log")

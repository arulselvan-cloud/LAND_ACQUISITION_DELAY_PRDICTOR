"""LandSight AI - Notification Log Database Model."""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin


class NotificationLog(Base, TimestampDataSourceMixin):
    """Simulated notification dispatch log for priority alerts."""

    __tablename__ = "notification_log"

    alert_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(50), default="sms", nullable=False)
    recipient_role = Column(String(100), default="District Collector", nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    alert = relationship("Alert", back_populates="notifications")

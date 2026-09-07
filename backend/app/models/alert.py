"""LandSight AI - System Alerts and Early Warning Notifications Database Model."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import AlertSeverityEnum


class Alert(Base, TimestampDataSourceMixin):
    """Early delay warning and critical statutory trigger alerts."""

    __tablename__ = "alerts"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    severity = Column(
        SAEnum(AlertSeverityEnum, name="alert_severity_enum", native_enum=True),
        default=AlertSeverityEnum.medium,
        nullable=False,
        index=True,
    )
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)

    project = relationship("Project", back_populates="alerts")
    notifications = relationship(
        "NotificationLog",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="desc(NotificationLog.sent_at)",
    )

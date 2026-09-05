"""LandSight AI - Legal Disputes Database Model."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import DisputeStatusEnum


class LegalDispute(Base, TimestampDataSourceMixin):
    """Litigation, title contestations, and tribunal court actions impacting land acquisition."""

    __tablename__ = "legal_disputes"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_number = Column(String(100), nullable=False, index=True)
    court_forum = Column(String(100), nullable=False, index=True)
    dispute_type = Column(String(100), nullable=False, index=True)
    stay_order_active = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(
        SAEnum(DisputeStatusEnum, name="dispute_status_enum", native_enum=True),
        default=DisputeStatusEnum.pending,
        nullable=False,
        index=True,
    )
    filed_date = Column(Date, nullable=False, index=True)
    resolution_date = Column(Date, nullable=True)
    delay_impact_estimate_days = Column(Integer, default=0, nullable=False)
    petitioner_name = Column(String(255), nullable=True)
    respondent_name = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)

    project = relationship("Project", back_populates="legal_disputes")

"""LandSight AI - AI Policy & Administrative Recommendations Database Model."""

from sqlalchemy import (
    Boolean,
    Column,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import PriorityEnum


class Recommendation(Base, TimestampDataSourceMixin):
    """Actionable prescriptive policy and operational recommendations linked to AI risk evaluations."""

    __tablename__ = "recommendations"

    risk_score_id = Column(
        UUID(as_uuid=True),
        ForeignKey("risk_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_text = Column(Text, nullable=False)
    priority = Column(
        SAEnum(PriorityEnum, name="priority_enum", native_enum=True),
        default=PriorityEnum.medium,
        nullable=False,
        index=True,
    )
    category = Column(String(100), nullable=True, index=True)
    expected_impact = Column(String(255), nullable=True)
    is_implemented = Column(Boolean, default=False, nullable=False, index=True)

    risk_score = relationship("RiskScore", back_populates="recommendations")
    project = relationship("Project", back_populates="recommendations")

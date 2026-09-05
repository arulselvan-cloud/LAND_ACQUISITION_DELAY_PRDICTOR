"""LandSight AI - AI Risk Scores and Stage Delay Predictions Database Model."""

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import RiskCategoryEnum


class RiskScore(Base, TimestampDataSourceMixin):
    """Machine Learning delay risk scoring with per-stage probability distribution and SHAP drivers."""

    __tablename__ = "risk_scores"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_category = Column(
        SAEnum(RiskCategoryEnum, name="risk_category_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    overall_delay_probability = Column(Float, nullable=False)
    # Stage breakdown: {"notification": 0.12, "survey": 0.25, "compensation": 0.65, "possession": 0.82, "rehabilitation": 0.45}
    stage_delay_probabilities = Column(JSONB, nullable=False)
    predicted_delay_days = Column(Integer, default=0, nullable=False)
    confidence_score = Column(Float, nullable=True)
    # Top SHAP explainability factors: [{"feature": "stay_order_active", "impact": 0.38, "description": "..."}, ...]
    top_risk_drivers = Column(JSONB, nullable=True)
    computed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    project = relationship("Project", back_populates="risk_scores")
    recommendations = relationship(
        "Recommendation",
        back_populates="risk_score",
        cascade="all, delete-orphan",
    )

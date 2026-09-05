"""LandSight AI - Rehabilitation and Resettlement (R&R) Progress Database Model."""

from sqlalchemy import (
    Column,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import RRSchemeStatusEnum


class RehabilitationProgress(Base, TimestampDataSourceMixin):
    """Rehabilitation and Resettlement (R&R) statutory milestones and progress tracking."""

    __tablename__ = "rehabilitation_progress"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_families_eligible = Column(Integer, default=0, nullable=False)
    families_resettled = Column(Integer, default=0, nullable=False)
    monetary_allowance_disbursed = Column(Numeric(15, 2), default=0.00, nullable=False)
    alternative_land_allotted_count = Column(Integer, default=0, nullable=False)
    housing_units_constructed = Column(Integer, default=0, nullable=False)
    housing_units_allotted = Column(Integer, default=0, nullable=False)
    rr_scheme_status = Column(
        SAEnum(RRSchemeStatusEnum, name="rr_scheme_status_enum", native_enum=True),
        default=RRSchemeStatusEnum.draft,
        nullable=False,
        index=True,
    )
    completion_percentage = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="rehabilitation_progress")

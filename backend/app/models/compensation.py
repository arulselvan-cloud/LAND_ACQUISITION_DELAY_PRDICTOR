"""LandSight AI - Compensation Records Database Model."""

from sqlalchemy import (
    Column,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import CompensationStatusEnum


class CompensationRecord(Base, TimestampDataSourceMixin):
    """Monetary compensation tracking and award disbursement per project."""

    __tablename__ = "compensation_records"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_amount_allocated = Column(Numeric(15, 2), nullable=False)
    total_amount_disbursed = Column(Numeric(15, 2), default=0.00, nullable=False)
    beneficiaries_count = Column(Integer, default=0, nullable=False)
    disbursed_count = Column(Integer, default=0, nullable=False)
    valuation_method = Column(String(255), nullable=True)
    status = Column(
        SAEnum(CompensationStatusEnum, name="compensation_status_enum", native_enum=True),
        default=CompensationStatusEnum.pending,
        nullable=False,
        index=True,
    )
    last_disbursement_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="compensation_records")

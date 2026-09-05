"""LandSight AI - Project Lifecycle Stages Model."""

from sqlalchemy import (
    Column,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin
from backend.app.models.enums import StageNameEnum, StageStatusEnum


class Stage(Base, TimestampDataSourceMixin):
    """5 Statutory lifecycle milestones per land acquisition project."""

    __tablename__ = "stages"
    __table_args__ = (
        UniqueConstraint("project_id", "stage_name", name="uq_project_stage_name"),
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_name = Column(
        SAEnum(StageNameEnum, name="stage_name_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    stage_order = Column(Integer, nullable=False)
    planned_duration_days = Column(Integer, nullable=False)
    actual_duration_days = Column(Integer, nullable=True)
    status = Column(
        SAEnum(StageStatusEnum, name="stage_status_enum", native_enum=True),
        default=StageStatusEnum.not_started,
        nullable=False,
        index=True,
    )
    start_date = Column(Date, nullable=True)
    target_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    delay_days = Column(Integer, default=0, nullable=False)

    project = relationship("Project", back_populates="stages")

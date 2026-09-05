"""LandSight AI - Stakeholder Database Model."""

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin


class Stakeholder(Base, TimestampDataSourceMixin):
    """Statutory actors, authorities, and agencies involved in land acquisition workflows.
    
    Tracks stakeholder responsiveness score (0-100) as a key delay prediction factor.
    """

    __tablename__ = "stakeholders"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    role = Column(String(100), nullable=False, index=True)
    responsiveness_score = Column(Float, nullable=False, default=50.0)  # 0 to 100 scale
    last_contact_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="stakeholders")

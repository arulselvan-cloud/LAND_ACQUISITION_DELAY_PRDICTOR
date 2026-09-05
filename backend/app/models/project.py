"""LandSight AI - Project Database Model with PostGIS Point Location."""

from geoalchemy2 import Geography
from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.models.base import TimestampDataSourceMixin


class Project(Base, TimestampDataSourceMixin):
    """Infrastructure land acquisition project entity with PostGIS spatial geography."""

    __tablename__ = "projects"

    name = Column(String(255), nullable=False, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    project_type = Column(String(100), nullable=False, index=True)
    land_area_hectares = Column(Float, nullable=False)
    affected_families_count = Column(Integer, default=0, nullable=False)
    notification_date = Column(Date, nullable=False, index=True)
    target_possession_date = Column(Date, nullable=True)
    actual_possession_date = Column(Date, nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)

    # PostGIS geography point (WGS84, SRID 4326)
    location = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Relationships
    stages = relationship(
        "Stage",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Stage.stage_order",
    )
    compensation_records = relationship(
        "CompensationRecord",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    legal_disputes = relationship(
        "LegalDispute",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    rehabilitation_progress = relationship(
        "RehabilitationProgress",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    risk_scores = relationship(
        "RiskScore",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(RiskScore.computed_at)",
    )
    recommendations = relationship(
        "Recommendation",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    alerts = relationship(
        "Alert",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(Alert.triggered_at)",
    )
    stakeholders = relationship(
        "Stakeholder",
        back_populates="project",
        cascade="all, delete-orphan",
    )

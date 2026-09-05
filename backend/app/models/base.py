"""LandSight AI - Base Model Mixin and Shared Attributes."""

import uuid
from sqlalchemy import Column, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database import Base
from backend.app.models.enums import DataSourceEnum


class TimestampDataSourceMixin:
    """Shared mixin adding UUID primary key, audit timestamps, and data source tracking."""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    data_source = Column(
        SAEnum(DataSourceEnum, name="data_source_enum", native_enum=True),
        default=DataSourceEnum.synthetic,
        nullable=False,
        index=True,
    )

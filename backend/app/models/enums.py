"""LandSight AI - Domain Enumerations for Database Models."""

import enum


class DataSourceEnum(str, enum.Enum):
    """Source origin of the record for data hygiene and benchmarking."""
    synthetic = "synthetic"
    real = "real"


class StageNameEnum(str, enum.Enum):
    """5 Statutory Land Acquisition Lifecycle Stages."""
    notification = "notification"
    survey = "survey"
    compensation = "compensation"
    possession = "possession"
    rehabilitation = "rehabilitation"


class StageStatusEnum(str, enum.Enum):
    """Status lifecycle of a project milestone/stage."""
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"
    blocked = "blocked"


class RiskCategoryEnum(str, enum.Enum):
    """Delay risk categorization."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class PriorityEnum(str, enum.Enum):
    """Action priority rating."""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class AlertSeverityEnum(str, enum.Enum):
    """Alert warning severity levels."""
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DisputeStatusEnum(str, enum.Enum):
    """Status of court/tribunal litigation."""
    pending = "pending"
    stay_granted = "stay_granted"
    hearing_scheduled = "hearing_scheduled"
    dismissed = "dismissed"
    resolved = "resolved"


class RRSchemeStatusEnum(str, enum.Enum):
    """Rehabilitation and Resettlement scheme status."""
    draft = "draft"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"


class CompensationStatusEnum(str, enum.Enum):
    """Status of compensation disbursement award."""
    pending = "pending"
    partially_disbursed = "partially_disbursed"
    fully_disbursed = "fully_disbursed"
    disputed = "disputed"


class StakeholderRoleEnum(str, enum.Enum):
    """Roles representing key actors in statutory land acquisition."""
    district_collector = "District Collector"
    revenue_department = "Revenue Department"
    project_implementing_agency = "Project Implementing Agency"
    land_acquisition_officer = "Land Acquisition Officer"
    competent_authority = "Competent Authority"
    forest_department = "Forest Department"
    gram_panchayat = "Gram Panchayat / Local Body"
    other = "Other"

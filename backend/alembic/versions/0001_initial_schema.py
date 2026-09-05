"""Initial database schema with PostGIS, projects, stages, and all analytics tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-05 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Define Enum Types
    data_source_enum = postgresql.ENUM("synthetic", "real", name="data_source_enum", create_type=False)
    stage_name_enum = postgresql.ENUM("notification", "survey", "compensation", "possession", "rehabilitation", name="stage_name_enum", create_type=False)
    stage_status_enum = postgresql.ENUM("not_started", "in_progress", "completed", "delayed", "blocked", name="stage_status_enum", create_type=False)
    risk_category_enum = postgresql.ENUM("low", "medium", "high", "critical", name="risk_category_enum", create_type=False)
    priority_enum = postgresql.ENUM("low", "medium", "high", "urgent", name="priority_enum", create_type=False)
    alert_severity_enum = postgresql.ENUM("info", "low", "medium", "high", "critical", name="alert_severity_enum", create_type=False)
    dispute_status_enum = postgresql.ENUM("pending", "stay_granted", "hearing_scheduled", "dismissed", "resolved", name="dispute_status_enum", create_type=False)
    rr_scheme_status_enum = postgresql.ENUM("draft", "approved", "in_progress", "completed", name="rr_scheme_status_enum", create_type=False)
    compensation_status_enum = postgresql.ENUM("pending", "partially_disbursed", "fully_disbursed", "disputed", name="compensation_status_enum", create_type=False)

    for enum_type in [
        data_source_enum,
        stage_name_enum,
        stage_status_enum,
        risk_category_enum,
        priority_enum,
        alert_severity_enum,
        dispute_status_enum,
        rr_scheme_status_enum,
        compensation_status_enum,
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    # 3. Create 'projects' table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("project_code", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("project_type", sa.String(length=100), nullable=False),
        sa.Column("land_area_hectares", sa.Float(), nullable=False),
        sa.Column("affected_families_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notification_date", sa.Date(), nullable=False),
        sa.Column("target_possession_date", sa.Date(), nullable=True),
        sa.Column("actual_possession_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geography(geometry_type="POINT", srid=4326, spatial_index=False, from_text="ST_GeogFromText"),
            nullable=True,
        ),
    )
    op.create_index("ix_projects_id", "projects", ["id"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])
    op.create_index("ix_projects_data_source", "projects", ["data_source"])
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_project_code", "projects", ["project_code"], unique=True)
    op.create_index("ix_projects_district", "projects", ["district"])
    op.create_index("ix_projects_state", "projects", ["state"])
    op.create_index("ix_projects_project_type", "projects", ["project_type"])
    op.create_index("ix_projects_notification_date", "projects", ["notification_date"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("idx_projects_location", "projects", ["location"], postgresql_using="gist")

    # 4. Create 'stages' table
    op.create_table(
        "stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage_name", stage_name_enum, nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False),
        sa.Column("planned_duration_days", sa.Integer(), nullable=False),
        sa.Column("actual_duration_days", sa.Integer(), nullable=True),
        sa.Column("status", stage_status_enum, server_default="not_started", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("target_completion_date", sa.Date(), nullable=True),
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column("delay_days", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("project_id", "stage_name", name="uq_project_stage_name"),
    )
    op.create_index("ix_stages_id", "stages", ["id"])
    op.create_index("ix_stages_created_at", "stages", ["created_at"])
    op.create_index("ix_stages_data_source", "stages", ["data_source"])
    op.create_index("ix_stages_project_id", "stages", ["project_id"])
    op.create_index("ix_stages_stage_name", "stages", ["stage_name"])
    op.create_index("ix_stages_status", "stages", ["status"])

    # 5. Create 'compensation_records' table
    op.create_table(
        "compensation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_amount_allocated", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_amount_disbursed", sa.Numeric(precision=15, scale=2), server_default="0.00", nullable=False),
        sa.Column("beneficiaries_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("disbursed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valuation_method", sa.String(length=255), nullable=True),
        sa.Column("status", compensation_status_enum, server_default="pending", nullable=False),
        sa.Column("last_disbursement_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_compensation_records_id", "compensation_records", ["id"])
    op.create_index("ix_compensation_records_created_at", "compensation_records", ["created_at"])
    op.create_index("ix_compensation_records_data_source", "compensation_records", ["data_source"])
    op.create_index("ix_compensation_records_project_id", "compensation_records", ["project_id"])
    op.create_index("ix_compensation_records_status", "compensation_records", ["status"])

    # 6. Create 'legal_disputes' table
    op.create_table(
        "legal_disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_number", sa.String(length=100), nullable=False),
        sa.Column("court_forum", sa.String(length=100), nullable=False),
        sa.Column("dispute_type", sa.String(length=100), nullable=False),
        sa.Column("stay_order_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", dispute_status_enum, server_default="pending", nullable=False),
        sa.Column("filed_date", sa.Date(), nullable=False),
        sa.Column("resolution_date", sa.Date(), nullable=True),
        sa.Column("delay_impact_estimate_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("petitioner_name", sa.String(length=255), nullable=True),
        sa.Column("respondent_name", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_legal_disputes_id", "legal_disputes", ["id"])
    op.create_index("ix_legal_disputes_created_at", "legal_disputes", ["created_at"])
    op.create_index("ix_legal_disputes_data_source", "legal_disputes", ["data_source"])
    op.create_index("ix_legal_disputes_project_id", "legal_disputes", ["project_id"])
    op.create_index("ix_legal_disputes_case_number", "legal_disputes", ["case_number"])
    op.create_index("ix_legal_disputes_court_forum", "legal_disputes", ["court_forum"])
    op.create_index("ix_legal_disputes_dispute_type", "legal_disputes", ["dispute_type"])
    op.create_index("ix_legal_disputes_stay_order_active", "legal_disputes", ["stay_order_active"])
    op.create_index("ix_legal_disputes_status", "legal_disputes", ["status"])
    op.create_index("ix_legal_disputes_filed_date", "legal_disputes", ["filed_date"])

    # 7. Create 'rehabilitation_progress' table
    op.create_table(
        "rehabilitation_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_families_eligible", sa.Integer(), server_default="0", nullable=False),
        sa.Column("families_resettled", sa.Integer(), server_default="0", nullable=False),
        sa.Column("monetary_allowance_disbursed", sa.Numeric(precision=15, scale=2), server_default="0.00", nullable=False),
        sa.Column("alternative_land_allotted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("housing_units_constructed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("housing_units_allotted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rr_scheme_status", rr_scheme_status_enum, server_default="draft", nullable=False),
        sa.Column("completion_percentage", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_rehabilitation_progress_id", "rehabilitation_progress", ["id"])
    op.create_index("ix_rehabilitation_progress_created_at", "rehabilitation_progress", ["created_at"])
    op.create_index("ix_rehabilitation_progress_data_source", "rehabilitation_progress", ["data_source"])
    op.create_index("ix_rehabilitation_progress_project_id", "rehabilitation_progress", ["project_id"])
    op.create_index("ix_rehabilitation_progress_rr_scheme_status", "rehabilitation_progress", ["rr_scheme_status"])

    # 8. Create 'risk_scores' table
    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_category", risk_category_enum, nullable=False),
        sa.Column("overall_delay_probability", sa.Float(), nullable=False),
        sa.Column("stage_delay_probabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("predicted_delay_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("top_risk_drivers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_risk_scores_id", "risk_scores", ["id"])
    op.create_index("ix_risk_scores_created_at", "risk_scores", ["created_at"])
    op.create_index("ix_risk_scores_data_source", "risk_scores", ["data_source"])
    op.create_index("ix_risk_scores_project_id", "risk_scores", ["project_id"])
    op.create_index("ix_risk_scores_risk_category", "risk_scores", ["risk_category"])
    op.create_index("ix_risk_scores_computed_at", "risk_scores", ["computed_at"])

    # 9. Create 'recommendations' table
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("risk_score_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("priority", priority_enum, server_default="medium", nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("expected_impact", sa.String(length=255), nullable=True),
        sa.Column("is_implemented", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_recommendations_id", "recommendations", ["id"])
    op.create_index("ix_recommendations_created_at", "recommendations", ["created_at"])
    op.create_index("ix_recommendations_data_source", "recommendations", ["data_source"])
    op.create_index("ix_recommendations_risk_score_id", "recommendations", ["risk_score_id"])
    op.create_index("ix_recommendations_project_id", "recommendations", ["project_id"])
    op.create_index("ix_recommendations_priority", "recommendations", ["priority"])
    op.create_index("ix_recommendations_category", "recommendations", ["category"])
    op.create_index("ix_recommendations_is_implemented", "recommendations", ["is_implemented"])

    # 10. Create 'alerts' table
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("severity", alert_severity_enum, server_default="medium", nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index("ix_alerts_data_source", "alerts", ["data_source"])
    op.create_index("ix_alerts_project_id", "alerts", ["project_id"])
    op.create_index("ix_alerts_triggered_at", "alerts", ["triggered_at"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_resolved", "alerts", ["resolved"])

    # 11. Create 'stakeholders' table
    op.create_table(
        "stakeholders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", data_source_enum, server_default="synthetic", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("responsiveness_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_stakeholders_id", "stakeholders", ["id"])
    op.create_index("ix_stakeholders_created_at", "stakeholders", ["created_at"])
    op.create_index("ix_stakeholders_data_source", "stakeholders", ["data_source"])
    op.create_index("ix_stakeholders_project_id", "stakeholders", ["project_id"])
    op.create_index("ix_stakeholders_name", "stakeholders", ["name"])
    op.create_index("ix_stakeholders_role", "stakeholders", ["role"])


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_table("stakeholders")
    op.drop_table("alerts")
    op.drop_table("recommendations")
    op.drop_table("risk_scores")
    op.drop_table("rehabilitation_progress")
    op.drop_table("legal_disputes")
    op.drop_table("compensation_records")
    op.drop_table("stages")
    op.drop_table("projects")

    # Drop enums
    for enum_name in [
        "compensation_status_enum",
        "rr_scheme_status_enum",
        "dispute_status_enum",
        "alert_severity_enum",
        "priority_enum",
        "risk_category_enum",
        "stage_status_enum",
        "stage_name_enum",
        "data_source_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE;")

"""LandSight AI - Dashboard & Spatial Analytics Router.

Provides paginated project listings with multi-dimensional filtering,
geospatial district-level risk aggregations for heatmaps, and prioritised early warning alerts.
Computes real-time risk predictions using the active ML classifier bundle with live telemetry.
"""

from collections import defaultdict
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.compensation import CompensationRecord
from backend.app.models.enums import DisputeStatusEnum, RiskCategoryEnum
from backend.app.models.legal import LegalDispute
from backend.app.models.project import Project
from backend.app.models.rehabilitation import RehabilitationProgress
from backend.app.models.risk import RiskScore
from backend.app.models.stakeholder import Stakeholder
from backend.app.services.project_lookup import get_project_or_404
from ml.features import ALL_FEATURE_COLUMNS, CATEGORICAL_FEATURES

router = APIRouter()


class ProjectSummaryItem(BaseModel):
    id: str
    project_code: str
    name: str
    district: str
    state: str
    project_type: str
    risk_category: str
    delay_probability: float
    computed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    projects: List[ProjectSummaryItem]


class DistrictSummaryItem(BaseModel):
    state: str
    district: str
    project_count: int
    avg_delay_probability: float
    high_risk_count: int
    critical_risk_count: int


class AlertItem(BaseModel):
    id: str
    project_code: str
    name: str
    district: str
    state: str
    project_type: str
    risk_category: str
    delay_probability: float
    land_area_hectares: float
    affected_families_count: int
    computed_at: Optional[datetime] = None


class AlertsResponse(BaseModel):
    total_alerts: int
    alerts: List[AlertItem]


def compute_live_predictions_for_projects(
    projects: List[Project],
    classifier_bundle: Optional[Dict[str, Any]],
    session: Session,
) -> Dict[str, Dict[str, Any]]:
    """Vectorized in-memory prediction computation for a list of projects in under 50ms."""
    if not projects or not classifier_bundle:
        return {}

    pids = [p.id for p in projects]
    model = classifier_bundle["model"]
    encoders = classifier_bundle["encoders"]
    inv_label_map = classifier_bundle["inv_label_map"]

    # Preload child tables in bulk for instant loading
    comps = {
        c.project_id: c
        for c in session.query(CompensationRecord)
        .filter(CompensationRecord.project_id.in_(pids))
        .all()
    }
    disputes = defaultdict(list)
    for d in session.query(LegalDispute).filter(LegalDispute.project_id.in_(pids)).all():
        disputes[d.project_id].append(d)

    stks = defaultdict(list)
    for s in session.query(Stakeholder).filter(Stakeholder.project_id.in_(pids)).all():
        stks[s.project_id].append(s)

    rehabs = {
        r.project_id: r
        for r in session.query(RehabilitationProgress)
        .filter(RehabilitationProgress.project_id.in_(pids))
        .all()
    }

    rows = []
    for p in projects:
        comp = comps.get(p.id)
        if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
            disbursed = float(comp.total_amount_disbursed or 0.0)
            allocated = float(comp.total_amount_allocated)
            disbursed_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
        else:
            disbursed_pct = 0.0

        p_disputes = disputes.get(p.id, [])
        has_active = (
            1
            if any(
                d.stay_order_active or d.status == DisputeStatusEnum.stay_granted
                for d in p_disputes
            )
            else 0
        )
        total_delay = sum(d.delay_impact_estimate_days or 0 for d in p_disputes)

        p_stks = stks.get(p.id, [])
        stk_scores = [
            float(s.responsiveness_score)
            for s in p_stks
            if s.responsiveness_score is not None
        ]
        avg_stk = float(np.mean(stk_scores)) if stk_scores else 50.0

        rehab = rehabs.get(p.id)
        rehab_pct = (
            float(rehab.completion_percentage)
            if rehab and rehab.completion_percentage is not None
            else 0.0
        )

        row_dict = {
            "compensation_disbursed_pct": disbursed_pct,
            "has_active_legal_dispute": has_active,
            "dispute_delay_impact_days": total_delay,
            "avg_stakeholder_responsiveness": avg_stk,
            "affected_families_count": int(p.affected_families_count or 0),
            "land_area_hectares": float(p.land_area_hectares or 0.0),
            "rehabilitation_completion_pct": rehab_pct,
        }
        for col in CATEGORICAL_FEATURES:
            mapping = encoders.get(col, {})
            val = getattr(p, col)
            row_dict[f"{col}_encoded"] = mapping.get(val, len(mapping))
        rows.append(row_dict)

    batch_df = pd.DataFrame(rows)[ALL_FEATURE_COLUMNS]
    probs = model.predict_proba(batch_df)
    pred_indices = np.argmax(probs, axis=1)

    now = datetime.now(timezone.utc)
    results = {}
    for idx, p in enumerate(projects):
        pred_cat = inv_label_map[int(pred_indices[idx])]
        delay_prob = float(probs[idx][2] + probs[idx][3])
        results[str(p.id)] = {
            "risk_category": pred_cat,
            "delay_probability": round(delay_prob, 4),
            "confidence_score": round(float(np.max(probs[idx])), 4),
            "computed_at": now,
        }
    return results


@router.get("/projects", response_model=PaginatedProjectsResponse)
def list_projects(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (min 1, default 20, max 100)"),
    state: Optional[str] = Query(None, description="Filter by state name (case-insensitive substring)"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category (low, medium, high, critical)"),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of all projects with real-time computed delay probabilities and risk categories."""
    query = (
        db.query(Project, RiskScore)
        .outerjoin(RiskScore, Project.id == RiskScore.project_id)
    )

    if state:
        query = query.filter(Project.state.ilike(f"%{state.strip()}%"))

    if risk_category:
        try:
            cat_enum = RiskCategoryEnum(risk_category.strip().lower())
            query = query.filter(
                func.coalesce(RiskScore.predicted_risk_category, RiskScore.risk_category) == cat_enum
            )
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid risk_category '{risk_category}'. Valid options are: low, medium, high, critical."
            )

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1

    offset = (page - 1) * page_size
    records = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()

    projects = [r[0] for r in records]
    classifier_bundle = getattr(request.app.state, "risk_classifier", None)

    # Compute live predictions for the page of projects
    live_preds = compute_live_predictions_for_projects(projects, classifier_bundle, db)

    items = []
    for proj, stored_risk in records:
        pid_str = str(proj.id)
        if pid_str in live_preds:
            cat_str = live_preds[pid_str]["risk_category"]
            prob = live_preds[pid_str]["delay_probability"]
            computed_at = live_preds[pid_str]["computed_at"]
        elif stored_risk:
            cat_str = stored_risk.risk_category.value if stored_risk.risk_category else "unassessed"
            prob = float(stored_risk.overall_delay_probability) if stored_risk.overall_delay_probability is not None else 0.0
            computed_at = stored_risk.computed_at
        else:
            cat_str = "unassessed"
            prob = 0.0
            computed_at = None

        items.append(
            ProjectSummaryItem(
                id=pid_str,
                project_code=proj.project_code,
                name=proj.name,
                district=proj.district,
                state=proj.state,
                project_type=proj.project_type,
                risk_category=cat_str,
                delay_probability=round(prob, 4),
                computed_at=computed_at,
            )
        )

    return PaginatedProjectsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        projects=items,
    )


@router.get("/projects/{project_id}")
def get_project_details(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Retrieves full details of a single project by UUID or project_code with live model inference."""
    proj = get_project_or_404(db, project_id)
    stored_risk = db.query(RiskScore).filter_by(project_id=proj.id).order_by(RiskScore.computed_at.desc()).first()

    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    live_preds = compute_live_predictions_for_projects([proj], classifier_bundle, db)

    pid_str = str(proj.id)
    if pid_str in live_preds:
        risk_cat = live_preds[pid_str]["risk_category"]
        delay_prob = live_preds[pid_str]["delay_probability"]
        conf_score = live_preds[pid_str]["confidence_score"]
        computed_at = live_preds[pid_str]["computed_at"]
    elif stored_risk:
        risk_cat = stored_risk.risk_category.value if stored_risk.risk_category else "unassessed"
        delay_prob = float(stored_risk.overall_delay_probability) if stored_risk.overall_delay_probability is not None else 0.0
        conf_score = float(stored_risk.confidence_score) if stored_risk.confidence_score is not None else 0.0
        computed_at = stored_risk.computed_at
    else:
        risk_cat = "unassessed"
        delay_prob = 0.0
        conf_score = 0.0
        computed_at = None

    return {
        "id": pid_str,
        "project_code": proj.project_code,
        "name": proj.name,
        "district": proj.district,
        "state": proj.state,
        "project_type": proj.project_type,
        "land_area_hectares": float(proj.land_area_hectares or 0.0),
        "affected_families_count": int(proj.affected_families_count or 0),
        "status": proj.status,
        "risk_category": risk_cat,
        "delay_probability": delay_prob,
        "stage_delay_probabilities": stored_risk.stage_delay_probabilities if stored_risk else {},
        "predicted_delay_days": stored_risk.predicted_delay_days if stored_risk else 0,
        "confidence_score": conf_score,
        "computed_at": computed_at,
    }


@router.get("/districts/summary", response_model=List[DistrictSummaryItem])
def get_districts_summary(
    state: Optional[str] = Query(None, description="Optional state filter"),
    db: Session = Depends(get_db),
):
    """Aggregates project count and average delay risk per district/state for geospatial heatmap rendering."""
    high_count_case = case((RiskScore.risk_category == RiskCategoryEnum.high, 1), else_=0)
    crit_count_case = case((RiskScore.risk_category == RiskCategoryEnum.critical, 1), else_=0)

    query = (
        db.query(
            Project.state,
            Project.district,
            func.count(Project.id).label("project_count"),
            func.avg(RiskScore.overall_delay_probability).label("avg_delay_prob"),
            func.sum(high_count_case).label("high_risk_count"),
            func.sum(crit_count_case).label("critical_risk_count"),
        )
        .join(RiskScore, Project.id == RiskScore.project_id)
        .group_by(Project.state, Project.district)
    )

    if state:
        query = query.filter(Project.state.ilike(f"%{state.strip()}%"))

    records = query.order_by(func.avg(RiskScore.overall_delay_probability).desc()).all()

    return [
        DistrictSummaryItem(
            state=row[0],
            district=row[1],
            project_count=int(row[2]),
            avg_delay_probability=round(float(row[3]), 4) if row[3] is not None else 0.0,
            high_risk_count=int(row[4] or 0),
            critical_risk_count=int(row[5] or 0),
        )
        for row in records
    ]


@router.get("/alerts", response_model=AlertsResponse)
def get_risk_alerts(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return"),
    db: Session = Depends(get_db),
):
    """Returns projects currently in 'high' or 'critical' risk categories, sorted by delay_probability descending with live model inference."""
    high_risk_cats = [RiskCategoryEnum.high, RiskCategoryEnum.critical]

    total_alerts = (
        db.query(RiskScore)
        .filter(func.coalesce(RiskScore.predicted_risk_category, RiskScore.risk_category).in_(high_risk_cats))
        .count()
    )

    records = (
        db.query(Project, RiskScore)
        .join(RiskScore, Project.id == RiskScore.project_id)
        .filter(func.coalesce(RiskScore.predicted_risk_category, RiskScore.risk_category).in_(high_risk_cats))
        .order_by(desc(func.coalesce(RiskScore.predicted_delay_probability, RiskScore.overall_delay_probability)))
        .limit(limit)
        .all()
    )

    projects = [r[0] for r in records]
    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    live_preds = compute_live_predictions_for_projects(projects, classifier_bundle, db)

    alerts = []
    for proj, stored_risk in records:
        pid_str = str(proj.id)
        if pid_str in live_preds:
            cat_str = live_preds[pid_str]["risk_category"]
            prob = live_preds[pid_str]["delay_probability"]
            computed_at = live_preds[pid_str]["computed_at"]
        else:
            cat_enum = stored_risk.predicted_risk_category or stored_risk.risk_category
            cat_str = cat_enum.value if cat_enum else "unassessed"
            prob = float(stored_risk.predicted_delay_probability or stored_risk.overall_delay_probability or 0.0)
            computed_at = stored_risk.computed_at

        alerts.append(
            AlertItem(
                id=pid_str,
                project_code=proj.project_code,
                name=proj.name,
                district=proj.district,
                state=proj.state,
                project_type=proj.project_type,
                risk_category=cat_str,
                delay_probability=round(prob, 4),
                land_area_hectares=float(proj.land_area_hectares or 0.0),
                affected_families_count=int(proj.affected_families_count or 0),
                computed_at=computed_at,
            )
        )

    # Sort alerts descending by live computed probability
    alerts.sort(key=lambda a: a.delay_probability, reverse=True)

    return AlertsResponse(
        total_alerts=total_alerts,
        alerts=alerts,
    )


class OverviewSummaryResponse(BaseModel):
    total_projects: int
    high_critical_count: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    avg_delay_probability: float
    total_land_area_hectares: float
    total_affected_families: int
    risk_breakdown: Dict[str, int]


@router.get("/summary", response_model=OverviewSummaryResponse)
def get_executive_summary(db: Session = Depends(get_db)):
    """Provides high-level system metrics and risk distribution for the executive overview cards and donut chart."""
    total_projects = db.query(Project).count()

    pred_col = func.coalesce(RiskScore.predicted_risk_category, RiskScore.risk_category)
    counts = dict(
        db.query(pred_col, func.count(RiskScore.id))
        .group_by(pred_col)
        .all()
    )

    low_cnt = counts.get(RiskCategoryEnum.low, 0)
    med_cnt = counts.get(RiskCategoryEnum.medium, 0)
    high_cnt = counts.get(RiskCategoryEnum.high, 0)
    crit_cnt = counts.get(RiskCategoryEnum.critical, 0)
    high_crit_cnt = high_cnt + crit_cnt

    avg_prob = db.query(
        func.avg(func.coalesce(RiskScore.predicted_delay_probability, RiskScore.overall_delay_probability))
    ).scalar() or 0.0

    totals = db.query(
        func.sum(Project.land_area_hectares),
        func.sum(Project.affected_families_count),
    ).first()

    tot_area = float(totals[0] or 0.0)
    tot_paf = int(totals[1] or 0)

    return OverviewSummaryResponse(
        total_projects=total_projects,
        high_critical_count=high_crit_cnt,
        low_risk_count=low_cnt,
        medium_risk_count=med_cnt,
        high_risk_count=high_cnt,
        critical_risk_count=crit_cnt,
        avg_delay_probability=round(float(avg_prob), 4),
        total_land_area_hectares=round(tot_area, 2),
        total_affected_families=tot_paf,
        risk_breakdown={
            "Low": low_cnt,
            "Medium": med_cnt,
            "High": high_cnt,
            "Critical": crit_cnt,
        },
    )


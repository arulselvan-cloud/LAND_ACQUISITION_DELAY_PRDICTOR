"""LandSight AI - Machine Learning Feature Extraction & Engineering.

Extracts project features directly from the PostgreSQL database using SQLAlchemy ORM
models without intermediate flat CSVs.
"""

from collections import defaultdict
from decimal import Decimal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# Setup python path to import backend models
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir.parent))
sys.path.insert(0, str(backend_dir))

from backend.app.database import SessionLocal
from backend.app.models import (
    CompensationRecord,
    DisputeStatusEnum,
    LegalDispute,
    Project,
    RehabilitationProgress,
    RiskCategoryEnum,
    RiskScore,
    Stage,
    StageNameEnum,
    StageStatusEnum,
    Stakeholder,
)

# Label mapping for risk category target
RISK_CATEGORY_MAP = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}
INV_RISK_CATEGORY_MAP = {v: k for k, v in RISK_CATEGORY_MAP.items()}

# Feature columns
NUMERICAL_FEATURES = [
    "compensation_disbursed_pct",
    "has_active_legal_dispute",
    "dispute_delay_impact_days",
    "avg_stakeholder_responsiveness",
    "affected_families_count",
    "land_area_hectares",
    "rehabilitation_completion_pct",
]
CATEGORICAL_FEATURES = [
    "project_type",
    "state",
]
ALL_FEATURE_COLUMNS = NUMERICAL_FEATURES + [
    f"{col}_encoded" for col in CATEGORICAL_FEATURES
]


def extract_raw_project_records(session: Session) -> List[Dict]:
    """Queries all projects joined with relational tables from PostgreSQL using high-performance bulk fetch."""
    projects = session.query(Project).order_by(Project.created_at.asc()).all()

    # Preload child tables in bulk for instant loading
    comps = {c.project_id: c for c in session.query(CompensationRecord).all()}
    
    disputes_by_proj = defaultdict(list)
    for d in session.query(LegalDispute).all():
        disputes_by_proj[d.project_id].append(d)

    stks_by_proj = defaultdict(list)
    for s in session.query(Stakeholder).all():
        stks_by_proj[s.project_id].append(s)

    rehabs = {r.project_id: r for r in session.query(RehabilitationProgress).all()}

    risks = {}
    for r in session.query(RiskScore).order_by(RiskScore.computed_at.asc()).all():
        risks[r.project_id] = r

    records = []
    for proj in projects:
        # 1. Compensation
        comp = comps.get(proj.id)
        if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
            disbursed = float(comp.total_amount_disbursed or 0.0)
            allocated = float(comp.total_amount_allocated)
            disbursed_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
        else:
            disbursed_pct = 0.0

        # 2. Legal disputes
        proj_disputes = disputes_by_proj.get(proj.id, [])
        has_active_dispute = 0
        total_delay_impact = 0
        for d in proj_disputes:
            if d.stay_order_active or d.status == DisputeStatusEnum.stay_granted:
                has_active_dispute = 1
            total_delay_impact += (d.delay_impact_estimate_days or 0)

        # 3. Stakeholders
        proj_stks = stks_by_proj.get(proj.id, [])
        if proj_stks:
            scores = [float(s.responsiveness_score) for s in proj_stks if s.responsiveness_score is not None]
            avg_stk_resp = float(np.mean(scores)) if scores else 50.0
        else:
            avg_stk_resp = 50.0

        # 4. Rehabilitation progress
        rehab = rehabs.get(proj.id)
        rehab_pct = float(rehab.completion_percentage) if rehab and rehab.completion_percentage is not None else 0.0

        # 5. Risk Score
        risk = risks.get(proj.id)
        risk_cat_str = risk.risk_category.value if risk and risk.risk_category else None

        records.append({
            "project_id": str(proj.id),
            "project_code": proj.project_code,
            "project_name": proj.name,
            "data_source": proj.data_source.value if proj.data_source else "synthetic",
            "project_type": proj.project_type,
            "state": proj.state,
            "district": proj.district,
            "land_area_hectares": float(proj.land_area_hectares or 0.0),
            "affected_families_count": int(proj.affected_families_count or 0),
            "compensation_disbursed_pct": disbursed_pct,
            "has_active_legal_dispute": has_active_dispute,
            "dispute_delay_impact_days": total_delay_impact,
            "avg_stakeholder_responsiveness": avg_stk_resp,
            "rehabilitation_completion_pct": rehab_pct,
            "risk_category": risk_cat_str,
        })

    return records


def build_feature_dataframe(session: Optional[Session] = None) -> pd.DataFrame:
    """Builds pandas DataFrame of engineered features from PostgreSQL."""
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        raw_records = extract_raw_project_records(session)
        df = pd.DataFrame(raw_records)
        return df
    finally:
        if close_session:
            session.close()


def fit_category_encoders(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """Builds deterministic category mappings for categorical columns."""
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        unique_vals = sorted(list(df[col].dropna().unique()))
        encoders[col] = {val: idx for idx, val in enumerate(unique_vals)}
    return encoders


def apply_category_encoders(df: pd.DataFrame, encoders: Dict[str, Dict[str, int]]) -> pd.DataFrame:
    """Applies categorical encoding to DataFrame."""
    df_out = df.copy()
    for col in CATEGORICAL_FEATURES:
        mapping = encoders[col]
        encoded_col = f"{col}_encoded"
        df_out[encoded_col] = df_out[col].map(lambda x: mapping.get(x, len(mapping)))
    return df_out


def load_feature_dataset(session: Optional[Session] = None) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, Dict]:
    """Loads feature matrix X, target series y, full df, and encoders for ML training."""
    df = build_feature_dataframe(session)

    # Filter out rows with missing risk_category
    df_valid = df.dropna(subset=["risk_category"]).copy()
    encoders = fit_category_encoders(df_valid)
    df_encoded = apply_category_encoders(df_valid, encoders)

    X = df_encoded[ALL_FEATURE_COLUMNS].copy()
    y = df_encoded["risk_category"].map(RISK_CATEGORY_MAP).astype(int)

    return X, y, df_encoded, encoders


def get_project_feature_vector(
    project_id: str,
    encoders: Dict[str, Dict[str, int]],
    session: Optional[Session] = None,
) -> pd.DataFrame:
    """Extracts single encoded feature vector for a given project_id."""
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        from uuid import UUID
        proj = None
        try:
            proj_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            proj = session.query(Project).filter_by(id=proj_uuid).first()
        except (ValueError, AttributeError):
            pass

        if not proj:
            proj = session.query(Project).filter_by(project_code=project_id).first()

        if not proj:
            raise ValueError(f"Project with ID or code '{project_id}' not found.")

        # Extract features
        comp = session.query(CompensationRecord).filter_by(project_id=proj.id).first()
        if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
            disbursed = float(comp.total_amount_disbursed or 0.0)
            allocated = float(comp.total_amount_allocated)
            disbursed_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
        else:
            disbursed_pct = 0.0

        disputes = session.query(LegalDispute).filter_by(project_id=proj.id).all()
        has_active_dispute = 0
        total_delay_impact = 0
        for d in disputes:
            if d.stay_order_active or d.status == DisputeStatusEnum.stay_granted:
                has_active_dispute = 1
            total_delay_impact += (d.delay_impact_estimate_days or 0)

        stk_scores = (
            session.query(Stakeholder.responsiveness_score)
            .filter_by(project_id=proj.id)
            .all()
        )
        avg_stk_resp = (
            float(np.mean([float(s[0]) for s in stk_scores if s[0] is not None]))
            if stk_scores
            else 50.0
        )

        rehab = session.query(RehabilitationProgress).filter_by(project_id=proj.id).first()
        rehab_pct = (
            float(rehab.completion_percentage)
            if rehab and rehab.completion_percentage is not None
            else 0.0
        )

        raw_dict = {
            "compensation_disbursed_pct": disbursed_pct,
            "has_active_legal_dispute": has_active_dispute,
            "dispute_delay_impact_days": total_delay_impact,
            "avg_stakeholder_responsiveness": avg_stk_resp,
            "affected_families_count": int(proj.affected_families_count or 0),
            "land_area_hectares": float(proj.land_area_hectares or 0.0),
            "rehabilitation_completion_pct": rehab_pct,
            "project_type": proj.project_type,
            "state": proj.state,
        }

        # Encode
        encoded_dict = {k: raw_dict[k] for k in NUMERICAL_FEATURES}
        for col in CATEGORICAL_FEATURES:
            mapping = encoders.get(col, {})
            val = raw_dict[col]
            encoded_dict[f"{col}_encoded"] = mapping.get(val, len(mapping))

        return pd.DataFrame([encoded_dict])[ALL_FEATURE_COLUMNS]
    finally:
        if close_session:
            session.close()

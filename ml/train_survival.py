"""LandSight AI - Milestone Survival Analysis (Cox Proportional Hazards).

Models statutory milestone durations and right-censored delays for critical stages
(Compensation & Possession) using Lifelines CoxPHFitter.

Strictly adheres to FIX 2:
- Excludes status='not_started' to prevent unelapsed stages from biasing hazard estimates.
- Uses actual_duration_days for completed stages (event=1).
- Uses elapsed duration for in_progress/delayed stages (event=0, right-censored).
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sqlalchemy.orm import Session

# Setup project path
ml_dir = Path(__file__).resolve().parent
root_dir = ml_dir.parent
sys.path.insert(0, str(root_dir))

from backend.app.database import SessionLocal
from backend.app.models import (
    CompensationRecord,
    DisputeStatusEnum,
    LegalDispute,
    Project,
    RehabilitationProgress,
    Stage,
    StageNameEnum,
    StageStatusEnum,
    Stakeholder,
)

SURVIVAL_COVARIATES = [
    "compensation_disbursed_pct",
    "has_active_legal_dispute",
    "dispute_delay_impact_days",
    "avg_stakeholder_responsiveness",
    "affected_families_count",
    "land_area_hectares",
    "rehabilitation_completion_pct",
]


def extract_stage_survival_data(
    stage_name_str: str, session: Optional[Session] = None
) -> pd.DataFrame:
    """Extracts survival analysis dataset for a statutory stage.
    
    CRITICAL (FIX 2):
    - EXCLUDES stages with status='not_started'
    - Only includes status IN ('completed', 'in_progress', 'delayed')
    - Completed: duration = actual_duration_days, event = 1
    - In_progress / Delayed: duration = elapsed duration, event = 0 (right-censored)
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        stage_enum = StageNameEnum(stage_name_str)
        # Filter strictly out 'not_started' (FIX 2)
        valid_statuses = [
            StageStatusEnum.completed,
            StageStatusEnum.in_progress,
            StageStatusEnum.delayed,
        ]

        query = (
            session.query(Stage, Project)
            .join(Project, Stage.project_id == Project.id)
            .filter(Stage.stage_name == stage_enum)
            .filter(Stage.status.in_(valid_statuses))
            .all()
        )

        from collections import defaultdict
        comps = {c.project_id: c for c in session.query(CompensationRecord).all()}
        disputes_by_proj = defaultdict(list)
        for d in session.query(LegalDispute).all():
            disputes_by_proj[d.project_id].append(d)
        stks_by_proj = defaultdict(list)
        for s in session.query(Stakeholder).all():
            stks_by_proj[s.project_id].append(s)
        rehabs = {r.project_id: r for r in session.query(RehabilitationProgress).all()}

        rows = []
        for stage, proj in query:
            # 1. Compensation disbursed %
            comp = comps.get(proj.id)
            if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
                disbursed = float(comp.total_amount_disbursed or 0.0)
                allocated = float(comp.total_amount_allocated)
                disbursed_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
            else:
                disbursed_pct = 0.0

            # 2. Disputes
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

            # 4. R&R
            rehab = rehabs.get(proj.id)
            rehab_pct = (
                float(rehab.completion_percentage)
                if rehab and rehab.completion_percentage is not None
                else 0.0
            )

            # Duration & Event definition (FIX 2)
            planned_days = stage.planned_duration_days or 90
            if stage.status == StageStatusEnum.completed:
                event = 1
                duration = float(stage.actual_duration_days or (planned_days + stage.delay_days))
            else:
                # in_progress or delayed: right-censored observation
                event = 0
                # Elapsed days so far
                duration = float(planned_days + (stage.delay_days or 0))

            duration = max(1.0, duration)

            rows.append({
                "project_id": str(proj.id),
                "planned_duration_days": planned_days,
                "duration": duration,
                "event": event,
                "compensation_disbursed_pct": disbursed_pct,
                "has_active_legal_dispute": has_active_dispute,
                "dispute_delay_impact_days": total_delay_impact,
                "avg_stakeholder_responsiveness": avg_stk_resp,
                "affected_families_count": int(proj.affected_families_count or 0),
                "land_area_hectares": float(proj.land_area_hectares or 0.0),
                "rehabilitation_completion_pct": rehab_pct,
            })

        df = pd.DataFrame(rows)
        return df
    finally:
        if close_session:
            session.close()


def train_cox_model(stage_name_str: str) -> Tuple[CoxPHFitter, float, pd.DataFrame]:
    """Trains a Cox Proportional Hazards model for the given stage."""
    print(f"\n[*] Training Cox PH Survival Model for Stage: '{stage_name_str}'...")
    df = extract_stage_survival_data(stage_name_str)
    print(f"[+] Total observations (excluding 'not_started'): {len(df)}")
    print(f"    Observed Events (completed, event=1): {int(df['event'].sum())}")
    print(f"    Right-Censored (ongoing/delayed, event=0): {int(len(df) - df['event'].sum())}")

    cols = ["duration", "event"] + SURVIVAL_COVARIATES
    data_to_fit = df[cols].copy()

    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(data_to_fit, duration_col="duration", event_col="event")

    # Concordance Index
    c_index = cph.concordance_index_
    print(f"[+] Model Fit Complete. Concordance Index (C-index): {c_index:.4f}")
    print("Summary of Hazard Ratios (exp(coef)):")
    summary = cph.summary[["coef", "exp(coef)", "p"]]
    for idx, row in summary.iterrows():
        print(f"    {idx:<32} coef={row['coef']:>7.4f} | HR={row['exp(coef)']:>7.4f} | p={row['p']:.4e}")

    # Save artifact
    models_dir = ml_dir / "models"
    models_dir.mkdir(exist_ok=True, parents=True)
    out_file = models_dir / f"survival_{stage_name_str}.joblib"
    artifact = {
        "model": cph,
        "stage_name": stage_name_str,
        "covariates": SURVIVAL_COVARIATES,
        "c_index": c_index,
        "summary": summary.to_dict(),
    }
    joblib.dump(artifact, out_file)
    print(f"[+] Saved survival artifact to: {out_file}")

    return cph, c_index, df


def predict_expected_delay(
    project_id: str,
    stage_name: str,
    override_features: Optional[Dict] = None,
    session: Optional[Session] = None,
) -> int:
    """Predicts expected delay days beyond planned duration using trained Cox PH model."""
    models_dir = ml_dir / "models"
    model_file = models_dir / f"survival_{stage_name}.joblib"
    if not model_file.exists():
        raise FileNotFoundError(f"Survival model for stage '{stage_name}' not found at {model_file}")

    bundle = joblib.load(model_file)
    cph = bundle["model"]

    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        from uuid import UUID
        p_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
        proj = session.query(Project).filter_by(id=p_uuid).first()
        if not proj:
            return 0

        # Extract features
        comp = session.query(CompensationRecord).filter_by(project_id=proj.id).first()
        disbursed_pct = (
            float(np.clip((float(comp.total_amount_disbursed or 0.0) / float(comp.total_amount_allocated)) * 100.0, 0.0, 100.0))
            if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0
            else 0.0
        )

        disputes = session.query(LegalDispute).filter_by(project_id=proj.id).all()
        has_active = 1 if any(d.stay_order_active or d.status == DisputeStatusEnum.stay_granted for d in disputes) else 0
        total_delay = sum(d.delay_impact_estimate_days or 0 for d in disputes)

        stk_scores = session.query(Stakeholder.responsiveness_score).filter_by(project_id=proj.id).all()
        avg_stk = float(np.mean([s[0] for s in stk_scores if s[0] is not None])) if stk_scores else 50.0

        rehab = session.query(RehabilitationProgress).filter_by(project_id=proj.id).first()
        rehab_pct = float(rehab.completion_percentage) if rehab and rehab.completion_percentage is not None else 0.0

        feat_dict = {
            "compensation_disbursed_pct": disbursed_pct,
            "has_active_legal_dispute": has_active,
            "dispute_delay_impact_days": total_delay,
            "avg_stakeholder_responsiveness": avg_stk,
            "affected_families_count": int(proj.affected_families_count or 0),
            "land_area_hectares": float(proj.land_area_hectares or 0.0),
            "rehabilitation_completion_pct": rehab_pct,
        }

        # Apply overrides if counterfactual what_if
        if override_features:
            for k, v in override_features.items():
                if k in feat_dict:
                    feat_dict[k] = v

        row_df = pd.DataFrame([feat_dict])[SURVIVAL_COVARIATES]

        # Predict expected milestone completion duration (restricted mean survival time)
        exp_duration_series = cph.predict_expectation(row_df)
        expected_duration = float(exp_duration_series.iloc[0])

        # Get planned duration
        stage_enum = StageNameEnum(stage_name)
        stg = session.query(Stage).filter_by(project_id=proj.id, stage_name=stage_enum).first()
        planned = stg.planned_duration_days if stg and stg.planned_duration_days else 90

        expected_delay = max(0, int(expected_duration - planned))
        return expected_delay
    finally:
        if close_session:
            session.close()


def train_all_survival_models():
    """Trains survival models for both Compensation and Possession stages."""
    print("=" * 60)
    print("LandSight AI - Training Cox Proportional Hazards Milestone Models")
    print("=" * 60)

    cph_comp, c_comp, df_comp = train_cox_model("compensation")
    cph_poss, c_poss, df_poss = train_cox_model("possession")

    print("\n" + "=" * 60)
    print("SURVIVAL MODEL SUMMARY")
    print("=" * 60)
    print(f"Compensation Stage C-Index: {c_comp:.4f}")
    print(f"Possession Stage C-Index:   {c_poss:.4f}")
    print("=" * 60)

    return {
        "compensation": {"c_index": c_comp, "model": cph_comp},
        "possession": {"c_index": c_poss, "model": cph_poss},
    }


if __name__ == "__main__":
    train_all_survival_models()

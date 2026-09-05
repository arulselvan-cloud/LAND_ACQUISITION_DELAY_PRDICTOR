"""LandSight AI - Delay Propagation Engine ("Impact Map").

Models sequential dependencies across the 5 statutory RFCTLARR lifecycle milestones:
    notification -> survey -> compensation -> possession -> rehabilitation

Fits stage-pair regressions from live database records and cascades upstream delays
downstream to forecast delays for unreached milestones.
"""

from collections import defaultdict
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
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
    Stage,
    StageNameEnum,
    StageStatusEnum,
    Stakeholder,
)

STAGE_SEQUENCE = [
    "notification",
    "survey",
    "compensation",
    "possession",
    "rehabilitation",
]

STAGE_PAIRS = [
    ("notification", "survey"),
    ("survey", "compensation"),
    ("compensation", "possession"),
    ("possession", "rehabilitation"),
]

FEATURE_COLS = [
    "upstream_delay",
    "has_active_legal_dispute",
    "avg_stakeholder_responsiveness",
    "compensation_disbursed_pct",
]

MODELS_DIR = ml_dir / "models"
PROPAGATION_MODELS_PATH = MODELS_DIR / "delay_propagation_models.joblib"


def extract_stage_pair_training_data(
    upstream_stage: str,
    downstream_stage: str,
    session: Optional[Session] = None,
) -> pd.DataFrame:
    """Extracts paired delay data for consecutive milestones.
    
    Excludes stages with status='not_started' so only projects that reached
    both milestones with meaningful elapsed progress are included.
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        # Preload data efficiently
        projects = {p.id: p for p in session.query(Project).all()}
        comps = {c.project_id: c for c in session.query(CompensationRecord).all()}

        disputes_by_proj = defaultdict(list)
        for d in session.query(LegalDispute).all():
            disputes_by_proj[d.project_id].append(d)

        stks_by_proj = defaultdict(list)
        for s in session.query(Stakeholder).all():
            stks_by_proj[s.project_id].append(s)

        stages_by_proj = defaultdict(dict)
        for s in session.query(Stage).all():
            stages_by_proj[s.project_id][s.stage_name.value] = s

        rows = []
        for pid in projects:
            stg_up = stages_by_proj[pid].get(upstream_stage)
            stg_down = stages_by_proj[pid].get(downstream_stage)

            if not stg_up or not stg_down:
                continue

            # Exclude stages not yet started (no elapsed delay recorded)
            if (
                stg_up.status == StageStatusEnum.not_started
                or stg_down.status == StageStatusEnum.not_started
            ):
                continue

            # Features
            comp = comps.get(pid)
            if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
                disbursed = float(comp.total_amount_disbursed or 0.0)
                allocated = float(comp.total_amount_allocated)
                comp_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
            else:
                comp_pct = 0.0

            proj_disputes = disputes_by_proj.get(pid, [])
            has_dispute = (
                1
                if any(
                    d.stay_order_active or d.status == DisputeStatusEnum.stay_granted
                    for d in proj_disputes
                )
                else 0
            )

            proj_stks = stks_by_proj.get(pid, [])
            if proj_stks:
                scores = [
                    float(s.responsiveness_score)
                    for s in proj_stks
                    if s.responsiveness_score is not None
                ]
                avg_stk = float(np.mean(scores)) if scores else 50.0
            else:
                avg_stk = 50.0

            rows.append({
                "upstream_delay": float(stg_up.delay_days or 0),
                "has_active_legal_dispute": float(has_dispute),
                "avg_stakeholder_responsiveness": float(avg_stk),
                "compensation_disbursed_pct": float(comp_pct),
                "downstream_delay": float(stg_down.delay_days or 0),
            })

        return pd.DataFrame(rows)
    finally:
        if close_session:
            session.close()


def train_propagation_models(session: Optional[Session] = None) -> Dict:
    """Trains regression models for each consecutive milestone pair and saves artifacts."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    models_dict = {}

    print("=" * 65)
    print("LandSight AI - Fitting Milestone Delay Propagation Models (Impact Map)")
    print("=" * 65)

    for s_up, s_down in STAGE_PAIRS:
        df = extract_stage_pair_training_data(s_up, s_down, session=session)
        X = df[FEATURE_COLS]
        y = df["downstream_delay"]

        model = Ridge(alpha=1.0)
        model.fit(X, y)

        y_pred = model.predict(X)
        r2 = float(r2_score(y, y_pred))

        coef_dict = {col: float(c) for col, c in zip(FEATURE_COLS, model.coef_)}
        intercept = float(model.intercept_)

        models_dict[f"{s_up}->{s_down}"] = {
            "model": model,
            "upstream_stage": s_up,
            "downstream_stage": s_down,
            "r2": r2,
            "n_samples": len(df),
            "intercept": intercept,
            "coefficients": coef_dict,
        }

        print(f"[*] Pair: {s_up.upper()} -> {s_down.upper()} (N={len(df)} active stages)")
        print(f"    R^2 Score: {r2:.4f} | Intercept: {intercept:+.4f}")
        for feat_name, coef in coef_dict.items():
            print(f"    {feat_name:<34}: {coef:+.4f}")
        print("-" * 65)

    joblib.dump(models_dict, PROPAGATION_MODELS_PATH)
    print(f"[+] Saved all propagation models to: {PROPAGATION_MODELS_PATH}\n")
    return models_dict


def load_propagation_models(session: Optional[Session] = None) -> Dict:
    """Loads fitted propagation models or trains them if not found."""
    if PROPAGATION_MODELS_PATH.exists():
        return joblib.load(PROPAGATION_MODELS_PATH)
    return train_propagation_models(session=session)


def propagate_delay(
    project_id: str,
    models: Optional[Dict] = None,
    session: Optional[Session] = None,
) -> List[Dict]:
    """Cascades delay downstream across statutory milestones for a given project.
    
    Takes the project's actual delay for completed/in-progress stages, and
    predicts expected delay for any stage not yet reached (or downstream of an
    unreached milestone), propagating the impact stage by stage.
    
    Returns:
        List of dicts: [
            {
                "stage_name": str,
                "stage_order": int,
                "current_status": str,
                "actual_or_predicted_delay_days": int,
                "is_predicted": bool
            }, ...
        ]
    """
    if models is None:
        models = load_propagation_models(session=session)

    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        from uuid import UUID
        proj = None
        try:
            p_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            proj = session.query(Project).filter_by(id=p_uuid).first()
        except (ValueError, AttributeError):
            pass

        if not proj:
            proj = session.query(Project).filter_by(project_code=project_id).first()

        if not proj:
            raise ValueError(f"Project with ID or code '{project_id}' not found.")

        # Extract project features
        comp = session.query(CompensationRecord).filter_by(project_id=proj.id).first()
        if comp and comp.total_amount_allocated and float(comp.total_amount_allocated) > 0:
            disbursed = float(comp.total_amount_disbursed or 0.0)
            allocated = float(comp.total_amount_allocated)
            comp_pct = float(np.clip((disbursed / allocated) * 100.0, 0.0, 100.0))
        else:
            comp_pct = 0.0

        disputes = session.query(LegalDispute).filter_by(project_id=proj.id).all()
        has_dispute = (
            1
            if any(
                d.stay_order_active or d.status == DisputeStatusEnum.stay_granted
                for d in disputes
            )
            else 0
        )

        stks = session.query(Stakeholder).filter_by(project_id=proj.id).all()
        if stks:
            scores = [
                float(s.responsiveness_score)
                for s in stks
                if s.responsiveness_score is not None
            ]
            avg_stk = float(np.mean(scores)) if scores else 50.0
        else:
            avg_stk = 50.0

        # Query all 5 stages ordered
        stages = (
            session.query(Stage)
            .filter_by(project_id=proj.id)
            .order_by(Stage.stage_order.asc())
            .all()
        )
        stage_dict = {s.stage_name.value: s for s in stages}

        results = []
        is_cascading = False
        prev_delay = 0.0

        for s_name in STAGE_SEQUENCE:
            stg = stage_dict.get(s_name)
            if not stg:
                continue

            # Check if this stage should be predicted:
            # 1. It is explicitly not_started, OR
            # 2. An upstream milestone was not_started / predicted (sequential gating)
            should_predict = is_cascading or (stg.status == StageStatusEnum.not_started)

            if not should_predict:
                # Stage has actual recorded delay
                actual_delay = int(stg.delay_days or 0)
                results.append({
                    "stage_name": s_name,
                    "stage_order": stg.stage_order,
                    "current_status": stg.status.value,
                    "actual_or_predicted_delay_days": actual_delay,
                    "is_predicted": False,
                })
                prev_delay = float(actual_delay)
            else:
                # Enter cascading prediction mode
                is_cascading = True
                prev_stage_name = STAGE_SEQUENCE[stg.stage_order - 2]
                pair_key = f"{prev_stage_name}->{s_name}"
                model_bundle = models[pair_key]
                model = model_bundle["model"]

                input_feat = pd.DataFrame([{
                    "upstream_delay": prev_delay,
                    "has_active_legal_dispute": float(has_dispute),
                    "avg_stakeholder_responsiveness": float(avg_stk),
                    "compensation_disbursed_pct": float(comp_pct),
                }])[FEATURE_COLS]

                pred_raw = model.predict(input_feat)[0]
                pred_delay = max(0, int(round(pred_raw)))

                results.append({
                    "stage_name": s_name,
                    "stage_order": stg.stage_order,
                    "current_status": stg.status.value,
                    "actual_or_predicted_delay_days": pred_delay,
                    "is_predicted": True,
                })
                prev_delay = float(pred_delay)

        return results
    finally:
        if close_session:
            session.close()


def print_propagation_table(project_code: str, results: List[Dict]):
    """Pretty-prints propagation impact table for a project."""
    print(f"\nDelay Propagation (Impact Map) for [{project_code}]:")
    print(f"  {'#':<2} {'Milestone':<16} {'Status':<14} {'Delay (Days)':<14} {'Mode':<12}")
    print("  " + "-" * 58)
    for r in results:
        mode_str = "PREDICTED (Cascaded)" if r["is_predicted"] else "ACTUAL (Observed)"
        print(
            f"  {r['stage_order']:<2} {r['stage_name'].title():<16} {r['current_status']:<14} "
            f"{r['actual_or_predicted_delay_days']:>3} days      {mode_str:<12}"
        )
    total_delay = sum(r["actual_or_predicted_delay_days"] for r in results)
    print("  " + "-" * 58)
    print(f"  Cumulative Gated Delay across All 5 Milestones: {total_delay} days\n")


if __name__ == "__main__":
    # Fit and save models
    models = train_propagation_models()

    # Test on the 3 real showcase projects
    session = SessionLocal()
    showcase_codes = ["CBIC-TN-PKG02", "BSRP-KA-CORR04", "MAHSR-MH-PAL03"]
    for code in showcase_codes:
        p = session.query(Project).filter_by(project_code=code).first()
        if p:
            res = propagate_delay(str(p.id), models=models, session=session)
            print_propagation_table(code, res)
    session.close()

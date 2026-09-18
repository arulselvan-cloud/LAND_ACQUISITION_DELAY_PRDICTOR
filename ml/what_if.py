"""LandSight AI - Interactive Counterfactual Simulation Engine ("What-If").

Enables policy-makers and acquisition officers to simulate interventions
(e.g., accelerating compensation disbursement from 20% to 85%, resolving active litigation)
and measure the quantitative impact on risk categories, delay probabilities, and expected delay days.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd

# Setup paths
ml_dir = Path(__file__).resolve().parent
root_dir = ml_dir.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import (
    Project,
    RiskCategoryEnum,
    RiskScore,
    Stage,
    StageStatusEnum,
)
from ml.features import (
    ALL_FEATURE_COLUMNS,
    CATEGORICAL_FEATURES,
    INV_RISK_CATEGORY_MAP,
    NUMERICAL_FEATURES,
    RISK_CATEGORY_MAP,
    get_project_feature_vector,
)
from ml.train_survival import predict_expected_delay


def what_if(
    project_id: str,
    hypothetical_changes: Dict[str, Any],
    session: Optional[Session] = None,
    classifier_bundle: Optional[Dict] = None,
    survival_comp_bundle: Optional[Dict] = None,
    survival_poss_bundle: Optional[Dict] = None,
) -> Dict:
    """Computes counterfactual predictions given hypothetical interventions for a project.
    
    Args:
        project_id: UUID string or project_code of target project.
        hypothetical_changes: Dictionary of features to mutate, e.g.
            {
                "compensation_disbursed_pct": 85.0,
                "has_active_legal_dispute": 0,
                "avg_stakeholder_responsiveness": 78.5
            }
        session: Optional SQLAlchemy Session.
        classifier_bundle: Optional pre-loaded classifier bundle.
        survival_comp_bundle: Optional pre-loaded compensation survival model bundle.
        survival_poss_bundle: Optional pre-loaded possession survival model bundle.
            
    Returns:
        Structured dictionary comparing baseline vs counterfactual outcomes.
    """
    if classifier_bundle is not None:
        bundle = classifier_bundle
    else:
        model_bundle_path = ml_dir / "models" / "risk_classifier.joblib"
        if not model_bundle_path.exists():
            raise FileNotFoundError(f"Classifier model not found at {model_bundle_path}. Run ml/train_classifier.py first.")
        bundle = joblib.load(model_bundle_path)

    model = bundle["model"]
    encoders = bundle["encoders"]
    inv_label_map = bundle["inv_label_map"]

    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        # 1. Fetch baseline feature vector
        base_df = get_project_feature_vector(project_id, encoders, session=session)
        base_features = base_df.iloc[0].to_dict()

        # Baseline predictions
        base_probs = model.predict_proba(base_df)[0]
        base_pred_idx = int(np.argmax(base_probs))
        base_cat = inv_label_map[base_pred_idx]

        # Delay probability (sum of High + Critical probabilities)
        # Class 0: low, 1: medium, 2: high, 3: critical
        base_delay_prob = float(base_probs[2] + base_probs[3])

        # Baseline expected delay in compensation and possession stages
        base_comp_delay = predict_expected_delay(
            project_id, "compensation", session=session, model_bundle=survival_comp_bundle
        )
        base_poss_delay = predict_expected_delay(
            project_id, "possession", session=session, model_bundle=survival_poss_bundle
        )
        base_total_delay = base_comp_delay + base_poss_delay

        # Fetch actual delay accumulated so far from the stages table (same source as /propagation)
        from uuid import UUID
        proj_obj = None
        try:
            p_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            proj_obj = session.query(Project).filter_by(id=p_uuid).first()
        except (ValueError, AttributeError):
            pass
        if not proj_obj:
            proj_obj = session.query(Project).filter_by(project_code=project_id).first()

        actual_delay_so_far = 0
        if proj_obj:
            stages = (
                session.query(Stage)
                .filter_by(project_id=proj_obj.id)
                .order_by(Stage.stage_order.asc())
                .all()
            )
            for stg in stages:
                if stg.status == StageStatusEnum.not_started:
                    break
                actual_delay_so_far += int(stg.delay_days or 0)

        # 2. Construct Counterfactual feature vector
        cf_features = base_features.copy()
        for k, v in hypothetical_changes.items():
            if k in NUMERICAL_FEATURES:
                cf_features[k] = float(v)
            elif k in CATEGORICAL_FEATURES:
                mapping = encoders.get(k, {})
                cf_features[f"{k}_encoded"] = mapping.get(v, len(mapping))
            elif f"{k}_encoded" in cf_features:
                cf_features[f"{k}_encoded"] = v

        # Domain safety net: if has_active_legal_dispute is explicitly set to 0
        # and dispute_delay_impact_days is NOT provided in the request,
        # automatically default dispute_delay_impact_days to 0 rather than silently
        # keeping the baseline's original value. This prevents contradictory feature vectors.
        if (
            "has_active_legal_dispute" in hypothetical_changes
            and float(hypothetical_changes["has_active_legal_dispute"]) == 0.0
            and "dispute_delay_impact_days" not in hypothetical_changes
        ):
            cf_features["dispute_delay_impact_days"] = 0.0

        cf_df = pd.DataFrame([cf_features])[ALL_FEATURE_COLUMNS]

        # Counterfactual predictions
        cf_probs = model.predict_proba(cf_df)[0]
        cf_pred_idx = int(np.argmax(cf_probs))
        cf_cat = inv_label_map[cf_pred_idx]
        cf_delay_prob = float(cf_probs[2] + cf_probs[3])

        # Counterfactual expected delay in survival stages
        cf_comp_delay = predict_expected_delay(
            project_id, "compensation", override_features=cf_features, session=session, model_bundle=survival_comp_bundle
        )
        cf_poss_delay = predict_expected_delay(
            project_id, "possession", override_features=cf_features, session=session, model_bundle=survival_poss_bundle
        )
        cf_total_delay = cf_comp_delay + cf_poss_delay

        # 3. Compute Net Impact
        risk_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        risk_reduced = risk_rank[cf_cat] < risk_rank[base_cat]
        risk_delta = risk_rank[cf_cat] - risk_rank[base_cat]
        prob_reduction = round(base_delay_prob - cf_delay_prob, 4)
        days_saved = max(0, base_total_delay - cf_total_delay)

        return {
            "project_id": str(project_id),
            "simulated_interventions": hypothetical_changes,
            "baseline": {
                "risk_category": base_cat,
                "delay_probability": round(base_delay_prob, 4),
                "actual_delay_so_far_days": actual_delay_so_far,
                "expected_delay_days": base_total_delay,
                "stage_breakdown": {
                    "additional_expected_compensation_delay_days": base_comp_delay,
                    "additional_expected_possession_delay_days": base_poss_delay,
                },
                "class_probabilities": {
                    inv_label_map[i]: round(float(base_probs[i]), 4) for i in range(len(base_probs))
                },
                "features": {
                    "compensation_disbursed_pct": float(base_features.get("compensation_disbursed_pct", 0.0)),
                    "avg_stakeholder_responsiveness": float(base_features.get("avg_stakeholder_responsiveness", 0.0)),
                    "has_active_legal_dispute": int(base_features.get("has_active_legal_dispute", 0)),
                },
            },
            "counterfactual": {
                "risk_category": cf_cat,
                "delay_probability": round(cf_delay_prob, 4),
                "expected_delay_days": cf_total_delay,
                "stage_breakdown": {
                    "additional_expected_compensation_delay_days": cf_comp_delay,
                    "additional_expected_possession_delay_days": cf_poss_delay,
                },
                "class_probabilities": {
                    inv_label_map[i]: round(float(cf_probs[i]), 4) for i in range(len(cf_probs))
                },
            },
            "impact": {
                "risk_category_reduced": risk_reduced,
                "risk_tier_change": f"{base_cat.upper()} -> {cf_cat.upper()}",
                "delay_probability_reduction": prob_reduction,
                "estimated_delay_days_saved": days_saved,
                "summary": (
                    f"Intervention shifts risk tier from {base_cat.upper()} to {cf_cat.upper()} "
                    f"(delay prob {base_delay_prob*100:.1f}% -> {cf_delay_prob*100:.1f}%), "
                    f"saving an estimated ~{days_saved} days across compensation and possession milestones."
                ),
            },
        }
    finally:
        session.close()


if __name__ == "__main__":
    # Test on first project in database
    session = SessionLocal()
    sample_proj = session.query(Project).first()
    session.close()

    if sample_proj:
        print(f"Testing what_if on sample project {sample_proj.project_code} ({sample_proj.id})...")
        changes = {
            "compensation_disbursed_pct": 95.0,
            "has_active_legal_dispute": 0,
            "avg_stakeholder_responsiveness": 85.0,
        }
        res = what_if(str(sample_proj.id), changes)
        print("\nWhat-If Result:")
        print(f"  Baseline:       {res['baseline']['risk_category']} (Prob: {res['baseline']['delay_probability']:.2f}, Days: {res['baseline']['expected_delay_days']})")
        print(f"  Counterfactual: {res['counterfactual']['risk_category']} (Prob: {res['counterfactual']['delay_probability']:.2f}, Days: {res['counterfactual']['expected_delay_days']})")
        print(f"  Impact:         {res['impact']['summary']}")

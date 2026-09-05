"""LandSight AI - Model Explainability Engine (SHAP).

Computes local feature attributions using TreeExplainer for individual projects,
extracting top 5 risk drivers with magnitude and direction, and global feature importance.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
import shap

# Setup paths
ml_dir = Path(__file__).resolve().parent
root_dir = ml_dir.parent
sys.path.insert(0, str(root_dir))

from ml.features import (
    ALL_FEATURE_COLUMNS,
    INV_RISK_CATEGORY_MAP,
    RISK_CATEGORY_MAP,
    get_project_feature_vector,
    load_feature_dataset,
)

FEATURE_HUMAN_NAMES = {
    "compensation_disbursed_pct": "Compensation Disbursement Rate (%)",
    "has_active_legal_dispute": "Active Court Stay / Judicial Injunction",
    "dispute_delay_impact_days": "Legal Dispute Delay Impact (Days)",
    "avg_stakeholder_responsiveness": "Stakeholder Responsiveness Score (0-100)",
    "affected_families_count": "Number of Project Affected Families",
    "land_area_hectares": "Total Acquisition Land Area (Hectares)",
    "rehabilitation_completion_pct": "R&R Resettlement Completion (%)",
    "project_type_encoded": "Infrastructure Sector Type",
    "state_encoded": "State Administrative Jurisdiction",
}


class ModelExplainer:
    """Wrapper around trained XGBoost classifier and SHAP TreeExplainer."""

    def __init__(
        self,
        model_bundle_path: Optional[Path] = None,
        bundle: Optional[Dict] = None,
        explainer: Optional[shap.TreeExplainer] = None,
    ):
        if bundle is not None:
            self.bundle = bundle
        else:
            if model_bundle_path is None:
                model_bundle_path = ml_dir / "models" / "risk_classifier.joblib"

            if not model_bundle_path.exists():
                raise FileNotFoundError(f"Classifier model not found at {model_bundle_path}. Run ml/train_classifier.py first.")

            self.bundle = joblib.load(model_bundle_path)

        self.model = self.bundle["model"]
        self.feature_names = self.bundle["feature_names"]
        self.encoders = self.bundle["encoders"]
        self.label_map = self.bundle["label_map"]
        self.inv_label_map = self.bundle["inv_label_map"]

        # Initialize TreeExplainer or reuse preloaded
        self.explainer = explainer if explainer is not None else shap.TreeExplainer(self.model)

    def explain_prediction(self, project_id: str, session: Optional[Any] = None) -> Dict:
        """Explains risk prediction for an individual project by ID or code."""
        # 1. Fetch encoded feature vector
        feat_df = get_project_feature_vector(project_id, self.encoders, session=session)
        feat_vals = feat_df.iloc[0].to_dict()

        # 2. Predict probabilities and risk class
        probs = self.model.predict_proba(feat_df)[0]
        pred_idx = int(np.argmax(probs))
        pred_cat = self.inv_label_map[pred_idx]

        # 3. Compute SHAP values
        shap_values = self.explainer.shap_values(feat_df)
        # shap_values shape: (1, n_features, n_classes) or list of (1, n_features) per class
        if isinstance(shap_values, list):
            class_shap = shap_values[pred_idx][0]
        elif len(shap_values.shape) == 3:
            class_shap = shap_values[0, :, pred_idx]
        else:
            class_shap = shap_values[0]

        # 4. Rank features by magnitude
        factors = []
        for feat_name, shap_val in zip(self.feature_names, class_shap):
            raw_val = feat_vals.get(feat_name, None)
            direction = "increases_risk" if shap_val > 0 else "decreases_risk"
            factors.append({
                "feature": feat_name,
                "display_name": FEATURE_HUMAN_NAMES.get(feat_name, feat_name),
                "value": raw_val,
                "shap_value": round(float(shap_val), 4),
                "magnitude": round(float(abs(shap_val)), 4),
                "impact": round(float(abs(shap_val)), 4),
                "direction": direction,
            })

        # Sort by absolute SHAP impact
        factors.sort(key=lambda x: x["impact"], reverse=True)
        top_5 = factors[:5]

        return {
            "project_id": str(project_id),
            "predicted_risk_category": pred_cat,
            "prediction_probabilities": {
                self.inv_label_map[i]: round(float(probs[i]), 4) for i in range(len(probs))
            },
            "top_drivers": top_5,
            "all_drivers": factors,
        }

    def compute_global_importance(self, sample_size: int = 500) -> List[Dict]:
        """Computes global dataset-level feature importance across classes."""
        X, y, df, encoders = load_feature_dataset()
        if len(X) > sample_size:
            X_sample = X.sample(n=sample_size, random_state=42)
        else:
            X_sample = X

        shap_vals = self.explainer.shap_values(X_sample)

        # Average |SHAP| across all classes and samples
        if isinstance(shap_vals, list):
            # List of (N, P) for each class
            all_abs = np.mean([np.abs(sv) for sv in shap_vals], axis=0)  # (N, P)
            mean_importance = np.mean(all_abs, axis=0)  # (P,)
        elif len(shap_vals.shape) == 3:
            mean_importance = np.mean(np.abs(shap_vals), axis=(0, 2))
        else:
            mean_importance = np.mean(np.abs(shap_vals), axis=0)

        importance_list = []
        for feat_name, score in zip(self.feature_names, mean_importance):
            importance_list.append({
                "feature": feat_name,
                "display_name": FEATURE_HUMAN_NAMES.get(feat_name, feat_name),
                "mean_abs_shap": round(float(score), 4),
            })

        importance_list.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        return importance_list


def explain_prediction(project_id: str) -> Dict:
    """Standalone convenience helper for project explanation."""
    explainer = ModelExplainer()
    return explainer.explain_prediction(project_id)


def get_global_importance() -> List[Dict]:
    """Standalone convenience helper for global feature importance."""
    explainer = ModelExplainer()
    return explainer.compute_global_importance()


if __name__ == "__main__":
    print("Computing global feature importance...")
    global_imp = get_global_importance()
    print("\nTop 10 Global SHAP Feature Importances:")
    for idx, item in enumerate(global_imp[:10], 1):
        print(f"  {idx:>2}. {item['display_name']:<42}: {item['mean_abs_shap']:.4f}")

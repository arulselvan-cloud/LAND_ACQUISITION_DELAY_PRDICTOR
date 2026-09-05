"""LandSight AI - Refresh Risk Scores Database Table against Current ML Model."""

from datetime import datetime, timezone
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

from backend.app.database import SessionLocal
from backend.app.models.enums import RiskCategoryEnum
from backend.app.models.project import Project
from backend.app.models.risk import RiskScore
from ml.features import (
    ALL_FEATURE_COLUMNS,
    INV_RISK_CATEGORY_MAP,
    apply_category_encoders,
    build_feature_dataframe,
)


def refresh_all_risk_scores():
    print("=" * 70)
    print("LandSight AI - Refreshing Stored Risk Scores against Production Model")
    print("=" * 70)

    models_dir = root_dir / "ml" / "models"
    bundle_path = models_dir / "risk_classifier.joblib"
    if not bundle_path.exists():
        raise FileNotFoundError(f"Model not found at {bundle_path}")

    bundle = joblib.load(bundle_path)
    model = bundle["model"]
    encoders = bundle["encoders"]
    inv_label_map = bundle["inv_label_map"]

    session = SessionLocal()
    try:
        t0 = time.perf_counter()
        print("[*] Extracting project features from database...")
        df = build_feature_dataframe(session=session)
        print(f"[+] Loaded {len(df)} project records in {time.perf_counter() - t0:.2f}s.")

        print("[*] Running batch ML inference across all projects...")
        t1 = time.perf_counter()
        df_encoded = apply_category_encoders(df, encoders)
        X = df_encoded[ALL_FEATURE_COLUMNS]
        probs = model.predict_proba(X)
        pred_indices = np.argmax(probs, axis=1)
        print(f"[+] Computed predictions for {len(X)} projects in {time.perf_counter() - t1:.2f}s.")

        print("[*] Updating database risk_scores table...")
        now = datetime.now(timezone.utc)
        existing_scores = {str(r.project_id): r for r in session.query(RiskScore).all()}

        updated_count = 0
        inserted_count = 0

        for i, row in df.iterrows():
            pid_str = str(row["project_id"])
            pred_idx = int(pred_indices[i])
            pred_cat_str = inv_label_map[pred_idx]
            cat_enum = RiskCategoryEnum(pred_cat_str)
            delay_prob = float(probs[i][2] + probs[i][3])
            conf = float(np.max(probs[i]))

            risk_rec = existing_scores.get(pid_str)
            if risk_rec:
                risk_rec.risk_category = cat_enum
                risk_rec.overall_delay_probability = round(delay_prob, 4)
                risk_rec.confidence_score = round(conf, 4)
                risk_rec.computed_at = now
                updated_count += 1
            else:
                new_rec = RiskScore(
                    project_id=row["project_id"],
                    risk_category=cat_enum,
                    overall_delay_probability=round(delay_prob, 4),
                    confidence_score=round(conf, 4),
                    stage_delay_probabilities={},
                    predicted_delay_days=0,
                    computed_at=now,
                )
                session.add(new_rec)
                inserted_count += 1

        session.commit()
        total_time = time.perf_counter() - t0
        print(f"[+] Successfully refreshed {updated_count} risk scores (and inserted {inserted_count}) in {total_time:.2f}s.")

        # Check CBIC-TN-PKG02
        cbic_proj = session.query(Project).filter_by(project_code="CBIC-TN-PKG02").first()
        if cbic_proj:
            cbic_risk = session.query(RiskScore).filter_by(project_id=cbic_proj.id).first()
            print("\nVerification for [CBIC-TN-PKG02]:")
            print(f"  Risk Category:    {cbic_risk.risk_category.value}")
            print(f"  Delay Probability: {cbic_risk.overall_delay_probability:.4f}")
            print(f"  Confidence:       {cbic_risk.confidence_score:.4f}")
            print(f"  Computed At:      {cbic_risk.computed_at}")
    finally:
        session.close()


if __name__ == "__main__":
    refresh_all_risk_scores()

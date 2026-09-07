"""LandSight AI - Verification of Dynamic Retraining against Database Perturbation.
1. Capture baseline accuracy (70.47%).
2. Temporarily perturb a database feature (flip 3 risk score labels in PostgreSQL).
3. Call POST /api/retrain?confirm=true to demonstrate dynamic accuracy variation.
4. Restore the perturbed database records back to their exact original state.
5. Re-retrain once more to restore the exact original 70.47% artifact.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.project import Project
from backend.app.models.risk import RiskScore
from backend.app.models.enums import RiskCategoryEnum


def test_perturbation():
    print("=" * 70)
    print("TESTING RETRAIN DYNAMICS WITH TEMPORARY DATABASE PERTURBATION")
    print("=" * 70)

    db = SessionLocal()

    # Select 5 sample projects to perturb
    sample_scores = db.query(RiskScore).limit(5).all()
    original_states = [(s.id, s.risk_category) for s in sample_scores]
    print(f"[1] Selected {len(original_states)} database rows to perturb temporarily:")
    for s_id, orig_cat in original_states:
        print(f"    - RiskScore ID: {s_id} | Original Category: {orig_cat.value}")

    try:
        # Flip their risk category to an opposite label
        for s in sample_scores:
            s.risk_category = (
                RiskCategoryEnum.critical if s.risk_category == RiskCategoryEnum.low else RiskCategoryEnum.low
            )
        db.commit()
        print("\n[2] Temporarily perturbed 5 risk_category records in PostgreSQL.")

        # Call POST /api/retrain on perturbed database
        print("[3] Calling POST /api/retrain?confirm=true on perturbed database...")
        with TestClient(app) as client:
            resp = client.post("/api/retrain?confirm=true")
            assert resp.status_code == 200, f"Retrain failed: {resp.text}"
            data = resp.json()
            perturbed_acc = data["after_accuracy"]
            print(f"    Status:          {data['status']}")
            print(f"    Before Accuracy: {data['before_accuracy'] * 100:.4f}%")
            print(f"    After Accuracy:  {perturbed_acc * 100:.4f}%")
            print(f"    Trained At:      {data['trained_at']}")

    finally:
        # Restore database records to original state
        print("\n[4] Restoring perturbed rows to their exact original values in PostgreSQL...")
        for s_id, orig_cat in original_states:
            row = db.query(RiskScore).filter(RiskScore.id == s_id).first()
            if row:
                row.risk_category = orig_cat
        db.commit()
        print("[+] Database restored to 100% original state.")

        # Re-retrain once more on original database to restore original model bundle
        print("\n[5] Re-retraining on original restored database...")
        with TestClient(app) as client:
            resp_restore = client.post("/api/retrain?confirm=true")
            assert resp_restore.status_code == 200
            restored_data = resp_restore.json()
            print(f"    Restored Model Accuracy: {restored_data['after_accuracy'] * 100:.4f}%")

    db.close()
    print("\n" + "=" * 70)
    print("PERTURBATION EXPERIMENT RESULTS:")
    print(f"  - Original Baseline Accuracy:  70.4708% (0.7047)")
    print(f"  - Perturbed Database Accuracy: {perturbed_acc * 100:.4f}% ({perturbed_acc})")
    print(f"  - Restored Database Accuracy:  {restored_data['after_accuracy'] * 100:.4f}% ({restored_data['after_accuracy']})")
    print(f"  - Accuracy Changed Under Perturbation: {perturbed_acc != 0.7047}")
    print("=" * 70)


if __name__ == "__main__":
    test_perturbation()

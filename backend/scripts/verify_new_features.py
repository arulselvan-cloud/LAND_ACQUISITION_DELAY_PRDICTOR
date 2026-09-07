"""LandSight AI - Verification Suite for New Features:
1. Mock Notification Dispatch & De-duplication on repeated calls
2. GET /api/alerts/{alert_id}/notifications retrieval
3. POST /api/retrain endpoint with ?confirm=true guard & atomic in-memory reload
4. Side-by-side data retrieval for Showcase Trio (CBIC, BSRP, MAHSR)
"""

import os
import sys
from pathlib import Path

# Setup path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.alert import Alert
from backend.app.models.notification import NotificationLog
from backend.app.models.project import Project


def run_verification():
    print("=" * 70)
    print("LANDSIGHT AI - VERIFICATION OF NEW FEATURES (SIH26017)")
    print("=" * 70)

    db = SessionLocal()

    with TestClient(app) as client:
        # Find CBIC project
        cbic = db.query(Project).filter(Project.project_code == "CBIC-TN-PKG02").first()
        assert cbic is not None, "CBIC-TN-PKG02 project record not found in database."
        print(f"[+] Found Showcase Project: {cbic.project_code} (UUID: {cbic.id})")

        # Clean existing notifications for CBIC to start from a clean baseline test
        cbic_alert = db.query(Alert).filter(Alert.project_id == cbic.id).first()
        if cbic_alert:
            db.query(NotificationLog).filter(NotificationLog.alert_id == cbic_alert.id).delete()
            # Also reset alert so we test the full creation lifecycle
            db.delete(cbic_alert)
            db.commit()
            print("[+] Cleaned previous test alerts/notifications for CBIC-TN-PKG02 for clean test baseline.")

        # -------------------------------------------------------------
        # 1 & 3: CALL GENERATE-RECOMMENDATION 3 TIMES IN A ROW
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print("[TEST 1 & 3] Calling generate-recommendation on CBIC-TN-PKG02 3 times in a row...")
        print("-" * 70)

        for call_idx in range(1, 4):
            resp = client.post(f"/api/projects/{cbic.project_code}/generate-recommendation?simulate_failure=true")
            assert resp.status_code == 200, f"Call {call_idx} failed: {resp.text}"
            data = resp.json()
            print(f"  Call {call_idx}: status={resp.status_code}, risk={data['predicted_risk_category']}, "
                  f"alert_created={data['alert_created']}, notification_dispatched={data['notification_dispatched']}")

        # Verify alert and notification rows in DB
        db_alert = db.query(Alert).filter(Alert.project_id == cbic.id, Alert.resolved == False).first()
        assert db_alert is not None, "Alert was not created for CBIC-TN-PKG02!"

        notif_rows = db.query(NotificationLog).filter(NotificationLog.alert_id == db_alert.id).all()
        print(f"\n[+] Total notification_log rows for CBIC-TN-PKG02 alert ({db_alert.id}): {len(notif_rows)}")
        for n in notif_rows:
            print(f"    - ID: {n.id} | Channel: {n.channel} | Role: {n.recipient_role}")
            print(f"      Message: {n.message}")
            print(f"      Sent At: {n.sent_at}")

        assert len(notif_rows) == 1, f"Expected exactly 1 notification row after 3 calls, got {len(notif_rows)}!"
        print("  -> CHECK PASSED: Calling generate-recommendation 3 times created exactly 1 notification row (no duplicates)!")

        # -------------------------------------------------------------
        # 2: TEST GET /api/alerts/{alert_id}/notifications
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print("[TEST 2] Testing GET /api/alerts/{alert_id}/notifications...")
        print("-" * 70)

        # A: Query by alert UUID
        resp_by_uuid = client.get(f"/api/alerts/{db_alert.id}/notifications")
        assert resp_by_uuid.status_code == 200, f"Query by alert UUID failed: {resp_by_uuid.text}"
        notifs_by_uuid = resp_by_uuid.json()
        assert len(notifs_by_uuid) == 1
        print(f"  [+] Query by Alert UUID ({db_alert.id}): retrieved {len(notifs_by_uuid)} notification.")
        print(f"      channel={notifs_by_uuid[0]['channel']}, recipient={notifs_by_uuid[0]['recipient_role']}")
        print(f"      message=\"{notifs_by_uuid[0]['message']}\"")

        # B: Query by project code
        resp_by_code = client.get(f"/api/alerts/{cbic.project_code}/notifications")
        assert resp_by_code.status_code == 200, f"Query by project code failed: {resp_by_code.text}"
        notifs_by_code = resp_by_code.json()
        assert len(notifs_by_code) == 1
        print(f"  [+] Query by Project Code ({cbic.project_code}): retrieved {len(notifs_by_code)} notification.")

        # C: Query GET /api/alerts to verify AlertsFeed indicator fields
        resp_feed = client.get("/api/alerts?limit=100")
        assert resp_feed.status_code == 200
        feed_data = resp_feed.json()
        cbic_in_feed = next((a for a in feed_data["alerts"] if a["project_code"] == "CBIC-TN-PKG02"), None)
        assert cbic_in_feed is not None, "CBIC not found in /api/alerts feed."
        print(f"  [+] /api/alerts feed for CBIC: alert_id={cbic_in_feed.get('alert_id')}")
        print(f"      notification_preview=\"{cbic_in_feed.get('notification_preview')}\"")
        print(f"      notification_channel={cbic_in_feed.get('notification_channel')}")
        assert cbic_in_feed.get("notification_preview") is not None
        print("  -> CHECK PASSED: AlertsFeed notification preview properly delivered in /api/alerts!")

        # -------------------------------------------------------------
        # 4 & RETRAIN: TEST POST /api/retrain
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print("[TEST 4 & RETRAIN] Testing POST /api/retrain endpoint...")
        print("-" * 70)

        # A: Guard check without ?confirm=true
        resp_unconfirmed = client.post("/api/retrain")
        print(f"  A. Calling POST /api/retrain without confirm: status={resp_unconfirmed.status_code}")
        assert resp_unconfirmed.status_code == 400, f"Expected 400 for unconfirmed retrain, got {resp_unconfirmed.status_code}"
        print(f"     Detail: {resp_unconfirmed.json()['detail']}")
        print("     -> Guard works correctly!")

        # B: Authorized retrain with ?confirm=true
        print("  B. Calling POST /api/retrain?confirm=true...")
        resp_retrain = client.post("/api/retrain?confirm=true")
        assert resp_retrain.status_code == 200, f"Retrain failed: {resp_retrain.text}"
        retrain_data = resp_retrain.json()
        print(f"     Status:           {retrain_data['status']}")
        print(f"     Before Accuracy:  {retrain_data['before_accuracy'] * 100:.2f}%")
        print(f"     After Accuracy:   {retrain_data['after_accuracy'] * 100:.2f}%")
        print(f"     Trained At:       {retrain_data['trained_at']}")

        # C: Verify loaded models still perform inference and SHAP attribution after atomic reload
        resp_pred_post = client.post(f"/api/predict/{cbic.project_code}")
        assert resp_pred_post.status_code == 200
        print(f"  C. Post-retrain /predict check on CBIC: risk={resp_pred_post.json()['risk_category']}, "
              f"prob={resp_pred_post.json()['delay_probability']}")

        resp_exp_post = client.get(f"/api/projects/{cbic.project_code}/explain")
        assert resp_exp_post.status_code == 200
        exp_data = resp_exp_post.json()
        print(f"     Post-retrain /explain check: {len(exp_data['factors'])} SHAP factors computed cleanly.")
        print("     -> Retrain and atomic in-memory model reload verified!")

        # -------------------------------------------------------------
        # 5: TEST PROJECT COMPARISON VIEW DATA (CBIC, BSRP, MAHSR)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print("[TEST 5] Testing Project Comparison Data for Showcase Trio (CBIC, BSRP, MAHSR)...")
        print("-" * 70)

        showcase_codes = ["CBIC-TN-PKG02", "BSRP-KA-CORR04", "MAHSR-MH-PAL03"]
        comparison_results = {}

        for code in showcase_codes:
            pred = client.post(f"/api/predict/{code}").json()
            exp = client.get(f"/api/projects/{code}/explain").json()
            prop = client.get(f"/api/projects/{code}/propagation").json()
            cum_delay = sum(s.get("delay_days", 0) for s in prop)
            top_3 = exp.get("factors", [])[:3]

            comparison_results[code] = {
                "risk_category": pred["risk_category"],
                "delay_probability": pred["delay_probability"],
                "cumulative_delay_days": cum_delay,
                "top_3_shap": [f"{f['display_name']} ({f['direction']})" for f in top_3],
            }

            print(f"  Corridor: {code:<16} | Risk: {pred['risk_category'].upper():<8} | "
                  f"Prob: {pred['delay_probability'] * 100:.1f}% | Cum Delay: +{cum_delay}d")
            print(f"    Top SHAP: {comparison_results[code]['top_3_shap'][0]}")

        print("\n" + "=" * 70)
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    db.close()


if __name__ == "__main__":
    run_verification()

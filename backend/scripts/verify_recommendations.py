"""LandSight AI - AI Recommendations & Alerts Loop Verification Script.

Tests the recommendations loop across all 3 showcase projects (CBIC, MAHSR, BSRP),
validates Gemini 2.5 Flash memo generation, tests simulated failure fallback,
and checks alert feed recommendation snippet delivery.
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

def run_tests():
    with TestClient(app) as client:
        results = {}

        print("=================================================================")
        print("1. Testing CBIC-TN-PKG02 (Critical Risk) LLM Action Memo")
        print("=================================================================")
        r_cbic = client.post("/api/projects/CBIC-TN-PKG02/generate-recommendation")
        assert r_cbic.status_code == 200, f"CBIC failed: {r_cbic.text}"
        d_cbic = r_cbic.json()
        print(f"Status: {r_cbic.status_code}")
        print(f"Model: {d_cbic['model']}")
        print(f"Is LLM Generated: {d_cbic['is_llm_generated']}")
        print(f"Memo:\n{d_cbic['memo']}\n")
        print(f"Total Directives: {len(d_cbic['recommendations'])}")
        print(f"Alert Created: {d_cbic['alert_created']}")
        results["CBIC"] = d_cbic

        print("\n=================================================================")
        print("2. Testing MAHSR-MH-PAL03 (Critical Risk) LLM Action Memo")
        print("=================================================================")
        r_mahsr = client.post("/api/projects/MAHSR-MH-PAL03/generate-recommendation")
        assert r_mahsr.status_code == 200, f"MAHSR failed: {r_mahsr.text}"
        d_mahsr = r_mahsr.json()
        print(f"Status: {r_mahsr.status_code}")
        print(f"Model: {d_mahsr['model']}")
        print(f"Is LLM Generated: {d_mahsr['is_llm_generated']}")
        print(f"Memo:\n{d_mahsr['memo']}\n")
        print(f"Total Directives: {len(d_mahsr['recommendations'])}")
        print(f"Alert Created: {d_mahsr['alert_created']}")
        results["MAHSR"] = d_mahsr

        print("\n=================================================================")
        print("3. Testing BSRP-KA-CORR04 (Low Risk) Action Directives")
        print("=================================================================")
        r_bsrp = client.post("/api/projects/BSRP-KA-CORR04/generate-recommendation")
        assert r_bsrp.status_code == 200, f"BSRP failed: {r_bsrp.text}"
        d_bsrp = r_bsrp.json()
        print(f"Status: {r_bsrp.status_code}")
        print(f"Predicted Risk: {d_bsrp['predicted_risk_category']}")
        print(f"Model: {d_bsrp['model']}")
        print(f"Memo:\n{d_bsrp['memo']}\n")
        print(f"Alert Created (Must be False): {d_bsrp['alert_created']}")
        assert d_bsrp['alert_created'] is False, "Low risk project should NOT create a critical/high alert!"
        results["BSRP"] = d_bsrp

        print("\n=================================================================")
        print("4. Testing Simulated Failure Fallback Mechanism")
        print("=================================================================")
        r_fallback = client.post("/api/projects/CBIC-TN-PKG02/generate-recommendation?simulate_failure=true")
        assert r_fallback.status_code == 200, f"Fallback failed: {r_fallback.text}"
        d_fb = r_fallback.json()
        print(f"Status: {r_fallback.status_code}")
        print(f"Fallback Used: {d_fb['fallback_used']}")
        print(f"Is LLM Generated: {d_fb['is_llm_generated']}")
        print(f"Model: {d_fb['model']}")
        print(f"Fallback Memo:\n{d_fb['memo']}\n")
        assert d_fb['fallback_used'] is True
        assert d_fb['is_llm_generated'] is False
        results["FALLBACK"] = d_fb

        print("\n=================================================================")
        print("5. Testing Alerts Feed with Recommendation Snippet")
        print("=================================================================")
        r_alerts = client.get("/api/alerts?limit=5")
        assert r_alerts.status_code == 200, f"Alerts failed: {r_alerts.text}"
        alerts_data = r_alerts.json()
        print(f"Total High/Critical Alerts: {alerts_data['total_alerts']}")
        for a in alerts_data["alerts"][:3]:
            print(f"- Alert [{a['project_code']}]: {a['name']}")
            print(f"  Risk: {a['risk_category']} ({a['delay_probability']*100:.1f}%)")
            print(f"  Snippet: {a.get('recommendation_snippet')}")

        print("\n=================================================================")
        print("6. Testing GET /api/projects/{project_id}/recommendations")
        print("=================================================================")
        r_get_recs = client.get("/api/projects/CBIC-TN-PKG02/recommendations")
        assert r_get_recs.status_code == 200
        recs_list = r_get_recs.json()
        print(f"Total stored recommendations for CBIC: {recs_list['total_recommendations']}")
        for r in recs_list['recommendations'][:3]:
            print(f"  * [{r['priority'].upper()}] ({r['category']}): {r['action_text'][:80]}...")

        # Save results to json
        with open("backend/scripts/recommendations_verification_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n[PASS] All recommendation & alert tests PASSED and recorded in recommendations_verification_results.json")

if __name__ == "__main__":
    run_tests()

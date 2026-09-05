"""LandSight AI - Comprehensive Verification Suite for ML API Endpoints.

Validates all 7 endpoints, 4 initial refinements, and 2 consistency fixes:
- ISSUE 1: Real-time delay_probability matching across /predict, /projects, /alerts, and computed_at telemetry.
- ISSUE 2: Ambiguous field renaming to additional_expected_* and actual_delay_so_far_days in what-if.
"""

from datetime import datetime
import json
import sys
import time
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from backend.app.main import app

SHOWCASE_PROJECTS = [
    {"code": "CBIC-TN-PKG02", "uuid": "b7e129af-46b6-4a23-8626-5a8c0d3540ca", "name": "Chennai-Bengaluru Industrial Corridor"},
    {"code": "BSRP-KA-CORR04", "uuid": "3f857dce-8775-4cd2-b00a-84af2bb4d3dd", "name": "Bengaluru Suburban Rail Corridor 4"},
    {"code": "MAHSR-MH-PAL03", "uuid": "d4342972-891e-4786-96b6-6b9c51621d60", "name": "Mumbai-Ahmedabad High Speed Rail Palghar"},
]


def run_verification():
    print("=" * 80)
    print("LandSight AI - FastAPI ML Pipeline Comprehensive Verification Suite")
    print("=" * 80)

    cbic_responses = {}

    with TestClient(app) as client:
        # 1. Health & Startup Models Check
        print("\n[1] Verifying Lifespan Model Pre-loading & Health...")
        t0 = time.perf_counter()
        resp = client.get("/api/health")
        latency = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        health_data = resp.json()
        print(f"    Status: {health_data['status']} (Latency: {latency:.2f}ms)")
        print(f"    Loaded Models in app.state: {health_data['models_loaded']}")
        for model_name, is_loaded in health_data["models_loaded"].items():
            assert is_loaded is True, f"Model {model_name} failed to load in app.state!"

        # 2. CORS Verification
        print("\n[2] Verifying CORS Configuration for Vite Dev Server (localhost:5173)...")
        cors_headers = {"Origin": "http://localhost:5173"}
        resp = client.options("/api/projects", headers=cors_headers)
        allow_origin = resp.headers.get("access-control-allow-origin")
        print(f"    Access-Control-Allow-Origin: {allow_origin}")
        assert allow_origin == "http://localhost:5173", f"Expected CORS header not found: {resp.headers}"

        # 3. Test Predictions, Explain, Propagation, and What-If on Showcase Projects
        print("\n[3] Testing ML Endpoints across Showcase Projects...")
        predicted_probs = {}

        for proj in SHOWCASE_PROJECTS:
            code = proj["code"]
            p_uuid = proj["uuid"]
            print(f"\n--- Testing Project: [{code}] ({proj['name']}) ---")

            # A. POST /api/predict/{project_id} (test with code)
            t0 = time.perf_counter()
            resp = client.post(f"/api/predict/{code}")
            lat_predict = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Predict failed for {code}: {resp.text}"
            pred_data = resp.json()
            predicted_probs[code] = pred_data["delay_probability"]
            print(f"    [POST /api/predict/{code}]:")
            print(f"      Risk Category: {pred_data['risk_category']} | Delay Prob: {pred_data['delay_probability']:.4f} | Conf: {pred_data['confidence_score']:.4f} ({lat_predict:.2f}ms)")

            # Also test predict by UUID
            resp_uuid = client.post(f"/api/predict/{p_uuid}")
            assert resp_uuid.status_code == 200, f"Predict by UUID failed: {resp_uuid.text}"

            if code == "CBIC-TN-PKG02":
                cbic_responses["POST /api/predict/{project_id}"] = pred_data

            # B. GET /api/projects/{project_id}/explain
            t0 = time.perf_counter()
            resp = client.get(f"/api/projects/{code}/explain")
            lat_explain = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Explain failed for {code}: {resp.text}"
            explain_data = resp.json()
            print(f"    [GET /api/projects/{code}/explain]:")
            print(f"      Top 5 SHAP factors ({lat_explain:.2f}ms):")
            for idx, factor in enumerate(explain_data["factors"][:3], 1):
                print(f"        {idx}. {factor['display_name']} ({factor['feature']}): {factor['magnitude']} ({factor['direction']})")

            # Also test explain by UUID
            resp_uuid = client.get(f"/api/projects/{p_uuid}/explain")
            assert resp_uuid.status_code == 200

            if code == "CBIC-TN-PKG02":
                cbic_responses["GET /api/projects/{project_id}/explain"] = explain_data

            # C. GET /api/projects/{project_id}/propagation
            t0 = time.perf_counter()
            resp = client.get(f"/api/projects/{code}/propagation")
            lat_prop = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Propagation failed for {code}: {resp.text}"
            prop_data = resp.json()
            print(f"    [GET /api/projects/{code}/propagation]:")
            print(f"      5-Stage Impact Map ({lat_prop:.2f}ms):")
            total_delay = 0
            for stage in prop_data:
                mode = "PREDICTED" if stage["is_predicted"] else "ACTUAL"
                total_delay += stage["delay_days"]
                print(f"        Stage {stage['stage_order']} {stage['stage_name']:<14}: {stage['delay_days']:>3}d ({stage['status']}) [{mode}]")
            print(f"      Cumulative Delay: {total_delay} days")

            # Also test propagation by UUID
            resp_uuid = client.get(f"/api/projects/{p_uuid}/propagation")
            assert resp_uuid.status_code == 200

            if code == "CBIC-TN-PKG02":
                cbic_responses["GET /api/projects/{project_id}/propagation"] = prop_data

            # D. POST /api/projects/{project_id}/what-if (ISSUE 2 Verification)
            what_if_payload = {
                "compensation_disbursed_pct": 98.0,
                "has_active_legal_dispute": 0,
                "dispute_delay_impact_days": 0,
                "avg_stakeholder_responsiveness": 92.0,
            }
            t0 = time.perf_counter()
            resp = client.post(f"/api/projects/{code}/what-if", json=what_if_payload)
            lat_whatif = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"What-if failed for {code}: {resp.text}"
            whatif_data = resp.json()
            print(f"    [POST /api/projects/{code}/what-if]:")
            print(f"      Actual Delay So Far:        {whatif_data['baseline']['actual_delay_so_far_days']} days")
            print(f"      Baseline Additional Delay:  {whatif_data['baseline']['stage_breakdown']}")
            print(f"      Counterfactual Add Delay:   {whatif_data['counterfactual']['stage_breakdown']}")
            print(f"      Impact Summary:             {whatif_data['impact']['summary']} ({lat_whatif:.2f}ms)")

            # ISSUE 2 Assertions: Check renamed fields and actual_delay_so_far_days
            assert "actual_delay_so_far_days" in whatif_data["baseline"]
            assert "additional_expected_compensation_delay_days" in whatif_data["baseline"]["stage_breakdown"]
            assert "additional_expected_possession_delay_days" in whatif_data["baseline"]["stage_breakdown"]
            assert "additional_expected_compensation_delay_days" in whatif_data["counterfactual"]["stage_breakdown"]
            assert "additional_expected_possession_delay_days" in whatif_data["counterfactual"]["stage_breakdown"]

            if code == "CBIC-TN-PKG02":
                cbic_responses["POST /api/projects/{project_id}/what-if"] = whatif_data
                assert whatif_data["baseline"]["actual_delay_so_far_days"] == 165
                drop = whatif_data["impact"]["delay_probability_reduction"]
                print(f"      >>> Verified CBIC probability drop: {drop*100:.1f}%")
                assert drop >= 0.90, f"Expected ~96% drop, got {drop}"

        # 4. Refinement 1: Explicit 404 Handling
        print("\n[4] Verifying Refinement 1: Explicit 404 on Non-Existent Project Identifiers...")
        non_existent_id = "NON-EXISTENT-XYZ999"
        for endpoint, method in [
            (f"/api/predict/{non_existent_id}", client.post),
            (f"/api/projects/{non_existent_id}/explain", client.get),
            (f"/api/projects/{non_existent_id}/propagation", client.get),
            (f"/api/projects/{non_existent_id}/what-if", lambda url: client.post(url, json={"has_active_legal_dispute": 0})),
        ]:
            r_404 = method(endpoint)
            assert r_404.status_code == 404, f"Expected 404, got {r_404.status_code}"
            print(f"    {endpoint} -> 404: {r_404.json()['detail']}")

        # 5. Refinement 2: Pydantic Field Validation (422 Unprocessable Entity)
        print("\n[5] Verifying Refinement 2: What-If Field Validation (422 Errors)...")
        invalid_body_pct = {"compensation_disbursed_pct": 150.0}
        resp = client.post("/api/projects/CBIC-TN-PKG02/what-if", json=invalid_body_pct)
        assert resp.status_code == 422, f"Expected 422 on pct > 100, got {resp.status_code}"
        print(f"    compensation_disbursed_pct=150.0 -> 422: {resp.json()['detail'][0]['msg']}")

        invalid_dispute = {"has_active_legal_dispute": 2}
        resp = client.post("/api/projects/CBIC-TN-PKG02/what-if", json=invalid_dispute)
        assert resp.status_code == 422, f"Expected 422 on dispute > 1, got {resp.status_code}"
        print(f"    has_active_legal_dispute=2 -> 422: {resp.json()['detail'][0]['msg']}")

        invalid_days = {"dispute_delay_impact_days": -10}
        resp = client.post("/api/projects/CBIC-TN-PKG02/what-if", json=invalid_days)
        assert resp.status_code == 422, f"Expected 422 on negative delay days, got {resp.status_code}"
        print(f"    dispute_delay_impact_days=-10 -> 422: {resp.json()['detail'][0]['msg']}")

        # 6. Refinement 3 & ISSUE 1: GET /api/projects Pagination, Latency & Live Risk Score
        print("\n[6] Verifying Refinement 3 & ISSUE 1: GET /api/projects Pagination & Live Prediction Latency...")
        t0 = time.perf_counter()
        resp = client.get("/api/projects?page_size=20")
        lat_page_20 = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"List projects failed: {resp.text}"
        proj_list = resp.json()
        print(f"    >>> Measured Live-Computation Latency for full page of 20 projects: {lat_page_20:.2f} ms")
        print(f"    Default Pagination: Total={proj_list['total']}, Page={proj_list['page']}, PageSize={proj_list['page_size']}, Returned Items={len(proj_list['projects'])}")
        assert proj_list["page_size"] == 20 and len(proj_list["projects"]) == 20
        assert "computed_at" in proj_list["projects"][0]

        # Hard max violation: page_size=101
        resp_max = client.get("/api/projects?page_size=101")
        assert resp_max.status_code == 422, f"Expected 422 on page_size > 100, got {resp_max.status_code}"
        print(f"    PageSize=101 -> 422 Error: {resp_max.json()['detail'][0]['msg']}")

        # Single project details for CBIC (ISSUE 1 check)
        resp_cbic_detail = client.get("/api/projects/CBIC-TN-PKG02")
        assert resp_cbic_detail.status_code == 200
        cbic_detail = resp_cbic_detail.json()
        cbic_responses["GET /api/projects/{project_id}"] = cbic_detail
        print(f"\n    [GET /api/projects/CBIC-TN-PKG02]:")
        print(f"      Risk Category:    {cbic_detail['risk_category']}")
        print(f"      Delay Probability: {cbic_detail['delay_probability']:.4f}")
        print(f"      Computed At:      {cbic_detail['computed_at']}")
        assert cbic_detail["delay_probability"] == predicted_probs["CBIC-TN-PKG02"], (
            f"Expected {predicted_probs['CBIC-TN-PKG02']}, got {cbic_detail['delay_probability']}"
        )

        # Find CBIC in projects list
        resp_filter = client.get("/api/projects?state=Tamil%20Nadu&risk_category=critical&page_size=100")
        assert resp_filter.status_code == 200
        filt_data = resp_filter.json()
        cbic_in_list = next((p for p in filt_data["projects"] if p["project_code"] == "CBIC-TN-PKG02"), None)
        assert cbic_in_list is not None, "CBIC-TN-PKG02 must be found in Tamil Nadu critical projects!"
        cbic_responses["GET /api/projects (Item in list)"] = cbic_in_list
        print(f"\n    [GET /api/projects - CBIC Item]:")
        print(f"      Risk Category:    {cbic_in_list['risk_category']}")
        print(f"      Delay Probability: {cbic_in_list['delay_probability']:.4f}")
        print(f"      Computed At:      {cbic_in_list['computed_at']}")
        assert cbic_in_list["delay_probability"] == predicted_probs["CBIC-TN-PKG02"], (
            f"Expected {predicted_probs['CBIC-TN-PKG02']}, got {cbic_in_list['delay_probability']}"
        )

        # 7. GET /api/districts/summary (Heatmap)
        print("\n[7] Verifying GET /api/districts/summary (Heatmap Analytics)...")
        t0 = time.perf_counter()
        resp = client.get("/api/districts/summary")
        lat_dist = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"Districts summary failed: {resp.text}"
        dist_data = resp.json()
        print(f"    Total Districts aggregated: {len(dist_data)} ({lat_dist:.2f}ms)")
        cbic_responses["GET /api/districts/summary (Ranipet)"] = next(d for d in dist_data if d["district"].lower() == "ranipet")

        # 8. GET /api/alerts (High / Critical Alerts sorted desc with live probabilities)
        print("\n[8] Verifying GET /api/alerts (Early Warnings with Live Scoring)...")
        t0 = time.perf_counter()
        resp = client.get("/api/alerts?limit=50")
        lat_alerts = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"Alerts failed: {resp.text}"
        alerts_data = resp.json()
        print(f"    Total Critical/High Risk Projects in DB: {alerts_data['total_alerts']} ({lat_alerts:.2f}ms)")
        print(f"    Top 3 Priority Delay Alerts:")
        for a in alerts_data["alerts"][:3]:
            print(f"      [{a['project_code']}] {a['name'][:40]}...: {a['risk_category'].upper()} ({a['delay_probability']:.4f}) [computed_at: {a['computed_at']}]")

        # Verify CBIC in alerts
        resp_cbic_alert = client.get("/api/alerts?limit=500")
        cbic_alert = next((a for a in resp_cbic_alert.json()["alerts"] if a["project_code"] == "CBIC-TN-PKG02"), None)
        assert cbic_alert is not None, "CBIC-TN-PKG02 should be in alerts!"
        cbic_responses["GET /api/alerts (Alert for CBIC)"] = cbic_alert
        print(f"\n    [GET /api/alerts - CBIC Entry]:")
        print(f"      Risk Category:    {cbic_alert['risk_category']}")
        print(f"      Delay Probability: {cbic_alert['delay_probability']:.4f}")
        print(f"      Computed At:      {cbic_alert['computed_at']}")
        assert cbic_alert["delay_probability"] == predicted_probs["CBIC-TN-PKG02"], (
            f"Expected {predicted_probs['CBIC-TN-PKG02']}, got {cbic_alert['delay_probability']}"
        )

    print("\n" + "=" * 80)
    print("ALL TESTS & CONSISTENCY CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)

    # Save CBIC responses to artifact / json for user reporting
    output_file = Path("backend/scripts/verification_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cbic_responses, f, indent=2, default=str)
    print(f"\n[+] Saved updated verification responses to {output_file}")


if __name__ == "__main__":
    run_verification()

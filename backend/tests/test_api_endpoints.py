"""LandSight AI - Phase 8 Automated Integration Test Suite.

Validates core API endpoints against real showcase projects, regression constraints,
error handling (404/422), SHAP structure, and ground truth distribution.
"""

import pytest
from fastapi.testclient import TestClient


def test_showcase_projects_risk_prediction(client: TestClient):
    """Verifies that all 3 real showcase projects return expected risk categories from /api/predict."""
    expected_categories = {
        "CBIC-TN-PKG02": "critical",
        "BSRP-KA-CORR04": "low",
        "MAHSR-MH-PAL03": "critical",
    }

    for project_code, expected_cat in expected_categories.items():
        resp = client.post(f"/api/predict/{project_code}")
        assert resp.status_code == 200, f"Predict failed for {project_code}: {resp.text}"
        data = resp.json()
        assert data["risk_category"] == expected_cat, (
            f"Expected {expected_cat} for {project_code}, got {data['risk_category']}"
        )
        assert 0.0 <= data["delay_probability"] <= 1.0
        assert 0.0 <= data["confidence_score"] <= 1.0


def test_nonexistent_project_404_handling(client: TestClient):
    """Verifies 404 handling across all primary endpoints when given a nonexistent project ID."""
    invalid_id = "NONEXISTENT-PROJECT-99999"

    # 1. /predict
    resp_pred = client.post(f"/api/predict/{invalid_id}")
    assert resp_pred.status_code == 404
    assert "not found" in resp_pred.json()["detail"].lower()

    # 2. /explain
    resp_exp = client.get(f"/api/projects/{invalid_id}/explain")
    assert resp_exp.status_code == 404
    assert "not found" in resp_exp.json()["detail"].lower()

    # 3. /propagation
    resp_prop = client.get(f"/api/projects/{invalid_id}/propagation")
    assert resp_prop.status_code == 404
    assert "not found" in resp_prop.json()["detail"].lower()

    # 4. /what-if
    resp_wi = client.post(
        f"/api/projects/{invalid_id}/what-if",
        json={"compensation_disbursed_pct": 80.0},
    )
    assert resp_wi.status_code == 404
    assert "not found" in resp_wi.json()["detail"].lower()


def test_what_if_validation_422(client: TestClient):
    """Verifies 422 Unprocessable Entity for invalid or out-of-range what-if inputs."""
    # Out-of-range percentage (> 100%)
    resp_pct = client.post(
        "/api/projects/CBIC-TN-PKG02/what-if",
        json={"compensation_disbursed_pct": 150.0},
    )
    assert resp_pct.status_code == 422

    # Negative PAF count (< 0)
    resp_neg = client.post(
        "/api/projects/CBIC-TN-PKG02/what-if",
        json={"affected_families_count": -10},
    )
    assert resp_neg.status_code == 422

    # Out-of-range binary flag (not 0 or 1)
    resp_bin = client.post(
        "/api/projects/CBIC-TN-PKG02/what-if",
        json={"has_active_legal_dispute": 5},
    )
    assert resp_bin.status_code == 422

    # Empty body with no intervention modifications
    resp_empty = client.post(
        "/api/projects/CBIC-TN-PKG02/what-if",
        json={},
    )
    assert resp_empty.status_code == 422


def test_shap_explain_structure(client: TestClient):
    """Verifies SHAP explain endpoint returns exactly 5 factors with valid direction and magnitude."""
    resp = client.get("/api/projects/CBIC-TN-PKG02/explain")
    assert resp.status_code == 200, f"Explain failed: {resp.text}"
    data = resp.json()

    assert "factors" in data
    factors = data["factors"]
    assert len(factors) == 5, f"Expected exactly 5 top SHAP factors, got {len(factors)}"

    for factor in factors:
        assert factor["direction"] in ["increases_risk", "decreases_risk"]
        assert factor["magnitude"] >= 0.0
        assert isinstance(factor["shap_value"], (int, float))
        assert factor["display_name"]
        assert factor["feature"]


def test_what_if_response_field_naming(client: TestClient):
    """Verifies what-if response includes actual_delay_so_far_days and unambiguous delay fields."""
    payload = {
        "compensation_disbursed_pct": 95.0,
        "has_active_legal_dispute": 0,
        "avg_stakeholder_responsiveness": 90.0,
    }
    resp = client.post("/api/projects/CBIC-TN-PKG02/what-if", json=payload)
    assert resp.status_code == 200, f"What-if failed: {resp.text}"
    data = resp.json()

    # 1. Check actual delay so far on baseline
    assert "baseline" in data
    baseline = data["baseline"]
    assert "actual_delay_so_far_days" in baseline
    assert isinstance(baseline["actual_delay_so_far_days"], (int, float))
    assert baseline["actual_delay_so_far_days"] >= 0

    # 2. Check unambiguous field names in baseline stage breakdown
    base_breakdown = baseline.get("stage_breakdown", {})
    assert "additional_expected_compensation_delay_days" in base_breakdown
    assert "additional_expected_possession_delay_days" in base_breakdown
    # Verify legacy ambiguous name is NOT present
    assert "compensation_delay_days" not in base_breakdown
    assert "possession_delay_days" not in base_breakdown

    # 3. Check unambiguous field names in counterfactual stage breakdown
    assert "counterfactual" in data
    counterfactual = data["counterfactual"]
    cf_breakdown = counterfactual.get("stage_breakdown", {})
    assert "additional_expected_compensation_delay_days" in cf_breakdown
    assert "additional_expected_possession_delay_days" in cf_breakdown
    assert "compensation_delay_days" not in cf_breakdown
    assert "possession_delay_days" not in cf_breakdown

    # 4. Check impact summary
    assert "impact" in data
    assert "risk_tier_change" in data["impact"]
    assert "estimated_delay_days_saved" in data["impact"]


def test_summary_ground_truth_totals(client: TestClient):
    """Verifies /api/summary returns calibrated ground truth totals (1225/1050/700/525 + 3 real projects)."""
    resp = client.get("/api/summary")
    assert resp.status_code == 200, f"Summary failed: {resp.text}"
    data = resp.json()

    assert data["total_projects"] == 3503

    breakdown = data["risk_breakdown"]
    # 1225 synthetic + 1 BSRP = 1226 Low
    assert breakdown["Low"] == 1226, f"Expected 1226 Low, got {breakdown['Low']}"
    # 1050 synthetic = 1050 Medium
    assert breakdown["Medium"] == 1050, f"Expected 1050 Medium, got {breakdown['Medium']}"
    # 700 synthetic = 700 High
    assert breakdown["High"] == 700, f"Expected 700 High, got {breakdown['High']}"
    # 525 synthetic + 2 real (CBIC, MAHSR) = 527 Critical
    assert breakdown["Critical"] == 527, f"Expected 527 Critical, got {breakdown['Critical']}"

    # Verify matching top-level count fields
    assert data["low_risk_count"] == 1226
    assert data["medium_risk_count"] == 1050
    assert data["high_risk_count"] == 700
    assert data["critical_risk_count"] == 527
    assert data["high_critical_count"] == 700 + 527


def test_what_if_dispute_safety_net(client: TestClient):
    """Verifies that setting has_active_legal_dispute=0 without dispute_delay_impact_days
    safely defaults dispute_delay_impact_days to 0 rather than preserving baseline's 90 days.
    """
    payload_3field = {
        "compensation_disbursed_pct": 98.0,
        "has_active_legal_dispute": 0,
        "avg_stakeholder_responsiveness": 92.0,
    }
    resp = client.post("/api/projects/CBIC-TN-PKG02/what-if", json=payload_3field)
    assert resp.status_code == 200, f"What-if failed: {resp.text}"
    data = resp.json()

    # Counterfactual should drop cleanly from CRITICAL to LOW
    assert data["counterfactual"]["risk_category"] == "low"
    assert data["counterfactual"]["delay_probability"] < 0.05
    assert data["counterfactual"]["expected_delay_days"] == 0
    assert data["impact"]["risk_tier_change"] == "CRITICAL -> LOW"
    assert data["impact"]["estimated_delay_days_saved"] >= 100


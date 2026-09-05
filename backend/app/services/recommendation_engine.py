"""LandSight AI - Rule-Based Administrative Recommendation Engine.

Maps model explainability drivers (SHAP factors) to standardized administrative action templates
and priority ratings for infrastructure land acquisition authorities.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.models.enums import PriorityEnum
from ml.explain import ModelExplainer


def map_shap_to_priority(magnitude: float) -> PriorityEnum:
    """Maps absolute SHAP attribution magnitude to standard priority tier."""
    if magnitude >= 1.0:
        return PriorityEnum.urgent
    elif magnitude >= 0.5:
        return PriorityEnum.high
    elif magnitude >= 0.2:
        return PriorityEnum.medium
    else:
        return PriorityEnum.low


# Standard Administrative Action Templates for Land Acquisition Bottlenecks
TEMPLATE_CATALOG = {
    "legal_dispute": {
        "category": "Legal & Litigation",
        "action_text": "Coordinate with Legal Cell to expedite resolution of active stay order / litigation",
        "expected_impact": "Vacate judicial stay order or file urgency memo to unblock statutory land vesting",
    },
    "compensation": {
        "category": "Treasury & Disbursement",
        "action_text": "Escalate pending compensation disbursement with District Treasury / SLAO",
        "expected_impact": "Accelerate direct benefit transfer (DBT) to landowners to satisfy Section 30 requirements",
    },
    "stakeholder": {
        "category": "Inter-Agency Coordination",
        "action_text": "Schedule direct coordination meeting with low-responsiveness stakeholders",
        "expected_impact": "Resolve inter-departmental NOCs and joint field inspection clearances within 14 days",
    },
    "rehabilitation": {
        "category": "Resettlement & Rehabilitation",
        "action_text": "Accelerate R&R scheme implementation, review housing/land allotment bottlenecks",
        "expected_impact": "Clear Section 31 R&R entitlements to facilitate peaceful physical possession",
    },
    "survey_land": {
        "category": "Land Administration & Survey",
        "action_text": "Deploy additional revenue surveyor teams and DGPS/drone survey units for parcel demarcation",
        "expected_impact": "Complete Cadastral boundary demarcation and joint measurement survey (JMS)",
    },
    "paf_engagement": {
        "category": "Public Engagement & Solatium",
        "action_text": "Convene Special Gram Sabha and localized grievance redressal camps for Project Affected Families",
        "expected_impact": "Address community compensation grievances and minimize risk of Section 15 objections",
    },
    "routine_monitoring": {
        "category": "Milestone Supervision",
        "action_text": "Maintain statutory milestone cadence and continue scheduled weekly inter-departmental reviews",
        "expected_impact": "Sustain on-track project trajectory across remaining acquisition phases",
    },
}


def get_rule_based_recommendations(
    project_id: str,
    explanation: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
    bundle: Optional[Dict[str, Any]] = None,
    explainer: Optional[ModelExplainer] = None,
) -> List[Dict[str, Any]]:
    """Evaluates project SHAP feature attributions and produces top 2-3 prioritized administrative actions.

    Args:
        project_id: Project UUID or project_code.
        explanation: Optional precomputed explanation dictionary from ModelExplainer.
        session: Active SQLAlchemy database session.
        bundle: Preloaded classifier bundle from app.state.
        explainer: Pre-initialized ModelExplainer instance.

    Returns:
        List of 2-3 recommendation dictionaries with action_text, priority, category, and expected_impact.
    """
    if explanation is None:
        if explainer is None:
            explainer = ModelExplainer(bundle=bundle)
        explanation = explainer.explain_prediction(project_id, session=session)

    pred_cat = explanation.get("predicted_risk_category", "medium")
    drivers = explanation.get("top_drivers", [])
    all_drivers = {d["feature"]: d for d in explanation.get("all_drivers", drivers)}

    recommendations: List[Dict[str, Any]] = []
    seen_categories = set()

    # Helper to add recommendation without duplicates
    def add_rec(template_key: str, feature_key: str, custom_text: Optional[str] = None, custom_impact: Optional[str] = None):
        tpl = TEMPLATE_CATALOG[template_key]
        if tpl["category"] in seen_categories:
            return
        
        driver_info = all_drivers.get(feature_key, {})
        mag = float(driver_info.get("magnitude", 0.3))
        val = driver_info.get("value")
        priority = map_shap_to_priority(mag)

        action = custom_text or tpl["action_text"]
        impact = custom_impact or tpl["expected_impact"]

        # Contextualize text with concrete project numbers where appropriate
        if template_key == "legal_dispute" and val:
            if feature_key == "dispute_delay_impact_days" and val > 0:
                impact = f"Vacate active stay order to avert up to {int(val)} days of projected judicial delay"
        elif template_key == "compensation" and val is not None:
            if float(val) < 80.0:
                action = f"Escalate pending compensation disbursement (currently at {val:.1f}%) with District Treasury / SLAO"
        elif template_key == "rehabilitation" and val is not None:
            if float(val) < 80.0:
                action = f"Accelerate R&R scheme implementation (currently at {val:.1f}%), review housing/land allotment bottlenecks"
        elif template_key == "stakeholder" and val is not None:
            action = f"Schedule direct coordination meeting with low-responsiveness stakeholders (index: {val:.1f}/100)"

        recommendations.append({
            "feature": feature_key,
            "priority": priority,
            "priority_str": priority.value,
            "category": tpl["category"],
            "action_text": action,
            "expected_impact": impact,
            "shap_value": float(driver_info.get("shap_value", 0.0)),
            "magnitude": mag,
        })
        seen_categories.add(tpl["category"])

    # High / Critical risk projects: prioritize features causing delay (positive SHAP attributions only)
    if pred_cat in ["high", "critical"]:
        for d in drivers:
            # Strictly skip factors that decrease risk (negative SHAP)
            if float(d.get("shap_value", 0.0)) <= 0:
                continue

            feat = d["feature"]
            val = d.get("value")
            
            if feat in ("has_active_legal_dispute", "dispute_delay_impact_days") and (val and val > 0):
                add_rec("legal_dispute", feat)
            elif feat == "compensation_disbursed_pct" and (val is None or float(val) < 85.0):
                add_rec("compensation", feat)
            elif feat == "avg_stakeholder_responsiveness" and (val is None or float(val) < 80.0):
                add_rec("stakeholder", feat)
            elif feat == "rehabilitation_completion_pct" and (val is None or float(val) < 85.0):
                add_rec("rehabilitation", feat)
            elif feat == "land_area_hectares" and (val and float(val) > 100.0):
                add_rec("survey_land", feat)
            elif feat == "affected_families_count" and (val and float(val) > 150):
                add_rec("paf_engagement", feat)

            if len(recommendations) >= 3:
                break

    # If low/medium risk or drivers did not match sufficient categories, inspect all features
    if len(recommendations) < 2:
        # Check if active dispute exists anywhere
        disp_drv = all_drivers.get("has_active_legal_dispute", {})
        if disp_drv.get("value", 0) == 1:
            add_rec("legal_dispute", "has_active_legal_dispute")

        # Check compensation
        comp_drv = all_drivers.get("compensation_disbursed_pct", {})
        comp_val = comp_drv.get("value")
        if comp_val is not None and float(comp_val) < 90.0:
            add_rec("compensation", "compensation_disbursed_pct")

        # Check R&R
        rr_drv = all_drivers.get("rehabilitation_completion_pct", {})
        rr_val = rr_drv.get("value")
        if rr_val is not None and float(rr_val) < 90.0:
            add_rec("rehabilitation", "rehabilitation_completion_pct")

        # Check stakeholder responsiveness
        stk_drv = all_drivers.get("avg_stakeholder_responsiveness", {})
        stk_val = stk_drv.get("value")
        if stk_val is not None and float(stk_val) < 80.0:
            add_rec("stakeholder", "avg_stakeholder_responsiveness")

    # If project is low risk and on track with no major bottlenecks, provide positive governance directives
    if len(recommendations) < 2:
        if pred_cat == "low":
            add_rec(
                "routine_monitoring",
                "avg_stakeholder_responsiveness",
                custom_text="Maintain scheduled milestone cadence and sustain proactive stakeholder engagement",
                custom_impact="Maintain positive acquisition momentum toward timely physical land possession",
            )
            add_rec(
                "compensation",
                "compensation_disbursed_pct",
                custom_text="Continue scheduled compensation disbursements to maintain high clearance rates",
                custom_impact="Prevent payment backlogs and maintain landholder satisfaction",
            )
        else:
            add_rec("compensation", "compensation_disbursed_pct")
            add_rec("stakeholder", "avg_stakeholder_responsiveness")

    # Sort descending by priority / magnitude
    priority_order = {
        PriorityEnum.urgent: 0,
        PriorityEnum.high: 1,
        PriorityEnum.medium: 2,
        PriorityEnum.low: 3,
    }
    recommendations.sort(key=lambda r: (priority_order[r["priority"]], -r["magnitude"]))

    # Return top 2-3 recommendations
    return recommendations[:3]

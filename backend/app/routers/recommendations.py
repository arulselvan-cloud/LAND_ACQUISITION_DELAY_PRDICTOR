"""LandSight AI - AI Recommendations & Executive Action Plan Router.

Provides endpoints to trigger real-time AI recommendation synthesis using Gemini 2.5 Flash
grounded in SHAP explainability drivers, persist action directives and alerts, and retrieve stored recommendations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.alert import Alert
from backend.app.models.enums import AlertSeverityEnum, PriorityEnum
from backend.app.models.recommendation import Recommendation
from backend.app.models.risk import RiskScore
from backend.app.services.llm_recommendations import generate_action_memo
from backend.app.services.project_lookup import get_project_or_404
from backend.app.services.recommendation_engine import get_rule_based_recommendations
from ml.explain import ModelExplainer

router = APIRouter()


class RecommendationItem(BaseModel):
    id: str
    action_text: str
    priority: str
    category: Optional[str] = None
    expected_impact: Optional[str] = None
    is_implemented: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GenerateRecommendationResponse(BaseModel):
    project_id: str
    project_code: str
    name: str
    predicted_risk_category: str
    delay_probability: float
    memo: str
    is_llm_generated: bool
    fallback_used: bool
    model: str
    recommendations: List[RecommendationItem]
    alert_created: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectRecommendationsListResponse(BaseModel):
    project_id: str
    project_code: str
    total_recommendations: int
    recommendations: List[RecommendationItem]

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/projects/{project_id}/generate-recommendation",
    response_model=GenerateRecommendationResponse,
    tags=["AI Recommendations & Alerts"],
)
def generate_project_recommendation(
    project_id: str,
    request: Request,
    simulate_failure: bool = Query(
        False,
        description="Simulate LLM failure to exercise deterministic fallback path",
    ),
    db: Session = Depends(get_db),
):
    """Generates an executive administrative action memo and detailed statutory directives.

    Uses Gemini 2.5 Flash grounded in SHAP explainability. Automatically persists recommendations
    to the database and triggers an early warning alert if project is High or Critical risk.
    """
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    # 1. Obtain explanation
    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    tree_explainer = getattr(request.app.state, "tree_explainer", None)
    explainer = ModelExplainer(bundle=classifier_bundle, explainer=tree_explainer)
    explanation = explainer.explain_prediction(canonical_id, session=db)

    pred_cat = explanation.get("predicted_risk_category", "medium")
    probs = explanation.get("prediction_probabilities", {})
    delay_prob = round(float(probs.get("high", 0.0) + probs.get("critical", 0.0)), 4)

    # 2. Rule-based recommendations
    rule_recs = get_rule_based_recommendations(
        canonical_id, explanation=explanation, session=db, explainer=explainer
    )

    # 3. Generate LLM memo (with fallback)
    memo_result = generate_action_memo(
        proj, explanation, rule_recs, simulate_failure=simulate_failure
    )

    # 4. Find latest risk score
    latest_risk = (
        db.query(RiskScore)
        .filter(RiskScore.project_id == proj.id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )

    # 5. Persist Executive Directive Memo
    memo_priority = (
        PriorityEnum.urgent
        if pred_cat == "critical"
        else (PriorityEnum.high if pred_cat == "high" else PriorityEnum.medium)
    )

    exec_rec = Recommendation(
        project_id=proj.id,
        risk_score_id=latest_risk.id if latest_risk else None,
        action_text=memo_result["memo"],
        priority=memo_priority,
        category="Executive Directive",
        expected_impact="Mitigate statutory milestone delays and unblock inter-agency execution under RFCTLARR 2013",
        is_implemented=False,
        data_source=proj.data_source,
    )
    db.add(exec_rec)
    db.flush()

    # 6. Persist Rule-Based Directives if not already present
    persisted_recs = [exec_rec]
    for r in rule_recs:
        existing = (
            db.query(Recommendation)
            .filter(
                Recommendation.project_id == proj.id,
                Recommendation.action_text == r["action_text"],
            )
            .first()
        )
        if not existing:
            sub_rec = Recommendation(
                project_id=proj.id,
                risk_score_id=latest_risk.id if latest_risk else None,
                action_text=r["action_text"],
                priority=r["priority"],
                category=r["category"],
                expected_impact=r["expected_impact"],
                is_implemented=False,
                data_source=proj.data_source,
            )
            db.add(sub_rec)
            persisted_recs.append(sub_rec)
        else:
            persisted_recs.append(existing)

    # 7. Automatic Alert Trigger for High / Critical Risk Projects
    alert_created = False
    if pred_cat in ["high", "critical"]:
        existing_alert = (
            db.query(Alert)
            .filter(Alert.project_id == proj.id, Alert.resolved == False)
            .first()
        )
        if not existing_alert:
            new_alert = Alert(
                project_id=proj.id,
                title=f"{proj.project_code}: Priority Delay Bottleneck Alert",
                message=memo_result["memo"][:240] + "...",
                severity=(
                    AlertSeverityEnum.critical
                    if pred_cat == "critical"
                    else AlertSeverityEnum.high
                ),
                resolved=False,
                data_source=proj.data_source,
            )
            db.add(new_alert)
            alert_created = True

    db.commit()

    return GenerateRecommendationResponse(
        project_id=canonical_id,
        project_code=proj.project_code,
        name=proj.name,
        predicted_risk_category=pred_cat,
        delay_probability=delay_prob,
        memo=memo_result["memo"],
        is_llm_generated=memo_result["is_llm_generated"],
        fallback_used=memo_result["fallback_used"],
        model=memo_result["model"],
        recommendations=[
            RecommendationItem(
                id=str(r.id),
                action_text=r.action_text,
                priority=r.priority.value if hasattr(r.priority, "value") else str(r.priority),
                category=r.category,
                expected_impact=r.expected_impact,
                is_implemented=bool(r.is_implemented),
                created_at=r.created_at,
            )
            for r in persisted_recs
        ],
        alert_created=alert_created,
    )


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=ProjectRecommendationsListResponse,
    tags=["AI Recommendations & Alerts"],
)
def get_project_recommendations(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all stored administrative recommendations and action directives for a project."""
    proj = get_project_or_404(db, project_id)

    recs = (
        db.query(Recommendation)
        .filter(Recommendation.project_id == proj.id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    return ProjectRecommendationsListResponse(
        project_id=str(proj.id),
        project_code=proj.project_code,
        total_recommendations=len(recs),
        recommendations=[
            RecommendationItem(
                id=str(r.id),
                action_text=r.action_text,
                priority=r.priority.value if hasattr(r.priority, "value") else str(r.priority),
                category=r.category,
                expected_impact=r.expected_impact,
                is_implemented=bool(r.is_implemented),
                created_at=r.created_at,
            )
            for r in recs
        ],
    )
